# Changelog

## [1.3.0] - 2026-01-27

### Added
- **Selfish Mining Attack**: `--attack selfish` with `--attacker-hashrate`
- **51% Double Spend Attack**: `--attack double-spend` with `--confirmations`
- **Eclipse Attack**: `--attack eclipse` with `--victim-nodes`
- Attack metrics in output for each attack type

### New Files
- `attacks/selfish_miner.py` - Selfish mining (Eyal & Sirer 2014)
- `attacks/double_spend.py` - 51% double spend (Nakamoto 2008)
- `attacks/eclipse.py` - Eclipse attack (Heilman et al. 2015)

## [1.2.0] - 2026-01-27

### Added
- New `--export-metrics FILE` flag to export simulation metrics to JSON
- New `--checkpoint FILE` flag to save simulation state at each print interval
- New `--resume FILE` flag to resume a simulation from a saved checkpoint

### Changed
- Coordinator now accepts `initial_state` and `checkpoint_file` parameters for checkpoint/resume support
- SimulationState now includes `to_dict()`, `from_dict()`, `save()`, and `load()` methods for serialization

## [1.1.1] - 2026-01-27

### Fixed
- Test functions dont return values (fixes pytest warnings)
- Dogecoin test now validates coin issuance correctly
- Renamed `Test` class to `ValidationResult` to avoid pytest warning

### Changed
- `network_data` and `io_requests` are now properties delegating to `metrics`

## [1.1.0] - 2026-01-26

### Added
- `SimulationState` dataclass for checkpoint/resume support
- `SimulationMetrics` dataclass with `to_dict()` for metrics export
- `retarget_interval` config option
- Comprehensive test suite (66 tests)

### Changed
- Mempool uses `deque` for O(1) FIFO
- Coordinator uses extracted state and metrics components

### Fixed
- Seed wiring for reproducibility
- Dogecoin config halving behavior

### Removed
- Unused code (`node.env`, `create_wallets()`, `record_block()`)