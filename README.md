# Blockchain Lab

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

A discrete event simulator for blockchain networks models realistic blockchain networks including mining competition, difficulty adjustment, transaction processing, block propagation, and economic incentives. It supports Bitcoin, Litecoin, Bitcoin Cash, and Dogecoin configurations out of the box.

Results include metrics on block times, transaction throughput, mining efficiency, network bandwidth usage, and economic parameters like total coins issued and mining rewards.

## Configuration

The simulator uses YAML configuration files to define network topology, mining parameters, economic models, and transaction generation. Default configurations are provided for major cryptocurrencies, and all parameters can be customized for specific research needs.

## Installation

```bash
pip install blockchain-lab
```

## Quick Start

Run a Bitcoin-like simulation with 100 blocks:

```bash
blocklab --chain btc --blocks 100 --transactions 1000
```

Run a custom fast blockchain simulation:

```bash
blocklab --blocktime 30 --blocks 50 --miners 5 --transactions 500
```

See all available options:

```bash
blocklab --help
```


## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.