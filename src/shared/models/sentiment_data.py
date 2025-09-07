#!/usr/bin/env python3
"""
Domain model for sentiment data.
Follows Clean Code principles: Single Responsibility, Clear Naming, Immutability.
"""
from dataclasses import dataclass
from typing import Final
from enum import Enum

class SentimentType(Enum):
    """Enumeration of possible sentiment types."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

@dataclass(frozen=True)
class SentimentData:
    """
    Immutable sentiment data for a currency pair.
    
    Attributes:
        pair: Currency pair identifier (e.g., 'EUR_USD')
        sentiment: Sentiment classification
        long_percentage: Percentage of long positions (0-100)
        short_percentage: Percentage of short positions (0-100)
        source: Data source identifier
        timestamp: Unix timestamp when data was collected
    """
    pair: str
    sentiment: SentimentType
    long_percentage: int
    short_percentage: int
    source: str
    timestamp: float
    
    def __post_init__(self):
        """Validate data integrity after initialization."""
        self._validate_percentages()
        self._validate_pair_format()
    
    def _validate_percentages(self):
        """Ensure percentages are valid and sum to 100."""
        if not (0 <= self.long_percentage <= 100):
            raise ValueError(f"Long percentage must be between 0 and 100, got {self.long_percentage}")
        
        if not (0 <= self.short_percentage <= 100):
            raise ValueError(f"Short percentage must be between 0 and 100, got {self.short_percentage}")
        
        if self.long_percentage + self.short_percentage != 100:
            raise ValueError(f"Percentages must sum to 100, got {self.long_percentage} + {self.short_percentage}")
    
    def _validate_pair_format(self):
        """Ensure currency pair follows expected format."""
        if not self.pair or '_' not in self.pair:
            raise ValueError(f"Invalid pair format: {self.pair}. Expected format: 'EUR_USD'")
    
    @property
    def is_bullish(self) -> bool:
        """Check if sentiment is bullish."""
        return self.sentiment == SentimentType.BULLISH
    
    @property
    def is_bearish(self) -> bool:
        """Check if sentiment is bearish."""
        return self.sentiment == SentimentType.BEARISH
    
    @property
    def is_neutral(self) -> bool:
        """Check if sentiment is neutral."""
        return self.sentiment == SentimentType.NEUTRAL
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'pair': self.pair,
            'sentiment': self.sentiment.value,
            'long_percentage': self.long_percentage,
            'short_percentage': self.short_percentage,
            'source': self.source,
            'timestamp': self.timestamp
        }
