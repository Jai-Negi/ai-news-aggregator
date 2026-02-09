"""
List Subscribers - CLI Tool

View all subscribers in the database.

Usage:
    python3 scripts/list_subscribers.py
"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from main import create_app
from app.api.validation import SubscriberValidator
from app.models import SubscriberStatus

app = create_app()

def main():
    with app.app_context():
        print("=" * 60)
        print("All Subscribers")
        print("=" * 60)
        print()
        
        subscribers = SubscriberValidator.get_all()
        
        if not subscribers:
            print("No subscribers found")
            print()
            print("Add subscribers using: python3 scripts/add_subscriber.py")
            return
        
        # Group by status
        active = [s for s in subscribers if s.status == SubscriberStatus.ACTIVE]
        inactive = [s for s in subscribers if s.status != SubscriberStatus.ACTIVE]
        
        # Show active
        print(f"Active Subscribers ({len(active)}):")
        print()
        if active:
            for i, sub in enumerate(active, 1):
                print(f"{i}. ✅ {sub.email}")
                print(f"   Joined: {sub.created_at.strftime('%Y-%m-%d')}")
                print(f"   Digests sent: {sub.total_digests_sent}")
                print()
        else:
            print("  (none)")
            print()
        
        # Show inactive
        if inactive:
            print(f"Inactive Subscribers ({len(inactive)}):")
            print()
            for i, sub in enumerate(inactive, 1):
                status_icon = "❌" if sub.status == SubscriberStatus.UNSUBSCRIBED else "⚠️"
                print(f"{i}. {status_icon} {sub.email} ({sub.status.value})")
            print()
        
        # Stats
        stats = SubscriberValidator.get_stats()
        print("=" * 60)
        print(f"Total: {stats['total']} | Active: {stats['active']} | Unsubscribed: {stats['unsubscribed']}")
        print("=" * 60)
        print()

if __name__ == '__main__':
    main()