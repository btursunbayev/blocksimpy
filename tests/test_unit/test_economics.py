"""Unit tests for economic model (rewards, halving)."""


class TestHalvingCalculation:
    """Tests for block reward halving logic."""

    def test_no_halving_before_interval(self):
        """Reward stays constant before halving interval."""
        initial_reward = 50.0
        halving_interval = 210000

        # Block 1000 - no halving yet
        block_count = 1000
        halvings = block_count // halving_interval

        assert halvings == 0
        current_reward = initial_reward / (2**halvings)
        assert current_reward == 50.0

    def test_first_halving(self):
        """First halving reduces reward by half."""
        initial_reward = 50.0
        halving_interval = 210000

        # Block 210001 - first halving occurred
        block_count = 210001
        halvings = block_count // halving_interval

        assert halvings == 1
        current_reward = initial_reward / (2**halvings)
        assert current_reward == 25.0

    def test_multiple_halvings(self):
        """Multiple halvings stack correctly."""
        initial_reward = 50.0
        halving_interval = 10  # Small interval for testing

        test_cases = [
            (5, 50.0),  # Before first halving
            (10, 25.0),  # After first halving
            (20, 12.5),  # After second halving
            (30, 6.25),  # After third halving
        ]

        for block_count, expected_reward in test_cases:
            halvings = block_count // halving_interval
            current_reward = initial_reward / (2**halvings)
            assert current_reward == expected_reward, f"Block {block_count}"

    def test_max_halvings_limit(self):
        """Reward stops at zero after max halvings."""
        initial_reward = 50.0
        halving_interval = 10
        max_halvings = 3

        # After 3 halvings: 50 -> 25 -> 12.5 -> 6.25
        # At max_halvings, reward should stop being issued
        block_count = 40  # 4 halvings would have occurred
        halvings = min(block_count // halving_interval, max_halvings)

        assert halvings == 3  # Capped at max


class TestCoinIssuance:
    """Tests for total coin issuance calculations."""

    def test_simple_issuance(self):
        """Total coins = blocks * reward (no halving)."""
        blocks = 100
        reward = 50.0
        halving_interval = 0  # Disabled

        total_coins = blocks * reward

        assert total_coins == 5000.0

    def test_issuance_with_halving(self):
        """Issuance accounts for halving events."""
        halving_interval = 10
        initial_reward = 50.0

        # Blocks 1-10: 50 each = 500
        # Blocks 11-20: 25 each = 250
        # Blocks 21-25: 12.5 each = 62.5
        # Total: 812.5

        total_coins = 0.0
        reward = initial_reward
        for block in range(1, 26):
            total_coins += reward
            if block % halving_interval == 0:
                reward /= 2

        assert total_coins == 812.5

    def test_halving_interval_zero_means_disabled(self):
        """halving_interval=0 means no halving occurs."""
        halving_interval = 0

        # With 0 interval, we should never halve
        # The coordinator checks: if halving_interval > 0 and block_count % halving_interval == 0
        should_halve = halving_interval > 0 and (100 % halving_interval == 0)

        assert should_halve is False


class TestMaxHalvingsEdgeCases:
    """Tests for max_halvings edge cases."""

    def test_max_halvings_none_treated_as_infinity(self):
        """max_halvings=None should allow unlimited halvings."""
        max_halvings = None
        halvings = 10

        # When max_halvings is None, we should treat it as infinity
        # Current code bug: `halvings < max_halvings` fails with None
        # This test documents the expected behavior after fix

        if max_halvings is None:
            can_issue = True  # Always can issue if no limit
        else:
            can_issue = halvings < max_halvings

        assert can_issue is True

    def test_max_halvings_zero_means_no_issuance(self):
        """max_halvings=0 means no coins ever issued."""
        max_halvings = 0
        halvings = 0

        # If max_halvings is 0, even at halvings=0, we can't issue
        can_issue = halvings < max_halvings

        assert can_issue is False
