"""
Proof of Stake (PoS) consensus implementation.

PoS validators are selected to produce blocks based on their stake amount.
No computational puzzle - selection is probabilistic based on stake weight.

Used by: Ethereum 2.0, Cardano, Solana, Polkadot, Tezos

Key differences from PoW:
- No mining competition (single validator selected per slot)
- Block time is deterministic (slot-based)
- Energy efficient (no hash computation)
- Stake = security deposit, can be slashed for misbehavior
"""

import random

import simpy

from .base import BlockProducer


class PoSValidator(BlockProducer):
    """
    Proof of Stake validator that produces blocks based on stake weight.

    In PoS, validators are selected proportionally to their stake.
    Block production is deterministic per slot (no racing).

    Attributes:
        id: Unique validator identifier
        stake: Amount of tokens staked (determines selection probability)
    """

    def __init__(self, validator_id: int, stake: float):
        """
        Initialize PoS validator.

        Args:
            validator_id: Unique identifier
            stake: Amount of tokens staked
        """
        super().__init__(validator_id)
        self.stake = stake

    def get_weight(self) -> float:
        """Return stake as weight for selection probability."""
        return self.stake

    def produce_block(
        self,
        env: simpy.Environment,
        difficulty: float,
        block_found_event: simpy.Event,
    ):
        """
        Produce a block as selected validator.

        In PoS, the selected validator immediately produces a block.
        No competition or puzzle solving.

        Args:
            env: SimPy environment
            difficulty: Not used in PoS (kept for interface compatibility)
            block_found_event: Event to signal block production
        """
        # Selected validator produces block immediately
        # (selection happens in coordinator before calling this)
        if not block_found_event.triggered:
            block_found_event.succeed(self)

        yield block_found_event


def select_validator(validators: list, seed: float = None) -> PoSValidator:
    """
    Select a validator weighted by stake.

    Uses stake-weighted random selection (like Ethereum 2.0 RANDAO).

    Args:
        validators: List of PoSValidator instances
        seed: Optional random seed for reproducibility

    Returns:
        Selected validator
    """
    if seed is not None:
        random.seed(seed)

    total_stake = sum(v.stake for v in validators)
    if total_stake == 0:
        return random.choice(validators)

    # Weighted random selection
    pick = random.uniform(0, total_stake)
    cumulative = 0
    for validator in validators:
        cumulative += validator.stake
        if pick <= cumulative:
            return validator

    return validators[-1]  # Fallback
