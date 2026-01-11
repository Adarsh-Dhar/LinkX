"""
Trading Engine - Orchestrates node data aggregation, neural prediction, and trade execution
Bridges the gap between 48 nodes and the neural network brain
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class SimulatedTrade:
    """Represents a simulated trade"""
    trade_id: str
    timestamp: str
    token_in: str
    token_out: str
    amount_in: float
    predicted_amount_out: float
    entry_price: float
    exit_price: float
    confidence: float
    neural_decision: str  # BUY, SELL, HOLD
    reasoning: str
    nodes_used: List[str]
    simulation_status: str  # "pending", "executing", "completed", "failed"
    actual_output: Optional[float] = None
    transaction_hash: Optional[str] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None


class TradingEngine:
    """
    Main orchestrator for trading operations
    Handles:
    - Data aggregation from 48 nodes
    - Neural network predictions
    - Trade simulation and execution tracking
    - Performance metrics and reporting
    """
    
    def __init__(self, smart_router, data_pipeline, neural_brain):
        """
        Initialize trading engine with core components
        
        Args:
            smart_router: SmartRouter for node discovery and routing
            data_pipeline: DataPipeline for aggregating data from 48 nodes
            neural_brain: RLAgent (neural network) for predictions
        """
        self.smart_router = smart_router
        self.data_pipeline = data_pipeline
        self.neural_brain = neural_brain
        
        # Simulation tracking
        self.trade_history: List[SimulatedTrade] = []
        self.active_trades: Dict[str, SimulatedTrade] = {}
        
        # Performance metrics
        self.metrics = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_pnl": 0.0,
            "cumulative_return": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "average_confidence": 0.0
        }
        
        # Track equity curve for Sharpe ratio
        self.equity_curve = [1.0]  # Start with 1.0 (100%)
        
    async def get_market_data(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch aggregated market data from 48 nodes
        
        Args:
            category: Specific category to fetch, or None for all
            
        Returns:
            Normalized market data vector ready for neural network
        """
        try:
            if hasattr(self.data_pipeline, 'get_normalized_vector'):
                market_data = self.data_pipeline.get_normalized_vector()
                return market_data
            else:
                # Fallback: create mock market data
                return {
                    'data': self._generate_mock_market_data(),
                    'nodes': [f"Node_{i}" for i in range(48)],
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return self._generate_mock_market_data()
    
    def _generate_mock_market_data(self) -> Dict[str, Any]:
        """Generate mock market data for testing"""
        return {
            'price': np.random.uniform(0.4, 0.5),
            'volume_24h': np.random.uniform(1000000, 2000000),
            'liquidity': np.random.uniform(5000000, 10000000),
            'whale_transactions': np.random.uniform(0, 100),
            'sentiment_score': np.random.uniform(-1, 1),
            'rsi': np.random.uniform(30, 70),
            'moving_average_50': np.random.uniform(0.4, 0.5),
            'volatility': np.random.uniform(0.01, 0.05)
        }
    
    async def simulate_trade(
        self, 
        token_in: str, 
        token_out: str, 
        amount: float
    ) -> SimulatedTrade:
        """
        Simulate a trade using neural network prediction
        
        Args:
            token_in: Token to swap from (e.g., 'USDC')
            token_out: Token to swap to (e.g., 'CRO')
            amount: Amount to trade
            
        Returns:
            SimulatedTrade object with prediction and reasoning
        """
        trade_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        try:
            # Fetch market data from 48 nodes
            market_data = await self.get_market_data()
            nodes_used = market_data.get('nodes', [])
            
            # Get neural network prediction
            neural_decision = "HOLD"
            confidence = 0.5
            predicted_amount_out = amount * 0.98  # Assume 2% slippage
            
            if hasattr(self.neural_brain, 'predict'):
                try:
                    prediction = self.neural_brain.predict(market_data)
                    neural_decision = prediction.get('action', 'HOLD')
                    confidence = min(1.0, max(0.0, prediction.get('confidence', 0.5)))
                    # Adjust output based on prediction
                    if neural_decision == "BUY":
                        predicted_amount_out = amount * (0.98 + confidence * 0.05)
                    elif neural_decision == "SELL":
                        predicted_amount_out = amount * (0.98 - confidence * 0.02)
                except Exception as e:
                    print(f"Neural prediction error: {e}")
            
            # Simulate pricing based on market data and confidence
            base_price = market_data.get('data', {}).get('price', 0.45)
            entry_price = base_price * (1 - np.random.uniform(0, 0.005))  # Slight slippage
            
            # Exit price influenced by confidence and decision
            if neural_decision == "BUY":
                exit_price = entry_price * (1 + confidence * 0.05)
            elif neural_decision == "SELL":
                exit_price = entry_price * (1 - confidence * 0.03)
            else:
                exit_price = entry_price * (1 + (confidence - 0.5) * 0.02)
            
            # Create reasoning explanation
            reasoning = self._generate_trade_reasoning(
                neural_decision, 
                confidence, 
                market_data,
                len(nodes_used)
            )
            
            # Create simulated trade
            trade = SimulatedTrade(
                trade_id=trade_id,
                timestamp=timestamp,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount,
                predicted_amount_out=predicted_amount_out,
                entry_price=entry_price,
                exit_price=exit_price,
                confidence=confidence,
                neural_decision=neural_decision,
                reasoning=reasoning,
                nodes_used=nodes_used,
                simulation_status="completed"
            )
            
            # Track trade
            self.trade_history.append(trade)
            self.active_trades[trade_id] = trade
            
            # Update metrics
            self._update_metrics(trade)
            
            return trade
            
        except Exception as e:
            print(f"Error simulating trade: {e}")
            # Return failed trade
            return SimulatedTrade(
                trade_id=trade_id,
                timestamp=timestamp,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount,
                predicted_amount_out=0,
                entry_price=0,
                exit_price=0,
                confidence=0,
                neural_decision="HOLD",
                reasoning=f"Simulation failed: {str(e)}",
                nodes_used=[],
                simulation_status="failed"
            )
    
    def _generate_trade_reasoning(
        self, 
        decision: str, 
        confidence: float, 
        market_data: Dict[str, Any],
        num_nodes: int
    ) -> str:
        """Generate human-readable explanation for trade decision"""
        data = market_data.get('data', {})
        
        if decision == "BUY":
            reason = f"Neural network recommends BUY with {confidence:.1%} confidence. "
            if data.get('sentiment_score', 0) > 0:
                reason += "Positive sentiment detected. "
            if data.get('rsi', 50) < 50:
                reason += "RSI indicates oversold conditions. "
            reason += f"Analysis based on {num_nodes} data providers."
        elif decision == "SELL":
            reason = f"Neural network recommends SELL with {confidence:.1%} confidence. "
            if data.get('sentiment_score', 0) < 0:
                reason += "Negative sentiment detected. "
            if data.get('rsi', 50) > 70:
                reason += "RSI indicates overbought conditions. "
            reason += f"Analysis based on {num_nodes} data providers."
        else:
            reason = f"Neural network recommends HOLD with {confidence:.1%} confidence. "
            reason += "Market conditions neutral. "
            reason += f"Analysis based on {num_nodes} data providers."
        
        return reason
    
    def _update_metrics(self, trade: SimulatedTrade) -> None:
        """Update performance metrics after each trade"""
        self.metrics["total_trades"] += 1
        
        if trade.simulation_status == "completed":
            self.metrics["successful_trades"] += 1
            
            # Calculate P&L
            if trade.actual_output:
                pnl = trade.actual_output - trade.amount_in
                pnl_percent = (pnl / trade.amount_in) * 100
            else:
                pnl = (trade.predicted_amount_out - trade.amount_in)
                pnl_percent = (pnl / trade.amount_in) * 100
            
            trade.pnl = pnl
            trade.pnl_percent = pnl_percent
            
            self.metrics["total_pnl"] += pnl
            
            # Update equity curve
            current_equity = self.equity_curve[-1] * (1 + pnl / 1000)  # Assume 1000 starting
            self.equity_curve.append(current_equity)
            
            # Update win rate
            if pnl > 0:
                self.metrics["successful_trades"] += 1
            else:
                self.metrics["failed_trades"] += 1
        else:
            self.metrics["failed_trades"] += 1
        
        # Recalculate averages
        if self.metrics["total_trades"] > 0:
            self.metrics["win_rate"] = self.metrics["successful_trades"] / self.metrics["total_trades"]
            avg_confidence = np.mean([t.confidence for t in self.trade_history])
            self.metrics["average_confidence"] = avg_confidence
            
            # Calculate Sharpe ratio
            if len(self.equity_curve) > 1:
                returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])
                self.metrics["sharpe_ratio"] = np.mean(returns) / (np.std(returns) + 1e-10) if len(returns) > 0 else 0
                
                # Calculate max drawdown
                cummax = np.maximum.accumulate(self.equity_curve)
                drawdown = (np.array(self.equity_curve) - cummax) / cummax
                self.metrics["max_drawdown"] = np.min(drawdown) if len(drawdown) > 0 else 0
    
    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trade history"""
        recent_trades = self.trade_history[-limit:]
        return [asdict(trade) for trade in recent_trades]
    
    def get_active_trades(self) -> List[Dict[str, Any]]:
        """Get currently active trades"""
        return [asdict(trade) for trade in self.active_trades.values()]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.metrics,
            "equity_curve": self.equity_curve,
            "recent_trades": self.get_trade_history(10)
        }
    
    async def execute_live_trade(
        self,
        token_in: str,
        token_out: str,
        amount: float,
        confidence_threshold: float = 0.6
    ) -> SimulatedTrade:
        """
        Execute a live trade if confidence exceeds threshold
        
        Args:
            token_in: Token to swap from
            token_out: Token to swap to
            amount: Amount to trade
            confidence_threshold: Minimum confidence to execute (default 0.6)
            
        Returns:
            Trade with execution result
        """
        # First simulate
        trade = await self.simulate_trade(token_in, token_out, amount)
        
        # Check confidence
        if trade.confidence < confidence_threshold:
            trade.simulation_status = "pending"
            return trade
        
        # Try to execute (would call actual swap function)
        try:
            # In real implementation, would call:
            # from tools import execute_swap
            # tx_hash = execute_swap(token_in, token_out, amount, slippage=1.0)
            # trade.transaction_hash = tx_hash
            # trade.actual_output = get_output_amount(tx_hash)
            
            # For now, simulate execution
            trade.transaction_hash = f"0x{''.join([str(i) for i in np.random.randint(0,9,64)])[:64]}"
            trade.actual_output = trade.predicted_amount_out * (1 - np.random.uniform(0, 0.02))
            trade.simulation_status = "completed"
            
            # Update metrics with actual output
            self._update_metrics(trade)
            
        except Exception as e:
            print(f"Trade execution error: {e}")
            trade.simulation_status = "failed"
            self.metrics["failed_trades"] += 1
        
        return trade
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        self.trade_history.clear()
        self.active_trades.clear()
        self.equity_curve = [1.0]
        self.metrics = {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_pnl": 0.0,
            "cumulative_return": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "average_confidence": 0.0
        }


# Global instance (will be initialized by the agent)
_engine_instance: Optional[TradingEngine] = None


def initialize_engine(smart_router, data_pipeline, neural_brain) -> TradingEngine:
    """Initialize the global trading engine"""
    global _engine_instance
    _engine_instance = TradingEngine(smart_router, data_pipeline, neural_brain)
    return _engine_instance


def get_engine() -> Optional[TradingEngine]:
    """Get the global trading engine instance"""
    return _engine_instance
