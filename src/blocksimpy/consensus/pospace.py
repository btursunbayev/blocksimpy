"""
Proof of Space (PoSpace) consensus implementation.

PoSpace farmers allocate disk space to participate in block production.
Selection is space-weighted, similar to PoS but based on committed storage.

Used by: Chia, Spacemesh
"""

import random

import simpy

from .base import BlockProducer


class PoSpaceFarmer(BlockProducer):
    """
    Proof of Space farmer producing blocks based on allocated space.

    Attributes:
        id: Unique farmer identifier
        space: Storage space committed in GB
    """

    def __init__(self, farmer_id: int, space: float):
        """
        Initialize PoSpace farmer.

        Args:
            farmer_id: Unique identifier
            space: Allocated storage in GB
        """
        super().__init__(farmer_id)
        self.space = space

    def get_weight(self) -> float:
        """Return space as weight for selection probability."""
        return self.space

    def produce_block(
        self,
        env: simpy.Environment,
        difficulty: float,
        block_found_event: simpy.Event,
    ):
        """
        Produce block as selected farmer.

        In PoSpace, the selected farmer immediately produces a block.
        No competition or puzzle solving.

        Args:
            env: SimPy environment
            difficulty: Not used in PoSpace (kept for interface compatibility)
            block_found_event: Event to signal block production
        """
        # Selected farmer produces block immediately
        if not block_found_event.triggered:
            block_found_event.succeed(self)

        yield block_found_event


def select_farmer(farmers: list, seed: float = None) -> PoSpaceFarmer:
    """
    Select a farmer weighted by allocated space.

    Uses space-weighted random selection similar to PoS stake selection.

    Args:
        farmers: List of PoSpaceFarmer instances
        seed: Random seed for reproducibility

    Returns:
        Selected farmer based on space-weighted probability
    """
    if seed is not None:
        random.seed(seed)

    weights = [f.get_weight() for f in farmers]
    total_weight = sum(weights)

    if total_weight == 0:
        return farmers[0]

    probabilities = [w / total_weight for w in weights]
    return random.choices(farmers, weights=probabilities, k=1)[0]
