#!/usr/bin/env python3
"""
Configuration management utility.
Follows Clean Code principles: Single Responsibility, Clear Naming, Error Handling.
"""
import os
from typing import Optional

class ConfigurationManager:
    """
    Manages application configuration and environment variables.
    
    This class provides a clean interface for accessing configuration
    values, following the Single Responsibility Principle.
    """
    
    # Configuration keys
    OANDA_API_KEY = 'OANDA_API_KEY'
    OANDA_ACCOUNT_ID = 'OANDA_ACCOUNT_ID'
    OANDA_BASE_URL = 'OANDA_BASE_URL'
    OANDA_PRACTICE_MODE = 'OANDA_PRACTICE_MODE'
    
    # Default values
    DEFAULT_OANDA_BASE_URL = "https://api-fxtrade.oanda.com"
    DEFAULT_PRACTICE_BASE_URL = "https://api-fxpractice.oanda.com"
    
    @classmethod
    def get_oanda_api_key(cls) -> str:
        """
        Get OANDA API key from environment.
        
        Returns:
            OANDA API key
            
        Raises:
            ValueError: If API key is not set
        """
        api_key = os.getenv(cls.OANDA_API_KEY)
        if not api_key:
            raise ValueError(f"{cls.OANDA_API_KEY} environment variable not set")
        return api_key
    
    @classmethod
    def get_oanda_account_id(cls) -> str:
        """
        Get OANDA account ID from environment.
        
        Returns:
            OANDA account ID
            
        Raises:
            ValueError: If account ID is not set
        """
        account_id = os.getenv(cls.OANDA_ACCOUNT_ID)
        if not account_id:
            raise ValueError(f"{cls.OANDA_ACCOUNT_ID} environment variable not set")
        return api_key
    
    @classmethod
    def get_oanda_base_url(cls) -> str:
        """
        Get OANDA base URL from environment or use default.
        
        Returns:
            OANDA API base URL
        """
        return os.getenv(cls.OANDA_BASE_URL, cls.DEFAULT_OANDA_BASE_URL)
    
    @classmethod
    def is_practice_mode(cls) -> bool:
        """
        Check if running in practice mode.
        
        Returns:
            True if practice mode is enabled
        """
        practice_mode = os.getenv(cls.OANDA_PRACTICE_MODE, 'false').lower()
        return practice_mode in ('true', '1', 'yes', 'on')
    
    @classmethod
    def get_appropriate_base_url(cls) -> str:
        """
        Get the appropriate base URL based on practice mode setting.
        
        Returns:
            Appropriate OANDA API base URL
        """
        if cls.is_practice_mode():
            return cls.DEFAULT_PRACTICE_BASE_URL
        return cls.get_oanda_base_url()
    
    @classmethod
    def validate_configuration(cls) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If required configuration is missing
        """
        try:
            cls.get_oanda_api_key()
            cls.get_oanda_account_id()
            return True
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    @classmethod
    def get_configuration_summary(cls) -> dict:
        """
        Get a summary of current configuration.
        
        Returns:
            Dictionary containing configuration summary
        """
        try:
            config_valid = cls.validate_configuration()
        except ValueError:
            config_valid = False
            
        return {
            'oanda_api_key_set': bool(os.getenv(cls.OANDA_API_KEY)),
            'oanda_account_id_set': bool(os.getenv(cls.OANDA_ACCOUNT_ID)),
            'oanda_base_url': cls.get_oanda_base_url(),
            'practice_mode': cls.is_practice_mode(),
            'configuration_valid': config_valid
        }
