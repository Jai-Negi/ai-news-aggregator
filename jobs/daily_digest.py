"""
Daily Digest Job

Automated job that runs daily at 8 AM.

This script:
1. Fetches new content (last 24 hours)
2. Processes with AI
3. Generates digest
4. Sends to ALL active subscribers

Usage:
    python3 jobs/daily_digest.py
    
Cron (8 AM daily):
    0 8 * * * cd /path/to/project && /path/to/venv/bin/python3 jobs/daily_digest.py >> logs/daily.log 2>&1
"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from main import create_app
from app.agents import ContentFetcherAgent, ContentProcessorAgent, DigestGeneratorAgent
from app.services import ResendService
from app.api.validation import SubscriberValidator

app = create_app()

def log(message):
    """Print with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def main():
    with app.app_context():
        log("=" * 70)
        log("Daily AI News Digest Pipeline Starting")
        log("=" * 70)
        
        # Check subscribers
        log("")
        log("STEP 0: Checking subscribers...")
        
        active_subscribers = SubscriberValidator.get_all_active()
        
        if not active_subscribers:
            log("⚠️  No active subscribers")
            log("   Add subscribers: python3 scripts/add_subscriber.py")
            log("")
            log("Pipeline stopped")
            return 0
        
        log(f"  Active subscribers: {len(active_subscribers)}")
        for sub in active_subscribers:
            log(f"    • {sub.email}")
        
        # Fetch content
        log("")
        log("STEP 1: Fetching content...")
        
        fetcher = ContentFetcherAgent()
        fetch_results = fetcher.fetch_all(hours_back=24)
        
        log(f"  Fetched: {fetch_results['total_fetched']}")
        log(f"  New: {fetch_results['total_saved']}")
        
        if fetch_results['total_saved'] == 0:
            log("")
            log("⚠️  No new content")
            log("  Will try again tomorrow")
            return 0
        
        # Process with AI
        log("")
        log("STEP 2: Processing with AI...")
        
        processor = ContentProcessorAgent()
        process_results = processor.process_all(limit=50)
        
        log(f"  Processed: {process_results['processed']}")
        
        if process_results['processed'] == 0:
            log("⚠️  No articles processed")
            return 1
        
        # Generate digest
        log("")
        log("STEP 3: Generating digest...")
        
        generator = DigestGeneratorAgent()
        stats = generator.get_stats()
        
        log(f"  Available: {stats.get('available_for_digest', 0)}")
        
        if stats.get('available_for_digest', 0) == 0:
            log("⚠️  No articles available")
            return 0
        
        html = generator.generate_digest(max_articles=10, min_quality=5)
        
        if not html:
            log("❌ Failed to generate digest")
            return 1
        
        log("✅ Digest generated")
        
        # Send to subscribers
        log("")
        log("STEP 4: Sending emails...")
        
        resend = ResendService()
        sent = 0
        failed = 0
        
        for sub in active_subscribers:
            log(f"  → {sub.email}")
            success = resend.send_digest(to=sub.email, html=html)
            
            if success:
                sent += 1
                sub.last_digest_sent = datetime.utcnow()
                sub.total_digests_sent += 1
            else:
                failed += 1
        
        from app.models import db
        db.session.commit()
        
        # Summary
        log("")
        log("=" * 70)
        log("✅ Pipeline complete!")
        log("=" * 70)
        log(f"  Sent: {sent}/{len(active_subscribers)}")
        if failed > 0:
            log(f"  Failed: {failed}")
        log("=" * 70)
        
        return 0 if sent > 0 else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
