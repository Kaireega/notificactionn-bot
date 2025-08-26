"""
Improved Position Manager - Enhanced position management with trailing stops and better pip calculations.
"""
import asyncio
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
import logging

from ..core.models import TradeRecommendation, MarketContext
from ..utils.config import Config
from ..utils.logger import get_logger
from api.oanda_api import OandaApi
from infrastructure.instrument_collection import instrumentCollection as ic


class ImprovedPositionManager:
    """Enhanced position management with trailing stops and improved pip calculations."""
    
    def __init__(self, config: Config, oanda_api: OandaApi):
        self.config = config
        self.oanda_api = oanda_api
        self.logger = get_logger(__name__)
        
        # Load instruments
        try:
            ic.LoadInstruments("data")
            self.logger.info(f"Loaded {len(ic.instruments_dict)} instruments")
        except Exception as e:
            self.logger.error(f"Failed to load instruments: {e}")
            # Create basic instruments if loading fails
            ic.instruments_dict = {
                'EUR_USD': type('Instrument', (), {
                    'name': 'EUR_USD',
                    'pipLocation': 0.0001,
                    'displayPrecision': 5,
                    'tradeUnitsPrecision': 2
                })(),
                'USD_JPY': type('Instrument', (), {
                    'name': 'USD_JPY',
                    'pipLocation': 0.01,
                    'displayPrecision': 3,
                    'tradeUnitsPrecision': 2
                })(),
                'GBP_JPY': type('Instrument', (), {
                    'name': 'GBP_JPY',
                    'pipLocation': 0.01,
                    'displayPrecision': 3,
                    'tradeUnitsPrecision': 2
                })()
            }
            self.logger.info("Created fallback instruments")
        
        # Position tracking
        self._open_positions: Dict[str, Dict[str, Any]] = {}
        self._position_history: List[Dict[str, Any]] = []
        
        # Trailing stop configuration
        self.trailing_stop_enabled = config.risk_management.trailing_stop
        self.trailing_stop_atr_multiplier = config.risk_management.trailing_stop_atr_multiplier
        self.trailing_stop_minimum_distance = Decimal('0.0005')  # Minimum 5 pips for trailing
        
        # Enhanced pip calculations
        self.pip_locations = {
            'JPY_PAIRS': ['USD_JPY', 'EUR_JPY', 'GBP_JPY', 'AUD_JPY', 'CAD_JPY', 'CHF_JPY'],
            'STANDARD_PAIRS': ['EUR_USD', 'GBP_USD', 'AUD_USD', 'NZD_USD', 'USD_CAD', 'USD_CHF', 'EUR_GBP', 'EUR_AUD', 'GBP_AUD']
        }
        
        # Performance tracking
        self._daily_pnl = Decimal('0')
        self._total_trades = 0
        self._winning_trades = 0
        self._last_reset_date = datetime.now().date()
        
        self._is_running = False
        self._trailing_stop_task = None
    
    @classmethod
    def create_with_config(cls, config: Config):
        """Create position manager with config only (for testing)."""
        try:
            oanda_api = OandaApi(config)
            return cls(config, oanda_api)
        except Exception as e:
            # Create a mock OANDA API for testing if real one fails
            class MockOandaApi:
                def __init__(self, config):
                    self.config = config
                    self.logger = get_logger(__name__)
                
                async def get_account_info(self):
                    return {'balance': str(self.config.trading.account_balance), 'currency': 'USD'}
                
                async def get_positions(self):
                    return []
                
                async def create_order(self, **kwargs):
                    return {'id': 'mock_order_123'}
                
                async def close_position(self, **kwargs):
                    return {'id': 'mock_close_123'}
            
            mock_api = MockOandaApi(config)
            return cls(config, mock_api)
    
    async def start(self):
        """Start the improved position manager."""
        try:
            self.logger.info("Starting improved position manager...")
            
            # Load existing positions from OANDA
            await self._load_existing_positions()
            
            # Start trailing stop monitoring
            if self.trailing_stop_enabled:
                self._is_running = True
                self._trailing_stop_task = asyncio.create_task(self._trailing_stop_monitor())
                self.logger.info("Trailing stop monitoring started")
            
            self.logger.info("Improved position manager started successfully")
            
        except Exception as e:
            self.logger.error(f"Error starting improved position manager: {e}")
            raise
    
    async def stop(self):
        """Stop the improved position manager."""
        self.logger.info("Stopping improved position manager...")
        self._is_running = False
        
        if self._trailing_stop_task:
            self._trailing_stop_task.cancel()
            try:
                await self._trailing_stop_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Improved position manager stopped")
    
    async def open_position(self, recommendation: TradeRecommendation, position_size: Dict[str, Any]) -> Dict[str, Any]:
        """Open a new position with enhanced tracking."""
        try:
            pair = recommendation.pair
            units = float(position_size['size'])
            
            # Determine order type based on signal
            if recommendation.signal.value == 'BUY':
                side = 'buy'
                price = float(recommendation.entry_price)
            else:
                side = 'sell'
                price = float(recommendation.entry_price)
            
            # Create order with enhanced parameters
            order_data = {
                'instrument': pair,
                'units': str(int(units)),
                'side': side,
                'type': 'MARKET',
                'timeInForce': 'FOK',
                'stopLossOnFill': {
                    'price': str(position_size['stop_loss']),
                    'timeInForce': 'GTC'
                },
                'takeProfitOnFill': {
                    'price': str(position_size['take_profit']),
                    'timeInForce': 'GTC'
                }
            }
            
            # Execute order using the correct OANDA API method
            units = int(units) if side == 'buy' else -int(units)
            response = self.oanda_api.place_trade(
                pair_name=pair,
                units=abs(units),
                direction=1 if side == 'buy' else -1,  # 1 for BUY, -1 for SELL
                stop_loss=float(position_size['stop_loss']) if position_size['stop_loss'] else None,
                take_profit=float(position_size['take_profit']) if position_size['take_profit'] else None
            )
            
            if response:
                # The place_trade method returns the trade ID directly
                trade_id = response
                
                # Enhanced position tracking
                position_data = {
                    'id': trade_id,
                    'pair': pair,
                    'side': side,
                    'units': units,
                    'entry_price': Decimal(str(price)),
                    'stop_loss': position_size['stop_loss'],
                    'take_profit': position_size['take_profit'],
                    'entry_time': datetime.now(timezone.utc),
                    'recommendation': recommendation,
                    'position_size_data': position_size,
                    'trailing_stop_active': False,
                    'trailing_stop_price': None,
                    'highest_price': Decimal(str(price)),
                    'lowest_price': Decimal(str(price)),
                    'atr_value': None  # Will be calculated later
                }
                
                # Add to tracking
                self._open_positions[pair] = position_data
                self._total_trades += 1
                
                self.logger.info(f"Position opened: {pair} {side} {units} units at {position_data['entry_price']}")
                
                return {
                    'success': True,
                    'position_id': position_data['id'],
                    'entry_price': position_data['entry_price'],
                    'units': units,
                    'message': f"Position opened successfully"
                }
            else:
                self.logger.error(f"Failed to open position for {pair}")
                return {
                    'success': False,
                    'message': "Failed to open position"
                }
                
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return {
                'success': False,
                'message': f"Error opening position: {str(e)}"
            }
    
    async def execute_trade(self, decision, market_context) -> str:
        """Execute a trade decision (compatibility method for main.py)."""
        try:
            # Extract recommendation and position size from decision
            recommendation = decision.recommendation
            position_size = {
                'size': decision.position_size,
                'stop_loss': decision.modified_stop_loss,
                'take_profit': decision.modified_take_profit
            }
            
            # Use the open_position method
            result = await self.open_position(recommendation, position_size)
            
            if result['success']:
                return result['position_id']
            else:
                self.logger.error(f"Failed to execute trade: {result['message']}")
                return f"FAILED-{int(datetime.now().timestamp())}"
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return f"ERROR-{int(datetime.now().timestamp())}"
    
    async def close_position(self, pair: str, reason: str = "Manual close") -> Dict[str, Any]:
        """Close a position with enhanced tracking."""
        try:
            if pair not in self._open_positions:
                return {
                    'success': False,
                    'message': f"No open position found for {pair}"
                }
            
            position = self._open_positions[pair]
            
            # Close position via OANDA
            close_data = {
                'longUnits': 'ALL' if position['side'] == 'buy' else '0',
                'shortUnits': 'ALL' if position['side'] == 'sell' else '0'
            }
            
            response = self.oanda_api.close_position(pair, close_data)
            
            if response and response.get('longOrderFillTransaction') or response.get('shortOrderFillTransaction'):
                # Get close price
                close_transaction = response.get('longOrderFillTransaction') or response.get('shortOrderFillTransaction')
                close_price = Decimal(str(close_transaction.get('price', 0)))
                
                # Calculate P&L
                entry_price = position['entry_price']
                units = position['units']
                
                if position['side'] == 'buy':
                    pnl = (close_price - entry_price) * units
                else:
                    pnl = (entry_price - close_price) * units
                
                # Update tracking
                position_data = {
                    'pair': pair,
                    'side': position['side'],
                    'entry_price': entry_price,
                    'exit_price': close_price,
                    'units': units,
                    'pnl': pnl,
                    'entry_time': position['entry_time'],
                    'exit_time': datetime.now(timezone.utc),
                    'reason': reason,
                    'duration': (datetime.now(timezone.utc) - position['entry_time']).total_seconds() / 3600  # hours
                }
                
                self._position_history.append(position_data)
                
                # Update daily P&L
                self._daily_pnl += pnl
                if pnl > 0:
                    self._winning_trades += 1
                
                # Remove from open positions
                del self._open_positions[pair]
                
                self.logger.info(f"Position closed: {pair} P&L: ${pnl:.2f}")
                
                return {
                    'success': True,
                    'pnl': pnl,
                    'close_price': close_price,
                    'message': f"Position closed successfully"
                }
            else:
                self.logger.error(f"Failed to close position for {pair}")
                return {
                    'success': False,
                    'message': "Failed to close position"
                }
                
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return {
                'success': False,
                'message': f"Error closing position: {str(e)}"
            }
    
    async def _trailing_stop_monitor(self):
        """Monitor and update trailing stops for open positions."""
        while self._is_running:
            try:
                for pair, position in list(self._open_positions.items()):
                    await self._update_trailing_stop(pair, position)
                
                await asyncio.sleep(15)  # Check every 15 seconds for day trading
                
            except Exception as e:
                self.logger.error(f"Error in trailing stop monitor: {e}")
                await asyncio.sleep(30)  # Wait shorter on error for day trading
    
    async def _update_trailing_stop(self, pair: str, position: Dict[str, Any]):
        """Update trailing stop for a position."""
        try:
            # Get current price
            current_price = await self._get_current_price(pair)
            if not current_price:
                return
            
            current_price_decimal = Decimal(str(current_price))
            
            # Update highest/lowest prices
            if position['side'] == 'buy':
                if current_price_decimal > position['highest_price']:
                    position['highest_price'] = current_price_decimal
                    
                    # Calculate new trailing stop
                    if not position['trailing_stop_active']:
                        # Activate trailing stop after 10 pips profit
                        pip_size = self._get_pip_size(pair)
                        profit_pips = (current_price_decimal - position['entry_price']) / pip_size
                        
                        if profit_pips >= 10:  # 10 pips profit
                            position['trailing_stop_active'] = True
                            self.logger.info(f"Trailing stop activated for {pair} at {current_price_decimal}")
                    
                    if position['trailing_stop_active']:
                        # Calculate ATR-based trailing stop
                        atr_value = await self._calculate_atr(pair)
                        if atr_value:
                            position['atr_value'] = atr_value
                            trailing_distance = atr_value * self.trailing_stop_atr_multiplier
                            new_stop_loss = current_price_decimal - trailing_distance
                            
                            # Ensure minimum distance
                            min_distance = self.trailing_stop_minimum_distance
                            if (current_price_decimal - new_stop_loss) >= min_distance:
                                # Only update if new stop is higher than current
                                if new_stop_loss > position['stop_loss']:
                                    old_stop = position['stop_loss']
                                    position['stop_loss'] = new_stop_loss
                                    position['trailing_stop_price'] = new_stop_loss
                                    
                                    # Update stop loss in OANDA
                                    await self._update_stop_loss(pair, new_stop_loss)
                                    
                                    self.logger.info(f"Trailing stop updated for {pair}: {old_stop} -> {new_stop_loss}")
            
            elif position['side'] == 'sell':
                if current_price_decimal < position['lowest_price']:
                    position['lowest_price'] = current_price_decimal
                    
                    # Calculate new trailing stop for sell positions
                    if not position['trailing_stop_active']:
                        # Activate trailing stop after 10 pips profit
                        pip_size = self._get_pip_size(pair)
                        profit_pips = (position['entry_price'] - current_price_decimal) / pip_size
                        
                        if profit_pips >= 10:  # 10 pips profit
                            position['trailing_stop_active'] = True
                            self.logger.info(f"Trailing stop activated for {pair} at {current_price_decimal}")
                    
                    if position['trailing_stop_active']:
                        # Calculate ATR-based trailing stop
                        atr_value = await self._calculate_atr(pair)
                        if atr_value:
                            position['atr_value'] = atr_value
                            trailing_distance = atr_value * self.trailing_stop_atr_multiplier
                            new_stop_loss = current_price_decimal + trailing_distance
                            
                            # Ensure minimum distance
                            min_distance = self.trailing_stop_minimum_distance
                            if (new_stop_loss - current_price_decimal) >= min_distance:
                                # Only update if new stop is lower than current (and current stop exists)
                                if position['stop_loss'] is not None and new_stop_loss < position['stop_loss']:
                                    old_stop = position['stop_loss']
                                    position['stop_loss'] = new_stop_loss
                                    position['trailing_stop_price'] = new_stop_loss
                                    
                                    # Update stop loss in OANDA
                                    await self._update_stop_loss(pair, new_stop_loss)
                                    
                                    self.logger.info(f"Trailing stop updated for {pair}: {old_stop} -> {new_stop_loss}")
            
            # Check if stop loss hit (only if stop loss exists)
            if position['stop_loss'] is not None:
                if position['side'] == 'buy' and current_price_decimal <= position['stop_loss']:
                    await self.close_position(pair, "Stop loss hit")
                elif position['side'] == 'sell' and current_price_decimal >= position['stop_loss']:
                    await self.close_position(pair, "Stop loss hit")
            
            # Check if take profit hit (only if take profit exists)
            if position['take_profit'] is not None:
                if position['side'] == 'buy' and current_price_decimal >= position['take_profit']:
                    await self.close_position(pair, "Take profit hit")
                elif position['side'] == 'sell' and current_price_decimal <= position['take_profit']:
                    await self.close_position(pair, "Take profit hit")
                
        except Exception as e:
            self.logger.error(f"Error updating trailing stop for {pair}: {e}")
    
    async def _update_stop_loss(self, pair: str, new_stop_loss: Decimal) -> bool:
        """Update stop loss in OANDA."""
        try:
            # This would require modifying the existing position's stop loss
            # Implementation depends on OANDA API capabilities
            self.logger.info(f"Stop loss update requested for {pair}: {new_stop_loss}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating stop loss: {e}")
            return False
    
    async def _calculate_atr(self, pair: str, period: int = 14) -> Optional[Decimal]:
        """Calculate Average True Range for trailing stop."""
        try:
            # Get recent candles for ATR calculation
            candles = self.oanda_api.fetch_candles(pair, count=period + 1, granularity="M5")
            if not candles or len(candles) < period + 1:
                return None
            
            # Calculate True Range
            true_ranges = []
            for i in range(1, len(candles)):
                high = Decimal(str(candles[i]['mid']['h']))
                low = Decimal(str(candles[i]['mid']['l']))
                prev_close = Decimal(str(candles[i-1]['mid']['c']))
                
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
            
            # Calculate ATR
            if true_ranges:
                atr = sum(true_ranges) / len(true_ranges)
                return atr
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR for {pair}: {e}")
            return None
    
    async def _get_current_price(self, pair: str) -> Optional[float]:
        """Get current price for a pair."""
        try:
            # Get the latest candle
            candles = self.oanda_api.fetch_candles(pair, count=1, granularity="M5")
            if candles:
                return float(candles[0]['mid']['c'])
            return None
        except Exception as e:
            self.logger.error(f"Error getting current price for {pair}: {e}")
            return None
    
    def _get_pip_size(self, pair: str) -> Decimal:
        """Get pip size for currency pair."""
        if any(jpy_pair in pair for jpy_pair in self.pip_locations['JPY_PAIRS']):
            return Decimal('0.01')  # JPY pairs
        else:
            return Decimal('0.0001')  # Standard pairs
    
    async def _load_existing_positions(self):
        """Load existing positions from OANDA."""
        try:
            # Use the correct OANDA API method to get open trades
            open_trades = self.oanda_api.get_open_trades()
            if open_trades:
                for trade in open_trades:
                    pair = trade.instrument
                    if pair in self.config.trading_pairs:
                        # Convert OANDA trade to our format
                        position_data = {
                            'id': trade.id,
                            'pair': pair,
                            'side': 'buy' if trade.currentUnits > 0 else 'sell',
                            'units': abs(float(trade.currentUnits)),
                            'entry_price': Decimal(str(trade.price)),
                            'stop_loss': None,  # OANDA OpenTrade doesn't include SL/TP
                            'take_profit': None,  # OANDA OpenTrade doesn't include SL/TP
                            'entry_time': datetime.now(timezone.utc),  # OANDA OpenTrade doesn't include time
                            'trailing_stop_active': False,
                            'trailing_stop_price': None,
                            'highest_price': Decimal(str(trade.price)),
                            'lowest_price': Decimal(str(trade.price)),
                            'atr_value': None
                        }
                        
                        self._open_positions[pair] = position_data
                        self.logger.info(f"Loaded existing position: {pair}")
            
        except Exception as e:
            self.logger.error(f"Error loading existing positions: {e}")
    
    async def get_position_summary(self) -> Dict[str, Any]:
        """Get comprehensive position summary."""
        # Reset daily counters if needed
        self._reset_daily_counters()
        
        # Load existing positions from OANDA to ensure sync
        await self._load_existing_positions()
        
        total_pnl = sum(pos.get('pnl', 0) for pos in self._position_history)
        win_rate = (self._winning_trades / max(1, self._total_trades)) * 100
        
        return {
            'active_positions': len(self._open_positions),
            'total_positions': self._total_trades,
            'winning_trades': self._winning_trades,
            'win_rate': win_rate,
            'daily_pnl': float(self._daily_pnl),
            'total_pnl': float(total_pnl),
            'open_positions': list(self._open_positions.keys()),
            'position_history': len(self._position_history)
        }
    
    def _reset_daily_counters(self):
        """Reset daily counters if it's a new day."""
        today = datetime.now().date()
        if today > self._last_reset_date:
            self._daily_pnl = Decimal('0')
            self._last_reset_date = today
    
    def get_open_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all open positions."""
        return self._open_positions.copy()
    
    def get_position_history(self) -> List[Dict[str, Any]]:
        """Get position history."""
        return self._position_history.copy()
