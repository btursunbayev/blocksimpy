# Configuration Reference

## Presets

| Chain | Block Time | Reward | Halving | Block Size | Use Case |
|-------|-----------|--------|---------|-----------|----------|
| **btc** | 600s | 50 BTC | 210k blocks | 4096 tx | Bitcoin modeling |
| **bch** | 600s | 6.25 BCH | 210k blocks | 32768 tx | Large block testing |
| **ltc** | 150s | 50 LTC | 840k blocks | 4096 tx | Fast simulations (4× speed) |
| **doge** | 60s | 10000 DOGE | None | 4096 tx | Rapid testing (10× speed) |
| **defaults** | 10s | 50 | 210k blocks | 4096 tx | Development |

Usage: `blocksimpy --chain btc --blocks 100`

## Parameters

### Network

```yaml
network:
  nodes: 10              # Number of network peers
  neighbors: 5           # Connections per node
  propagation_delay: 0.1 # Unused (legacy parameter)
```

**nodes**: Total network participants storing blockchain.  
**neighbors**: Peer connections per node. Must be < nodes. Real Bitcoin uses 8-125.  
**propagation_delay**: Ignored by current BFS optimization.

### Mining

```yaml
mining:
  miners: 10           # Number of competing miners
  hashrate: 1000000.0  # Hashrate per miner (H/s)
  blocktime: 600.0     # Target block interval (seconds)
  blocksize: 4096      # Max transactions per block
  difficulty: null     # Auto-calculated if null
```

**miners**: Active mining participants.  
**hashrate**: Individual miner capacity. Total network hashrate = miners × hashrate.  
**blocktime**: Target seconds between blocks. Bitcoin: 600s, Litecoin: 150s, Dogecoin: 60s.  
**blocksize**: Transaction capacity. Bitcoin: ~4096, Bitcoin Cash: ~32768.  
**difficulty**: Mining difficulty. If null, auto-calculates as blocktime × total_hashrate.

### Economics

```yaml
economics:
  initial_reward: 50.0      # Starting block reward
  halving_interval: 210000  # Blocks between halvings
  max_halvings: 64          # Maximum halving count
```

**initial_reward**: Coins per block at genesis.  
**halving_interval**: Blocks until reward halves. Bitcoin: 210k, Litecoin: 840k.  
**max_halvings**: Halving iterations before reward reaches zero. Set to 0 to disable halvings (constant reward).

Total supply: initial_reward × halving_interval × 2 (for infinite halvings).

### Transactions

```yaml
transactions:
  wallets: 10                    # Transaction sources
  transactions_per_wallet: 10    # Transactions per source
  interval: 10.0                 # Seconds between transactions
```

**wallets**: Number of transaction generators.  
**transactions_per_wallet**: Total transactions per wallet. Total tx = wallets × transactions_per_wallet.  
**interval**: Delay between transaction generation events. Rate ≈ wallets / interval tx/s.

Transactions enter FIFO mempool. Blocks include up to blocksize transactions.

### Simulation

```yaml
simulation:
  blocks: 100          # Max blocks (null = unlimited)
  years: null          # Simulated time (if blocks is null)
  print_interval: 144  # Summary frequency
  debug: false         # Verbose per-block output
  seed: 42             # RNG seed (null = random)
```

**blocks**: Simulation stops after this many blocks.  
**years**: Alternative termination. Stops after simulated time. Formula: blocks ≈ (years × 365.25 × 86400) / blocktime.  
**print_interval**: Print summary every N blocks. Bitcoin uses 144 (daily).  
**debug**: If true, prints every block with full details.  
**seed**: Random seed for reproducibility.

## Command-Line Overrides

CLI arguments override YAML values:

```bash
blocksimpy --chain btc --blocktime 30 --blocks 50 --miners 5
```

All YAML parameters have corresponding CLI flags. See `blocksimpy --help`.

## Validation Rules

Startup validates:
- miners > 0
- hashrate > 0
- blocktime > 0
- blocksize > 0
- nodes > 0
- neighbors < nodes

## See Also

[Architecture](../docs/ARCHITECTURE.md) - Design rationale, algorithms, complexity analysis