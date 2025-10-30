#!/usr/bin/env python3
"""
Blockchain network node implementation for discrete event simulation.

This module implements the Node class representing individual peer nodes in the
blockchain network. Nodes maintain block storage, handle network propagation,
and implement realistic networking behavior for accurate blockchain simulation.

Network Behavior:
- Each node maintains a set of stored block IDs (duplicate detection)
- Random peer topology with configurable neighbor connections
- Block broadcasting with network bandwidth and I/O tracking
- Realistic propagation delays and network congestion modeling
"""

import simpy
from typing import Set, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .block import Block
    from ..simulation.coordinator import SimulationCoordinator


class Node:
    """
    Blockchain network peer node for realistic network simulation.
    
    Implements peer-to-peer network behavior including block storage, propagation,
    and network metrics tracking for bandwidth and I/O analysis.
    
    Network Features:
        - Maintains set of stored block IDs for duplicate detection
        - Connected to configurable number of random peer nodes
        - Broadcasts new blocks to all connected neighbors
        - Tracks network I/O: increments global io_requests per send
        - Tracks bandwidth: adds block size to network_data per send
        - Ignores duplicate blocks (efficiency optimization)
    
    Attributes:
        env (simpy.Environment): Discrete event simulation environment
        id (int): Unique node identifier (0, 1, 2, ..., nodes-1)
        blocks (Set[int]): Set of block IDs this node has received/stored
        neighbors (List[Node]): Connected peer nodes for block propagation
        
    Network Topology:
        Nodes are randomly connected to a specified number of distinct peers during
        initialization. This creates a realistic P2P network topology where
        block propagation follows realistic network paths and delays.
    """
    
    def __init__(self, env: simpy.Environment, node_id: int):
        """
        Initialize a new blockchain network node.
        
        Args:
            env: SimPy discrete event simulation environment
            node_id: Unique identifier for this node (0 to --nodes-1)
            
        Note:
            Neighbor connections are established after all nodes are created
            to ensure proper random topology generation without self-connections.
        """
        self.env = env
        self.id = node_id
        self.blocks: Set[int] = set()  # Block IDs this node has received
        self.neighbors: List['Node'] = []  # Connected peer nodes
        
    def receive(self, block: 'Block') -> simpy.events.Process:
        """
        Receive and propagate a block through the network.
        
        Implements realistic block propagation behavior:
        1. Check for duplicate blocks (ignore if already received)
        2. Store block ID in local block set
        3. Broadcast to all connected neighbors
        4. Update global network metrics (I/O requests, bandwidth usage)
        
        Args:
            block: Block object to receive and propagate
            
        Returns:
            SimPy process for the block reception and propagation
            
        Network Metrics Tracking:
            - io_requests: Incremented for each neighbor broadcast
            - network_data: Block size added for each neighbor broadcast
            
        Note:
            Propagation delay is minimal (timeout=0) as the simulation focuses
            on mining dynamics rather than detailed network latency modeling.
            Real implementations could add configurable propagation delays.
        """
        yield self.env.timeout(0)  # Minimal propagation delay
        
        # Ignore duplicate blocks (already received and stored)
        if block.id in self.blocks:
            return
            
        # Store block locally
        self.blocks.add(block.id)
        
        # Broadcast to all neighbors with network metrics tracking
        coordinator: 'SimulationCoordinator' = self.env.coordinator
        for neighbor in self.neighbors:
            # Track network I/O per specification (Section 2.1.3)
            coordinator.io_requests += 1        # Increment global I/O counter
            coordinator.network_data += block.size  # Add block size to bandwidth tracking
            
            # Asynchronously propagate to neighbor
            self.env.process(neighbor.receive(block))
            
    def add_neighbor(self, neighbor: 'Node') -> None:
        """
        Add a peer connection to another node.
        
        Args:
            neighbor: Node to connect as a peer
            
        Note:
            Used during network topology initialization to create random
            peer connections according to --neighbors parameter.
        """
        if neighbor != self and neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Node(id={self.id}, blocks={len(self.blocks)}, neighbors={len(self.neighbors)})"
        
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Node #{self.id}: {len(self.blocks)} blocks, {len(self.neighbors)} peers"