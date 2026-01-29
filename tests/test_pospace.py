"""Tests for Proof of Space consensus mechanism."""

import simpy

from blocksimpy.consensus import PoSpaceFarmer, select_farmer


class TestPoSpaceFarmer:
    """Test PoSpaceFarmer class."""

    def test_farmer_initialization(self):
        """Farmer should initialize with id and space."""
        farmer = PoSpaceFarmer(farmer_id=1, space=100.0)
        assert farmer.id == 1
        assert farmer.space == 100.0

    def test_get_weight_returns_space(self):
        """get_weight() should return allocated space."""
        farmer = PoSpaceFarmer(1, 200.0)
        assert farmer.get_weight() == 200.0

    def test_produce_block_immediate(self):
        """PoSpace produce_block() should succeed immediately."""
        env = simpy.Environment()
        farmer = PoSpaceFarmer(1, 100.0)
        event = env.event()

        def run_farmer():
            yield from farmer.produce_block(
                env, difficulty=0, block_found_event=event
            )
            assert event.triggered

        env.process(run_farmer())
        env.run()


class TestFarmerSelection:
    """Test farmer selection logic."""

    def test_select_farmer_returns_farmer(self):
        """select_farmer() should return a PoSpaceFarmer instance."""
        farmers = [PoSpaceFarmer(i, 100.0) for i in range(3)]
        selected = select_farmer(farmers)
        assert isinstance(selected, PoSpaceFarmer)
        assert selected.id in [0, 1, 2]

    def test_select_farmer_with_seed_reproducible(self):
        """select_farmer() with same seed should return same farmer."""
        farmers = [PoSpaceFarmer(i, 100.0) for i in range(3)]
        selected1 = select_farmer(farmers, seed=42)
        selected2 = select_farmer(farmers, seed=42)
        assert selected1.id == selected2.id

    def test_select_farmer_weighted_distribution(self):
        """Farmer with more space should be selected more often."""
        farmers = [
            PoSpaceFarmer(0, 100.0),  # 10% of space
            PoSpaceFarmer(1, 900.0),  # 90% of space
        ]

        # Run 1000 selections
        selections = [select_farmer(farmers, seed=i) for i in range(1000)]
        farmer1_count = sum(1 for f in selections if f.id == 1)

        # Farmer with 90% space should win ~90% of time (allow variance)
        assert farmer1_count > 800

    def test_select_farmer_zero_space(self):
        """select_farmer() with zero total space should return first farmer."""
        farmers = [
            PoSpaceFarmer(0, 0.0),
            PoSpaceFarmer(1, 0.0),
        ]
        selected = select_farmer(farmers)
        assert selected.id == 0

    def test_select_farmer_single_farmer(self):
        """select_farmer() with one farmer should always return that farmer."""
        farmers = [PoSpaceFarmer(0, 100.0)]
        selected = select_farmer(farmers)
        assert selected.id == 0
