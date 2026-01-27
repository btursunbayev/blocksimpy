"""Unit tests for Block class."""

from blocksimpy.core.block import Block
from blocksimpy.utils.formatting import HEADER_SIZE


class TestBlockCreation:
    """Tests for block creation and properties."""

    def test_block_basic_properties(self):
        """Block stores correct id, tx count, and time delta."""
        block = Block(block_id=5, transaction_count=100, time_since_last=60.0)

        assert block.id == 5
        assert block.tx == 100
        assert block.dt == 60.0

    def test_block_size_calculation(self):
        """Block size = header (1024) + tx_count * 256."""
        block = Block(block_id=1, transaction_count=10, time_since_last=0.0)

        expected_size = HEADER_SIZE + (10 * 256)  # 1024 + 2560 = 3584
        assert block.size == expected_size

    def test_empty_block_size(self):
        """Empty block (0 transactions) has only header size."""
        block = Block(block_id=0, transaction_count=0, time_since_last=0.0)

        assert block.size == HEADER_SIZE  # 1024 bytes

    def test_large_block_size(self):
        """Large blocks calculate size correctly."""
        tx_count = 4096  # Max typical block
        block = Block(block_id=1, transaction_count=tx_count, time_since_last=600.0)

        expected_size = HEADER_SIZE + (tx_count * 256)  # 1024 + 1048576 = 1049600
        assert block.size == expected_size

    def test_block_timestamp_default(self):
        """Block gets timestamp if not provided."""
        block = Block(block_id=1, transaction_count=1, time_since_last=0.0)

        assert block.timestamp is not None
        assert isinstance(block.timestamp, float)

    def test_block_timestamp_custom(self):
        """Block accepts custom timestamp."""
        custom_time = 1234567890.0
        block = Block(
            block_id=1, transaction_count=1, time_since_last=0.0, timestamp=custom_time
        )

        assert block.timestamp == custom_time


class TestBlockRepresentation:
    """Tests for block string representations."""

    def test_repr(self):
        """__repr__ includes key info."""
        block = Block(block_id=42, transaction_count=100, time_since_last=30.5)

        repr_str = repr(block)
        assert "42" in repr_str
        assert "100" in repr_str

    def test_str(self):
        """__str__ is human readable."""
        block = Block(block_id=1, transaction_count=50, time_since_last=600.0)

        str_repr = str(block)
        assert "Block #1" in str_repr
        assert "50 transactions" in str_repr
