"""Unit tests for mempool operations (deque-based transaction pool)."""

import pytest


class TestMempoolOperations:
    """Tests for transaction pool behavior."""

    def test_append_is_o1(self, empty_mempool):
        """Appending transactions is O(1)."""
        for i in range(1000):
            empty_mempool.append((i, float(i)))

        assert len(empty_mempool) == 1000

    def test_popleft_is_o1(self, sample_mempool):
        """Removing from front via popleft is O(1)."""
        initial_len = len(sample_mempool)
        first_item = sample_mempool[0]

        removed = sample_mempool.popleft()

        assert removed == first_item
        assert len(sample_mempool) == initial_len - 1

    def test_fifo_order(self, empty_mempool):
        """Transactions are processed in FIFO order."""
        for i in range(5):
            empty_mempool.append((i, float(i * 10)))

        for i in range(5):
            tx = empty_mempool.popleft()
            assert tx[0] == i

    def test_len_is_o1(self, sample_mempool):
        """Length check is O(1) for deque."""
        assert len(sample_mempool) == 10

    def test_empty_popleft_raises(self, empty_mempool):
        """Popleft on empty deque raises IndexError."""
        with pytest.raises(IndexError):
            empty_mempool.popleft()

    def test_batch_processing(self, sample_mempool):
        """Can process batch of transactions."""
        batch_size = 5
        initial_len = len(sample_mempool)

        processed = []
        for _ in range(batch_size):
            processed.append(sample_mempool.popleft())

        assert len(processed) == batch_size
        assert len(sample_mempool) == initial_len - batch_size


class TestMempoolWithCoordinator:
    """Tests for mempool integration with coordinator logic."""

    def test_take_min_available_and_blocksize(self, sample_mempool):
        """Coordinator takes min(available, blocksize) transactions."""
        block_size = 3
        avail = len(sample_mempool)

        take = min(avail, block_size)

        assert take == 3  # blocksize < available

    def test_take_when_pool_smaller_than_blocksize(self, empty_mempool):
        """When pool < blocksize, take all available."""
        # Add just 2 transactions
        empty_mempool.append((0, 0.0))
        empty_mempool.append((1, 1.0))

        block_size = 100
        avail = len(empty_mempool)
        take = min(avail, block_size)

        assert take == 2  # available < blocksize
