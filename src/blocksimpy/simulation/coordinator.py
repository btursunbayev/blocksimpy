#!/usr/bin/env python3
"""
Blockchain simulation coordinator and main event loop.

This module implements the central coordination logic for the blockchain discrete
event simulation. The coordinator manages mining rounds, difficulty adjustments,
transaction processing, block creation, network propagation using graph-based
optimization, and comprehensive metrics tracking.

Core Responsibilities:
- Mining competition coordination between multiple miners
- Dynamic difficulty adjustment every 2016 blocks (Bitcoin-like)
- Transaction mempool management with FIFO block inclusion
- Economic model with block rewards and halving schedule
- Optimized network propagation using pre-computed BFS paths (5-10x speedup)
- Network metrics tracking (bandwidth, I/O operations)
- Comprehensive reporting and progress monitoring
"""

import random
from collections import deque
from typing import Any, Deque, Dict, List, Optional

import simpy

from ..core.block import Block
from ..core.miner import Miner
from ..core.node import Node
from ..utils.formatting import YEAR, human
from ..utils.network_optimizer import NetworkPropagationOptimizer
from .metrics import SimulationMetrics
from .state import SimulationState


class SimulationCoordinator:
    """
    Central coordinator for blockchain discrete event simulation.

    Manages all aspects of the blockchain simulation including mining competition,
    difficulty adjustments, transaction processing, economic modeling, optimized
    network propagation, and metrics collection. Implements realistic blockchain
    behavior with configurable parameters for research and analysis purposes.

    Key Features:
        - Realistic mining competition using exponential timing
        - Dynamic difficulty adjustment (every 2016 blocks)
        - Transaction mempool with FIFO block inclusion
        - Economic model with rewards and halving events
        - Optimized network propagation using pre-computed BFS paths (5-10x speedup)
        - Network bandwidth and I/O tracking
        - Comprehensive metrics and progress reporting

    Attributes:
        config (Dict): Complete simulation configuration parameters
        network_data (int): Total bytes transmitted across network
        io_requests (int): Total network I/O operations performed
        total_tx (int): Cumulative transactions confirmed in blocks
        total_coins (float): Total coins issued through mining rewards
        pool (Deque): Unconfirmed transaction pool (mempool, using deque for O(1) FIFO)
        network_optimizer (NetworkPropagationOptimizer): Graph-based network propagation optimizer
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize simulation coordinator with configuration.

        Args:
            config: Complete configuration dictionary with all simulation parameters
                   including network, mining, economics, transactions, and simulation settings
        """
        self.config = config

        # Metrics tracking (network, performance)
        self.metrics = SimulationMetrics()

        # Final results (set after simulation completes)
        self.final_simulated_time = 0.0
        self.final_blocks = 0
        self.total_tx = 0
        self.total_coins = 0.0

        # Transaction mempool
        self.pool: Deque[tuple] = deque()  # (wallet_id, timestamp) tuples

        # Network optimizer (initialized later when nodes are created)
        self.network_optimizer: Optional[NetworkPropagationOptimizer] = None

    @property
    def network_data(self) -> int:
        """Total bytes transmitted across network."""
        return self.metrics.network_data

    @property
    def io_requests(self) -> int:
        """Total network I/O operations performed."""
        return self.metrics.io_requests

    def coord(self, env: simpy.Environment, nodes: List[Node], miners: List[Miner]):
        """
        Main coordination loop for blockchain discrete event simulation.

        Implements the complete blockchain simulation algorithm including mining
        competition, difficulty adjustment, transaction processing, and economic
        modeling. Runs until termination conditions are met (block limit reached
        or all transactions processed).

        Args:
            env: SimPy discrete event simulation environment
            nodes: List of network nodes for block propagation
            miners: List of miners competing to discover blocks

        Simulation Algorithm:
            1. Initialize difficulty and economic parameters
            2. Build network propagation optimizer (if enabled)
            3. For each block:
               a. Check termination conditions (blocks limit, transactions done)
               b. Adjust difficulty every 2016 blocks (Bitcoin-like retargeting)
               c. Start mining competition between all miners
               d. Create new block when miner succeeds
               e. Process transactions from mempool (FIFO, up to block size)
               f. Apply economic model (rewards, halving events)
               g. Propagate block through network (optimized or standard)
               h. Update metrics and generate reports
            4. Continue until simulation completion

        Termination Conditions:
            - Block limit reached (if --blocks specified)
            - All wallet transactions confirmed (if no block limit)

        Yields:
            SimPy generator that drives the entire simulation
        """
        # Extract configuration parameters
        target_blocktime = self.config["mining"]["blocktime"]
        initial_difficulty = self.config["mining"][
            "difficulty"
        ]  # None = auto-calculate
        blocks_limit = self.config["simulation"]["blocks"]  # None = unlimited
        block_size = self.config["mining"]["blocksize"]
        print_interval = self.config["simulation"]["print_interval"]
        debug_mode = self.config["simulation"]["debug"]
        wallets = self.config["transactions"]["wallets"]
        tx_per_wallet = self.config["transactions"]["transactions_per_wallet"]
        init_reward = self.config["economics"]["initial_reward"]
        halving_interval = self.config["economics"]["halving_interval"]
        retarget_interval = self.config["mining"].get("retarget_interval", 2016)

        # Initialize network propagation optimizer
        # Pre-computes block propagation paths using BFS for optimal performance
        if nodes:
            self.network_optimizer = NetworkPropagationOptimizer(nodes)
        else:
            self.network_optimizer = None

        # Initialize simulation state (serializable for checkpoint/resume)
        total_hashrate = sum(m.h for m in miners)
        state = SimulationState.from_config(self.config, total_hashrate)

        # Local aliases for frequently accessed state (readability)
        difficulty = state.difficulty
        reward = state.reward

        # Cache total hashrate for performance (miners don't change during simulation)
        total_hashrate_str = human(total_hashrate)  # Pre-format for logging

        # Economic model config
        max_halvings = self.config["economics"]["max_halvings"]
        # Treat None as infinity (always issue rewards)
        if max_halvings is None:
            max_halvings = float("inf")

        # Transaction processing setup
        has_tx = tx_per_wallet > 0
        total_needed = wallets * tx_per_wallet if has_tx else None

        while True:
            # Check block limit first - if specified, it takes precedence
            if blocks_limit is not None and state.block_count >= blocks_limit:
                break
            # Only check transaction completion if we have transactions AND no block limit
            # (if block limit is set, keep mining until we hit it)
            if (
                blocks_limit is None
                and has_tx
                and total_needed > 0
                and state.pool_processed >= total_needed
            ):
                break

            # Difficulty retarget every retarget_interval blocks
            if (
                initial_difficulty is None
                and state.blocks_since_adjustment >= retarget_interval
            ):
                elapsed = env.now - state.last_adjustment_time
                actual_avg = (
                    elapsed / state.blocks_since_adjustment
                    if state.blocks_since_adjustment
                    else target_blocktime
                )
                factor = target_blocktime / actual_avg if actual_avg > 0 else 1
                difficulty *= factor
                state.difficulty = difficulty
                state.last_adjustment_time = env.now
                state.blocks_since_adjustment = 0
                if debug_mode:
                    print(
                        f"[{env.now:.2f}] Diff:{human(difficulty)} H:{total_hashrate_str} "
                        f"Tx:{state.total_tx} C:{human(state.total_coins)} Pool:{len(self.pool)} "
                        f"infl:N/A NMB:{self.metrics.network_data / 1e6:.2f} IO:{self.metrics.io_requests}"
                    )

            # Mining round
            block_found_event = env.event()
            for m in miners:
                env.process(m.mine(env, difficulty, block_found_event))
            winner = yield block_found_event

            # New block
            time_since_last = env.now - state.last_block_time
            state.last_block_time = env.now
            state.block_count += 1
            state.blocks_since_adjustment += 1

            if has_tx:
                avail = len(self.pool)
                take = min(avail, block_size)
                state.pool_processed += take
                for _ in range(take):
                    self.pool.popleft()
                txs = take + 1
            else:
                txs = 1

            b = Block(state.block_count, txs, time_since_last)
            state.total_tx += txs

            # Mint reward and halving
            if state.halvings < max_halvings:
                state.total_coins += reward
            if (
                halving_interval > 0
                and state.block_count % halving_interval == 0
                and state.halvings < max_halvings
            ):
                state.halvings += 1
                reward = reward / 2 if state.halvings < max_halvings else 0
                state.reward = reward

            # Propagate block through network using optimized graph-based algorithm
            # Uses pre-computed BFS paths for 5-10x performance improvement
            start_node = random.choice(nodes)
            self.network_optimizer.propagate_block(b, start_node, self)

            # Logging / summary
            if debug_mode:
                print(
                    f"[{env.now:.2f}] B{b.id} by M{winner.id} dt:{b.dt:.2f}s "
                    f"Diff:{human(difficulty)} H:{total_hashrate_str} Tx:{state.total_tx} "
                    f"C:{human(state.total_coins)} Pool:{len(self.pool)} "
                    f"infl:N/A NMB:{self.metrics.network_data / 1e6:.2f} IO:{self.metrics.io_requests}"
                )
            elif state.block_count % print_interval == 0:
                pct = (state.block_count / blocks_limit) * 100 if blocks_limit else 0
                ti = env.now - state.last_t
                dtx = state.total_tx - state.last_tx
                dcoins = state.total_coins - state.last_coins
                abt = (
                    ti / (state.block_count - state.last_b)
                    if state.block_count - state.last_b
                    else 0
                )
                tps = dtx / ti if ti > 0 else 0
                infl = (
                    (dcoins / state.last_coins) * (YEAR / ti) * 100
                    if state.last_coins > 0
                    else 0
                )
                eta = (blocks_limit - state.block_count) * abt if blocks_limit else 0
                print(
                    f"[{env.now:.2f}] Sum B:{state.block_count}/{blocks_limit} {pct:.1f}% abt:{abt:.2f}s "
                    f"tps:{tps:.2f} infl:{infl:.2f}% ETA:{eta:.2f}s "
                    f"Diff:{human(difficulty)} H:{total_hashrate_str} Tx:{state.total_tx} "
                    f"C:{human(state.total_coins)} Pool:{len(self.pool)} "
                    f"NMB:{self.metrics.network_data / 1e6:.2f} IO:{self.metrics.io_requests}"
                )
                state.last_t, state.last_b, state.last_tx, state.last_coins = (
                    env.now,
                    state.block_count,
                    state.total_tx,
                    state.total_coins,
                )

        # Final summary
        total_time = env.now

        # Finalize metrics (computes derived values)
        self.metrics.finalize(
            total_time=total_time,
            block_count=state.block_count,
            total_tx=state.total_tx,
            total_coins=state.total_coins,
            last_coins=state.last_coins,
            last_t=state.last_t,
        )

        abt = self.metrics.avg_block_time
        tps_total = self.metrics.transactions_per_second
        infl_total = self.metrics.inflation_rate

        # Sync final results for external access
        self.final_simulated_time = self.metrics.final_simulated_time
        self.final_blocks = self.metrics.final_blocks
        self.total_tx = state.total_tx
        self.total_coins = state.total_coins

        if blocks_limit:
            print(
                f"[******] End B:{state.block_count}/{blocks_limit} 100.0% abt:{abt:.2f}s tps:{tps_total:.2f} "
                f"infl:{infl_total:.2f}% Diff:{human(difficulty)} H:{total_hashrate_str} "
                f"Tx:{state.total_tx} C:{human(state.total_coins)} Pool:{len(self.pool)} "
                f"NMB:{self.metrics.network_data / 1e6:.2f} IO:{self.metrics.io_requests}"
            )
        else:
            print(
                f"[******] End B:{state.block_count} abt:{abt:.2f}s tps:{tps_total:.2f} "
                f"infl:{infl_total:.2f}% Diff:{human(difficulty)} H:{total_hashrate_str} "
                f"Tx:{state.total_tx} C:{human(state.total_coins)} Pool:{len(self.pool)} "
                f"NMB:{self.metrics.network_data / 1e6:.2f} IO:{self.metrics.io_requests}"
            )
