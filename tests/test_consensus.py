"""
Unit tests for the consensus module.

Tests cover:
- PoWMiner: exponential timing, hashrate as weight
- PoSValidator: stake as weight, deterministic production
- select_validator: stake-weighted random selection
- BlockProducer: interface compliance
"""

import simpy

from blocksimpy.consensus import BlockProducer, PoSValidator, PoWMiner, select_validator


class TestBlockProducerInterface:
    """Test the BlockProducer base class interface."""

    def test_pow_miner_is_block_producer(self):
        """PoWMiner should be a BlockProducer."""
        miner = PoWMiner(miner_id=1, hashrate=100)
        assert isinstance(miner, BlockProducer)

    def test_pos_validator_is_block_producer(self):
        """PoSValidator should be a BlockProducer."""
        validator = PoSValidator(validator_id=1, stake=32.0)
        assert isinstance(validator, BlockProducer)


class TestPoWMiner:
    """Test Proof of Work miner implementation."""

    def test_miner_initialization(self):
        """Miner should store id and hashrate."""
        miner = PoWMiner(miner_id=42, hashrate=500)
        assert miner.id == 42
        assert miner.h == 500

    def test_get_weight_returns_hashrate(self):
        """get_weight() should return hashrate."""
        miner = PoWMiner(miner_id=1, hashrate=1000)
        assert miner.get_weight() == 1000

    def test_mine_alias_exists(self):
        """mine() should be an alias for produce_block()."""
        miner = PoWMiner(miner_id=1, hashrate=100)
        assert hasattr(miner, "mine")

    def test_produce_block_succeeds_event(self):
        """produce_block() should trigger event on success."""
        env = simpy.Environment()
        miner = PoWMiner(miner_id=1, hashrate=1000)
        event = env.event()

        def run_miner():
            yield from miner.produce_block(env, difficulty=100, block_found_event=event)

        env.process(run_miner())
        env.run(until=1000)  # Give time for exponential delay

        assert event.triggered

    def test_multiple_miners_race(self):
        """Multiple miners racing should have one winner."""
        env = simpy.Environment()
        miners = [PoWMiner(miner_id=i, hashrate=100) for i in range(5)]
        event = env.event()

        for miner in miners:
            env.process(
                miner.produce_block(env, difficulty=10, block_found_event=event)
            )

        env.run(until=1000)

        # Event should have the winning miner
        assert event.triggered
        assert event.value in miners


class TestPoSValidator:
    """Test Proof of Stake validator implementation."""

    def test_validator_initialization(self):
        """Validator should store id and stake."""
        validator = PoSValidator(validator_id=7, stake=32.0)
        assert validator.id == 7
        assert validator.stake == 32.0

    def test_get_weight_returns_stake(self):
        """get_weight() should return stake."""
        validator = PoSValidator(validator_id=1, stake=100.5)
        assert validator.get_weight() == 100.5

    def test_produce_block_immediate(self):
        """PoS produce_block() should succeed immediately."""
        env = simpy.Environment()
        validator = PoSValidator(validator_id=1, stake=32.0)
        event = env.event()

        def run_validator():
            yield from validator.produce_block(
                env, difficulty=0, block_found_event=event
            )

        env.process(run_validator())
        env.run(until=1)

        # Should trigger immediately (no delay)
        assert event.triggered
        assert event.value == validator


class TestValidatorSelection:
    """Test stake-weighted validator selection."""

    def test_select_validator_returns_validator(self):
        """select_validator() should return a PoSValidator."""
        validators = [PoSValidator(i, stake=100) for i in range(3)]
        selected = select_validator(validators)
        assert isinstance(selected, PoSValidator)
        assert selected in validators

    def test_select_validator_with_seed_reproducible(self):
        """Same seed should produce same selection sequence."""
        validators = [PoSValidator(i, stake=100) for i in range(5)]

        results1 = [select_validator(validators, seed=42).id for _ in range(10)]
        results2 = [select_validator(validators, seed=42).id for _ in range(10)]

        assert results1 == results2

    def test_select_validator_weighted_distribution(self):
        """Validator with higher stake should be selected more often."""
        # Validator 0: 900 stake, Validator 1: 100 stake
        validators = [
            PoSValidator(0, stake=900),
            PoSValidator(1, stake=100),
        ]

        # Run many selections
        selections = {0: 0, 1: 0}
        for i in range(1000):
            selected = select_validator(validators, seed=i)
            selections[selected.id] += 1

        # Validator 0 should win ~90% of the time
        ratio = selections[0] / (selections[0] + selections[1])
        assert 0.85 < ratio < 0.95, f"Expected ~90% for validator 0, got {ratio:.2%}"

    def test_select_validator_zero_stake(self):
        """With zero total stake, should fall back to random choice."""
        validators = [PoSValidator(i, stake=0) for i in range(3)]
        selected = select_validator(validators, seed=42)
        assert selected in validators

    def test_select_validator_single_validator(self):
        """Single validator should always be selected."""
        validator = PoSValidator(99, stake=50)
        selected = select_validator([validator], seed=42)
        assert selected == validator


class TestConsensusTypes:
    """Test consensus type differences."""

    def test_pow_timing_varies(self):
        """PoW should have variable timing due to exponential distribution."""
        times = []

        for i in range(10):
            # Fresh environment for each run
            env = simpy.Environment()
            miner = PoWMiner(miner_id=1, hashrate=100)
            event = env.event()
            env.process(
                miner.produce_block(env, difficulty=100, block_found_event=event)
            )
            env.run()  # Run until event triggers
            times.append(env.now)

        # Times should vary (not all identical)
        unique_times = set(times)
        assert len(unique_times) > 1, f"PoW times should vary, got {times}"

    def test_pos_immediate_trigger(self):
        """PoS produce_block() should trigger event immediately in same step."""
        env = simpy.Environment()
        validator = PoSValidator(validator_id=1, stake=32.0)
        event = env.event()

        env.process(validator.produce_block(env, difficulty=0, block_found_event=event))
        env.step()  # Run one step

        # Event should trigger in first step (time 0)
        assert event.triggered
        assert env.now == 0
