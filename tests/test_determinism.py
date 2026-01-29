"""Tests for simulation determinism/reproducibility."""

import random

import simpy

from blocksimpy.consensus import Miner
from blocksimpy.core.node import Node
from blocksimpy.simulation.coordinator import SimulationCoordinator
from blocksimpy.simulation.wallet import wallet


def run_simulation_with_seed(config, seed):
    """Run a simulation with a specific seed and return key metrics."""
    random.seed(seed)

    env = simpy.Environment()
    coordinator = SimulationCoordinator(config)

    # Create wallets
    for i in range(config["transactions"]["wallets"]):
        env.process(
            wallet(
                env,
                i,
                config["transactions"]["transactions_per_wallet"],
                config["transactions"]["interval"],
                coordinator.pool,
            )
        )

    # Create nodes with deterministic topology
    nodes = [Node(env, i) for i in range(config["network"]["nodes"])]
    for n in nodes:
        other_nodes = [x for x in nodes if x != n]
        n.neighbors = random.sample(
            other_nodes, min(len(other_nodes), config["network"]["neighbors"])
        )

    # Create miners
    miners = [
        Miner(i, config["mining"]["hashrate"])
        for i in range(config["mining"]["miners"])
    ]

    # Run simulation
    coord_proc = env.process(coordinator.coord(env, nodes, miners))
    env.run(until=coord_proc)

    return {
        "blocks": coordinator.final_blocks,
        "simulated_time": coordinator.final_simulated_time,
        "total_coins": coordinator.total_coins,
        "total_tx": coordinator.total_tx,
        "network_data": coordinator.network_data,
        "io_requests": coordinator.io_requests,
    }


class TestDeterminism:
    """Tests to verify simulation reproducibility."""

    def test_same_seed_same_results(self, mini_config):
        """Same seed produces identical results."""
        seed = 12345

        result1 = run_simulation_with_seed(mini_config.copy(), seed)
        result2 = run_simulation_with_seed(mini_config.copy(), seed)

        assert result1["blocks"] == result2["blocks"]
        assert result1["simulated_time"] == result2["simulated_time"]
        assert result1["total_coins"] == result2["total_coins"]
        assert result1["total_tx"] == result2["total_tx"]
        assert result1["network_data"] == result2["network_data"]
        assert result1["io_requests"] == result2["io_requests"]

    def test_different_seeds_different_results(self, mini_config):
        """Different seeds produce different timing (usually)."""
        result1 = run_simulation_with_seed(mini_config.copy(), 111)
        result2 = run_simulation_with_seed(mini_config.copy(), 222)

        # Blocks should be same (fixed by config)
        assert result1["blocks"] == result2["blocks"]

        # But timing should differ (probabilistic mining)
        # Note: In rare cases they could match, but very unlikely
        assert result1["simulated_time"] != result2["simulated_time"]

    def test_seed_affects_mining_order(self, mini_config):
        """Different seeds lead to different mining histories."""
        # Run many simulations and collect winning miner sequences
        sequences = []

        for seed in range(5):
            random.seed(seed)

            env = simpy.Environment()
            miners = [Miner(i, 1000.0) for i in range(3)]
            winners = []

            for _ in range(5):
                block_event = env.event()
                for m in miners:
                    env.process(m.mine(env, 10000.0, block_event))
                env.run()
                winners.append(block_event.value.id)
                # Reset for next block by creating new event
                env = simpy.Environment()

            sequences.append(tuple(winners))

        # Not all sequences should be identical
        unique_sequences = set(sequences)
        assert len(unique_sequences) > 1


class TestReproducibilityAcrossRuns:
    """Tests for reproducibility across multiple runs."""

    def test_multiple_runs_consistent(self, mini_config):
        """Multiple runs with same seed are consistent."""
        seed = 42
        results = []

        for _ in range(3):
            result = run_simulation_with_seed(mini_config.copy(), seed)
            results.append(result)

        # All results should be identical
        for r in results[1:]:
            assert r == results[0]

    def test_config_changes_affect_outcome(self, mini_config):
        """Changing config produces different results even with same seed."""
        seed = 42

        # Use fixed difficulty so hashrate changes have effect
        config1 = mini_config.copy()
        config1["mining"] = mini_config["mining"].copy()
        config1["mining"]["difficulty"] = 10000.0
        config1["mining"]["hashrate"] = 1000.0

        config2 = mini_config.copy()
        config2["mining"] = mini_config["mining"].copy()
        config2["mining"]["difficulty"] = 10000.0
        config2["mining"]["hashrate"] = 2000.0  # Double hashrate

        result1 = run_simulation_with_seed(config1, seed)
        result2 = run_simulation_with_seed(config2, seed)

        # Blocks same, but timing different
        assert result1["blocks"] == result2["blocks"]
        # Higher hashrate = faster simulation time (with fixed difficulty)
        assert result2["simulated_time"] < result1["simulated_time"]
