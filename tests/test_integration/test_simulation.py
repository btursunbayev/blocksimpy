"""Integration tests for full simulation runs."""

import random

import simpy

from blocksimpy.consensus import Miner
from blocksimpy.core.node import Node
from blocksimpy.simulation.coordinator import SimulationCoordinator
from blocksimpy.simulation.wallet import wallet


class TestSimulationRun:
    """Tests for complete simulation execution."""

    def test_simulation_completes(self, mini_config, seeded_random):
        """Simulation runs to completion without errors."""
        env = simpy.Environment()
        coordinator = SimulationCoordinator(mini_config)

        # Create wallets
        for i in range(mini_config["transactions"]["wallets"]):
            env.process(
                wallet(
                    env,
                    i,
                    mini_config["transactions"]["transactions_per_wallet"],
                    mini_config["transactions"]["interval"],
                    coordinator.pool,
                )
            )

        # Create nodes
        nodes = [Node(env, i) for i in range(mini_config["network"]["nodes"])]
        for n in nodes:
            other_nodes = [x for x in nodes if x != n]
            n.neighbors = random.sample(
                other_nodes, min(len(other_nodes), mini_config["network"]["neighbors"])
            )

        # Create miners
        miners = [
            Miner(i, mini_config["mining"]["hashrate"])
            for i in range(mini_config["mining"]["miners"])
        ]

        # Run simulation
        coord_proc = env.process(coordinator.coord(env, nodes, miners))
        env.run(until=coord_proc)

        # Verify completion
        assert coordinator.final_blocks == mini_config["simulation"]["blocks"]

    def test_simulation_mines_correct_block_count(self, mini_config, seeded_random):
        """Simulation mines exactly the specified number of blocks."""
        mini_config["simulation"]["blocks"] = 10

        env = simpy.Environment()
        coordinator = SimulationCoordinator(mini_config)

        nodes = [Node(env, i) for i in range(mini_config["network"]["nodes"])]
        for n in nodes:
            other_nodes = [x for x in nodes if x != n]
            n.neighbors = random.sample(
                other_nodes, min(len(other_nodes), mini_config["network"]["neighbors"])
            )

        miners = [
            Miner(i, mini_config["mining"]["hashrate"])
            for i in range(mini_config["mining"]["miners"])
        ]

        coord_proc = env.process(coordinator.coord(env, nodes, miners))
        env.run(until=coord_proc)

        assert coordinator.final_blocks == 10

    def test_simulation_issues_coins(self, mini_config, seeded_random):
        """Simulation issues block rewards correctly."""
        mini_config["simulation"]["blocks"] = 5
        mini_config["economics"]["halving_interval"] = 100  # No halving in this test

        env = simpy.Environment()
        coordinator = SimulationCoordinator(mini_config)

        nodes = [Node(env, i) for i in range(mini_config["network"]["nodes"])]
        for n in nodes:
            other_nodes = [x for x in nodes if x != n]
            n.neighbors = random.sample(
                other_nodes, min(len(other_nodes), mini_config["network"]["neighbors"])
            )

        miners = [
            Miner(i, mini_config["mining"]["hashrate"])
            for i in range(mini_config["mining"]["miners"])
        ]

        coord_proc = env.process(coordinator.coord(env, nodes, miners))
        env.run(until=coord_proc)

        expected_coins = 5 * mini_config["economics"]["initial_reward"]
        assert coordinator.total_coins == expected_coins

    def test_simulation_tracks_transactions(self, mini_config, seeded_random):
        """Simulation tracks transaction count."""
        env = simpy.Environment()
        coordinator = SimulationCoordinator(mini_config)

        # Create wallets that generate transactions
        for i in range(mini_config["transactions"]["wallets"]):
            env.process(
                wallet(
                    env,
                    i,
                    mini_config["transactions"]["transactions_per_wallet"],
                    mini_config["transactions"]["interval"],
                    coordinator.pool,
                )
            )

        nodes = [Node(env, i) for i in range(mini_config["network"]["nodes"])]
        for n in nodes:
            other_nodes = [x for x in nodes if x != n]
            n.neighbors = random.sample(
                other_nodes, min(len(other_nodes), mini_config["network"]["neighbors"])
            )

        miners = [
            Miner(i, mini_config["mining"]["hashrate"])
            for i in range(mini_config["mining"]["miners"])
        ]

        coord_proc = env.process(coordinator.coord(env, nodes, miners))
        env.run(until=coord_proc)

        # Should have at least coinbase transactions
        assert coordinator.total_tx >= coordinator.final_blocks


class TestNetworkPropagation:
    """Tests for block propagation through network."""

    def test_blocks_propagate_to_all_nodes(self, mini_config, seeded_random):
        """All nodes receive all blocks."""
        mini_config["simulation"]["blocks"] = 3

        env = simpy.Environment()
        coordinator = SimulationCoordinator(mini_config)

        nodes = [Node(env, i) for i in range(mini_config["network"]["nodes"])]
        for n in nodes:
            other_nodes = [x for x in nodes if x != n]
            n.neighbors = random.sample(
                other_nodes, min(len(other_nodes), mini_config["network"]["neighbors"])
            )

        miners = [
            Miner(i, mini_config["mining"]["hashrate"])
            for i in range(mini_config["mining"]["miners"])
        ]

        coord_proc = env.process(coordinator.coord(env, nodes, miners))
        env.run(until=coord_proc)

        # All nodes should have all blocks
        for node in nodes:
            assert len(node.blocks) == 3

    def test_network_metrics_tracked(self, mini_config, seeded_random):
        """Network I/O and bandwidth are tracked."""
        env = simpy.Environment()
        coordinator = SimulationCoordinator(mini_config)

        nodes = [Node(env, i) for i in range(mini_config["network"]["nodes"])]
        for n in nodes:
            other_nodes = [x for x in nodes if x != n]
            n.neighbors = random.sample(
                other_nodes, min(len(other_nodes), mini_config["network"]["neighbors"])
            )

        miners = [
            Miner(i, mini_config["mining"]["hashrate"])
            for i in range(mini_config["mining"]["miners"])
        ]

        coord_proc = env.process(coordinator.coord(env, nodes, miners))
        env.run(until=coord_proc)

        assert coordinator.io_requests > 0
        assert coordinator.network_data > 0


class TestHalvingIntegration:
    """Integration tests for halving mechanism."""

    def test_halving_reduces_issuance(self, mini_config, seeded_random):
        """Halving events reduce coin issuance."""
        # Configure for halving test
        mini_config["simulation"]["blocks"] = 25
        mini_config["economics"]["halving_interval"] = 10
        mini_config["economics"]["initial_reward"] = 50.0
        mini_config["economics"]["max_halvings"] = 3

        env = simpy.Environment()
        coordinator = SimulationCoordinator(mini_config)

        nodes = [Node(env, i) for i in range(mini_config["network"]["nodes"])]
        for n in nodes:
            other_nodes = [x for x in nodes if x != n]
            n.neighbors = random.sample(
                other_nodes, min(len(other_nodes), mini_config["network"]["neighbors"])
            )

        miners = [
            Miner(i, mini_config["mining"]["hashrate"])
            for i in range(mini_config["mining"]["miners"])
        ]

        coord_proc = env.process(coordinator.coord(env, nodes, miners))
        env.run(until=coord_proc)

        # Expected: 10*50 + 10*25 + 5*12.5 = 812.5
        expected_coins = 812.5
        assert abs(coordinator.total_coins - expected_coins) < 0.01
