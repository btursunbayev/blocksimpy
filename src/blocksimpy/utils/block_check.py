#!/usr/bin/env python3
"""
Block validation and configuration optimization utilities.

This module provides validation functions for blockchain simulation parameters,
particularly focusing on block count estimation and configuration optimization.
Helps prevent unrealistic simulations and provides intelligent parameter
adjustments for better simulation efficiency.

Key Functions:
- Block count calculation based on transaction load
- Configuration validation and auto-adjustment
- Time-based vs transaction-based simulation planning
"""

from typing import Dict, Any, Tuple, Optional
from .formatting import YEAR


def calculate_expected_blocks(total_transactions: int, block_size: int) -> int:
    """
    Calculate expected number of blocks needed for given transaction load.
    
    Determines minimum blocks required to process all transactions based on
    block capacity. Uses ceiling division to ensure all transactions can
    be included even if the last block is partially filled.
    
    Args:
        total_transactions: Total number of transactions to process
        block_size: Maximum transactions that can fit in one block
        
    Returns:
        Minimum number of blocks needed (integer, rounded up)
        
    Formula:
        expected_blocks = ceil(total_transactions / block_size)
        
    Examples:
        >>> calculate_expected_blocks(10000, 4096)  # 10k tx, 4k per block
        3  # Need 3 blocks: 4096 + 4096 + 1808 = 10000
        
        >>> calculate_expected_blocks(4096, 4096)   # Exactly one block
        1
        
    Edge Cases:
        - Returns 0 if total_transactions <= 0 or block_size <= 0
        - Always returns at least 1 for positive transaction counts
    """
    if total_transactions <= 0 or block_size <= 0:
        return 0
    # Use ceiling division: (a + b - 1) // b equivalent to ceil(a / b)
    return (total_transactions + block_size - 1) // block_size


def validate_blocks_count(total_transactions: int, block_size: int, 
                         actual_blocks: Optional[int] = None) -> Tuple[int, Optional[int]]:
    """
    Validate block count configuration against transaction requirements.
    
    Compares expected blocks needed for transaction processing with
    actual configured block limits. Used for validation and reporting.
    
    Args:
        total_transactions: Total transactions to be processed
        block_size: Transactions per block capacity
        actual_blocks: Configured block limit (None if unlimited)
        
    Returns:
        Tuple of (expected_blocks, actual_blocks) for comparison
        
    Usage:
        Used primarily for validation reporting and configuration analysis.
        The main validation logic is handled by validate_configuration().
    """
    expected = calculate_expected_blocks(total_transactions, block_size)
    return expected, actual_blocks


def validate_configuration(config):
    """Validate and adjust configuration, return validation results."""
    # Extract basic configuration values
    wallets = config['transactions']['wallets']
    tx_per_wallet = config['transactions']['transactions_per_wallet']
    total_transactions = wallets * tx_per_wallet
    blocksize = config['mining']['blocksize']
    expected_blocks = calculate_expected_blocks(total_transactions, blocksize)
    
    # Handle blocks vs years calculation
    blocks = config['simulation']['blocks']
    original_limit = blocks
    calculated_from_years = None
    user_specified_blocks = blocks is not None
    
    if blocks is None and config['simulation']['years']:
        calculated_limit = int(config['simulation']['years'] * YEAR / config['mining']['blocktime'])
        config['simulation']['blocks'] = calculated_limit
        blocks = calculated_limit
        calculated_from_years = calculated_limit
        user_specified_blocks = False
    
    # Auto-adjust blocks if it was calculated from years, not user-specified
    # AND only if there are actually transactions to process
    auto_adjusted = False
    if blocks and blocks > expected_blocks * 3 and not user_specified_blocks and total_transactions > 0:
        original_limit = blocks
        blocks = expected_blocks
        config['simulation']['blocks'] = blocks
        auto_adjusted = True
    
    # Check for warnings
    warning = None
    if blocks and blocks < expected_blocks:
        warning = f"blocks ({blocks}) < expected blocks ({expected_blocks}) - some transactions may not be processed!"
    
    # Return validation results
    return {
        'expected_blocks': expected_blocks,
        'total_transactions': total_transactions,
        'blocks': blocks,
        'original_limit': original_limit,
        'calculated_from_years': calculated_from_years,
        'auto_adjusted': auto_adjusted,
        'warning': warning
    }