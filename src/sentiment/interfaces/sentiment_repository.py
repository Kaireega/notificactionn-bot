#!/usr/bin/env python3
"""
Interface for sentiment data repository.
Follows Clean Code principles: Interface Segregation, Dependency Inversion.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from src.shared.models.sentiment_data import SentimentData

class SentimentRepository(ABC):
    """
    Abstract interface for sentiment data retrieval.
    
    This interface defines the contract that all sentiment data sources
    must implement, following the Interface Segregation Principle.
    """
    
    @abstractmethod
    def retrieve_sentiment_data(self) -> List[SentimentData]:
        """
        Retrieve sentiment data for all supported currency pairs.
        
        Returns:
            List of sentiment data for different currency pairs
            
        Raises:
            Exception: If sentiment data cannot be retrieved
        """
        pass
    
    @abstractmethod
    def retrieve_sentiment_for_pair(self, pair: str) -> Optional[SentimentData]:
        """
        Retrieve sentiment data for a specific currency pair.
        
        Args:
            pair: Currency pair identifier (e.g., 'EUR_USD')
            
        Returns:
            Sentiment data for the specified pair, or None if not available
        """
        pass
    
    @abstractmethod
    def get_supported_pairs(self) -> List[str]:
        """
        Get list of supported currency pairs.
        
        Returns:
            List of supported currency pair identifiers
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the sentiment data source is available.
        
        Returns:
            True if the source is available, False otherwise
        """
        pass
