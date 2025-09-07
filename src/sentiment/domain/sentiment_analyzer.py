#!/usr/bin/env python3
"""
Domain service for sentiment analysis.
Follows Clean Code principles: Single Responsibility, Clear Naming, Business Logic Focus.
"""
from typing import List
from src.shared.models.sentiment_data import SentimentData, SentimentType

class SentimentAnalyzer:
    """
    Analyzes sentiment data to provide business insights.
    
    This class encapsulates the business logic for sentiment analysis,
    following the Single Responsibility Principle.
    """
    
    BULLISH_THRESHOLD: int = 10
    NEUTRAL_THRESHOLD: int = 5
    
    def calculate_sentiment_type(self, long_percentage: int, short_percentage: int) -> SentimentType:
        """
        Determine sentiment type based on long/short percentages.
        
        Args:
            long_percentage: Percentage of long positions
            short_percentage: Percentage of short positions
            
        Returns:
            SentimentType classification
            
        Raises:
            ValueError: If percentages don't sum to 100
        """
        if long_percentage + short_percentage != 100:
            raise ValueError(f"Percentages must sum to 100, got {long_percentage} + {short_percentage}")
        
        difference = long_percentage - short_percentage
        
        if difference > self.BULLISH_THRESHOLD:
            return SentimentType.BULLISH
        elif difference < -self.BULLISH_THRESHOLD:
            return SentimentType.BEARISH
        else:
            return SentimentType.NEUTRAL
    
    def calculate_overall_sentiment_score(self, sentiment_data: List[SentimentData]) -> float:
        """
        Calculate overall sentiment score from multiple pairs.
        
        Args:
            sentiment_data: List of sentiment data for different pairs
            
        Returns:
            Float between 0.0 (very bearish) and 1.0 (very bullish)
            
        Raises:
            ValueError: If sentiment_data is empty
        """
        if not sentiment_data:
            raise ValueError("Cannot calculate sentiment score from empty data")
        
        sentiment_scores = []
        for item in sentiment_data:
            if item.is_bullish:
                sentiment_scores.append(0.7)
            elif item.is_bearish:
                sentiment_scores.append(0.3)
            else:
                sentiment_scores.append(0.5)
        
        return sum(sentiment_scores) / len(sentiment_scores)
    
    def get_sentiment_summary(self, sentiment_data: List[SentimentData]) -> dict:
        """
        Generate summary statistics for sentiment data.
        
        Args:
            sentiment_data: List of sentiment data for different pairs
            
        Returns:
            Dictionary containing summary statistics
        """
        if not sentiment_data:
            return {
                'total_pairs': 0,
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0,
                'overall_score': 0.5
            }
        
        bullish_count = sum(1 for item in sentiment_data if item.is_bullish)
        bearish_count = sum(1 for item in sentiment_data if item.is_bearish)
        neutral_count = sum(1 for item in sentiment_data if item.is_neutral)
        
        return {
            'total_pairs': len(sentiment_data),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'overall_score': self.calculate_overall_sentiment_score(sentiment_data)
        }
