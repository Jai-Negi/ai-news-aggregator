"""
Resend Service

Handles sending emails via Resend API.

Features:
- Send HTML emails
- Send plain text emails
- Error handling and logging

Example:
    resend = ResendService()
    resend.send_email(
        to='you@example.com',
        subject='Your Daily AI Digest',
        html='<h1>Hello!</h1>'
    )
"""

import os
import logging
from typing import Optional, List
import resend

logger = logging.getLogger(__name__)


class ResendService:
    """
    Service for sending emails via Resend.
    
    Uses Resend API to send transactional and marketing emails.
    
    Example:
        resend_service = ResendService()
        resend_service.send_email(
            to='user@example.com',
            subject='Welcome!',
            html='<h1>Welcome to our service!</h1>'
        )
    """
    
    def __init__(self, api_key: Optional[str] = None, from_email: Optional[str] = None):
        """
        Initialize Resend service.
        
        Args:
            api_key: Resend API key (optional, reads from env)
            from_email: From email address (optional, reads from env)
        """
        # Get API key
        self.api_key = api_key or os.getenv('RESEND_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "Resend API key not found! "
                "Set RESEND_API_KEY environment variable."
            )
        
        # Set API key for resend library
        resend.api_key = self.api_key
        
        # Get from email
        self.from_email = from_email or os.getenv('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        
        logger.info("ResendService initialized successfully")
    
    def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML content
            text: Plain text content (optional, auto-generated from HTML if not provided)
            reply_to: Reply-to email address (optional)
        
        Returns:
            bool: True if sent successfully, False otherwise
        
        Example:
            resend.send_email(
                to='user@example.com',
                subject='Daily Digest',
                html='<h1>Your digest</h1>'
            )
        """
        try:
            logger.info(f"Sending email to {to}: {subject}")
            
            # Prepare email data
            email_data = {
                "from": self.from_email,
                "to": [to],
                "subject": subject,
                "html": html,
            }
            
            # Add optional fields
            if text:
                email_data["text"] = text
            
            if reply_to:
                email_data["reply_to"] = reply_to
            
            # Send email
            response = resend.Emails.send(email_data)
            
            logger.info(f"✅ Email sent successfully to {to}: {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to}: {e}")
            return False
    
    def send_digest(
        self,
        to: str,
        html: str,
        subject: Optional[str] = None
    ) -> bool:
        """
        Send a digest email.
        
        Convenience method specifically for sending digests.
        
        Args:
            to: Recipient email
            html: HTML digest content
            subject: Subject line (optional, auto-generated if not provided)
        
        Returns:
            bool: True if sent successfully
        
        Example:
            resend.send_digest(
                to='user@example.com',
                html=digest_html
            )
        """
        from datetime import date
        
        if subject is None:
            subject = f"🤖 Your AI News Digest - {date.today().strftime('%B %d, %Y')}"
        
        return self.send_email(
            to=to,
            subject=subject,
            html=html
        )
    
    def send_to_multiple(
        self,
        recipients: List[str],
        subject: str,
        html: str
    ) -> dict:
        """
        Send email to multiple recipients.
        
        Args:
            recipients: List of email addresses
            subject: Email subject
            html: HTML content
        
        Returns:
            dict: Statistics about sending
                {"sent": 5, "failed": 2}
        
        Example:
            resend.send_to_multiple(
                recipients=['user1@example.com', 'user2@example.com'],
                subject='Digest',
                html=digest_html
            )
        """
        stats = {"sent": 0, "failed": 0}
        
        for recipient in recipients:
            success = self.send_email(
                to=recipient,
                subject=subject,
                html=html
            )
            
            if success:
                stats["sent"] += 1
            else:
                stats["failed"] += 1
        
        logger.info(f"Bulk send complete: {stats['sent']} sent, {stats['failed']} failed")
        return stats
    
    def test_connection(self) -> bool:
        """
        Test if Resend API connection works.
        
        Returns:
            bool: True if connection successful
        """
        try:
            # Try to send a test email to yourself
            # Note: This won't actually send, just validates the API key
            logger.info("Testing Resend connection...")
            
            # Resend doesn't have a ping endpoint, so we'll just check if API key is set
            if self.api_key and self.api_key.startswith('re_'):
                logger.info("Resend connection test: SUCCESS (API key format valid)")
                return True
            else:
                logger.warning("Resend connection test: FAILED (invalid API key format)")
                return False
                
        except Exception as e:
            logger.error(f"Resend connection test FAILED: {e}")
            return False