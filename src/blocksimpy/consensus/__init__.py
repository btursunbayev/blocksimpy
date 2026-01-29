"""
Consensus mechanisms for blockchain simulation.

This module provides pluggable consensus implementations:
- PoW (Proof of Work): Mining-based consensus with hashrate competition
- PoS (Proof of Stake): Stake-weighted validator selection
- PoSpace (Proof of Space): Space-weighted farmer selection

Usage:
    from blocksimpy.consensus import PoWMiner, PoSValidator, PoSpaceFarmer
    from blocksimpy.consensus import Miner  # Alias for PoWMiner (backward compat)
"""

from .base import BlockProducer
from .pos import PoSValidator, select_validator
from .pospace import PoSpaceFarmer, select_farmer
from .pow import Miner, PoWMiner

__all__ = [
    "BlockProducer",
    "Miner",
    "PoWMiner",
    "PoSValidator",
    "select_validator",
    "PoSpaceFarmer",
    "select_farmer",
]
