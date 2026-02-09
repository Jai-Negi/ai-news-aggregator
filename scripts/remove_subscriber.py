"""
Remove Subscriber - CLI Tool

Unsubscribe an email address.

Usage:
    python3 scripts/remove_subscriber.py
"""

import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from main import create_app
from app.api.validation import SubscriberValidator

app = create_app()

def main():
    with app.app_context():
        print("=" * 60)
        print("Remove Subscriber")
        print("=" * 60)
        print()
        
        email = input("Enter email to unsubscribe: ").strip()
        
        if not email:
            print("❌ Email is required")
            return
        
        confirm = input(f"Unsubscribe {email}? (yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("Cancelled")
            return
        
        print()
        success, message = SubscriberValidator.remove_subscriber(email)
        
        print()
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        print()

if __name__ == '__main__':
    main()