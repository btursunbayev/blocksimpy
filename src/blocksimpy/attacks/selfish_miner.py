#!/usr/bin/env python3
"""
Selfish Mining attack implementation.

Selfish Mining is an attack strategy where a miner withholds discovered blocks
instead of broadcasting them immediately. The attacker builds a private chain
and releases it strategically to waste honest miners' work.


Strategy:
- When attacker finds a block: keep it private, extend private chain
- When honest miners find a block:
  - If private chain is longer: release to override honest chain
  - If chains are equal: race to propagate (gamma factor)
  - If attacker is behind: abandon private chain

Key metric: Attacker's relative revenue vs their hashrate share
- Honest mining: revenue = hashrate share
- Selfish mining: revenue > hashrate share (when alpha > threshold)
"""

from dataclasses import dataclass


@dataclass
class SelfishMinerState:
    """
    Tracks the state of a selfish mining attack.

    The attacker maintains a private chain and decides when to publish
    based on the lead over the honest chain.
    """

    # Chain lengths
    private_chain_length: int = 0  # Blocks attacker found but not published
    public_chain_length: int = 0  # Current honest chain length

    # Attack metrics
    attacker_blocks_won: int = 0  # Blocks that ended up in main chain (attacker)
    honest_blocks_won: int = 0  # Blocks that ended up in main chain (honest)
    wasted_honest_blocks: int = 0  # Honest blocks orphaned by attack

    # Revenue tracking
    attacker_rewards: float = 0.0
    honest_rewards: float = 0.0

    # State machine
    # 0: attacker has no lead
    # positive: attacker leads by N blocks
    lead: int = 0

    def attacker_found_block(self, reward: float) -> str:
        """
        Attacker found a new block. Always keep it private.

        Returns action taken: "extend_private"
        """
        self.private_chain_length += 1
        self.lead += 1
        return "extend_private"

    def honest_found_block(self, reward: float) -> str:
        """
        Honest miner found a block. Decide response based on lead.

        Returns action: "publish_all", "publish_one", "adopt_honest", "continue"
        """
        self.public_chain_length += 1

        if self.lead == 0:
            # No private chain, honest block wins
            self.honest_blocks_won += 1
            self.honest_rewards += reward
            return "adopt_honest"

        elif self.lead == 1:
            # Race condition - publish immediately to compete
            # Assume attacker wins race (gamma factor = 1 for simplicity)
            self.attacker_blocks_won += 1
            self.attacker_rewards += reward
            self.wasted_honest_blocks += 1
            self.private_chain_length = 0
            self.lead = 0
            return "publish_one"

        elif self.lead == 2:
            # Publish entire private chain to override honest block
            self.attacker_blocks_won += 2
            self.attacker_rewards += reward * 2
            self.wasted_honest_blocks += 1
            self.private_chain_length = 0
            self.lead = 0
            return "publish_all"

        else:
            # lead > 2: Keep extending, publish one to maintain lead
            self.attacker_blocks_won += 1
            self.attacker_rewards += reward
            self.wasted_honest_blocks += 1
            self.private_chain_length -= 1
            self.lead -= 1
            return "publish_one"

    def get_metrics(self) -> dict:
        """Return attack metrics."""
        total_blocks = self.attacker_blocks_won + self.honest_blocks_won
        attacker_share = (
            self.attacker_blocks_won / total_blocks if total_blocks > 0 else 0
        )

        return {
            "attacker_blocks": self.attacker_blocks_won,
            "honest_blocks": self.honest_blocks_won,
            "wasted_blocks": self.wasted_honest_blocks,
            "attacker_share": attacker_share,
            "attacker_rewards": self.attacker_rewards,
            "honest_rewards": self.honest_rewards,
            "private_chain_length": self.private_chain_length,
        }


class SelfishMiner:
    """
    A miner that implements selfish mining strategy.

    Same interface as regular Miner but tracks attack state.
    Used to replace one or more honest miners in simulation.
    """

    def __init__(self, miner_id: int, hashrate: float):
        """Initialize selfish miner with attack state tracking."""
        self.id = miner_id
        self.h = hashrate
        self.is_selfish = True  # Flag to identify this miner type
        self.state = SelfishMinerState()

    def mine(self, env, difficulty: float, block_found_event):
        """
        Mine like a regular miner.

        The selfish strategy is applied in the coordinator when deciding
        whether to propagate the block. This method just handles mining.
        """
        import random

        mining_time = random.expovariate(self.h / difficulty)
        mining_timeout = env.timeout(mining_time)

        race_result = yield env.any_of([mining_timeout, block_found_event])

        if mining_timeout in race_result and not block_found_event.triggered:
            block_found_event.succeed(self)

        yield block_found_event

    def on_block_found(self, is_attacker_block: bool, reward: float) -> str:
        """
        Called when any block is found. Returns strategy action.

        Args:
            is_attacker_block: True if this selfish miner found the block
            reward: Current block reward

        Returns:
            Action string for coordinator to handle
        """
        if is_attacker_block:
            return self.state.attacker_found_block(reward)
        else:
            return self.state.honest_found_block(reward)

    def get_attack_metrics(self) -> dict:
        """Return current attack metrics."""
        return self.state.get_metrics()
