# Configuration Files Documentation

## Available Configurations

### `btc.yml`
- Bitcoin network simulation with realistic parameters
- 10k nodes, 1000 miners, 10-minute blocks
- Use for Bitcoin-like blockchain research and modeling

### `defaults.yml`
- Balanced default configuration for general use
- 100 nodes, 10 miners, 10-second blocks
- Good starting point for custom configurations or fast testing

## Configuration Structure (YAML)

```yaml
network:
  nodes: 100              # Number of network nodes
  neighbors: 4            # Connections per node
  propagation_delay: 0.0  # Block propagation delay (seconds)

mining:
  miners: 10              # Number of mining entities
  hashrate: 1000.0        # Hashrate per miner (H/s equivalent)
  blocktime: 10.0         # Target block interval (seconds)
  blocksize: 100          # Max transactions per block
  difficulty: null        # Manual difficulty (null = auto-adjust)

economics:
  initial_reward: 50.0    # Starting block reward
  halving_interval: 210000 # Blocks between halvings
  max_halvings: 35        # Max halvings before reward = 0

transactions:
  wallets: 100            # Number of wallet entities
  transactions_per_wallet: 5  # Transactions each wallet creates
  interval: 30.0          # Avg time between transactions (seconds)

simulation:
  blocks_limit: 1000      # Max blocks (null = unlimited)
  years: null             # Duration in years (if blocks_limit is null)
  print_interval: 144     # Print summary every N blocks
  debug: false            # Enable detailed logging
  seed: null              # Random seed (null = random each run)
```

## Why YAML?
- **Easy to parse**: `yaml.safe_load()` is much cleaner than JSON
- **Human readable**: Comments and nested structure
- **No syntax mess**: Unlike JSON with quotes and brackets everywhere
- **Configuration friendly**: Standard for modern config files

## Parameter Relationships
- Total hashrate = miners × hashrate
- Auto-difficulty = block_time × total_hashrate (when difficulty=null)
- Network load = nodes × neighbors × block_size × transaction_size
- Simulation length = blocks_limit OR (years × 365 × 24 × 3600 / block_time)

## Realistic Bitcoin Values
- Real Bitcoin: ~10 minute blocks, 210k halving, 8 connections, 4MB blocks
- Simulation scaling: Use smaller networks (100-10k nodes) for performance
- Testing: Use faster block times (1-10s) and smaller limits for development