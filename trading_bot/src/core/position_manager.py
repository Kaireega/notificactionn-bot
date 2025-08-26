"""
Position Management & Execution Layer - Real-time position monitoring and execution.
Uses existing OANDA API and trade management components.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from decimal import Decimal
import math

import sys
from pathlib import Path

# Add the project root to the path to import API modules
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.append(str(root_dir))

from api.oanda_api import OandaApi
from models.open_trade import OpenTrade
from ..core.models import TradeDecision, MarketContext, TimeFrame
from ..utils.config import Config
from ..utils.logger import get_logger


class PositionManager:
    """Real-time position monitoring and execution system."""
    
    def __init__(self, config: Config, oanda_api: OandaApi):
        self.config = config
        self.oanda_api = oanda_api
        self.logger = get_logger(__name__)
        
        # Position tracking
        self.active_positions: Dict[str, Dict[str, Any]] = {}
        self.position_history: List[Dict[str, Any]] = []
        self.scaling_levels: Dict[str, List[Dict[str, Any]]] = {}
        
        # Risk management
        self.max_daily_loss = config.risk_management.max_daily_loss
        self.max_open_trades = config.risk_management.max_open_trades
        self.daily_pnl = 0.0
        self.daily_trades = 0
        
        # Execution tracking
        self.execution_stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_slippage': 0.0,
            'avg_slippage': 0.0
        }
        
        # Monitoring task
        self._monitoring_task = None
        self._is_running = False
    
    async def start(self) -> None:
        """Start position monitoring."""
        print("💰 [DEBUG] Starting position manager...")
        self.logger.info("Starting position manager...")
        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._position_monitoring_loop())
        print("✅ [DEBUG] Position manager started successfully")
        self.logger.info("Position manager started successfully")
    
    async def stop(self) -> None:
        """Stop position monitoring."""
        self.logger.info("Stopping position manager...")
        self._is_running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Position manager stopped")
    
    async def execute_trade(self, decision: TradeDecision, market_context: MarketContext) -> Optional[str]:
        """Execute a trade based on the decision."""
        self.logger.info(f"📈 Starting trade execution for {decision.recommendation.pair}...")
        self.logger.info(
            f"🎯 {decision.recommendation.pair}: Signal: {decision.recommendation.signal.value}, Entry: {decision.recommendation.entry_price}"
        )
        
        try:
            # Check if we already have a position for this pair
            self.logger.info(f"🔍 {decision.recommendation.pair}: Checking existing positions...")
            existing_position = await self._get_existing_position(decision.recommendation.pair)
            
            if existing_position:
                self.logger.info(f"⚠️ {decision.recommendation.pair}: Found existing position, checking if we should close it...")
                should_close = await self._should_close_position(existing_position, decision, market_context)
                
                if should_close:
                    self.logger.info(f"🔄 {decision.recommendation.pair}: Closing existing position...")
                    close_result = await self._close_position(existing_position)
                    if close_result:
                        self.logger.info(f"✅ {decision.recommendation.pair}: Position closed successfully")
                    else:
                        self.logger.error(f"❌ {decision.recommendation.pair}: Failed to close position")
                        return None
                else:
                    self.logger.info(f"ℹ️ {decision.recommendation.pair}: Keeping existing position")
                    return existing_position['id']
            
            # Calculate position size
            self.logger.info(f"💰 {decision.recommendation.pair}: Calculating position size...")
            position_size = await self._calculate_position_size(decision, market_context)
            self.logger.info(f"💰 {decision.recommendation.pair}: Position size: {position_size}")
            
            # Respect live trade toggle
            if not self.config.notifications.live_trade_enabled:
                self.logger.warning("LIVE TRADE DISABLED - Dry run: order not sent to broker")
                trade_id = f"DRYRUN-{int(datetime.now(timezone.utc).timestamp())}"
                await self._record_trade(decision, trade_id, position_size)
                return trade_id

            # Execute the trade
            self.logger.info(f"🚀 {decision.recommendation.pair}: Executing trade...")
            trade_id = await self._execute_trade_order(decision, position_size)
            
            if trade_id:
                self.logger.info(f"✅ {decision.recommendation.pair}: Trade executed successfully, ID: {trade_id}")
                
                # Record the trade
                await self._record_trade(decision, trade_id, position_size)
                
                return trade_id
            else:
                self.logger.error(f"❌ {decision.recommendation.pair}: Trade execution failed")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error executing trade for {decision.recommendation.pair}: {e}")
            return None
    
    async def _can_execute_trade(self, decision: TradeDecision) -> bool:
        """Check if we can execute this trade based on risk management rules."""
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            self.logger.warning(f"Daily loss limit reached: ${self.daily_pnl:.2f}")
            return False
        
        # Check max open trades
        if len(self.active_positions) >= self.max_open_trades:
            self.logger.warning(f"Max open trades reached: {len(self.active_positions)}")
            return False
        
        # Check if we already have a position in this pair
        if decision.recommendation.pair in self.active_positions:
            self.logger.info(f"Already have position in {decision.recommendation.pair}")
            return False
        
        return True
    
    async def _calculate_optimal_entry(self, decision: TradeDecision) -> tuple[Decimal, float]:
        """Calculate optimal entry price with slippage consideration."""
        # Get current market prices
        prices = self.oanda_api.get_prices([decision.recommendation.pair])
        if not prices:
            return decision.recommendation.entry_price, 0.0
        
        current_price = Decimal(str(prices[0].close))
        target_price = decision.recommendation.entry_price
        
        # Calculate slippage (difference between target and current)
        slippage = abs(float(current_price - target_price))
        
        # Use current price as entry (market order)
        return current_price, slippage
    
    async def _track_new_position(self, trade_id: str, decision: TradeDecision, 
                                 entry_price: Decimal, slippage: float, 
                                 market_context: MarketContext) -> None:
        """Track a new position."""
        position_data = {
            'trade_id': trade_id,
            'pair': decision.recommendation.pair,
            'signal': decision.recommendation.signal.value,
            'entry_price': entry_price,
            'position_size': decision.position_size,
            'stop_loss': decision.modified_stop_loss,
            'take_profit': decision.modified_take_profit,
            'entry_time': datetime.now(timezone.utc),
            'market_context': market_context,
            'slippage': slippage,
            'scaling_levels': [],
            'partial_exits': []
        }
        
        self.active_positions[decision.recommendation.pair] = position_data
        self.execution_stats['total_trades'] += 1
        self.execution_stats['successful_trades'] += 1
        self.execution_stats['total_slippage'] += slippage
        self.execution_stats['avg_slippage'] = (
            self.execution_stats['total_slippage'] / self.execution_stats['successful_trades']
        )
    
    async def _position_monitoring_loop(self) -> None:
        """Main position monitoring loop."""
        while self._is_running:
            try:
                await self._update_all_positions()
                await self._check_scaling_opportunities()
                await self._check_partial_exits()
                await self._adjust_stop_losses()
                
                # Update daily P&L
                await self._update_daily_pnl()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in position monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _update_all_positions(self) -> None:
        """Update all active positions with current P&L."""
        open_trades = self.oanda_api.get_open_trades()
        if not open_trades:
            return
        
        for trade in open_trades:
            if trade.instrument in self.active_positions:
                position = self.active_positions[trade.instrument]
                position['current_price'] = Decimal(str(trade.price))
                position['unrealized_pl'] = float(trade.unrealizedPL)
                position['margin_used'] = float(trade.marginUsed)
                position['last_update'] = datetime.now(timezone.utc)
    
    async def _check_scaling_opportunities(self) -> None:
        """Check for position scaling opportunities."""
        for pair, position in self.active_positions.items():
            # Initialize scaling_levels if it doesn't exist
            if 'scaling_levels' not in position:
                position['scaling_levels'] = []
            
            if len(position['scaling_levels']) >= 3:  # Max 3 scaling levels
                continue
            
            # Check if price moved in our favor by 1R (risk-reward ratio)
            entry_price = position['entry_price']
            current_price = position.get('current_price', entry_price)
            stop_loss = position['stop_loss']
            
            if not stop_loss:
                continue
            
            # Calculate 1R move
            risk = abs(float(entry_price - stop_loss))
            if position['side'] == 'buy':
                target_price = entry_price + Decimal(str(risk))
                if current_price >= target_price:
                    await self._scale_into_position(pair, position, 'long')
            else:
                target_price = entry_price - Decimal(str(risk))
                if current_price <= target_price:
                    await self._scale_into_position(pair, position, 'short')
    
    async def _scale_into_position(self, pair: str, position: Dict[str, Any], direction: str) -> None:
        """Scale into an existing position."""
        try:
            # Calculate scaling size (50% of original position)
            scaling_size = position['position_size'] * 0.5
            
            # Execute scaling trade
            trade_id = self.oanda_api.place_trade(
                pair_name=pair,
                units=float(scaling_size),
                direction=1 if direction == 'long' else -1,
                stop_loss=float(position['stop_loss']) if position['stop_loss'] else None,
                take_profit=float(position['take_profit']) if position['take_profit'] else None
            )
            
            if trade_id:
                scaling_level = {
                    'trade_id': trade_id,
                    'size': scaling_size,
                    'entry_price': position.get('current_price', position['entry_price']),
                    'entry_time': datetime.now(timezone.utc)
                }
                
                position['scaling_levels'].append(scaling_level)
                self.logger.info(f"📈 Scaled into {pair}: Size={scaling_size:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error scaling into position {pair}: {e}")
    
    async def _check_partial_exits(self) -> None:
        """Check for partial profit taking opportunities."""
        for pair, position in self.active_positions.items():
            # Initialize partial_exits if it doesn't exist
            if 'partial_exits' not in position:
                position['partial_exits'] = []
            
            if len(position['partial_exits']) >= 3:  # Max 3 partial exits
                continue
            
            # Check profit targets (0.5R, 1R, 1.5R)
            entry_price = position['entry_price']
            current_price = position.get('current_price', entry_price)
            stop_loss = position['stop_loss']
            
            if not stop_loss:
                continue
            
            risk = abs(float(entry_price - stop_loss))
            profit_targets = [0.5, 1.0, 1.5]
            
            for target in profit_targets:
                if target in [exit['target'] for exit in position['partial_exits']]:
                    continue
                
                if position['side'] == 'buy':
                    target_price = entry_price + Decimal(str(risk * target))
                    if current_price >= target_price:
                        await self._partial_exit(pair, position, target)
                else:
                    target_price = entry_price - Decimal(str(risk * target))
                    if current_price <= target_price:
                        await self._partial_exit(pair, position, target)
    
    async def _partial_exit(self, pair: str, position: Dict[str, Any], target: float) -> None:
        """Execute partial profit taking."""
        try:
            # Close 30% of position at each target
            exit_size = position['position_size'] * 0.3
            
            # Get open trades for this pair
            open_trades = self.oanda_api.get_open_trades()
            pair_trades = [t for t in open_trades if t.instrument == pair]
            
            if pair_trades:
                # Close the oldest trade (original position)
                trade_id = pair_trades[0].id
                success = self.oanda_api.close_trade(trade_id)
                
                if success:
                    partial_exit = {
                        'trade_id': trade_id,
                        'size': exit_size,
                        'exit_price': position.get('current_price', position['entry_price']),
                        'target': target,
                        'exit_time': datetime.now(timezone.utc)
                    }
                    
                    position['partial_exits'].append(partial_exit)
                    self.logger.info(f"💰 Partial exit {pair}: Target={target}R, Size={exit_size:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error in partial exit {pair}: {e}")
    
    async def _adjust_stop_losses(self) -> None:
        """Dynamically adjust stop losses based on market conditions."""
        for pair, position in self.active_positions.items():
            # Only adjust if we have unrealized profit
            if position.get('unrealized_pl', 0) <= 0:
                continue
            
            # Move stop loss to breakeven after 0.5R profit
            entry_price = position['entry_price']
            current_price = position.get('current_price', entry_price)
            stop_loss = position['stop_loss']
            
            if not stop_loss:
                continue
            
            risk = abs(float(entry_price - stop_loss))
            profit = abs(float(current_price - entry_price))
            
            # Move to breakeven after 0.5R
            if profit >= risk * 0.5 and float(stop_loss) != float(entry_price):
                new_stop_loss = entry_price
                # Update stop loss in OANDA (this would require additional API call)
                self.logger.info(f"🔄 Moving stop loss to breakeven: {pair}")
    
    async def _update_daily_pnl(self) -> None:
        """Update daily P&L tracking."""
        total_pnl = 0.0
        
        for position in self.active_positions.values():
            total_pnl += position.get('unrealized_pl', 0)
        
        self.daily_pnl = total_pnl
    
    async def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions."""
        return {
            'active_positions': len(self.active_positions),
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'execution_stats': self.execution_stats,
            'positions': self.active_positions
        }
    
    async def close_all_positions(self) -> None:
        """Close all active positions."""
        self.logger.info("Closing all active positions...")
        
        for pair, position in self.active_positions.items():
            try:
                open_trades = self.oanda_api.get_open_trades()
                pair_trades = [t for t in open_trades if t.instrument == pair]
                
                for trade in pair_trades:
                    self.oanda_api.close_trade(trade.id)
                
                self.logger.info(f"Closed position: {pair}")
                
            except Exception as e:
                self.logger.error(f"Error closing position {pair}: {e}")
        
        self.active_positions.clear()
    
    async def _get_existing_position(self, pair: str) -> Optional[Dict[str, Any]]:
        """Get existing position for a pair."""
        try:
            # Check our local tracking first
            if pair in self.active_positions:
                return self.active_positions[pair]
            
            # Check OANDA API for open trades
            open_trades = self.oanda_api.get_open_trades()
            pair_trades = [t for t in open_trades if t.instrument == pair]
            
            if pair_trades:
                trade = pair_trades[0]  # Take the first trade for this pair
                position_data = {
                    'id': trade.id,
                    'pair': pair,
                    'side': trade.side,
                    'units': trade.units,
                    'entry_price': Decimal(str(trade.price)),
                    'stop_loss': Decimal(str(trade.stop_loss)) if trade.stop_loss else None,
                    'take_profit': Decimal(str(trade.take_profit)) if trade.take_profit else None,
                    'entry_time': trade.time,
                    'unrealized_pl': float(trade.unrealized_pl) if trade.unrealized_pl else 0.0
                }
                
                # Add to our tracking
                self.active_positions[pair] = position_data
                return position_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting existing position for {pair}: {e}")
            return None
    
    async def _should_close_position(self, existing_position: Dict[str, Any], decision: TradeDecision, market_context: MarketContext) -> bool:
        """Determine if we should close an existing position."""
        try:
            # Close if signal direction is opposite
            existing_side = existing_position.get('side', 'buy')
            new_signal = decision.recommendation.signal.value
            
            if (existing_side == 'buy' and new_signal == 'sell') or (existing_side == 'sell' and new_signal == 'buy'):
                return True
            
            # Close if position is in significant loss (more than 2R)
            unrealized_pl = existing_position.get('unrealized_pl', 0)
            if unrealized_pl < -200:  # $200 loss threshold
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking if should close position: {e}")
            return False
    
    async def _close_position(self, position: Dict[str, Any]) -> bool:
        """Close an existing position."""
        try:
            trade_id = position['id']
            success = self.oanda_api.close_trade(trade_id)
            
            if success:
                # Remove from our tracking
                pair = position['pair']
                if pair in self.active_positions:
                    del self.active_positions[pair]
                
                self.logger.info(f"✅ Position closed successfully: {pair}")
                return True
            else:
                self.logger.error(f"❌ Failed to close position: {position['pair']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False
    
    async def _calculate_position_size(self, decision: TradeDecision, market_context: MarketContext) -> Dict[str, Any]:
        """Calculate position size based on risk management rules."""
        try:
            # Use the position size from the decision
            position_size = decision.position_size
            stop_loss = decision.modified_stop_loss
            take_profit = decision.modified_take_profit
            
            return {
                'size': position_size,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return {
                'size': 1000,  # Default size
                'stop_loss': None,
                'take_profit': None
            }
    
    async def _execute_trade_order(self, decision: TradeDecision, position_size: Dict[str, Any]) -> Optional[str]:
        """Execute the actual trade order."""
        try:
            pair = decision.recommendation.pair
            side = decision.recommendation.signal.value
            units = int(position_size['size'])
            
            # Create order data
            order_data = {
                'instrument': pair,
                'units': str(units),
                'side': side,
                'type': 'MARKET',
                'timeInForce': 'FOK'
            }
            
            # Add stop loss if provided
            if position_size.get('stop_loss'):
                order_data['stopLossOnFill'] = {
                    'price': str(position_size['stop_loss']),
                    'timeInForce': 'GTC'
                }
            
            # Add take profit if provided
            if position_size.get('take_profit'):
                order_data['takeProfitOnFill'] = {
                    'price': str(position_size['take_profit']),
                    'timeInForce': 'GTC'
                }
            
            # Execute order
            response = self.oanda_api.create_order(order_data)
            
            if response and response.get('orderFillTransaction'):
                trade_id = response['orderFillTransaction'].get('id')
                self.logger.info(f"✅ Trade order executed: {trade_id}")
                return trade_id
            else:
                self.logger.error(f"❌ Trade order failed: {response}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing trade order: {e}")
            return None
    
    async def _record_trade(self, decision: TradeDecision, trade_id: str, position_size: Dict[str, Any]) -> None:
        """Record trade in our tracking system."""
        try:
            position_data = {
                'id': trade_id,
                'pair': decision.recommendation.pair,
                'side': decision.recommendation.signal.value,
                'units': position_size['size'],
                'entry_price': decision.recommendation.entry_price,
                'stop_loss': position_size.get('stop_loss'),
                'take_profit': position_size.get('take_profit'),
                'entry_time': datetime.now(timezone.utc),
                'unrealized_pl': 0.0,
                'scaling_levels': [],  # Initialize scaling levels
                'partial_exits': []    # Initialize partial exits
            }
            
            self.active_positions[decision.recommendation.pair] = position_data
            self.daily_trades += 1
            
            self.logger.info(f"📝 Trade recorded: {decision.recommendation.pair}")
            
        except Exception as e:
            self.logger.error(f"Error recording trade: {e}") 