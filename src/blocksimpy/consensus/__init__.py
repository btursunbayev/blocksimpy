"""
Consensus mechanisms for blockchain simulation.

This module provides pluggable consensus implementations:
- PoW (Proof of Work): Mining-based consensus with hashrate competition
- PoS (Proof of Stake): Stake-weighted validator selection

Usage:
    from blocksimpy.consensus import PoWMiner, PoSValidator
    from blocksimpy.consensus import Miner  # Alias for PoWMiner (backward compat)
"""

from .base import BlockProducer
from .pos import PoSValidator, select_validator
from .pow import Miner, PoWMiner

__all__ = ["BlockProducer", "Miner", "PoWMiner", "PoSValidator", "select_validator"]
