#!/usr/bin/env python3
"""
Configuration loading and management for blockchain simulation.

This module handles loading YAML configuration files for different blockchain
presets and merging command-line arguments with configuration values.
Supports both default configurations and chain-specific presets (btc, etc.)
with proper fallback handling and parameter validation.

Configuration Structure:
- network: Node topology and propagation settings
- mining: Mining parameters, difficulty, block timing
- economics: Reward system, halving schedule, inflation
- transactions: Wallet and transaction generation settings
- simulation: Runtime control, reporting, debug options
"""

import argparse
from pathlib import Path
from typing import Any, Dict

import yaml


def load_config(chain_name: str = "defaults") -> Dict[str, Any]:
    """
    Load blockchain configuration from YAML files.

    Loads configuration presets for different blockchain types (Bitcoin-like, etc.)
    or default simulation parameters. Supports hierarchical configuration structure
    with proper fallback to defaults if chain-specific config is not found.

    Args:
        chain_name: Configuration preset name ("defaults", "btc", etc.)
                   Maps to config files in config/chains/{chain_name}/{chain_name}.yml

    Returns:
        Complete configuration dictionary with all simulation parameters

    Configuration Hierarchy:
        1. Try chain-specific config: config/chains/{chain_name}/{chain_name}.yml
        2. Fallback to defaults: config/defaults.yml

    Raises:
        FileNotFoundError: If neither chain config nor defaults exist
        yaml.YAMLError: If configuration file has invalid YAML syntax

    Example:
        >>> config = load_config("btc")
        >>> print(config['mining']['blocktime'])  # 600.0 (10 minutes)
    """
    # Config files are now in the package directory
    config_dir = Path(__file__).parent

    if chain_name == "defaults":
        # Load defaults.yml from root config directory
        config_path = config_dir / "defaults.yml"
    else:
        # Load chain-specific config from chains subdirectory
        # Try direct path first, then search in pow/ and pos/ folders
        config_path = config_dir / "chains" / chain_name / f"{chain_name}.yml"

        if not config_path.exists():
            # Search in pow/ and pos/ subfolders
            for consensus_type in ["pow", "pos"]:
                alt_path = (
                    config_dir
                    / "chains"
                    / consensus_type
                    / chain_name
                    / f"{chain_name}.yml"
                )
                if alt_path.exists():
                    config_path = alt_path
                    break

    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            # Fallback to defaults if chain-specific config not found
            defaults_path = config_dir / "defaults.yml"
            with open(defaults_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    except (FileNotFoundError, PermissionError) as e:
        raise FileNotFoundError(f"Could not load configuration: {e}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in configuration file: {e}")


def merge_cli_args(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Merge command-line arguments into loaded configuration.

    Overlays CLI arguments onto base configuration, allowing users to override
    specific parameters without modifying config files. Only merges arguments
    that were explicitly provided (not None), preserving config file defaults
    for unspecified parameters.

    Args:
        config: Base configuration dictionary loaded from YAML files
        args: Parsed command-line arguments from argparse

    Returns:
        Updated configuration with CLI overrides applied

    CLI Argument Mapping:
        Maps CLI argument names to nested configuration paths:
        --nodes -> config['network']['nodes']
        --blocktime -> config['mining']['blocktime']
        --transactions -> config['transactions']['transactions_per_wallet']
        etc.

    Override Behavior:
        - Only arguments explicitly provided by user are merged
        - None values (unspecified arguments) are ignored
        - Preserves all other configuration values unchanged
        - Maintains type consistency (int, float, bool, str)

    Example:
        >>> config = load_config("btc")
        >>> args = parse_args(["--blocktime", "30", "--miners", "5"])
        >>> updated = merge_cli_args(config, args)
        >>> print(updated['mining']['blocktime'])  # 30.0 (overridden)
        >>> print(updated['mining']['blocksize'])  # 4096 (from config file)
    """
    # Map CLI argument names to nested configuration paths
    cli_mapping = {
        "nodes": ("network", "nodes"),
        "neighbors": ("network", "neighbors"),
        "blocksize": ("mining", "blocksize"),
        "blocktime": ("mining", "blocktime"),
        "miners": ("mining", "miners"),
        "hashrate": ("mining", "hashrate"),
        "difficulty": ("mining", "difficulty"),
        "stake": ("mining", "stake"),
        "consensus": ("consensus", "type"),
        "blocks": ("simulation", "blocks"),
        "years": ("simulation", "years"),
        "wallets": ("transactions", "wallets"),
        "transactions": ("transactions", "transactions_per_wallet"),
        "interval": ("transactions", "interval"),
        "print_int": ("simulation", "print_interval"),
        "debug": ("simulation", "debug"),
        "init_reward": ("economics", "initial_reward"),
        "halving_interval": ("economics", "halving_interval"),
    }

    # Merge only explicitly provided CLI arguments (skip None values)
    for arg_name, (section, key) in cli_mapping.items():
        if hasattr(args, arg_name):
            value = getattr(args, arg_name)
            if value is not None:  # Only override if user provided the argument
                if section not in config:
                    config[section] = {}  # Create section if missing
                config[section][key] = value

    # Special handling: if user specified --years, clear blocks to allow calculation from years
    if hasattr(args, "years") and args.years is not None:
        config["simulation"]["blocks"] = None

    return config
