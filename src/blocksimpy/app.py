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

import random
import time
from typing import Any, Dict

import simpy

from .cli.args_parser import parse_args
from .config.config_loader import load_config, merge_cli_args
from .core.miner import Miner
from .core.node import Node
from .simulation.coordinator import SimulationCoordinator
from .simulation.state import SimulationState
from .simulation.wallet import wallet
from .utils.block_check import validate_configuration


def print_configuration_summary(
    config: Dict[str, Any],
    chain_name: str,
    blocks_mined: int,
    coordinator: SimulationCoordinator,
) -> None:
    """
    Display comprehensive simulation results and configuration summary.

    Provides complete overview of configuration used and results achieved,
    designed to be displayed at the end of simulation so users can see
    all metrics even after long-running simulations.

    Args:
        config: Complete configuration dictionary
        chain_name: Name of blockchain preset being used
        blocks_mined: Total blocks mined during simulation
        coordinator: Coordinator with final metrics and results
    """
    print()
    print("=" * 60)
    print("SIMULATION RESULTS")
    print("=" * 60)

    # Configuration recap
    print("Configuration:")
    print(f"  Chain: {chain_name}")
    print(
        f"  Network: {config['network']['nodes']} nodes, "
        f"{config['network']['neighbors']} neighbors each"
    )
    print(
        f"  Miners: {config['mining']['miners']} miners @ "
        f"{config['mining']['hashrate']:,.0f} H/s each"
    )
    print(
        f"  Wallets: {config['transactions']['wallets']} wallets, "
        f"{config['transactions']['transactions_per_wallet']} tx each"
    )

    # Block time display
    blocktime = config["mining"]["blocktime"]
    if blocktime >= 60:
        time_str = f"{int(blocktime / 60)} min"
    else:
        time_str = f"{blocktime} sec"
    print(f"  Block time: {time_str}")
    print(f"  Block size: {config['mining']['blocksize']:,} transactions/block")

    print()

    # Simulation results
    simulated_time = coordinator.final_simulated_time
    simulated_days = simulated_time / 86400
    simulated_years = simulated_time / (365.25 * 86400)

    print("Results:")
    print(f"  Blocks mined: {blocks_mined:,}")
    print(f"  Transactions: {coordinator.total_tx:,}")
    print(f"  Coins issued: {coordinator.total_coins:,.2f}")
    print(f"  Network data: {coordinator.network_data / 1_000_000:,.2f} MB")
    print(f"  I/O requests: {coordinator.io_requests:,}")

    print()

    # Timing information placeholder (to be filled by caller)
    print("Performance:")
    print(
        f"  Simulated time: {simulated_time:,.2f} seconds "
        f"({simulated_days:,.2f} days / {simulated_years:,.4f} years)"
    )


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

    # Validate configuration
    validate_configuration(config)

    # Set random seed for reproducibility
    seed = config["simulation"].get("seed")
    if seed is not None:
        random.seed(seed)

    actual_start_time = time.time()

    env = simpy.Environment()
    coordinator = SimulationCoordinator(config)
    env.coordinator = coordinator

    # Create wallets
    for i in range(config["transactions"]["wallets"]):
        env.process(
            wallet(
                env,
                i,
                config["transactions"]["transactions_per_wallet"],
                config["transactions"]["interval"],
                coordinator.pool,
            )
        )

    # Create nodes and network topology
    nodes = [Node(env, i) for i in range(config["network"]["nodes"])]
    for n in nodes:
        n.neighbors = random.sample(
            [x for x in nodes if x != n], config["network"]["neighbors"]
        )

    # Create miners
    miners = []
    num_miners = config["mining"]["miners"]
    hashrate = config["mining"]["hashrate"]

    # Check for attack mode
    if args.attack == "selfish":
        from .attacks import SelfishMiner

        attacker_ratio = args.attacker_hashrate or 0.3  # Default 30%
        attacker_hashrate = hashrate * num_miners * attacker_ratio
        honest_hashrate = (
            hashrate * num_miners * (1 - attacker_ratio) / (num_miners - 1)
        )

        # One selfish miner with proportional hashrate
        miners.append(SelfishMiner(0, attacker_hashrate))

        # Rest are honest miners
        for i in range(1, num_miners):
            miners.append(Miner(i, honest_hashrate))

        print(
            f"Attack mode: selfish mining (attacker={attacker_ratio * 100:.0f}% hashrate)"
        )

    elif args.attack == "double-spend":
        from .attacks import DoubleSpendMiner

        attacker_ratio = args.attacker_hashrate or 0.51  # Default 51%
        attacker_hashrate = hashrate * num_miners * attacker_ratio
        honest_hashrate = (
            hashrate * num_miners * (1 - attacker_ratio) / (num_miners - 1)
        )

        # One double-spend attacker
        miners.append(DoubleSpendMiner(0, attacker_hashrate, args.confirmations))

        # Rest are honest miners
        for i in range(1, num_miners):
            miners.append(Miner(i, honest_hashrate))

        print(
            f"Attack mode: double-spend (attacker={attacker_ratio * 100:.0f}% hashrate, "
            f"{args.confirmations} confirmations)"
        )

    elif args.attack == "eclipse":
        from .attacks import EclipseAttacker

        # Eclipse attack uses normal miners but manipulates propagation
        miners = [Miner(i, hashrate) for i in range(num_miners)]
        victim_ids = list(range(args.victim_nodes))
        eclipse_attacker = EclipseAttacker(victim_ids)
        coordinator.eclipse_attacker = eclipse_attacker
        print(f"Attack mode: eclipse ({args.victim_nodes} victim nodes)")

    else:
        # Normal mode: all honest miners
        miners = [Miner(i, hashrate) for i in range(num_miners)]

    # Load checkpoint if resuming
    initial_state = None
    if args.resume:
        initial_state = SimulationState.load(args.resume)
        print(
            f"Resuming from checkpoint: {args.resume} (block {initial_state.block_count})"
        )

    # Run simulation
    coord_proc = env.process(
        coordinator.coord(
            env,
            nodes,
            miners,
            initial_state=initial_state,
            checkpoint_file=args.checkpoint,
        )
    )
    env.run(until=coord_proc)

    actual_elapsed_time = time.time() - actual_start_time

    print_configuration_summary(
        config, args.chain, coordinator.final_blocks, coordinator
    )

    print(f"  Actual time: {actual_elapsed_time:.6f} seconds")

    if coordinator.final_simulated_time > 0:
        speed_factor = coordinator.final_simulated_time / actual_elapsed_time
        print(f"  Speed: {speed_factor:,.0f}x faster than real-time")

    if coordinator.final_blocks > 0:
        avg_block_time = coordinator.final_simulated_time / coordinator.final_blocks
        print(f"  Average block time: {avg_block_time:.2f} seconds")

    print("=" * 60)

    # Print attack results if present
    if coordinator.attack_metrics:
        m = coordinator.attack_metrics
        attack_type = m.get("attack_type", "selfish")

        print()
        if attack_type == "double_spend_51":
            print("ATTACK RESULTS (51% Double Spend)")
            print("-" * 40)
            print(f"  Attack attempts: {m['attack_attempts']}")
            print(f"  Successful: {m['successful_attacks']}")
            print(f"  Failed: {m['failed_attacks']}")
            print(f"  Success rate: {m['success_rate'] * 100:.1f}%")
            print(f"  Double-spent value: {m['double_spent_value']:.2f}")
            print(f"  Confirmations: {m['target_confirmations']}")
        elif attack_type == "eclipse":
            print("ATTACK RESULTS (Eclipse)")
            print("-" * 40)
            print(f"  Victim node: {m['victim_node_id']}")
            print(f"  Blocks withheld: {m['blocks_withheld']}")
            print(f"  Victim wasted blocks: {m['wasted_victim_blocks']}")
            print(f"  Eclipse duration: {m['eclipse_duration_blocks']} blocks")
        else:
            # Selfish mining (default)
            print("ATTACK RESULTS (Selfish Mining)")
            print("-" * 40)
            print(f"  Attacker blocks: {m['attacker_blocks']}")
            print(f"  Honest blocks: {m['honest_blocks']}")
            print(f"  Wasted honest blocks: {m['wasted_blocks']}")
            print(f"  Attacker share: {m['attacker_share'] * 100:.1f}%")
            print(f"  Attacker rewards: {m['attacker_rewards']:.2f}")
            print(f"  Honest rewards: {m['honest_rewards']:.2f}")
        print("=" * 60)

    # Export metrics if requested
    if args.export_metrics:
        coordinator.metrics.export_json(
            args.export_metrics, coordinator.total_tx, coordinator.total_coins
        )
        print(f"Metrics exported to: {args.export_metrics}")


if __name__ == "__main__":
    main()
