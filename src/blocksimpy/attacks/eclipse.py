#!/usr/bin/env python3
"""
Eclipse Attack implementation.

An eclipse attack isolates a victim node from the honest network by
surrounding it with attacker-controlled nodes. The victim only sees
blocks from the attacker, enabling various exploits.

Attack effects:
- Victim sees a different (attacker-controlled) chain
- Can enable double spends against the victim
- Victim's mining power works on attacker's chain
- Victim can be fed stale blocks

Reference: Heilman et al., "Eclipse Attacks on Bitcoin's Peer-to-Peer Network" (2015)
"""

from dataclasses import dataclass
from typing import List, Set


@dataclass
class EclipseState:
    """
    Tracks the state of an eclipse attack.

    The attacker controls connections to a victim node,
    feeding it a different view of the blockchain.
    """

    # Victim tracking
    victim_node_id: int = 0
    victim_chain_length: int = 0  # What victim thinks is the chain
    honest_chain_length: int = 0  # Actual honest chain

    # Attack status
    is_eclipsed: bool = False  # Is victim currently eclipsed
    blocks_withheld: int = 0  # Blocks not shown to victim

    # Metrics
    eclipse_duration_blocks: int = 0  # How long victim was eclipsed
    wasted_victim_blocks: int = 0  # Victim blocks on wrong chain

    def eclipse_victim(self, victim_id: int) -> None:
        """Start eclipsing a victim node."""
        self.victim_node_id = victim_id
        self.is_eclipsed = True
        self.victim_chain_length = 0
        self.honest_chain_length = 0

    def on_honest_block(self) -> str:
        """Honest network found a block (hidden from victim)."""
        self.honest_chain_length += 1
        self.blocks_withheld += 1
        self.eclipse_duration_blocks += 1
        return "block_withheld"

    def on_victim_block(self) -> str:
        """Victim found a block (will be orphaned later)."""
        self.victim_chain_length += 1
        self.wasted_victim_blocks += 1
        return "victim_wasted_work"

    def release_chain(self) -> str:
        """Release honest chain to victim, orphaning their work."""
        orphaned = self.victim_chain_length
        self.victim_chain_length = self.honest_chain_length
        return f"released_orphaned_{orphaned}"

    def get_metrics(self) -> dict:
        """Return attack metrics."""
        return {
            "attack_type": "eclipse",
            "victim_node_id": self.victim_node_id,
            "is_eclipsed": self.is_eclipsed,
            "blocks_withheld": self.blocks_withheld,
            "wasted_victim_blocks": self.wasted_victim_blocks,
            "eclipse_duration_blocks": self.eclipse_duration_blocks,
            "chain_difference": self.honest_chain_length - self.victim_chain_length,
        }


class EclipseAttacker:
    """
    Simulates an eclipse attack by controlling a victim's network view.

    This doesn't mine - it manipulates network propagation.
    Used alongside the coordinator to filter blocks to victim.
    """

    def __init__(self, victim_node_ids: List[int]):
        """
        Initialize eclipse attacker.

        Args:
            victim_node_ids: List of node IDs to eclipse
        """
        self.victim_ids: Set[int] = set(victim_node_ids)
        self.state = EclipseState()
        self.attack_type = "eclipse"

        if victim_node_ids:
            self.state.eclipse_victim(victim_node_ids[0])

    def should_propagate_to(self, node_id: int, block_from_attacker: bool) -> bool:
        """
        Decide if a block should propagate to a node.

        Args:
            node_id: Target node ID
            block_from_attacker: True if block is from attacker-controlled source

        Returns:
            True if block should propagate to this node
        """
        if node_id not in self.victim_ids:
            return True  # Non-victims get all blocks

        # Victim only sees attacker-approved blocks
        return block_from_attacker

    def on_block_found(self, is_victim_block: bool) -> str:
        """Called when any block is found."""
        if is_victim_block:
            return self.state.on_victim_block()
        else:
            return self.state.on_honest_block()

    def get_attack_metrics(self) -> dict:
        """Return current attack metrics."""
        return self.state.get_metrics()
