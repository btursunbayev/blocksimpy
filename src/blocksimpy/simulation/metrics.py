"""Simulation metrics tracking for analysis and export."""

from dataclasses import dataclass
from typing import Any, Dict

from ..utils.formatting import YEAR


@dataclass
class SimulationMetrics:
    """
    Collects simulation metrics for analysis and export.

    Separates observable metrics from mutable simulation state,
    enabling clean export to CSV/JSON and performance analysis.
    """

    # Network metrics
    network_data: int = 0  # Total bytes transmitted
    io_requests: int = 0  # Total I/O operations

    # Timing metrics
    final_simulated_time: float = 0.0
    final_blocks: int = 0

    # Performance metrics (computed at end)
    avg_block_time: float = 0.0
    transactions_per_second: float = 0.0
    inflation_rate: float = 0.0

    def record_network_io(self, bytes_sent: int, io_ops: int = 1) -> None:
        """Record network I/O for a propagation event."""
        self.network_data += bytes_sent
        self.io_requests += io_ops

    def finalize(
        self,
        total_time: float,
        block_count: int,
        total_tx: int,
        total_coins: float,
        last_coins: float,
        last_t: float,
    ) -> None:
        """Compute final metrics after simulation ends."""
        self.final_simulated_time = total_time
        self.final_blocks = block_count

        # Average block time
        self.avg_block_time = total_time / block_count if block_count > 0 else 0.0

        # Transactions per second
        self.transactions_per_second = total_tx / total_time if total_time > 0 else 0.0

        # Annualized inflation rate
        if block_count > 0 and total_time > 0 and last_coins > 0:
            coins_issued = total_coins - last_coins
            period = total_time - last_t
            if period > 0:
                self.inflation_rate = (
                    (coins_issued / last_coins) * (YEAR / period) * 100
                )

    def to_dict(self, total_tx: int = 0, total_coins: float = 0.0) -> Dict[str, Any]:
        """Export metrics as dictionary for JSON/CSV export."""
        return {
            "network_data_bytes": self.network_data,
            "network_data_mb": self.network_data / 1e6,
            "io_requests": self.io_requests,
            "simulated_time_seconds": self.final_simulated_time,
            "total_blocks": self.final_blocks,
            "avg_block_time": self.avg_block_time,
            "tps": self.transactions_per_second,
            "inflation_rate_percent": self.inflation_rate,
            "total_transactions": total_tx,
            "total_coins_issued": total_coins,
        }

    def export_json(
        self, filepath: str, total_tx: int = 0, total_coins: float = 0.0
    ) -> None:
        """Export metrics to JSON file."""
        import json

        with open(filepath, "w") as f:
            json.dump(self.to_dict(total_tx, total_coins), f, indent=2)
