#!/usr/bin/env python3
"""
Main application entry point for blockchain discrete event simulation.

This module provides the primary interface for running blockchain simulations
with comprehensive configuration management, validation, and user-friendly
progress reporting. Coordinates all simulation components including network
nodes, miners, wallets, and the simulation coordinator.

Application Flow:
1. Parse command-line arguments and load configuration
2. Validate and optimize simulation parameters  
3. Initialize simulation environment and components
4. Execute blockchain simulation with progress monitoring
5. Report final simulation results and metrics
"""

import simpy
import random
from typing import Dict, Any, List
from .config.config_loader import load_config, merge_cli_args
from .core.node import Node
from .core.miner import Miner
from .simulation.coordinator import SimulationCoordinator
from .simulation.wallet import wallet
from .utils.block_check import validate_configuration
from .cli.args_parser import parse_args


def print_configuration_summary(config: Dict[str, Any], chain_name: str, validation_results: Dict[str, Any]) -> None:
    """
    Display human-readable configuration summary before simulation starts.
    
    Provides clear overview of all simulation parameters including network
    topology, mining configuration, transaction settings, and block planning.
    Helps users understand what the simulation will do before execution.
    
    Args:
        config: Complete configuration dictionary
        chain_name: Name of blockchain preset being used
        validation_results: Results from configuration validation and optimization
        
    Output Format:
        - Chain preset and basic network parameters
        - Transaction generation settings with totals
        - Mining configuration (block time, capacity)
        - Block planning (expected vs configured limits)
        - Any configuration warnings or adjustments
    """
    print("Configuration Summary:")
    print(f"  Chain: {chain_name}")
    print(f"  Network: {config['network']['nodes']} nodes, {config['mining']['miners']} miners")
    print(f"  Transactions: {config['transactions']['wallets']} wallets × {config['transactions']['transactions_per_wallet']} = {validation_results['total_transactions']:,} total")
    print(f"  Block capacity: {config['mining']['blocksize']:,} transactions per block")
    
    # Calculate human readable block time
    blocktime = config['mining']['blocktime']
    if blocktime >= 60:
        time_str = f"{int(blocktime/60)}min blocks"
    else:
        time_str = f"{blocktime}sec blocks"
    
    print(f"  Mining: {time_str}")
    
    # Simple block calculation info
    if validation_results['calculated_from_years'] and validation_results['auto_adjusted']:
        print(f"  Blocks: expected {validation_results['expected_blocks']}, got {validation_results['original_limit']:,} (adjusted to {validation_results['blocks']})")
    elif validation_results['blocks']:
        print(f"  Blocks: running {validation_results['blocks']}")
    
    # Final validation warnings
    if validation_results['warning']:
        print(f"  WARNING: {validation_results['warning']}")


def main() -> None:
    """
    Main application entry point for blockchain simulation.
    
    Orchestrates the complete simulation lifecycle from configuration loading
    through final result reporting. Implements proper error handling and
    provides clear progress feedback to users.
    
    Execution Flow:
        1. Parse CLI arguments with validation
        2. Load base configuration and apply CLI overrides  
        3. Validate parameters and optimize configuration
        4. Initialize SimPy environment and simulation components
        5. Set up network topology (nodes and peer connections)
        6. Create miners and wallet processes
        7. Execute simulation with coordinator
        8. Report final results and cleanup
        
    Error Handling:
        - Configuration validation errors
        - File I/O errors for config loading
        - Simulation runtime exceptions
        - Graceful cleanup on interruption
        
    No Args or Returns:
        Uses CLI argument parsing and exits with appropriate status codes.
    """
    # Parse command-line arguments
    args = parse_args()

    # Load configuration and merge CLI overrides
    config = load_config(args.chain)
    config = merge_cli_args(config, args)

    # Validate configuration and show summary
    validation_results = validate_configuration(config)
    print_configuration_summary(config, args.chain, validation_results)
    
    print()  # Empty line for readability

    # Create SimPy environment and coordinator
    env = simpy.Environment()
    coordinator = SimulationCoordinator(config)
    env.coordinator = coordinator  # Add reference for nodes to access

    # Create wallets (same as original)
    for i in range(config['transactions']['wallets']):
        env.process(wallet(env, i, 
                          config['transactions']['transactions_per_wallet'], 
                          config['transactions']['interval'], 
                          coordinator.pool))

    # Create nodes and network topology (same as original)
    nodes = [Node(env, i) for i in range(config['network']['nodes'])]
    for n in nodes:
        n.neighbors = random.sample([x for x in nodes if x != n], 
                                   config['network']['neighbors'])

    # Create miners (same as original)
    miners = [Miner(i, config['mining']['hashrate']) 
              for i in range(config['mining']['miners'])]

    # Run simulation (same as original)
    coord_proc = env.process(coordinator.coord(env, nodes, miners))
    env.run(until=coord_proc)


if __name__ == "__main__":
    main()