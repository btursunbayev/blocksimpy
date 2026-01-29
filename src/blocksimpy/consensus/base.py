"""
Base class for consensus block producers.

All consensus mechanisms (PoW miners, PoS validators, etc.) inherit from this.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import simpy


class BlockProducer(ABC):
    """
    Abstract base class for block producers in any consensus mechanism.

    Subclasses must implement:
        - produce_block(): The consensus-specific block production logic
    """

    def __init__(self, producer_id: int):
        """
        Initialize block producer.

        Args:
            producer_id: Unique identifier (0, 1, 2, ...)
        """
        self.id = producer_id

    @abstractmethod
    def produce_block(
        self,
        env: "simpy.Environment",
        difficulty: float,
        block_found_event: "simpy.Event",
    ):
        """
        Attempt to produce a block using consensus-specific logic.

        Args:
            env: SimPy simulation environment
            difficulty: Current network difficulty (interpretation varies by consensus)
            block_found_event: Event to trigger when block is produced

        Yields:
            SimPy generator
        """
        pass

    def get_weight(self) -> float:
        """
        Get producer's weight for block production probability.

        For PoW: hashrate
        For PoS: stake amount

        Returns:
            Weight value (higher = more likely to produce blocks)
        """
        return 1.0
