"""Simulation state management for checkpoint/resume support."""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class SimulationState:
    """
    Holds all mutable simulation state for checkpoint/resume.

    This dataclass captures the complete state of a running simulation,
    enabling pause/resume functionality and state inspection.
    """

    # Block tracking
    block_count: int = 0
    last_block_time: float = 0.0

    # Difficulty adjustment tracking
    difficulty: float = 0.0
    last_adjustment_time: float = 0.0
    blocks_since_adjustment: int = 0

    # Economic state
    reward: float = 50.0
    halvings: int = 0
    total_coins: float = 0.0

    # Transaction state
    total_tx: int = 0
    pool_processed: int = 0

    # Progress tracking for reporting
    last_t: float = 0.0
    last_b: int = 0
    last_tx: int = 0
    last_coins: float = 0.0

    @classmethod
    def from_config(
        cls, config: Dict[str, Any], total_hashrate: float
    ) -> "SimulationState":
        """Create initial state from configuration."""
        initial_difficulty = config["mining"]["difficulty"]
        target_blocktime = config["mining"]["blocktime"]

        # Auto-calculate difficulty if not specified
        if initial_difficulty is not None:
            difficulty = initial_difficulty
        else:
            difficulty = target_blocktime * total_hashrate

        return cls(
            difficulty=difficulty,
            reward=config["economics"]["initial_reward"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export state as dictionary for checkpoint."""
        return {
            "block_count": self.block_count,
            "last_block_time": self.last_block_time,
            "difficulty": self.difficulty,
            "last_adjustment_time": self.last_adjustment_time,
            "blocks_since_adjustment": self.blocks_since_adjustment,
            "reward": self.reward,
            "halvings": self.halvings,
            "total_coins": self.total_coins,
            "total_tx": self.total_tx,
            "pool_processed": self.pool_processed,
            "last_t": self.last_t,
            "last_b": self.last_b,
            "last_tx": self.last_tx,
            "last_coins": self.last_coins,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationState":
        """Restore state from checkpoint dictionary."""
        return cls(**data)

    def save(self, filepath: str) -> None:
        """Save state to JSON file."""
        import json

        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "SimulationState":
        """Load state from JSON file."""
        import json

        with open(filepath, "r") as f:
            return cls.from_dict(json.load(f))
