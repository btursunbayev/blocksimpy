#!/usr/bin/env python3
"""
Transaction generation and wallet simulation for blockchain networks.

This module implements wallet behavior that generates transactions at realistic
intervals and submits them to the unconfirmed transaction pool. Multiple wallets
operate concurrently to create realistic transaction load patterns.

Transaction Generation:
- Each wallet generates a specified number of transactions
- Transactions are created at regular intervals (Poisson-like process)
- All transactions go into a global unconfirmed pool (mempool)
- Transactions include wallet ID and timestamp for tracking
"""

from typing import List, Tuple

import simpy


def wallet(
    env: simpy.Environment,
    wallet_id: int,
    transaction_count: int,
    interval: float,
    transaction_pool: List[Tuple[int, float]],
):
    """
    Simulate a wallet that generates transactions over time.

    Creates a realistic transaction generation pattern where a wallet
    periodically creates new transactions and submits them to the global
    unconfirmed transaction pool. Multiple wallets can operate concurrently
    to simulate realistic network transaction load.

    Args:
        env: SimPy discrete event simulation environment
        wallet_id: Unique identifier for this wallet (0, 1, 2, ...)
        transaction_count: Total number of transactions this wallet will create
        interval: Time delay between transactions in seconds
        transaction_pool: Global list storing unconfirmed transactions (mempool)

    Transaction Flow:
        1. Wait for specified interval (inter-transaction delay)
        2. Create new transaction with wallet ID and timestamp
        3. Add transaction to global unconfirmed pool
        4. Repeat until all transactions generated

    Transaction Format:
        Each transaction is stored as (wallet_id, timestamp) tuple in the pool.
        Real implementations would include recipient, amount, fees, etc.

    Yields:
        SimPy process that completes when all transactions are generated

    Note:
        Transactions remain in the pool until miners include them in blocks.
        Block creation removes transactions from pool (FIFO order) up to
        the maximum block size limit.
    """
    for tx_index in range(transaction_count):
        # Wait for next transaction timing (regular intervals)
        yield env.timeout(interval)

        # Create transaction with wallet ID and current simulation time
        transaction = (wallet_id, env.now)
        transaction_pool.append(transaction)

        # Optional: Log transaction creation for debugging
        # print(f"Wallet {wallet_id} created tx #{tx_index + 1} at time {env.now:.2f}")


def create_wallets(
    env: simpy.Environment,
    wallet_count: int,
    transactions_per_wallet: int,
    interval: float,
    transaction_pool: List[Tuple[int, float]],
) -> List[simpy.Process]:
    """
    Create and start multiple wallet processes for concurrent transaction generation.

    Args:
        env: SimPy simulation environment
        wallet_count: Number of wallets to create
        transactions_per_wallet: Transactions each wallet will generate
        interval: Time between transactions per wallet
        transaction_pool: Shared transaction pool for all wallets

    Returns:
        List of SimPy processes for all wallet operations

    Note:
        All wallets start immediately and operate concurrently, creating
        overlapping transaction generation patterns that simulate realistic
        network behavior with multiple active users.
    """
    wallet_processes = []
    for wallet_id in range(wallet_count):
        process = env.process(
            wallet(env, wallet_id, transactions_per_wallet, interval, transaction_pool)
        )
        wallet_processes.append(process)
    return wallet_processes
