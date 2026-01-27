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

from typing import TYPE_CHECKING, List, Set

import simpy

if TYPE_CHECKING:
    pass


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
        self.id = node_id
        self.blocks: Set[int] = set()  # Block IDs this node has received
        self.neighbors: List["Node"] = []  # Connected peer nodes
