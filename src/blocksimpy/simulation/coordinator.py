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

import simpy
import random
from typing import List, Dict, Any, Optional
from ..core.block import Block
from ..core.node import Node
from ..core.miner import Miner
from ..utils.formatting import human, YEAR
from ..utils.network_optimizer import NetworkPropagationOptimizer


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
        pool (List): Unconfirmed transaction pool (mempool)
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
        
        # Network metrics tracking
        self.network_data = 0      # Total bytes transmitted (for bandwidth analysis)
        self.io_requests = 0       # Total I/O operations (for network load analysis)
        
        # Blockchain state tracking  
        self.total_tx = 0          # Cumulative confirmed transactions
        self.total_coins = 0.0     # Total coins issued via mining rewards
        
        # Transaction mempool (unconfirmed transaction pool)
        self.pool: List[tuple] = []  # Format: [(wallet_id, timestamp), ...]
        
        # Network optimizer (initialized later when nodes are created)
        self.network_optimizer: Optional[NetworkPropagationOptimizer] = None
    
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
        target_blocktime = self.config['mining']['blocktime']
        initial_difficulty = self.config['mining']['difficulty']  # None = auto-calculate
        blocks_limit = self.config['simulation']['blocks']  # None = unlimited
        block_size = self.config['mining']['blocksize']
        print_interval = self.config['simulation']['print_interval']
        debug_mode = self.config['simulation']['debug']
        wallets = self.config['transactions']['wallets']
        tx_per_wallet = self.config['transactions']['transactions_per_wallet']
        init_reward = self.config['economics']['initial_reward']
        halving_interval = self.config['economics']['halving_interval']
        
        # Initialize network propagation optimizer
        # Pre-computes block propagation paths using BFS for optimal performance
        if nodes:
            self.network_optimizer = NetworkPropagationOptimizer(nodes)
        else:
            self.network_optimizer = None
        
        # Initialize simulation state variables
        block_count = 0
        last_block_time = 0
        last_adjustment_time = 0
        blocks_since_adjustment = 0
        
        # Progress tracking for reporting
        last_t = last_b = last_tx = last_coins = 0
        
        # Initialize mining difficulty
        # Auto-calculate as blocktime * total_hashrate if not specified
        total_hashrate = sum(m.h for m in miners)
        difficulty = initial_difficulty if initial_difficulty is not None else target_blocktime * total_hashrate
        
        # Cache total hashrate for performance (miners don't change during simulation)
        total_hashrate_str = human(total_hashrate)  # Pre-format for logging
        
        # Initialize economic model
        reward = init_reward    # Current block reward
        halvings = 0           # Number of halvings completed
        max_halvings = self.config['economics']['max_halvings']
        
        # Transaction processing setup
        has_tx = tx_per_wallet > 0
        total_needed = wallets * tx_per_wallet if has_tx else None
        pool_processed = 0

        while True:
            # Check block limit first - if specified, it takes precedence
            if blocks_limit is not None and block_count >= blocks_limit:
                break
            # Only check transaction completion if we have transactions AND no block limit
            # (if block limit is set, keep mining until we hit it)
            if blocks_limit is None and has_tx and total_needed > 0 and pool_processed >= total_needed:
                break

            # Difficulty retarget every 2016 blocks
            if initial_difficulty is None and blocks_since_adjustment >= 2016:
                elapsed = env.now - last_adjustment_time
                actual_avg = elapsed / blocks_since_adjustment if blocks_since_adjustment else target_blocktime
                factor = target_blocktime / actual_avg if actual_avg > 0 else 1
                difficulty *= factor
                last_adjustment_time = env.now
                blocks_since_adjustment = 0
                if debug_mode:
                    print(f"[{env.now:.2f}] Diff:{human(difficulty)} H:{total_hashrate_str} "
                          f"Tx:{self.total_tx} C:{human(self.total_coins)} Pool:{len(self.pool)} "
                          f"infl:N/A NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")

            # Mining round
            block_found_event = env.event()
            for m in miners:
                env.process(m.mine(env, difficulty, block_found_event))
            winner = yield block_found_event

            # New block
            time_since_last = env.now - last_block_time
            last_block_time = env.now
            block_count += 1
            blocks_since_adjustment += 1

            if has_tx:
                avail = len(self.pool)
                take = min(avail, block_size)
                pool_processed += take
                for _ in range(take):
                    self.pool.pop(0)
                txs = take + 1
            else:
                txs = 1

            b = Block(block_count, txs, time_since_last)
            self.total_tx += txs

            # Mint reward and halving
            if halvings < max_halvings:
                self.total_coins += reward
            if halving_interval > 0 and block_count % halving_interval == 0 and halvings < max_halvings:
                halvings += 1
                reward = reward / 2 if halvings < max_halvings else 0

            # Propagate block through network using optimized graph-based algorithm
            # Uses pre-computed BFS paths for 5-10x performance improvement
            start_node = random.choice(nodes)
            self.network_optimizer.propagate_block(b, start_node, self)

            # Logging / summary
            if debug_mode:
                print(f"[{env.now:.2f}] B{b.id} by M{winner.id} dt:{b.dt:.2f}s "
                      f"Diff:{human(difficulty)} H:{total_hashrate_str} Tx:{self.total_tx} "
                      f"C:{human(self.total_coins)} Pool:{len(self.pool)} "
                      f"infl:N/A NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")
            elif block_count % print_interval == 0:
                pct = (block_count / blocks_limit) * 100 if blocks_limit else 0
                ti = env.now - last_t
                dtx = self.total_tx - last_tx
                dcoins = self.total_coins - last_coins
                abt = ti / (block_count - last_b) if block_count - last_b else 0
                tps = dtx / ti if ti > 0 else 0
                infl = (dcoins / last_coins) * (YEAR / ti) * 100 if last_coins > 0 else 0
                eta = (blocks_limit - block_count) * abt if blocks_limit else 0
                print(f"[{env.now:.2f}] Sum B:{block_count}/{blocks_limit} {pct:.1f}% abt:{abt:.2f}s "
                      f"tps:{tps:.2f} infl:{infl:.2f}% ETA:{eta:.2f}s "
                      f"Diff:{human(difficulty)} H:{total_hashrate_str} Tx:{self.total_tx} "
                      f"C:{human(self.total_coins)} Pool:{len(self.pool)} "
                      f"NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")
                last_t, last_b, last_tx, last_coins = env.now, block_count, self.total_tx, self.total_coins

        # Final summary
        total_time = env.now
        abt = total_time / block_count if block_count else 0
        tps_total = self.total_tx / total_time if total_time > 0 else 0
        
        # Calculate annualized inflation rate
        if block_count > 0 and total_time > 0 and last_coins > 0:
            coins_issued_this_period = self.total_coins - last_coins
            period_duration = total_time - last_t
            if period_duration > 0:
                infl_total = (coins_issued_this_period / last_coins) * (YEAR / period_duration) * 100
            else:
                infl_total = 0
        else:
            infl_total = 0
        
        # Store final results for timing display in main
        self.final_simulated_time = total_time
        self.final_blocks = block_count
        
        if blocks_limit:
            print(f"[******] End B:{block_count}/{blocks_limit} 100.0% abt:{abt:.2f}s tps:{tps_total:.2f} "
                  f"infl:{infl_total:.2f}% Diff:{human(difficulty)} H:{total_hashrate_str} "
                  f"Tx:{self.total_tx} C:{human(self.total_coins)} Pool:{len(self.pool)} "
                  f"NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")
        else:
            print(f"[******] End B:{block_count} abt:{abt:.2f}s tps:{tps_total:.2f} "
                  f"infl:{infl_total:.2f}% Diff:{human(difficulty)} H:{total_hashrate_str} "
                  f"Tx:{self.total_tx} C:{human(self.total_coins)} Pool:{len(self.pool)} "
                  f"NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")