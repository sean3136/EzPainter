from __future__ import annotations

from dataclasses import dataclass


@dataclass(eq=False)
class BinaryTreeNode:
    value: str

    left: BinaryTreeNode | None = None
    right: BinaryTreeNode | None = None
    parent: BinaryTreeNode | None = None

    def set_left(
        self,
        child: BinaryTreeNode | None,
    ) -> None:
        self.left = child

        if child is not None:
            child.parent = self

    def set_right(
        self,
        child: BinaryTreeNode | None,
    ) -> None:
        self.right = child

        if child is not None:
            child.parent = self
