#!/usr/bin/env python3
"""
Blockchain simulation coordinator and main event loop.

This module implements the central coordination logic for the blockchain discrete
event simulation. The coordinator manages mining rounds, difficulty adjustments,
transaction processing, block creation, network propagation, and comprehensive
metrics tracking.

Core Responsibilities:
- Mining competition coordination between multiple miners
- Dynamic difficulty adjustment every 2016 blocks (Bitcoin-like)
- Transaction mempool management with FIFO block inclusion
- Economic model with block rewards and halving schedule
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


class SimulationCoordinator:
    """
    Central coordinator for blockchain discrete event simulation.
    
    Manages all aspects of the blockchain simulation including mining competition,
    difficulty adjustments, transaction processing, economic modeling, and metrics
    collection. Implements realistic blockchain behavior with configurable parameters
    for research and analysis purposes.
    
    Key Features:
        - Realistic mining competition using exponential timing
        - Dynamic difficulty adjustment (every 2016 blocks)
        - Transaction mempool with FIFO block inclusion
        - Economic model with rewards and halving events
        - Network propagation simulation with bandwidth tracking
        - Comprehensive metrics and progress reporting
    
    Attributes:
        config (Dict): Complete simulation configuration parameters
        network_data (int): Total bytes transmitted across network
        io_requests (int): Total network I/O operations performed
        total_tx (int): Cumulative transactions confirmed in blocks
        total_coins (float): Total coins issued through mining rewards
        pool (List): Unconfirmed transaction pool (mempool)
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
            2. For each block:
               a. Check termination conditions (blocks limit, transactions done)
               b. Adjust difficulty every 2016 blocks (Bitcoin-like retargeting)
               c. Start mining competition between all miners
               d. Create new block when miner succeeds
               e. Process transactions from mempool (FIFO, up to block size)
               f. Apply economic model (rewards, halving events)
               g. Propagate block through network
               h. Update metrics and generate reports
            3. Continue until simulation completion
            
        Termination Conditions:
            - Block limit reached (if --blocks specified)
            - All wallet transactions confirmed (if no block limit)
            
        Yields:
            SimPy generator that drives the entire simulation
        """
        # Extract configuration parameters
        bt = self.config['mining']['blocktime']          # Target block time
        diff0 = self.config['mining']['difficulty']      # Initial difficulty (None = auto)
        blocks_limit = self.config['simulation']['blocks']  # Max blocks (None = unlimited)
        blk_sz = self.config['mining']['blocksize']      # Max transactions per block
        print_int = self.config['simulation']['print_interval']  # Reporting frequency
        dbg = self.config['simulation']['debug']         # Debug output flag
        wallets = self.config['transactions']['wallets'] # Number of wallets
        tx_per_wallet = self.config['transactions']['transactions_per_wallet']
        init_reward = self.config['economics']['initial_reward']  # Initial block reward
        halving_interval = self.config['economics']['halving_interval']  # Blocks between halvings
        
        # Initialize simulation state variables
        bc = 0        # Block count (total blocks mined)
        lt = 0        # Last block time (for inter-block timing)
        la = 0        # Last adjustment time (for difficulty retargeting)
        ba = 0        # Blocks since adjustment (for 2016-block cycles)
        
        # Progress tracking for reporting
        last_t = last_b = last_tx = last_coins = 0
        
        # Initialize mining difficulty
        # Auto-calculate as blocktime * total_hashrate if not specified
        th = sum(m.h for m in miners)  # Total network hashrate
        diff = diff0 if diff0 is not None else bt * th
        
        # Initialize economic model
        reward = init_reward    # Current block reward
        halvings = 0           # Number of halvings completed
        max_halvings = self.config['economics']['max_halvings']
        
        # Transaction processing setup
        has_tx = tx_per_wallet > 0
        total_needed = wallets * tx_per_wallet if has_tx else None
        pool_processed = 0     # Transactions included in blocks so far

        while True:
            if blocks_limit is not None and bc >= blocks_limit:
                break
            if has_tx and pool_processed >= total_needed:
                break

            # Difficulty retarget every 2016 blocks
            if diff0 is None and ba >= 2016:
                elapsed = env.now - la
                actual_avg = elapsed / ba if ba else bt
                factor = bt / actual_avg if actual_avg > 0 else 1
                diff *= factor
                la = env.now
                ba = 0
                if dbg:
                    print(f"[{env.now:.2f}] Diff:{human(diff)} H:{human(th)} "
                          f"Tx:{self.total_tx} C:{human(self.total_coins)} Pool:{len(self.pool)} "
                          f"infl:N/A NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")

            # Mining round
            ev = env.event()
            for m in miners:
                env.process(m.mine(env, diff, ev))
            winner = yield ev

            # New block
            dt = env.now - lt
            lt = env.now
            bc += 1
            ba += 1

            if has_tx:
                avail = len(self.pool)
                take = min(avail, blk_sz)
                pool_processed += take
                for _ in range(take):
                    self.pool.pop(0)
                txs = take + 1
            else:
                txs = 1

            b = Block(bc, txs, dt)
            self.total_tx += txs

            # Mint reward and halving
            if halvings < max_halvings:
                self.total_coins += reward
            if halving_interval > 0 and bc % halving_interval == 0 and halvings < max_halvings:
                halvings += 1
                reward = reward / 2 if halvings < max_halvings else 0

            env.process(random.choice(nodes).receive(b))

            # Logging / summary (same as original)
            if dbg:
                print(f"[{env.now:.2f}] B{b.id} by M{winner.id} dt:{b.dt:.2f}s "
                      f"Diff:{human(diff)} H:{human(th)} Tx:{self.total_tx} "
                      f"C:{human(self.total_coins)} Pool:{len(self.pool)} "
                      f"infl:N/A NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")
            elif bc % print_int == 0:
                pct = (bc / blocks_limit) * 100 if blocks_limit else 0
                ti = env.now - last_t
                dtx = self.total_tx - last_tx
                dcoins = self.total_coins - last_coins
                abt = ti / (bc - last_b) if bc - last_b else 0
                tps = dtx / ti if ti > 0 else 0
                infl = (dcoins / last_coins) * (YEAR / ti) * 100 if last_coins > 0 else 0
                eta = (blocks_limit - bc) * abt if blocks_limit else 0
                print(f"[{env.now:.2f}] Sum B:{bc}/{blocks_limit} {pct:.1f}% abt:{abt:.2f}s "
                      f"tps:{tps:.2f} infl:{infl:.2f}% ETA:{eta:.2f}s "
                      f"Diff:{human(diff)} H:{human(th)} Tx:{self.total_tx} "
                      f"C:{human(self.total_coins)} Pool:{len(self.pool)} "
                      f"NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")
                last_t, last_b, last_tx, last_coins = env.now, bc, self.total_tx, self.total_coins

        # Final summary (same as original)
        total_time = env.now
        abt = total_time / bc if bc else 0
        tps_total = self.total_tx / total_time if total_time > 0 else 0
        infl_total = (self.total_coins - last_coins) / last_coins * (YEAR / total_time) * 100 if last_coins > 0 else 0
        if blocks_limit:
            print(f"[******] End B:{bc}/{blocks_limit} 100.0% abt:{abt:.2f}s tps:{tps_total:.2f} "
                  f"infl:{infl_total:.2f}% Diff:{human(diff)} H:{human(th)} "
                  f"Tx:{self.total_tx} C:{human(self.total_coins)} Pool:{len(self.pool)} "
                  f"NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")
        else:
            print(f"[******] End B:{bc} abt:{abt:.2f}s tps:{tps_total:.2f} "
                  f"infl:{infl_total:.2f}% Diff:{human(diff)} H:{human(th)} "
                  f"Tx:{self.total_tx} C:{human(self.total_coins)} Pool:{len(self.pool)} "
                  f"NMB:{self.network_data/1e6:.2f} IO:{self.io_requests}")