#!/usr/bin/env python3
"""
Blockchain block implementation for discrete event simulation.

This module implements the Block class representing individual blockchain blocks
with realistic size calculation, transaction tracking, and timing metadata for
accurate blockchain behavior modeling.

Block Structure:
- Header: Fixed 1,024 bytes containing block metadata
- Transactions: Variable size (# transactions × 256 bytes each)
- Tracking: Block ID, timestamp, time-since-last-block, transaction count, total size
"""

import time
from typing import Optional

from ..utils.formatting import HEADER_SIZE


class Block:
    """
    Represents a single blockchain block in the discrete event simulation.

    Implements realistic block structure with accurate size calculations
    and comprehensive metadata tracking for simulation analysis and network
    propagation modeling.

    Block Structure:
        - Header: 1,024 bytes (fixed overhead)
        - Transactions: 256 bytes per transaction (realistic Bitcoin-like sizing)
        - Total Size: header + (transaction_count × 256 bytes)
        - Metadata: ID, timestamp, inter-block timing, transaction count

    Attributes:
        id (int): Unique sequential block identifier (0, 1, 2, ...)
        tx (int): Number of transactions included in this block
        size (int): Total block size in bytes (header + transaction data)
        dt (float): Time elapsed since previous block in seconds
        timestamp (float): Block creation time (simulation time)

    Note:
        Block propagation uses self.size for network bandwidth calculations.
        Each block broadcast increments global io_requests counter and adds
        self.size to network_data tracking for realistic network modeling.
    """

    def __init__(
        self,
        block_id: int,
        transaction_count: int,
        time_since_last: float,
        timestamp: Optional[float] = None,
    ):
        """
        Initialize a new blockchain block.

        Args:
            block_id: Sequential block identifier (genesis = 0, next = 1, etc.)
            transaction_count: Number of transactions included in block
            time_since_last: Seconds elapsed since previous block was mined
            timestamp: Block creation time (defaults to current simulation time)

        Block Size Calculation:
            Total size = 1,024 bytes (header) + (transaction_count × 256 bytes)
            This reflects realistic blockchain block sizing where:
            - Header contains previous hash, merkle root, nonce, difficulty, etc.
            - Each transaction averages ~256 bytes (simplified from Bitcoin ~250-500 bytes)
        """
        self.id = block_id
        self.tx = transaction_count
        self.size = (
            HEADER_SIZE + transaction_count * 256
        )  # Bytes: 1024 + (tx_count * 256)
        self.dt = time_since_last  # Inter-block time for difficulty analysis
        self.timestamp = timestamp if timestamp is not None else time.time()

    def __repr__(self) -> str:
        """String representation for debugging and logging."""
        return (
            f"Block(id={self.id}, tx={self.tx}, size={self.size}B, dt={self.dt:.1f}s)"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Block #{self.id}: {self.tx} transactions, "
            f"{self.size:,} bytes, {self.dt:.1f}s since last"
        )
