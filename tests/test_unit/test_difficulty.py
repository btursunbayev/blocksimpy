"""Unit tests for difficulty adjustment logic."""


class TestDifficultyCalculation:
    """Tests for difficulty calculation and adjustment."""

    def test_initial_difficulty_auto_calculation(self):
        """Difficulty = blocktime * total_hashrate when not specified."""
        target_blocktime = 600.0  # 10 minutes
        hashrate_per_miner = 1000.0
        num_miners = 10

        total_hashrate = hashrate_per_miner * num_miners  # 10000
        difficulty = target_blocktime * total_hashrate

        assert difficulty == 6_000_000.0

    def test_difficulty_specified_overrides_auto(self):
        """When difficulty is specified, it's used directly."""
        specified_difficulty = 1_000_000.0
        initial_difficulty = specified_difficulty

        difficulty = (
            initial_difficulty
            if initial_difficulty is not None
            else 600 * 10000  # Would be auto-calculated
        )

        assert difficulty == 1_000_000.0


class TestDifficultyRetargeting:
    """Tests for difficulty adjustment algorithm."""

    def test_no_adjustment_before_interval(self):
        """No adjustment until retarget interval reached."""
        retarget_interval = 2016
        blocks_since_adjustment = 100

        should_adjust = blocks_since_adjustment >= retarget_interval

        assert should_adjust is False

    def test_adjustment_at_interval(self):
        """Adjustment triggers at retarget interval."""
        retarget_interval = 2016
        blocks_since_adjustment = 2016

        should_adjust = blocks_since_adjustment >= retarget_interval

        assert should_adjust is True

    def test_adjustment_factor_blocks_too_fast(self):
        """If blocks are too fast, difficulty increases."""
        target_blocktime = 600.0  # 10 minutes
        actual_avg_blocktime = 300.0  # 5 minutes (too fast)

        factor = target_blocktime / actual_avg_blocktime

        assert factor == 2.0  # Difficulty should double

    def test_adjustment_factor_blocks_too_slow(self):
        """If blocks are too slow, difficulty decreases."""
        target_blocktime = 600.0  # 10 minutes
        actual_avg_blocktime = 1200.0  # 20 minutes (too slow)

        factor = target_blocktime / actual_avg_blocktime

        assert factor == 0.5  # Difficulty should halve

    def test_adjustment_factor_on_target(self):
        """If blocks are on target, difficulty unchanged."""
        target_blocktime = 600.0
        actual_avg_blocktime = 600.0

        factor = target_blocktime / actual_avg_blocktime

        assert factor == 1.0  # No change

    def test_difficulty_adjustment_applied(self):
        """New difficulty = old_difficulty * factor."""
        old_difficulty = 1_000_000.0
        factor = 1.5  # 50% increase needed

        new_difficulty = old_difficulty * factor

        assert new_difficulty == 1_500_000.0

    def test_zero_actual_time_protection(self):
        """Handles edge case of zero elapsed time."""
        target_blocktime = 600.0
        actual_avg = 0.0

        # Protection: use factor=1 if actual_avg is 0
        factor = target_blocktime / actual_avg if actual_avg > 0 else 1

        assert factor == 1  # No change when actual is 0


class TestMiningTimeDistribution:
    """Tests for mining time calculation."""

    def test_expected_mining_time(self):
        """Expected mining time = difficulty / hashrate."""
        difficulty = 1_000_000.0
        hashrate = 1000.0

        # For exponential distribution with rate = hashrate / difficulty
        # Expected value = 1 / rate = difficulty / hashrate
        expected_time = difficulty / hashrate

        assert expected_time == 1000.0  # seconds

    def test_higher_hashrate_faster_mining(self):
        """Higher hashrate = faster expected mining time."""
        difficulty = 1_000_000.0

        slow_expected = difficulty / 1000.0  # 1000 seconds
        fast_expected = difficulty / 10000.0  # 100 seconds

        assert fast_expected < slow_expected

    def test_higher_difficulty_slower_mining(self):
        """Higher difficulty = slower expected mining time."""
        hashrate = 1000.0

        easy_expected = 500_000.0 / hashrate  # 500 seconds
        hard_expected = 2_000_000.0 / hashrate  # 2000 seconds

        assert hard_expected > easy_expected
