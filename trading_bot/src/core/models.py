"""
Core data models for the Market Adaptive Trading Bot.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
import uuid


class MarketCondition(Enum):
    """Market condition types."""
    NEWS_REACTIONARY = "news_reactionary"
    REVERSAL = "reversal"
    BREAKOUT = "breakout"
    RANGING = "ranging"
    UNKNOWN = "unknown"


class TradeSignal(Enum):
    """Trade signal types."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class TimeFrame(Enum):
    """Trading timeframes."""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


@dataclass
class CandleData:
    """OHLCV candle data."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Optional[Decimal] = None
    pair: str = ""
    timeframe: TimeFrame = TimeFrame.M5
    
    def __post_init__(self):
        if isinstance(self.open, (int, float)):
            self.open = Decimal(str(self.open))
        if isinstance(self.high, (int, float)):
            self.high = Decimal(str(self.high))
        if isinstance(self.low, (int, float)):
            self.low = Decimal(str(self.low))
        if isinstance(self.close, (int, float)):
            self.close = Decimal(str(self.close))
        if self.volume and isinstance(self.volume, (int, float)):
            self.volume = Decimal(str(self.volume))


@dataclass
class TechnicalIndicators:
    """Technical analysis indicators."""
    # Core indicators
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    ema_fast: Optional[float] = None
    ema_slow: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    
    # Keltner Channels from custom indicators
    keltner_upper: Optional[float] = None
    keltner_lower: Optional[float] = None
    keltner_middle: Optional[float] = None
    
    # Bollinger Bands components
    bb_ma: Optional[float] = None  # Bollinger Bands Moving Average
    
    # RSI with period
    rsi_14: Optional[float] = None  # RSI with 14-period
    
    # MACD components
    macd_line: Optional[float] = None  # MACD line
    macd_signal_line: Optional[float] = None  # Signal line
    macd_histogram_line: Optional[float] = None  # Histogram


@dataclass
class MarketContext:
    """Market context and sentiment data."""
    condition: MarketCondition = MarketCondition.UNKNOWN
    volatility: float = 0.0
    trend_strength: float = 0.0
    news_sentiment: float = 0.0
    economic_events: List[Dict[str, Any]] = field(default_factory=list)
    key_levels: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TradeRecommendation:
    """AI-generated trade recommendation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pair: str = ""
    signal: TradeSignal = TradeSignal.HOLD
    entry_price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    confidence: float = 0.0
    market_condition: MarketCondition = MarketCondition.UNKNOWN
    reasoning: str = ""
    risk_reward_ratio: float = 0.0
    estimated_hold_time: timedelta = timedelta(minutes=30)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    technical_analysis: Optional[TechnicalIndicators] = None
    market_context: Optional[MarketContext] = None
    
    def __post_init__(self):
        if isinstance(self.entry_price, (int, float)):
            self.entry_price = Decimal(str(self.entry_price))
        if isinstance(self.stop_loss, (int, float)):
            self.stop_loss = Decimal(str(self.stop_loss))
        if isinstance(self.take_profit, (int, float)):
            self.take_profit = Decimal(str(self.take_profit))


@dataclass
class TradeDecision:
    """Final trade decision after risk management."""
    recommendation: TradeRecommendation
    approved: bool = False
    position_size: Optional[Decimal] = None
    risk_amount: Optional[Decimal] = None
    modified_stop_loss: Optional[Decimal] = None
    modified_take_profit: Optional[Decimal] = None
    risk_management_notes: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class NotificationMessage:
    """Notification message structure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    message: str = ""
    trade_decision: Optional[TradeDecision] = None
    chart_data: Optional[Dict[str, Any]] = None
    buttons: List[Dict[str, str]] = field(default_factory=list)
    priority: str = "normal"  # low, normal, high, urgent
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UserResponse:
    """User response to trade notification."""
    notification_id: str
    action: str  # accept, edit, deny
    user_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modified_params: Optional[Dict[str, Any]] = None
    notes: str = ""


@dataclass
class TradeExecution:
    """Trade execution details."""
    trade_decision: TradeDecision
    execution_price: Decimal
    execution_time: datetime
    trade_id: Optional[str] = None
    broker_response: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, filled, cancelled, rejected
    
    def __post_init__(self):
        if isinstance(self.execution_price, (int, float)):
            self.execution_price = Decimal(str(self.execution_price))


@dataclass
class PerformanceMetrics:
    """Trading performance metrics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_profit: Decimal = Decimal('0')
    total_loss: Decimal = Decimal('0')
    net_profit: Decimal = Decimal('0')
    max_drawdown: Decimal = Decimal('0')
    sharpe_ratio: float = 0.0
    average_win: Decimal = Decimal('0')
    average_loss: Decimal = Decimal('0')
    profit_factor: float = 0.0
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        if isinstance(self.total_profit, (int, float)):
            self.total_profit = Decimal(str(self.total_profit))
        if isinstance(self.total_loss, (int, float)):
            self.total_loss = Decimal(str(self.total_loss))
        if isinstance(self.net_profit, (int, float)):
            self.net_profit = Decimal(str(self.net_profit))
        if isinstance(self.max_drawdown, (int, float)):
            self.max_drawdown = Decimal(str(self.max_drawdown))
        if isinstance(self.average_win, (int, float)):
            self.average_win = Decimal(str(self.average_win))
        if isinstance(self.average_loss, (int, float)):
            self.average_loss = Decimal(str(self.average_loss)) 