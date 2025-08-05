#!/usr/bin/env python3
"""
Test script for notifications
This script tests both Telegram and Email notifications to ensure they work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.config import Config
from src.notifications.notification_layer import NotificationLayer

async def test_notifications():
    """Test both Telegram and Email notifications."""
    print("🧪 Testing Notifications")
    print("=" * 50)
    
    # Load config
    config = Config()
    print(f"✅ Config loaded")
    
    # Initialize notification layer
    notification_layer = NotificationLayer(config)
    await notification_layer.start()
    print(f"✅ Notification layer started")
    
    # Test message
    test_message = """
🤖 **Trading Bot Test Notification**

This is a test message to verify that notifications are working correctly.

**Test Details:**
• Telegram: Should send to your bot
• Email: Should send to your email
• Time: {timestamp}

If you receive this message, your notifications are working! 🎉
"""
    
    print("\n📱 Testing Telegram...")
    try:
        await notification_layer.send_notification(
            message=test_message.format(timestamp="2025-07-31 04:30:00"),
            notification_type="STARTUP"
        )
        print("✅ Telegram test completed")
    except Exception as e:
        print(f"❌ Telegram test failed: {e}")
    
    print("\n📧 Testing Email...")
    try:
        await notification_layer.send_notification(
            message=test_message.format(timestamp="2025-07-31 04:30:00"),
            notification_type="STARTUP"
        )
        print("✅ Email test completed")
    except Exception as e:
        print(f"❌ Email test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("• Check your Telegram for the test message")
    print("• Check your email for the test message")
    print("• If you don't receive messages, check the error logs above")
    
    await notification_layer.close()

if __name__ == "__main__":
    print("🚀 Notification Test Script")
    print("This will test both Telegram and Email notifications")
    print()
    asyncio.run(test_notifications()) 