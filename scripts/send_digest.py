from dotenv import load_dotenv
load_dotenv()

import os
from main import create_app
from app.agents import DigestGeneratorAgent
from app.services import ResendService

app = create_app()

with app.app_context():
    print("=== Send AI News Digest ===")
    print()
    
    # Get your email
    your_email = input("Enter YOUR email address: ")
    print()
    
    # Step 1: Generate digest
    print("Step 1: Generating digest...")
    generator = DigestGeneratorAgent()
    
    # Get stats first
    stats = generator.get_stats()
    print(f"  Available articles: {stats.get('available_for_digest', 0)}")
    print(f"  Average quality: {stats.get('avg_quality_available', 0)}/10")
    print()
    
    if stats.get('available_for_digest', 0) == 0:
        print("❌ No articles available for digest!")
        print()
        print("Run these first:")
        print("  1. python3 test_fetcher.py")
        print("  2. python3 test_processor.py")
        exit()
    
    # Generate the digest (NOT preview - this marks articles as included)
    html = generator.generate_digest(max_articles=10, min_quality=5)
    
    if not html:
        print("❌ Failed to generate digest")
        exit()
    
    print("✅ Digest generated!")
    print()
    
    # Step 2: Send email
    print(f"Step 2: Sending to {your_email}...")
    resend = ResendService()
    
    success = resend.send_digest(
        to=your_email,
        html=html
    )
    
    print()
    if success:
        print("=" * 60)
        print("🎉 SUCCESS! Your AI News Digest has been sent!")
        print("=" * 60)
        print()
        print(f"📧 Check your inbox: {your_email}")
        print()
        print("The digest includes:")
        print(f"  • {stats.get('available_for_digest', 0)} articles")
        print(f"  • AI-powered summaries")
        print(f"  • Quality ratings")
        print(f"  • Topic tags")
    else:
        print("❌ Failed to send email")
        print("Check the logs above for errors")
    
    print()
    print("Complete!")