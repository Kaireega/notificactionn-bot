#!/usr/bin/env python3
"""
Telegram Chat ID Helper Script
This script helps you get your correct Telegram chat ID for the trading bot.
"""

import os
import asyncio
from dotenv import load_dotenv
import httpx

async def get_telegram_chat_id():
    """Get the user's Telegram chat ID."""
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    current_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        return
    
    print(f"🤖 Bot Token: {bot_token}")
    print(f"📱 Current Chat ID: {current_chat_id}")
    print("\n" + "="*50)
    print("🔧 GETTING YOUR TELEGRAM CHAT ID")
    print("="*50)
    
    # Step 1: Check if bot exists
    print("\n1️⃣ Checking bot status...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"https://api.telegram.org/bot{bot_token}/getMe")
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    bot_name = bot_info['result']['username']
                    print(f"✅ Bot found: @{bot_name}")
                    print(f"📝 Bot name: {bot_info['result']['first_name']}")
                else:
                    print("❌ Bot token is invalid")
                    return
            else:
                print("❌ Failed to get bot info")
                return
        except Exception as e:
            print(f"❌ Error checking bot: {e}")
            return
    
    # Step 2: Get updates
    print("\n2️⃣ Getting recent messages...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"https://api.telegram.org/bot{bot_token}/getUpdates")
            if response.status_code == 200:
                updates = response.json()
                if updates.get('ok'):
                    results = updates.get('result', [])
                    if results:
                        print(f"✅ Found {len(results)} recent messages")
                        print("\n📋 Recent chats:")
                        chat_ids = set()
                        for update in results:
                            if 'message' in update:
                                chat = update['message']['chat']
                                chat_id = chat['id']
                                chat_type = chat['type']
                                chat_title = chat.get('title', chat.get('first_name', 'Unknown'))
                                chat_ids.add(chat_id)
                                print(f"   • Chat ID: {chat_id} | Type: {chat_type} | Name: {chat_title}")
                        
                        if chat_ids:
                            print(f"\n🎯 Recommended Chat ID: {list(chat_ids)[0]}")
                            print("\n📝 Update your .env file with:")
                            print(f"TELEGRAM_CHAT_ID={list(chat_ids)[0]}")
                        else:
                            print("❌ No chat messages found")
                    else:
                        print("❌ No recent messages found")
                        print("\n💡 To get your chat ID:")
                        print("1. Start a chat with your bot @{bot_name}")
                        print("2. Send any message to the bot")
                        print("3. Run this script again")
                else:
                    print("❌ Failed to get updates")
            else:
                print("❌ Failed to get updates")
        except Exception as e:
            print(f"❌ Error getting updates: {e}")

if __name__ == "__main__":
    print("🚀 Telegram Chat ID Helper")
    print("This will help you get the correct chat ID for your trading bot notifications")
    print()
    asyncio.run(get_telegram_chat_id()) 