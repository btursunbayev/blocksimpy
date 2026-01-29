"""
Pytest configuration and shared fixtures for BlockSimPy tests.

Provides reusable test configurations, seeded environments, and helper
functions for fast, reproducible testing.
"""

import random
from collections import deque
from typing import Any, Dict

import pytest
import simpy


@pytest.fixture
def mini_config() -> Dict[str, Any]:
    """
    Minimal configuration for fast unit/integration tests.

    Uses small values to complete quickly while still exercising core logic.
    """
    return {
        "network": {
            "nodes": 3,
            "neighbors": 2,
        },
        "mining": {
            "miners": 2,
            "hashrate": 1000.0,
            "blocktime": 10.0,
            "blocksize": 100,
            "difficulty": None,
            "retarget_interval": 2016,
        },
        "economics": {
            "initial_reward": 50.0,
            "halving_interval": 10,
            "max_halvings": 3,
        },
        "transactions": {
            "wallets": 2,
            "transactions_per_wallet": 5,
            "interval": 1.0,
        },
        "simulation": {
            "blocks": 5,
            "years": None,
            "print_interval": 9999,
            "debug": False,
            "seed": 42,
        },
    }


@pytest.fixture
def seeded_random():
    """Set random seed for reproducible tests."""
    random.seed(42)
    yield
    # Reset to random state after test
    random.seed()


@pytest.fixture
def simpy_env() -> simpy.Environment:
    """Create a fresh SimPy environment."""
    return simpy.Environment()


@pytest.fixture
def empty_mempool() -> deque:
    """Create an empty transaction mempool."""
    return deque()


@pytest.fixture
def sample_mempool() -> deque:
    """Create a mempool with sample transactions."""
    pool = deque()
    for i in range(10):
        pool.append((i % 3, float(i * 10)))  # (wallet_id, timestamp)
    return pool


# Chain-specific configs for validation tests
@pytest.fixture
def btc_config(mini_config) -> Dict[str, Any]:
    """Bitcoin-like configuration."""
    config = mini_config.copy()
    config["mining"]["blocktime"] = 600.0
    config["economics"]["halving_interval"] = 210000
    return config


@pytest.fixture
def fast_btc_config(mini_config) -> Dict[str, Any]:
    """Fast Bitcoin config for integration tests."""
    config = mini_config.copy()
    config["mining"]["blocktime"] = 1.0  # 1 second blocks
    config["simulation"]["blocks"] = 10
    return config
