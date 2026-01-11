"""
Simulation Service - Manages trade simulations and tracking
Records and replays trading simulations for backtesting and live display
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics


class SimulationStatus(Enum):
    """Trade simulation status"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SimulatedTrade:
    """Represents a simulated trade"""
    simulation_id: str
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
    status: str = "pending"
    actual_output: Optional[float] = None
    transaction_hash: Optional[str] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    execution_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SimulationService:
    """
    Manages trade simulations and historical tracking.
    Provides metrics calculation and simulation analysis.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize simulation service
        
        Args:
            max_history: Maximum number of simulations to keep in memory
        """
        self.max_history = max_history
        self.trades: List[SimulatedTrade] = []
        self.active_trades: Dict[str, SimulatedTrade] = {}
        self.equity_curve = [1.0]  # Starting equity = 100%
        self.timestamps = [datetime.now()]
        
        # Performance metrics cache
        self.metrics_cache = None
        self.metrics_cache_time = None
        self.metrics_cache_ttl = 5  # seconds
    
    def create_simulation(
        self,
        token_in: str,
        token_out: str,
        amount_in: float,
        predicted_amount_out: float,
        entry_price: float,
        exit_price: float,
        confidence: float,
        neural_decision: str,
        reasoning: str,
        nodes_used: List[str],
    ) -> SimulatedTrade:
        """
        Create a new trade simulation
        
        Args:
            token_in: Input token symbol
            token_out: Output token symbol
            amount_in: Input amount
            predicted_amount_out: Predicted output amount from neural network
            entry_price: Entry price of the trade
            exit_price: Exit/target price
            confidence: Neural network confidence (0-1)
            neural_decision: "BUY", "SELL", or "HOLD"
            reasoning: Explanation of the decision
            nodes_used: List of node IDs used for this trade
        
        Returns:
            SimulatedTrade object
        """
        trade = SimulatedTrade(
            simulation_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(),
            token_in=token_in,
            token_out=token_out,
            amount_in=amount_in,
            predicted_amount_out=predicted_amount_out,
            entry_price=entry_price,
            exit_price=exit_price,
            confidence=confidence,
            neural_decision=neural_decision,
            reasoning=reasoning,
            nodes_used=nodes_used,
            status="pending",
        )
        
        self.active_trades[trade.simulation_id] = trade
        return trade
    
    def execute_simulation(
        self,
        simulation_id: str,
        actual_output: float,
        transaction_hash: Optional[str] = None,
        execution_time_ms: float = 0.0,
    ) -> SimulatedTrade:
        """
        Mark a simulation as executed and update with actual results
        
        Args:
            simulation_id: Simulation ID to update
            actual_output: Actual output received from trade
            transaction_hash: Optional blockchain transaction hash
            execution_time_ms: Time taken to execute trade
        
        Returns:
            Updated SimulatedTrade
        """
        if simulation_id not in self.active_trades:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        trade = self.active_trades[simulation_id]
        trade.actual_output = actual_output
        trade.transaction_hash = transaction_hash
        trade.execution_time_ms = execution_time_ms
        trade.status = "completed"
        
        # Calculate P&L
        if trade.predicted_amount_out > 0:
            pnl = actual_output - trade.predicted_amount_out
            pnl_percent = (pnl / trade.predicted_amount_out) * 100
            trade.pnl = pnl
            trade.pnl_percent = pnl_percent
        
        # Update equity curve
        if trade.pnl is not None and trade.pnl_percent is not None:
            current_equity = self.equity_curve[-1]
            new_equity = current_equity * (1 + trade.pnl_percent / 100)
            self.equity_curve.append(new_equity)
            self.timestamps.append(datetime.now())
        
        # Move to history
        self.trades.append(trade)
        del self.active_trades[simulation_id]
        
        # Trim history if needed
        if len(self.trades) > self.max_history:
            self.trades = self.trades[-self.max_history:]
        
        # Invalidate metrics cache
        self.metrics_cache = None
        
        return trade
    
    def fail_simulation(
        self,
        simulation_id: str,
        error_message: str,
    ) -> SimulatedTrade:
        """
        Mark a simulation as failed
        
        Args:
            simulation_id: Simulation ID to update
            error_message: Error description
        
        Returns:
            Updated SimulatedTrade
        """
        if simulation_id not in self.active_trades:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        trade = self.active_trades[simulation_id]
        trade.status = "failed"
        trade.reasoning = f"{trade.reasoning} [FAILED: {error_message}]"
        
        # Move to history
        self.trades.append(trade)
        del self.active_trades[simulation_id]
        
        if len(self.trades) > self.max_history:
            self.trades = self.trades[-self.max_history:]
        
        # Invalidate metrics cache
        self.metrics_cache = None
        
        return trade
    
    def get_metrics(self, recalculate: bool = False) -> Dict[str, Any]:
        """
        Calculate performance metrics from simulation history
        
        Args:
            recalculate: Force recalculation even if cached
        
        Returns:
            Dictionary of performance metrics
        """
        # Check cache
        if not recalculate and self.metrics_cache:
            cache_age = (datetime.now() - self.metrics_cache_time).total_seconds()
            if cache_age < self.metrics_cache_ttl:
                return self.metrics_cache
        
        completed_trades = [t for t in self.trades if t.status == "completed"]
        
        if not completed_trades:
            return self._empty_metrics()
        
        # Calculate metrics
        win_trades = [t for t in completed_trades if t.pnl and t.pnl > 0]
        total_trades = len(completed_trades)
        successful_trades = len(win_trades)
        failed_trades = len([t for t in self.trades if t.status == "failed"])
        
        total_pnl = sum(t.pnl for t in completed_trades if t.pnl)
        
        # Win rate
        win_rate = successful_trades / total_trades if total_trades > 0 else 0
        
        # Average confidence
        average_confidence = (
            sum(t.confidence for t in completed_trades) / total_trades
            if total_trades > 0
            else 0
        )
        
        # Cumulative return
        cumulative_return = ((self.equity_curve[-1] - 1) * 100) if self.equity_curve else 0
        
        # Sharpe Ratio (simplified - requires more precise daily returns calculation in production)
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # Max Drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        metrics = {
            "total_trades": total_trades,
            "successful_trades": successful_trades,
            "failed_trades": failed_trades,
            "total_pnl": round(total_pnl, 4),
            "cumulative_return": round(cumulative_return, 2),
            "win_rate": round(win_rate * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "average_confidence": round(average_confidence * 100, 2),
            "average_trade_pnl": round(total_pnl / total_trades, 4) if total_trades > 0 else 0,
            "best_trade": round(max([t.pnl for t in completed_trades if t.pnl], default=0), 4),
            "worst_trade": round(min([t.pnl for t in completed_trades if t.pnl], default=0), 4),
        }
        
        # Cache metrics
        self.metrics_cache = metrics
        self.metrics_cache_time = datetime.now()
        
        return metrics
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio from equity curve
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        
        Returns:
            Sharpe Ratio
        """
        if len(self.equity_curve) < 2:
            return 0.0
        
        # Calculate returns
        returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            returns.append(ret)
        
        if not returns:
            return 0.0
        
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0
        
        if std_return == 0:
            return 0.0
        
        # Annualize (assuming ~250 trading days per year)
        excess_return = (mean_return * 250) - risk_free_rate
        annual_std = std_return * (250 ** 0.5)
        
        return excess_return / annual_std if annual_std > 0 else 0
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve"""
        if not self.equity_curve:
            return 0.0
        
        max_drawdown = 0.0
        peak = self.equity_curve[0]
        
        for value in self.equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_pnl": 0.0,
            "cumulative_return": 0.0,
            "win_rate": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "average_confidence": 0.0,
            "average_trade_pnl": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
        }
    
    def get_equity_curve(self) -> Dict[str, Any]:
        """Get equity curve for charting"""
        if not self.equity_curve:
            return {"data": [], "timestamps": []}
        
        return {
            "data": [round(e, 4) for e in self.equity_curve],
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "current_equity": round(self.equity_curve[-1], 4),
        }
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent completed trades"""
        completed = [t for t in self.trades if t.status == "completed"]
        recent = completed[-limit:] if len(completed) > limit else completed
        return [t.to_dict() for t in recent]
    
    def get_active_trades(self) -> List[Dict]:
        """Get currently active (pending) trades"""
        return [t.to_dict() for t in self.active_trades.values()]
    
    def get_trade_by_id(self, simulation_id: str) -> Optional[Dict]:
        """Get a specific trade by ID"""
        # Check active trades first
        if simulation_id in self.active_trades:
            return self.active_trades[simulation_id].to_dict()
        
        # Check history
        for trade in self.trades:
            if trade.simulation_id == simulation_id:
                return trade.to_dict()
        
        return None
    
    def get_confidence_distribution(self) -> List[Dict]:
        """Get distribution of neural network confidence levels"""
        completed_trades = [t for t in self.trades if t.status == "completed"]
        
        if not completed_trades:
            return []
        
        # Bucket confidence into 10% ranges
        buckets = {i: [] for i in range(10)}
        
        for trade in completed_trades:
            bucket = int(trade.confidence * 10)
            if bucket >= 10:
                bucket = 9
            buckets[bucket].append(trade)
        
        distribution = []
        for i in range(10):
            bucket_trades = buckets[i]
            distribution.append({
                "range": f"{i*10}-{(i+1)*10}%",
                "count": len(bucket_trades),
                "win_count": sum(1 for t in bucket_trades if t.pnl and t.pnl > 0),
                "avg_pnl": round(
                    sum(t.pnl for t in bucket_trades if t.pnl) / len(bucket_trades), 4
                ) if bucket_trades else 0,
            })
        
        return distribution
    
    def clear_history(self):
        """Clear all trade history"""
        self.trades.clear()
        self.active_trades.clear()
        self.equity_curve = [1.0]
        self.timestamps = [datetime.now()]
        self.metrics_cache = None


# Global simulation service instance
_service: Optional[SimulationService] = None


def get_simulation_service() -> SimulationService:
    """Get or create global simulation service instance"""
    global _service
    if _service is None:
        _service = SimulationService()
    return _service
