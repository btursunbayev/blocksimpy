# Changelog

## [1.5.0] - 2026-01-28

### Added
- Proof-of-Space (PoSpace) consensus mechanism with space-weighted farmer selection
- Chia Network chain configuration (`--chain chia`)


## [1.4.0] - 2026-01-28

### Added
- Proof-of-Stake (PoS) consensus mechanism with stake-weighted validator selection
- Ethereum 2.0 chain configuration (`--chain eth2`)
- Chain configs organized into `chains/pow/` and `chains/pos/` directories

### Changed
- All PoW chain configs now explicitly declare `consensus.type: pow`
- README updated
- CONFIGURATION_GUIDE updated with consensus mechanism documentation

### Fixed
- Critical bug: `max_halvings=None` comparison now properly handled (treats None as unlimited)

### Removed
- `propagation_delay` parameter removed from all configs and tests (unused legacy parameter)

## [1.3.1] - 2026-01-28

### Fixed
- Eclipse attack now properly integrated with coordinator

### Changed
- Author metadata moved to pyproject.toml with project URLs

## [1.3.0] - 2026-01-27

### Added
- `--attack selfish` flag for selfish mining attack with configurable attacker hashrate (Eyal & Sirer 2014)
- `--attack double-spend` flag for 51% double-spend attack with configurable confirmation depth (Nakamoto 2008)
- `--attack eclipse` flag for eclipse attack with configurable victim nodes (Heilman et al. 2015)
- Attack metrics in output for each attack type

## [1.2.0] - 2026-01-27

### Added
- `--export-metrics` flag to export simulation metrics to JSON
- `--checkpoint` flag to save simulation state at each print interval
- `--resume` flag to resume simulation from checkpoint

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