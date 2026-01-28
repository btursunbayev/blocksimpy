#!/usr/bin/env python3
"""
Command Line Interface (CLI) argument parser for blockchain simulator.

This module provides a comprehensive CLI interface for configuring blockchain simulation
parameters including network topology, mining settings, transaction generation, and
reporting options. All parameters follow the discrete event simulation specification
for realistic blockchain behavior modeling.

The CLI supports both individual parameter overrides and chain-based configuration
loading (btc, defaults) with parameter inheritance and validation.
"""

import argparse


def create_parser():
    """
    Create and configure the argument parser for blockchain simulation.

    Provides comprehensive CLI interface for blockchain simulation parameters:
    - Network topology (nodes, neighbors, propagation)
    - Mining configuration (miners, hashrate, difficulty, block timing)
    - Transaction generation (wallets, transaction patterns, intervals)
    - Economic model (rewards, halving schedule)
    - Simulation control (duration, termination conditions)
    - Reporting and debug options

    Returns:
        argparse.ArgumentParser: Configured parser with all blockchain simulation options.

    Parameter Details:
        --nodes N: Create N peer nodes, each maintaining stored block IDs
        --neighbors M: Randomly connect each node to M distinct peers
        --miners K: Spawn K miner processes with specified hashrate
        --hashrate H: Hashrate per miner (expected time follows exponential distribution)
        --blocktime T: Target block time in seconds for difficulty adjustment
        --difficulty D: Mining difficulty (auto-calculated if not set)
        --blocksize B: Max transactions per block (FIFO from unconfirmed pool)
        --wallets W: Generate W wallet processes for transaction generation
        --transactions X: Each wallet sends X transactions to unconfirmed pool
        --interval I: Average seconds between transactions per wallet
        --blocks L: Run until L blocks mined or all txs processed (whichever first)
        --reward R: Initial coinbase reward per block (default 50)
        --halving H: Blocks between reward halving (default 210000)
        --print P: Print summary every P blocks (default 144, daily if 10min blocks)
    """
    parser = argparse.ArgumentParser(
        description="Blockchain Discrete Event Simulator - Realistic blockchain behavior modeling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Bitcoin simulation for 100 blocks
  %(prog)s --chain btc --blocks 100

  # Custom blockchain
  %(prog)s --blocktime 30 --blocks 50 --miners 5

  # Large network simulation
  %(prog)s --nodes 50 --neighbors 8 --miners 20 --blocks 100
        """,
    )

    # === Configuration Loading ===
    parser.add_argument(
        "--chain",
        type=str,
        metavar="TYPE",
        default="defaults",
        help="Blockchain configuration preset (btc, defaults)",
    )

    # === Network Topology (Section 2.1) ===
    network_group = parser.add_argument_group("Network Configuration")
    network_group.add_argument(
        "--nodes",
        type=int,
        metavar="N",
        help="Number of peer nodes, each maintaining stored block IDs",
    )
    network_group.add_argument(
        "--neighbors",
        type=int,
        metavar="M",
        help="Number of distinct peer connections per node (random topology)",
    )

    # === Mining & Difficulty (Section 2.2) ===
    mining_group = parser.add_argument_group("Mining Configuration")
    mining_group.add_argument(
        "--miners",
        type=int,
        metavar="K",
        help="Number of mining processes competing for blocks",
    )
    mining_group.add_argument(
        "--hashrate",
        type=float,
        metavar="H",
        help="Hashrate per miner (total_hashrate affects block timing)",
    )
    mining_group.add_argument(
        "--difficulty",
        type=float,
        metavar="D",
        help="Mining difficulty (auto-calculated as blocktime × total_hashrate if not set)",
    )
    mining_group.add_argument(
        "--blocktime",
        type=float,
        metavar="T",
        help="Target block time in seconds (used for difficulty retargeting)",
    )
    mining_group.add_argument(
        "--blocksize",
        type=int,
        metavar="B",
        help="Maximum transactions per block (FIFO from unconfirmed pool)",
    )

    # === Economic Model (Section 2.2.3) ===
    economics_group = parser.add_argument_group("Economic Model")
    economics_group.add_argument(
        "--reward",
        dest="init_reward",
        type=float,
        default=50,
        metavar="R",
        help="Initial coinbase reward per block (default: 50)",
    )
    economics_group.add_argument(
        "--halving",
        dest="halving_interval",
        type=int,
        default=210000,
        metavar="H",
        help="Blocks between reward halving events (default: 210000, 0 disables)",
    )

    # === Transaction Generation (Section 2.3) ===
    tx_group = parser.add_argument_group("Transaction Generation")
    tx_group.add_argument(
        "--wallets",
        type=int,
        metavar="W",
        help="Number of wallet processes generating transactions",
    )
    tx_group.add_argument(
        "--transactions",
        type=int,
        metavar="X",
        help="Number of transactions each wallet will generate",
    )
    tx_group.add_argument(
        "--interval",
        type=float,
        metavar="I",
        help="Average seconds between transactions per wallet (Poisson process)",
    )

    # === Simulation Control (Section 2.3.3) ===
    control_group = parser.add_argument_group("Simulation Control")
    control_group.add_argument(
        "--blocks",
        type=int,
        metavar="L",
        help="Maximum blocks to mine (simulation ends when reached or all txs confirmed)",
    )
    control_group.add_argument(
        "--years",
        type=float,
        metavar="Y",
        help="Simulation duration in years (used if --blocks omitted)",
    )

    # === Attack Simulation ===
    attack_group = parser.add_argument_group("Attack Simulation")
    attack_group.add_argument(
        "--attack",
        type=str,
        choices=["selfish", "double-spend", "eclipse"],
        metavar="TYPE",
        help="Attack type: selfish, double-spend, eclipse",
    )
    attack_group.add_argument(
        "--attacker-hashrate",
        dest="attacker_hashrate",
        type=float,
        metavar="RATIO",
        help="Attacker's hashrate as fraction of total (0.0-1.0)",
    )
    attack_group.add_argument(
        "--confirmations",
        type=int,
        default=6,
        metavar="N",
        help="Confirmations for double-spend attack (default: 6)",
    )
    attack_group.add_argument(
        "--victim-nodes",
        dest="victim_nodes",
        type=int,
        default=1,
        metavar="N",
        help="Number of nodes to eclipse (default: 1)",
    )

    # === Reporting & Debug (Section 2.4) ===
    output_group = parser.add_argument_group("Reporting & Debug")
    output_group.add_argument(
        "--print",
        dest="print_int",
        type=int,
        default=144,
        metavar="P",
        help="Print summary every P blocks (default: 144, ~daily for 10min blocks)",
    )
    output_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug output (prints every block)",
    )
    output_group.add_argument(
        "--export-metrics",
        dest="export_metrics",
        type=str,
        metavar="FILE",
        help="Export simulation metrics to JSON file after completion",
    )
    output_group.add_argument(
        "--checkpoint",
        type=str,
        metavar="FILE",
        help="Save checkpoint to FILE at each print interval",
    )
    output_group.add_argument(
        "--resume",
        type=str,
        metavar="FILE",
        help="Resume simulation from checkpoint FILE",
    )

    return parser


def parse_args():
    """Parse command line arguments."""
    parser = create_parser()
    return parser.parse_args()
