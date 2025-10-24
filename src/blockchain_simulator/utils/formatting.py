#!/usr/bin/env python3
"""
Formatting utilities for blockchain simulation output and data presentation.

This module provides utility functions for human-readable number formatting
and constants used throughout the blockchain simulation. Designed for clear
presentation of large numbers (hashrates, difficulties, coin amounts) and
consistent time calculations.

Functions:
    human: Format large numbers with SI suffixes (K, M, B)
    
Constants:
    HEADER_SIZE: Fixed blockchain block header size (1,024 bytes)
    YEAR: Seconds in a year for time calculations (365 * 24 * 3600)
"""

from typing import Union


def human(n: Union[int, float]) -> str:
    """
    Format large numbers with human-readable SI suffixes.
    
    Converts large numeric values into compact string representations using
    standard SI prefixes (K, M, B) for improved readability in simulation
    output, particularly for hashrates, difficulties, and coin amounts.
    
    Args:
        n: Numeric value to format (int or float)
        
    Returns:
        Formatted string with appropriate suffix:
        - Values >= 1B: "1.5B", "2B", etc.
        - Values >= 1M: "500M", "1.2M", etc.
        - Values >= 1K: "750K", "1.5K", etc.
        - Values < 1K: "42", "999", etc. (no suffix)
        
    Examples:
        >>> human(1500)
        '1.5K'
        >>> human(2000000)
        '2M'
        >>> human(1500000000)
        '1.5B'
        >>> human(42)
        '42'
        
    Note:
        Uses integer representation when the scaled value is a whole number,
        otherwise shows one decimal place for clarity.
    """
    a = abs(n)
    if a >= 1e9:
        v, s = n / 1e9, 'B'
    elif a >= 1e6:
        v, s = n / 1e6, 'M'
    elif a >= 1e3:
        v, s = n / 1e3, 'K'
    else:
        return str(int(n))
    
    # Use integer formatting if the scaled value is whole, otherwise one decimal
    return f"{int(v) if v.is_integer() else f'{v:.1f}'}{s}"


# Blockchain simulation constants
HEADER_SIZE = 1024          # Block header size in bytes (realistic Bitcoin-like)
YEAR = 365 * 24 * 3600      # Seconds per year for time-based calculations