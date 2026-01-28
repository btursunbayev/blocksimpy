#!/usr/bin/env python3
"""
51% Attack (Double Spend) implementation.

The 51% attack is when an attacker with majority hashrate can:
1. Send payment to victim (on public chain)
2. Secretly mine a private chain without that payment
3. Once private chain is longer, release it to orphan the payment

Success depends on:
- Attacker hashrate (>50% guarantees success, <50% probabilistic)
- Number of confirmations victim waits for
- Race between attacker's private chain and honest chain

Reference: Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System" (2008)
"""

from dataclasses import dataclass


@dataclass
class DoubleSpendState:
    """
    Tracks the state of a double spend attack attempt.

    The attacker tries to build a private chain that will
    eventually overtake the honest chain.
    """

    # Chain tracking
    private_chain_length: int = 0  # Attacker's secret chain
    honest_chain_length: int = 0  # Public chain length

    # Attack phases
    # 0 = not started, 1 = mining privately, 2 = succeeded, 3 = failed
    phase: int = 0

    # Configuration
    target_confirmations: int = 6  # How many confirms before victim accepts

    # Metrics
    attack_attempts: int = 0  # How many attack attempts
    successful_attacks: int = 0  # Attacks where private chain won
    failed_attacks: int = 0  # Attacks where honest chain won
    blocks_until_success: int = 0  # Blocks needed to catch up

    # Revenue
    attacker_rewards: float = 0.0
    honest_rewards: float = 0.0
    double_spent_value: float = 0.0  # Total value successfully double-spent

    def start_attack(self) -> None:
        """Begin a new double spend attempt."""
        self.attack_attempts += 1
        self.phase = 1  # Mining privately
        self.private_chain_length = 0
        self.honest_chain_length = 0
        self.blocks_until_success = 0

    def attacker_found_block(self, reward: float) -> str:
        """Attacker found a block on private chain."""
        self.private_chain_length += 1
        self.attacker_rewards += reward
        self.blocks_until_success += 1

        # Check if we've caught up and can release
        if self.private_chain_length > self.honest_chain_length:
            return "private_longer"
        return "extend_private"

    def honest_found_block(self, reward: float) -> str:
        """Honest miner found a block on public chain."""
        self.honest_chain_length += 1
        self.honest_rewards += reward

        # Check if attack should be abandoned
        # Abandon if honest chain gets too far ahead (e.g., 2x confirmations)
        if self.honest_chain_length > self.target_confirmations * 2:
            self.phase = 3  # Failed
            self.failed_attacks += 1
            return "attack_failed"

        # Check if victim would accept payment now
        if self.honest_chain_length >= self.target_confirmations:
            # Victim accepted, now race to catch up
            if self.private_chain_length > self.honest_chain_length:
                self.phase = 2  # Success!
                self.successful_attacks += 1
                self.double_spent_value += reward * self.target_confirmations
                return "attack_succeeded"

        return "continue"

    def get_metrics(self) -> dict:
        """Return attack metrics."""
        success_rate = (
            self.successful_attacks / self.attack_attempts
            if self.attack_attempts > 0
            else 0
        )

        return {
            "attack_type": "double_spend_51",
            "attack_attempts": self.attack_attempts,
            "successful_attacks": self.successful_attacks,
            "failed_attacks": self.failed_attacks,
            "success_rate": success_rate,
            "double_spent_value": self.double_spent_value,
            "attacker_rewards": self.attacker_rewards,
            "honest_rewards": self.honest_rewards,
            "target_confirmations": self.target_confirmations,
        }


class DoubleSpendMiner:
    """
    A miner that attempts 51% double spend attacks.

    Builds private chain to try to orphan payments on public chain.
    """

    def __init__(self, miner_id: int, hashrate: float, target_confirmations: int = 6):
        """Initialize double spend attacker."""
        self.id = miner_id
        self.h = hashrate
        self.is_attacker = True
        self.attack_type = "double_spend"
        self.state = DoubleSpendState(target_confirmations=target_confirmations)

        # Start first attack immediately
        self.state.start_attack()

    def mine(self, env, difficulty: float, block_found_event):
        """Mine like a regular miner."""
        import random

        mining_time = random.expovariate(self.h / difficulty)
        mining_timeout = env.timeout(mining_time)

        race_result = yield env.any_of([mining_timeout, block_found_event])

        if mining_timeout in race_result and not block_found_event.triggered:
            block_found_event.succeed(self)

        yield block_found_event

    def on_block_found(self, is_attacker_block: bool, reward: float) -> str:
        """Called when any block is found."""
        if self.state.phase == 0:
            # No attack in progress, start one
            self.state.start_attack()

        if is_attacker_block:
            result = self.state.attacker_found_block(reward)
        else:
            result = self.state.honest_found_block(reward)

        # If attack ended, start a new one
        if result in ("attack_succeeded", "attack_failed"):
            self.state.start_attack()

        return result

    def get_attack_metrics(self) -> dict:
        """Return current attack metrics."""
        return self.state.get_metrics()
