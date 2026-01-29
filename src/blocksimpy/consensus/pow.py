"""
Proof of Work (PoW) consensus implementation.

PoW miners compete to solve cryptographic puzzles using hashrate.
Block production follows exponential distribution based on hashrate/difficulty.

Used by: Bitcoin, Litecoin, Dogecoin, Bitcoin Cash, Ethereum Classic
"""

import random

import simpy

from .base import BlockProducer


class PoWMiner(BlockProducer):
    """
    Proof of Work miner that competes to discover blocks.

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
        id: Unique miner identifier
        h: Hashrate (higher = faster mining)

    Mathematical Model:
        Expected time to find block = difficulty / total_network_hashrate
        Individual miner time ~ Exponential(individual_hashrate / difficulty)
    """

    def __init__(self, miner_id: int, hashrate: float):
        """
        Initialize PoW miner.

        Args:
            miner_id: Unique identifier
            hashrate: Mining power (H/s)
        """
        super().__init__(miner_id)
        self.h = hashrate

    def get_weight(self) -> float:
        """Return hashrate as weight."""
        return self.h

    def mine(
        self,
        env: simpy.Environment,
        difficulty: float,
        block_found_event: simpy.Event,
    ):
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
            SimPy generator that completes when mining attempt finishes
        """
        # Calculate mining attempt time using exponential distribution
        mining_time = random.expovariate(self.h / difficulty)
        mining_timeout = env.timeout(mining_time)

        # Race between this miner's attempt and block discovery by others
        race_result = yield env.any_of([mining_timeout, block_found_event])

        # If this miner won the race and no one else found the block yet
        if mining_timeout in race_result and not block_found_event.triggered:
            block_found_event.succeed(self)

        # Wait for block mining to complete
        yield block_found_event

    def produce_block(self, env, difficulty, block_found_event):
        """Alias for mine() to satisfy BlockProducer interface."""
        return self.mine(env, difficulty, block_found_event)


# Backward compatibility alias
Miner = PoWMiner
