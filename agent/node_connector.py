"""
Node Connector Service - Manages blockchain node connections and data aggregation
Handles multiple RPC endpoints with fallback and health checking
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiohttp
import time
from enum import Enum


class NodeStatus(Enum):
    """Node health status"""
    ONLINE = "online"
    OFFLINE = "offline"
    SLOW = "slow"


@dataclass
class NodeInfo:
    """Information about a blockchain node"""
    node_id: int
    name: str
    rpc_url: str
    provider_type: str  # "premium" or "budget"
    category: str  # "price", "liquidity", "volume", etc.
    status: NodeStatus = NodeStatus.ONLINE
    last_updated: datetime = None
    response_time_ms: float = 0.0
    data_freshness_ms: float = 0.0
    is_primary: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "rpc_url": self.rpc_url,
            "provider_type": self.provider_type,
            "category": self.category,
            "status": self.status.value,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "response_time_ms": self.response_time_ms,
            "data_freshness_ms": self.data_freshness_ms,
            "is_primary": self.is_primary,
        }


class NodeConnector:
    """
    Manages connections to multiple blockchain data sources.
    Implements health checking, fallback, and data aggregation.
    """
    
    def __init__(self):
        """Initialize node connector with predefined nodes"""
        self.nodes: Dict[int, NodeInfo] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.health_check_interval = 30  # seconds
        self.max_response_time = 5000  # ms - mark as slow if slower
        self.cache = {}
        self.cache_ttl = 10  # seconds
        
        # Initialize default nodes (48 total for the system)
        self._initialize_nodes()
    
    def _initialize_nodes(self):
        """Initialize 48 nodes from various categories"""
        
        # Cronos RPC nodes (8 nodes)
        cronos_rpcs = [
            ("https://evm-t3.cronos.org", "premium"),
            ("https://evm.cronos.org", "premium"),
            ("https://cronos-rpc.publicnode.com", "budget"),
            ("https://cronos.blockpi.network/v1/rpc/public", "budget"),
        ]
        
        node_id = 0
        
        # Price data nodes (12 nodes)
        for i, (rpc, provider_type) in enumerate(cronos_rpcs * 3):
            self.nodes[node_id] = NodeInfo(
                node_id=node_id,
                name=f"price_node_{i}",
                rpc_url=rpc,
                provider_type=provider_type,
                category="price",
                is_primary=(i == 0)
            )
            node_id += 1
        
        # Liquidity data nodes (12 nodes)
        for i, (rpc, provider_type) in enumerate(cronos_rpcs * 3):
            self.nodes[node_id] = NodeInfo(
                node_id=node_id,
                name=f"liquidity_node_{i}",
                rpc_url=rpc,
                provider_type=provider_type,
                category="liquidity",
                is_primary=(i == 0)
            )
            node_id += 1
        
        # Volume data nodes (12 nodes)
        for i, (rpc, provider_type) in enumerate(cronos_rpcs * 3):
            self.nodes[node_id] = NodeInfo(
                node_id=node_id,
                name=f"volume_node_{i}",
                rpc_url=rpc,
                provider_type=provider_type,
                category="volume",
                is_primary=(i == 0)
            )
            node_id += 1
        
        # Gas price nodes (12 nodes)
        for i, (rpc, provider_type) in enumerate(cronos_rpcs * 3):
            self.nodes[node_id] = NodeInfo(
                node_id=node_id,
                name=f"gas_node_{i}",
                rpc_url=rpc,
                provider_type=provider_type,
                category="gas",
                is_primary=(i == 0)
            )
            node_id += 1
    
    async def connect(self):
        """Establish async HTTP session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        
        # Start health check task
        asyncio.create_task(self._health_check_loop())
    
    async def disconnect(self):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _health_check_loop(self):
        """Periodic health check for all nodes"""
        while True:
            await asyncio.sleep(self.health_check_interval)
            await self._perform_health_checks()
    
    async def _perform_health_checks(self):
        """Check health of all nodes"""
        if not self.session:
            return
        
        tasks = []
        for node_id, node in self.nodes.items():
            tasks.append(self._check_node_health(node))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_node_health(self, node: NodeInfo):
        """Check if a node is responding"""
        if not self.session:
            return
        
        try:
            start_time = time.time()
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1,
            }
            
            async with self.session.post(
                node.rpc_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                response_time = (time.time() - start_time) * 1000
                node.response_time_ms = response_time
                node.last_updated = datetime.now()
                
                if response.status == 200:
                    data = await response.json()
                    if "result" in data:
                        node.status = (
                            NodeStatus.SLOW if response_time > self.max_response_time
                            else NodeStatus.ONLINE
                        )
                        node.data_freshness_ms = 0  # Just updated
                    else:
                        node.status = NodeStatus.OFFLINE
                else:
                    node.status = NodeStatus.OFFLINE
        
        except asyncio.TimeoutError:
            node.status = NodeStatus.SLOW
            node.last_updated = datetime.now()
        except Exception as e:
            node.status = NodeStatus.OFFLINE
            node.last_updated = datetime.now()
    
    async def get_data(self, method: str, params: List = None, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get data from nodes, using primary node first with fallback
        
        Args:
            method: RPC method to call
            params: RPC parameters
            category: Specific category of nodes to use, None for all
        
        Returns:
            Response data with metadata about which nodes were used
        """
        if not self.session:
            await self.connect()
        
        if params is None:
            params = []
        
        # Select nodes to query
        nodes_to_try = self._select_nodes(category)
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1,
        }
        
        # Try primary node first
        primary_nodes = [n for n in nodes_to_try if n.is_primary and n.status == NodeStatus.ONLINE]
        fallback_nodes = [n for n in nodes_to_try if not n.is_primary and n.status in (NodeStatus.ONLINE, NodeStatus.SLOW)]
        
        all_nodes_to_try = primary_nodes + fallback_nodes
        
        for node in all_nodes_to_try:
            try:
                start_time = time.time()
                async with self.session.post(
                    node.rpc_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=3)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        if "result" in data:
                            node.response_time_ms = response_time
                            node.last_updated = datetime.now()
                            node.data_freshness_ms = 0
                            
                            return {
                                "data": data.get("result"),
                                "node_used": node.to_dict(),
                                "timestamp": datetime.now().isoformat(),
                                "method": method,
                                "response_time_ms": response_time,
                                "success": True,
                            }
            except Exception:
                continue
        
        # All nodes failed
        return {
            "data": None,
            "node_used": None,
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "success": False,
            "error": "All nodes failed",
        }
    
    def _select_nodes(self, category: Optional[str] = None) -> List[NodeInfo]:
        """Select nodes for querying"""
        if category:
            return [n for n in self.nodes.values() if n.category == category]
        return list(self.nodes.values())
    
    def get_nodes_status(self, category: Optional[str] = None) -> Dict[str, Any]:
        """Get status of all nodes"""
        nodes_list = self._select_nodes(category)
        nodes_data = [n.to_dict() for n in nodes_list]
        
        online_count = sum(1 for n in nodes_data if n["status"] == "online")
        
        return {
            "total_nodes": len(nodes_data),
            "connected_nodes": online_count,
            "nodes": nodes_data,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def execute_batch(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple RPC calls in parallel"""
        if not self.session:
            await self.connect()
        
        tasks = [
            self.get_data(
                req.get("method"),
                req.get("params", []),
                req.get("category")
            )
            for req in requests
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results


# Global connector instance
_connector: Optional[NodeConnector] = None


async def get_connector() -> NodeConnector:
    """Get or create global connector instance"""
    global _connector
    if _connector is None:
        _connector = NodeConnector()
        await _connector.connect()
    return _connector


async def close_connector():
    """Close global connector instance"""
    global _connector
    if _connector:
        await _connector.disconnect()
        _connector = None
