#!/usr/bin/env python3
"""
Blockchain miner implementation for Proof-of-Work simulation.

This module implements the Miner class representing individual mining entities
that compete to solve blocks using realistic Proof-of-Work timing based on
exponential distribution modeling and configurable hashrate parameters.

Mining Behavior:
- Each miner has configurable hashrate determining mining speed
- Block discovery follows exponential distribution (realistic PoW modeling)
- Mining competition between multiple miners for each block
- Winner-takes-all mining reward system
"""

import random
import simpy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..simulation.coordinator import SimulationCoordinator


class Miner:
    """
    Blockchain miner that competes to discover new blocks using Proof-of-Work.
    
    Implements realistic mining behavior with exponential distribution timing
    that models the probabilistic nature of Proof-of-Work mining competition.
    Multiple miners compete simultaneously for each block, with mining time
    determined by hashrate and current network difficulty.
    
    Mining Process:
        - Each miner attempts to solve the current block independently
        - Mining time follows exponential distribution: Exp(hashrate / difficulty)
        - First miner to complete wins the block and mining reward
        - All other miners immediately start on the next block
        
    Attributes:
        id (int): Unique miner identifier (0, 1, 2, ..., miners-1)
        h (float): Hashrate of this miner (higher = faster mining)
        
    Mathematical Model:
        Expected time to find block = difficulty / total_network_hashrate
        Individual miner time ~ Exponential(individual_hashrate / difficulty)
        This creates realistic mining competition and timing variance
    """
    
    def __init__(self, miner_id: int, hashrate: float):
        """
        Initialize a new blockchain miner.
        
        Args:
            miner_id: Unique identifier for this miner
            hashrate: Mining hashrate (higher values mine faster)
            
        Note:
            Hashrate should be positive. The total network hashrate
            (sum of all miners) determines overall block timing when
            combined with network difficulty setting.
        """
        self.id = miner_id
        self.h = hashrate  # Individual miner hashrate
    
    def mine(self, env: simpy.Environment, difficulty: float, block_found_event: simpy.Event):
        """
        Attempt to mine a block using realistic Proof-of-Work timing.
        
        Simulates the probabilistic mining process where miners compete
        to solve cryptographic puzzles. Uses exponential distribution
        to model realistic mining time variance based on hashrate and difficulty.
        
        Args:
            env: SimPy simulation environment
            difficulty: Current network mining difficulty
            block_found_event: Shared event that triggers when any miner succeeds
            
        Returns:
            SimPy event that completes when mining attempt finishes
            
        Mining Competition:
            1. Calculate mining time using exponential distribution
            2. Race against other miners and block discovery event
            3. If this miner wins, trigger the block_found_event
            4. Wait for block completion (either win or loss)
            
        Mathematical Model:
            Mining time ~ Exponential(hashrate / difficulty)
            Lower difficulty or higher hashrate = faster expected mining time
            Exponential distribution provides realistic timing variance
        """
        # Calculate mining attempt time using exponential distribution
        mining_time = random.expovariate(self.h / difficulty)
        mining_timeout = env.timeout(mining_time)
        
        # Race between this miner's attempt and block discovery by others
        race_result = yield env.any_of([mining_timeout, block_found_event])
        
        # If this miner won the race and no one else found the block yet
        if mining_timeout in race_result and not block_found_event.triggered:
            block_found_event.succeed(self)  # This miner wins the block
            
        # Wait for block mining to complete (either by this miner or others)
        yield block_found_event
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Miner(id={self.id}, hashrate={self.h})"
        
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Miner #{self.id}: {self.h:,.0f} H/s"