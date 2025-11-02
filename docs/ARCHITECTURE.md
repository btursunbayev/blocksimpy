# Architecture

## Overview

BlockSimPy is a discrete event simulator for blockchain networks built on SimPy. It models proof-of-work consensus, network propagation, economic incentives, and transaction processing to enable controlled experimentation with blockchain protocols.

The simulator supports Bitcoin, Litecoin, Dogecoin, and Bitcoin Cash configurations. All parameters are customizable through YAML files. The implementation uses graph-based optimization for efficient block propagation.