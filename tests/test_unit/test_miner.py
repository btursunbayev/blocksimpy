"""Unit tests for Miner class."""

import random

import simpy

from blocksimpy.consensus import Miner


class TestMinerCreation:
    """Tests for miner initialization."""

    def test_miner_basic_properties(self):
        """Miner stores id and hashrate."""
        miner = Miner(miner_id=5, hashrate=1000.0)

        assert miner.id == 5
        assert miner.h == 1000.0

    def test_miner_zero_hashrate(self):
        """Miner can have zero hashrate (won't mine)."""
        miner = Miner(miner_id=0, hashrate=0.0)

        assert miner.h == 0.0


class TestMiningBehavior:
    """Tests for mining process behavior."""

    def test_mining_produces_winner(self, seeded_random, simpy_env):
        """Mining competition produces a winner."""
        miners = [Miner(i, 1000.0) for i in range(3)]
        difficulty = 10000.0

        block_found_event = simpy_env.event()

        for m in miners:
            simpy_env.process(m.mine(simpy_env, difficulty, block_found_event))

        # Run until someone wins
        simpy_env.run()

        assert block_found_event.triggered
        winner = block_found_event.value
        assert winner in miners

    def test_higher_hashrate_wins_more_often(self, simpy_env):
        """Miner with higher hashrate wins more often (statistical)."""
        random.seed(42)  # For reproducibility

        slow_miner = Miner(0, 100.0)
        fast_miner = Miner(1, 10000.0)  # 100x faster
        difficulty = 100000.0

        wins = {0: 0, 1: 0}
        trials = 100

        for _ in range(trials):
            env = simpy.Environment()
            block_found_event = env.event()

            env.process(slow_miner.mine(env, difficulty, block_found_event))
            env.process(fast_miner.mine(env, difficulty, block_found_event))

            env.run()
            winner = block_found_event.value
            wins[winner.id] += 1

        # Fast miner should win significantly more often
        assert wins[1] > wins[0] * 5  # At least 5x more wins

    def test_mining_respects_difficulty(self, seeded_random, simpy_env):
        """Higher difficulty = longer mining time."""
        miner = Miner(0, 1000.0)

        # Low difficulty
        low_diff_times = []
        for _ in range(10):
            env = simpy.Environment()
            event = env.event()
            env.process(miner.mine(env, 1000.0, event))
            env.run()
            low_diff_times.append(env.now)

        # High difficulty
        high_diff_times = []
        for _ in range(10):
            env = simpy.Environment()
            event = env.event()
            env.process(miner.mine(env, 100000.0, event))
            env.run()
            high_diff_times.append(env.now)

        # Average high difficulty time should be higher
        avg_low = sum(low_diff_times) / len(low_diff_times)
        avg_high = sum(high_diff_times) / len(high_diff_times)

        assert avg_high > avg_low


class TestMiningRaceCondition:
    """Tests for mining race between multiple miners."""

    def test_only_one_winner_per_block(self, seeded_random, simpy_env):
        """Only one miner can win each block."""
        miners = [Miner(i, 1000.0) for i in range(5)]
        difficulty = 5000.0

        block_found_event = simpy_env.event()

        for m in miners:
            simpy_env.process(m.mine(simpy_env, difficulty, block_found_event))

        simpy_env.run()

        # Event should be triggered exactly once
        assert block_found_event.triggered
        # Value should be a single miner
        assert isinstance(block_found_event.value, Miner)

    def test_late_miner_loses(self, simpy_env):
        """If event already triggered, new miner doesn't win."""
        random.seed(42)

        winner = Miner(0, 1000000.0)  # Very fast
        loser = Miner(1, 1.0)  # Very slow

        block_found_event = simpy_env.event()

        simpy_env.process(winner.mine(simpy_env, 1000.0, block_found_event))
        simpy_env.process(loser.mine(simpy_env, 1000.0, block_found_event))

        simpy_env.run()

        assert block_found_event.value == winner
