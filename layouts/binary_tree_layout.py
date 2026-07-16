from __future__ import annotations

from models.binary_tree_node import BinaryTreeNode


def calculate_binary_tree_positions(
    root: BinaryTreeNode,
    horizontal_gap: float = 110.0,
    vertical_gap: float = 110.0,
) -> dict[BinaryTreeNode, tuple[float, float]]:
    positions: dict[
        BinaryTreeNode,
        tuple[float, float],
    ] = {}

    next_x = 0.0

    def traverse(
        node: BinaryTreeNode | None,
        depth: int,
    ) -> None:
        nonlocal next_x

        if node is None:
            return

        traverse(
            node.left,
            depth + 1,
        )

        positions[node] = (
            next_x,
            depth * vertical_gap,
        )

        next_x += horizontal_gap

        traverse(
            node.right,
            depth + 1,
        )

    traverse(root, 0)

    return positions
