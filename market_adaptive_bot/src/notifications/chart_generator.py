"""
Chart Generator - Creates trading charts for notifications.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import plotly.graph_objects as go
import plotly.io as pio
import base64
import io

from core.models import CandleData, TradeRecommendation


class ChartGenerator:
    """Generates trading charts for notifications."""
    
    def __init__(self):
        """Initialize the chart generator."""
        # Set default chart style
        pio.templates.default = "plotly_white"
    
    def create_candlestick_chart(
        self, 
        candles: List[CandleData],
        trade_recommendation: Optional[TradeRecommendation] = None,
        title: str = "Price Chart"
    ) -> Dict[str, Any]:
        """Create a candlestick chart with optional trade signals."""
        
        try:
            # Prepare data
            dates = [c.timestamp for c in candles]
            opens = [float(c.open) for c in candles]
            highs = [float(c.high) for c in candles]
            lows = [float(c.low) for c in candles]
            closes = [float(c.close) for c in candles]
            
            # Create candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=dates,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name="Price"
            )])
            
            # Add trade recommendation if provided
            if trade_recommendation:
                self._add_trade_signals(fig, trade_recommendation)
            
            # Update layout
            fig.update_layout(
                title=title,
                xaxis_title="Time",
                yaxis_title="Price",
                xaxis_rangeslider_visible=False,
                height=400,
                width=600
            )
            
            # Convert to image
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            return {
                'image_data': img_base64,
                'image_format': 'png',
                'chart_type': 'candlestick',
                'data_points': len(candles)
            }
            
        except Exception as e:
            return {
                'error': f"Failed to create chart: {e}",
                'chart_type': 'candlestick'
            }
    
    def create_technical_chart(
        self, 
        candles: List[CandleData],
        indicators: Dict[str, Any],
        trade_recommendation: Optional[TradeRecommendation] = None
    ) -> Dict[str, Any]:
        """Create a chart with technical indicators."""
        
        try:
            # Prepare data
            dates = [c.timestamp for c in candles]
            closes = [float(c.close) for c in candles]
            
            # Create figure with secondary y-axis
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=dates,
                y=closes,
                mode='lines',
                name='Price',
                line=dict(color='blue')
            ))
            
            # Add technical indicators
            if 'ema_fast' in indicators and indicators['ema_fast']:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=[indicators['ema_fast']] * len(dates),
                    mode='lines',
                    name='EMA Fast',
                    line=dict(color='orange', dash='dash')
                ))
            
            if 'ema_slow' in indicators and indicators['ema_slow']:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=[indicators['ema_slow']] * len(dates),
                    mode='lines',
                    name='EMA Slow',
                    line=dict(color='red', dash='dash')
                ))
            
            if 'bollinger_upper' in indicators and indicators['bollinger_upper']:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=[indicators['bollinger_upper']] * len(dates),
                    mode='lines',
                    name='BB Upper',
                    line=dict(color='gray', dash='dot')
                ))
            
            if 'bollinger_lower' in indicators and indicators['bollinger_lower']:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=[indicators['bollinger_lower']] * len(dates),
                    mode='lines',
                    name='BB Lower',
                    line=dict(color='gray', dash='dot')
                ))
            
            # Add trade recommendation if provided
            if trade_recommendation:
                self._add_trade_signals(fig, trade_recommendation)
            
            # Update layout
            fig.update_layout(
                title="Technical Analysis Chart",
                xaxis_title="Time",
                yaxis_title="Price",
                height=400,
                width=600
            )
            
            # Convert to image
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            return {
                'image_data': img_base64,
                'image_format': 'png',
                'chart_type': 'technical',
                'data_points': len(candles),
                'indicators': list(indicators.keys())
            }
            
        except Exception as e:
            return {
                'error': f"Failed to create technical chart: {e}",
                'chart_type': 'technical'
            }
    
    def create_performance_chart(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a performance summary chart."""
        
        try:
            # Create bar chart for performance metrics
            metrics = ['Win Rate', 'Profit Factor', 'Sharpe Ratio']
            values = [
                performance_data.get('win_rate', 0) * 100,
                performance_data.get('profit_factor', 0),
                performance_data.get('sharpe_ratio', 0)
            ]
            
            fig = go.Figure(data=[go.Bar(
                x=metrics,
                y=values,
                marker_color=['green', 'blue', 'orange']
            )])
            
            fig.update_layout(
                title="Performance Metrics",
                xaxis_title="Metric",
                yaxis_title="Value",
                height=300,
                width=500
            )
            
            # Convert to image
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            return {
                'image_data': img_base64,
                'image_format': 'png',
                'chart_type': 'performance',
                'metrics': metrics
            }
            
        except Exception as e:
            return {
                'error': f"Failed to create performance chart: {e}",
                'chart_type': 'performance'
            }
    
    def _add_trade_signals(self, fig: go.Figure, recommendation: TradeRecommendation) -> None:
        """Add trade signals to the chart."""
        
        try:
            if recommendation.entry_price:
                # Add entry point
                fig.add_trace(go.Scatter(
                    x=[recommendation.timestamp],
                    y=[float(recommendation.entry_price)],
                    mode='markers',
                    name='Entry',
                    marker=dict(
                        symbol='triangle-up' if recommendation.signal.value == 'buy' else 'triangle-down',
                        size=15,
                        color='green' if recommendation.signal.value == 'buy' else 'red'
                    )
                ))
            
            if recommendation.stop_loss:
                # Add stop loss line
                fig.add_hline(
                    y=float(recommendation.stop_loss),
                    line_dash="dash",
                    line_color="red",
                    annotation_text="Stop Loss"
                )
            
            if recommendation.take_profit:
                # Add take profit line
                fig.add_hline(
                    y=float(recommendation.take_profit),
                    line_dash="dash",
                    line_color="green",
                    annotation_text="Take Profit"
                )
                
        except Exception as e:
            # Silently fail if we can't add signals
            pass
    
    def create_simple_chart(self, data: List[float], labels: List[str], title: str = "Chart") -> Dict[str, Any]:
        """Create a simple line chart."""
        
        try:
            fig = go.Figure(data=[go.Scatter(
                x=labels,
                y=data,
                mode='lines+markers',
                name='Data'
            )])
            
            fig.update_layout(
                title=title,
                xaxis_title="Time",
                yaxis_title="Value",
                height=300,
                width=500
            )
            
            # Convert to image
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            return {
                'image_data': img_base64,
                'image_format': 'png',
                'chart_type': 'simple',
                'data_points': len(data)
            }
            
        except Exception as e:
            return {
                'error': f"Failed to create simple chart: {e}",
                'chart_type': 'simple'
            } 