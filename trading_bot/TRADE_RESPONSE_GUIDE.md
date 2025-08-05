# Trade Response Guide

## How to Respond to Trade Notifications

When you receive a trade notification from your trading bot, you can respond in several ways to accept, edit, or deny the trade.

## 📱 Notification Format

You'll receive a notification like this:

```
🚨 BUY Signal: EUR_USD

📊 Pair: EUR_USD
💰 Entry Price: 1.08500
🛑 Stop Loss: 1.08200
🎯 Take Profit: 1.08800

📈 Confidence: 85.0%
⚖️ Risk/Reward: 2.50
⏱️ Hold Time: 0:30:00
🌍 Market Condition: Breakout

💡 AI Reasoning:
The EUR/USD pair shows strong bullish momentum with RSI at 65 and MACD crossing above signal line. Price is breaking above resistance at 1.08450 with increasing volume.

🔒 Risk Management:
• Position Size: 1000
• Risk Amount: 50.00
• Notes: Standard risk management applied

⏰ Timestamp: 2024-01-15 14:30:00 UTC

[✅ Accept] [✏️ Edit] [❌ Deny]
```

## 🔄 Response Methods

### Method 1: Click Inline Buttons (Recommended)
Simply click one of the three buttons:
- **✅ Accept** - Accept the trade as-is
- **✏️ Edit** - Modify trade parameters
- **❌ Deny** - Reject the trade

### Method 2: Send Text Messages
You can also respond with text messages:

#### Accept a Trade
```
accept abc123
```

#### Deny a Trade
```
deny abc123
```

#### Edit a Trade
```
edit abc123 1.08100 1.08900 1500
```
Format: `edit [trade_id] [new_stop_loss] [new_take_profit] [new_position_size]`

## 📋 Response Examples

### Example 1: Accept Trade
**Input:** Click "✅ Accept" button
**Result:**
```
✅ Trade Accepted!

📊 Pair: EUR_USD
💰 Entry Price: 1.08500
🛑 Stop Loss: 1.08200
🎯 Take Profit: 1.08800
📈 Position Size: 1000

⏰ Executed: 2024-01-15 14:30:15 UTC

Trade is being executed...
```

### Example 2: Edit Trade
**Input:** Click "✏️ Edit" button, then modify parameters
**Result:**
```
✏️ Trade Modified and Accepted!

📊 Pair: EUR_USD
💰 Entry Price: 1.08500
🛑 Stop Loss: 1.08100 (modified)
🎯 Take Profit: 1.08900 (modified)
📈 Position Size: 1500 (modified)

⏰ Executed: 2024-01-15 14:30:15 UTC

Modified trade is being executed...
```

### Example 3: Deny Trade
**Input:** Click "❌ Deny" button
**Result:**
```
❌ Trade Denied

📊 Pair: EUR_USD
⏰ Denied: 2024-01-15 14:30:15 UTC

Trade has been cancelled.
```

## ⚠️ Important Notes

1. **Response Time**: You have a limited time to respond to trade notifications (typically 5-10 minutes)

2. **Trade ID**: Each trade has a unique ID (like `abc123`) that you can use in text responses

3. **Parameter Limits**: When editing trades, ensure your modifications are within reasonable limits:
   - Stop Loss: Should be closer to entry than Take Profit
   - Take Profit: Should be further from entry than Stop Loss
   - Position Size: Should not exceed your account risk limits

4. **Error Messages**: If you make an error, you'll receive a helpful error message explaining what went wrong

## 🔧 Troubleshooting

### "Trade not found or expired"
- The trade notification has expired
- Wait for the next trade signal

### "Invalid response format"
- Check your text message format
- Use: `accept [trade_id]`, `deny [trade_id]`, or `edit [trade_id] [sl] [tp] [size]`

### "Invalid edit format"
- When editing, provide all required parameters
- Format: `edit abc123 1.08100 1.08900 1500`

## 📞 Support

If you encounter issues with trade responses:
1. Check your Telegram bot is running
2. Verify your chat ID is correct
3. Ensure you have proper permissions
4. Contact support with error messages

## 🎯 Best Practices

1. **Quick Response**: Respond within 2-3 minutes for best execution
2. **Review Parameters**: Always check stop loss and take profit levels
3. **Risk Management**: Don't increase position size beyond your risk tolerance
4. **Market Conditions**: Consider current market volatility when editing parameters
5. **Documentation**: Keep track of your trade decisions for analysis

---

*This guide covers the basic trade response functionality. For advanced features, refer to the main documentation.* 