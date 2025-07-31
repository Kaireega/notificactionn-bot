"""
Notification Layer - Sends trade alerts via multiple channels.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from decimal import Decimal
import json
import base64
import io

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import plotly.graph_objects as go
import plotly.io as pio

from ..core.models import TradeDecision, NotificationMessage, UserResponse
from ..utils.config import Config
from ..utils.logger import get_logger
from .chart_generator import ChartGenerator


class NotificationLayer:
    """Handles sending trade notifications via multiple channels."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Initialize notification channels
        self._init_telegram()
        self._init_email()
        
        # Initialize chart generator
        self.chart_generator = ChartGenerator()
        
        # Notification tracking
        self._sent_notifications: Dict[str, NotificationMessage] = {}
        self._notification_queue: List[NotificationMessage] = []
        
        # Rate limiting
        self._last_notification_time: Dict[str, datetime] = {}
    
    def _init_telegram(self) -> None:
        """Initialize Telegram bot."""
        try:
            if self.config.telegram_enabled:
                self.telegram_bot = Bot(token=self.config.telegram_bot_token)
                self.logger.info("Telegram bot initialized")
            else:
                self.telegram_bot = None
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram bot: {e}")
            self.telegram_bot = None
    
    def _init_email(self) -> None:
        """Initialize email configuration."""
        try:
            if self.config.email_enabled:
                self.smtp_server = self.config.smtp_server
                self.smtp_port = self.config.smtp_port
                self.email_username = self.config.email_username
                self.email_password = self.config.email_password
                self.logger.info("Email configuration initialized")
            else:
                self.smtp_server = None
        except Exception as e:
            self.logger.error(f"Failed to initialize email configuration: {e}")
            self.smtp_server = None
    
    async def send_trade_alert(self, trade_decision: TradeDecision, chart_data: Optional[Dict] = None) -> bool:
        """Send trade alert notification."""
        
        try:
            # Create notification message
            notification = self._create_trade_notification(trade_decision, chart_data)
            
            # Add to queue
            self._notification_queue.append(notification)
            
            # Send notifications
            success = True
            
            if self.config.telegram_enabled and self.telegram_bot:
                telegram_success = await self._send_telegram_notification(notification)
                success = success and telegram_success
            
            if self.config.email_enabled and self.smtp_server:
                email_success = await self._send_email_notification(notification)
                success = success and email_success
            
            # Track sent notification
            if success:
                self._sent_notifications[notification.id] = notification
                self._last_notification_time[trade_decision.recommendation.pair] = datetime.utcnow()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending trade alert: {e}")
            return False
    
    def _create_trade_notification(
        self, 
        trade_decision: TradeDecision, 
        chart_data: Optional[Dict] = None
    ) -> NotificationMessage:
        """Create notification message from trade decision."""
        
        recommendation = trade_decision.recommendation
        
        # Create title
        title = f"🚨 {recommendation.signal.value.upper()} Signal: {recommendation.pair}"
        
        # Create message
        message = self._format_trade_message(trade_decision)
        
        # Create interactive buttons
        buttons = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"accept_{trade_decision.recommendation.id}"),
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{trade_decision.recommendation.id}"),
                InlineKeyboardButton("❌ Deny", callback_data=f"deny_{trade_decision.recommendation.id}")
            ]
        ]
        
        # Generate chart if requested
        chart_image = None
        if self.config.send_charts and chart_data:
            chart_image = self.chart_generator.generate_chart(chart_data)
        
        return NotificationMessage(
            title=title,
            message=message,
            trade_decision=trade_decision,
            chart_data=chart_data,
            buttons=buttons,
            priority="high" if recommendation.confidence > 0.8 else "normal"
        )
    
    def _format_trade_message(self, trade_decision: TradeDecision) -> str:
        """Format trade decision into readable message."""
        
        rec = trade_decision.recommendation
        
        message = f"""
🎯 **{rec.signal.value.upper()} Signal Detected**

📊 **Pair:** {rec.pair}
💰 **Entry Price:** {rec.entry_price:.5f if rec.entry_price else 'N/A'}
🛑 **Stop Loss:** {rec.stop_loss:.5f if rec.stop_loss else 'N/A'}
🎯 **Take Profit:** {rec.take_profit:.5f if rec.take_profit else 'N/A'}

📈 **Confidence:** {rec.confidence:.1%}
⚖️ **Risk/Reward:** {rec.risk_reward_ratio:.2f}
⏱️ **Hold Time:** {rec.estimated_hold_time}
🌍 **Market Condition:** {rec.market_condition.value.replace('_', ' ').title()}

💡 **AI Reasoning:**
{rec.reasoning}

🔒 **Risk Management:**
• Position Size: {trade_decision.position_size if trade_decision.position_size else 'N/A'}
• Risk Amount: {trade_decision.risk_amount if trade_decision.risk_amount else 'N/A'}
• Notes: {trade_decision.risk_management_notes}

⏰ **Timestamp:** {rec.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        return message.strip()
    
    async def _send_telegram_notification(self, notification: NotificationMessage) -> bool:
        """Send notification via Telegram."""
        
        try:
            # Create inline keyboard
            keyboard = InlineKeyboardMarkup(notification.buttons)
            
            # Send message
            await self.telegram_bot.send_message(
                chat_id=self.config.telegram_chat_id,
                text=notification.message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
            # Send chart if available
            if notification.chart_data and self.config.send_charts:
                chart_image = self.chart_generator.generate_chart(notification.chart_data)
                if chart_image:
                    await self.telegram_bot.send_photo(
                        chat_id=self.config.telegram_chat_id,
                        photo=chart_image,
                        caption=f"📊 Chart for {notification.trade_decision.recommendation.pair}"
                    )
            
            self.logger.info(f"Telegram notification sent for {notification.trade_decision.recommendation.pair}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram notification: {e}")
            return False
    
    async def _send_email_notification(self, notification: NotificationMessage) -> bool:
        """Send notification via email."""
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.title
            msg['From'] = self.email_username
            msg['To'] = self.config.email_username  # Send to self for now
            
            # Create HTML version
            html_message = self._create_html_email(notification)
            html_part = MIMEText(html_message, 'html')
            msg.attach(html_part)
            
            # Create plain text version
            text_part = MIMEText(notification.message, 'plain')
            msg.attach(text_part)
            
            # Attach chart if available
            if notification.chart_data and self.config.send_charts:
                chart_image = self.chart_generator.generate_chart(notification.chart_data)
                if chart_image:
                    image_part = MIMEImage(chart_image)
                    image_part.add_header('Content-ID', '<chart>')
                    image_part.add_header('Content-Disposition', 'inline', filename='chart.png')
                    msg.attach(image_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_username, self.email_password)
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent for {notification.trade_decision.recommendation.pair}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
            return False
    
    def _create_html_email(self, notification: NotificationMessage) -> str:
        """Create HTML version of email."""
        
        rec = notification.trade_decision.recommendation
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .signal {{ font-size: 24px; font-weight: bold; color: {'#28a745' if rec.signal.value == 'buy' else '#dc3545'}; }}
                .details {{ margin: 20px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .label {{ font-weight: bold; }}
                .reasoning {{ background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .buttons {{ margin: 20px 0; }}
                .button {{ display: inline-block; padding: 10px 20px; margin: 5px; text-decoration: none; border-radius: 5px; }}
                .accept {{ background-color: #28a745; color: white; }}
                .edit {{ background-color: #ffc107; color: black; }}
                .deny {{ background-color: #dc3545; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="signal">{rec.signal.value.upper()} Signal: {rec.pair}</div>
                <p>AI-powered trading recommendation</p>
            </div>
            
            <div class="details">
                <div class="detail-row">
                    <span class="label">Entry Price:</span>
                    <span>{rec.entry_price:.5f if rec.entry_price else 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Stop Loss:</span>
                    <span>{rec.stop_loss:.5f if rec.stop_loss else 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Take Profit:</span>
                    <span>{rec.take_profit:.5f if rec.take_profit else 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Confidence:</span>
                    <span>{rec.confidence:.1%}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Risk/Reward:</span>
                    <span>{rec.risk_reward_ratio:.2f}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Market Condition:</span>
                    <span>{rec.market_condition.value.replace('_', ' ').title()}</span>
                </div>
            </div>
            
            <div class="reasoning">
                <h3>AI Reasoning:</h3>
                <p>{rec.reasoning}</p>
            </div>
            
            <div class="buttons">
                <a href="mailto:?subject=Accept Trade {rec.id}&body=I accept this trade recommendation" class="button accept">✅ Accept</a>
                <a href="mailto:?subject=Edit Trade {rec.id}&body=I want to edit this trade" class="button edit">✏️ Edit</a>
                <a href="mailto:?subject=Deny Trade {rec.id}&body=I deny this trade recommendation" class="button deny">❌ Deny</a>
            </div>
            
            <p><small>Timestamp: {rec.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</small></p>
        </body>
        </html>
        """
        
        return html
    
    async def send_daily_summary(self, performance_metrics: Any) -> bool:
        """Send daily performance summary."""
        
        try:
            title = "📊 Daily Trading Summary"
            message = self._format_daily_summary(performance_metrics)
            
            notification = NotificationMessage(
                title=title,
                message=message,
                priority="normal"
            )
            
            success = True
            
            if self.config.telegram_enabled and self.telegram_bot:
                await self.telegram_bot.send_message(
                    chat_id=self.config.telegram_chat_id,
                    text=notification.message,
                    parse_mode='Markdown'
                )
            
            if self.config.email_enabled and self.smtp_server:
                await self._send_email_notification(notification)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
            return False
    
    def _format_daily_summary(self, metrics: Any) -> str:
        """Format daily performance metrics."""
        
        message = f"""
📊 **Daily Trading Summary**

📈 **Performance:**
• Total Trades: {metrics.total_trades}
• Winning Trades: {metrics.winning_trades}
• Losing Trades: {metrics.losing_trades}
• Win Rate: {metrics.win_rate:.1%}

💰 **P&L:**
• Total Profit: {metrics.total_profit:.2f}
• Total Loss: {metrics.total_loss:.2f}
• Net Profit: {metrics.net_profit:.2f}
• Profit Factor: {metrics.profit_factor:.2f}

📉 **Risk Metrics:**
• Max Drawdown: {metrics.max_drawdown:.2f}
• Average Win: {metrics.average_win:.2f}
• Average Loss: {metrics.average_loss:.2f}
• Sharpe Ratio: {metrics.sharpe_ratio:.2f}

⏰ **Period:** {metrics.period_start.strftime('%Y-%m-%d')} to {metrics.period_end.strftime('%Y-%m-%d')}
"""
        
        return message.strip()
    
    async def send_error_alert(self, error_message: str, context: str = "") -> bool:
        """Send error alert notification."""
        
        try:
            title = "🚨 System Error Alert"
            message = f"""
🚨 **System Error Detected**

📍 **Context:** {context}
❌ **Error:** {error_message}
⏰ **Time:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please check the system logs for more details.
"""
            
            notification = NotificationMessage(
                title=title,
                message=message,
                priority="urgent"
            )
            
            success = True
            
            if self.config.telegram_enabled and self.telegram_bot:
                await self.telegram_bot.send_message(
                    chat_id=self.config.telegram_chat_id,
                    text=notification.message,
                    parse_mode='Markdown'
                )
            
            if self.config.email_enabled and self.smtp_server:
                await self._send_email_notification(notification)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending error alert: {e}")
            return False
    
    def can_send_notification(self, pair: str) -> bool:
        """Check if we can send a notification for this pair (rate limiting)."""
        
        if pair not in self._last_notification_time:
            return True
        
        time_since_last = datetime.utcnow() - self._last_notification_time[pair]
        return time_since_last.total_seconds() >= self.config.notification_cooldown
    
    async def close(self) -> None:
        """Close notification layer."""
        try:
            # Clear queues
            self._notification_queue.clear()
            self._sent_notifications.clear()
            
            self.logger.info("Notification layer closed")
        except Exception as e:
            self.logger.error(f"Error closing notification layer: {e}") 