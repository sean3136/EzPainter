from __future__ import annotations

from dataclasses import dataclass


@dataclass(eq=False)
class BSTNode:
    value: int
    left: BSTNode | None = None
    right: BSTNode | None = None
    parent: BSTNode | None = None


class BST:
    def __init__(self) -> None:
        self.root: BSTNode | None = None

    def insert(self, value: int) -> None:
        new_node = BSTNode(value=value)
        if self.root is None:
            self.root = new_node
            return

        current = self.root
        parent = None
        while current is not None:
            parent = current
            if value < current.value:
                current = current.left
            elif value > current.value:
                current = current.right
            else:
                return

        new_node.parent = parent
        if value < parent.value:
            parent.left = new_node
        else:
            parent.right = new_node

    def find(self, value: int) -> BSTNode | None:
        current = self.root
        while current is not None:
            if value == current.value:
                return current
            elif value < current.value:
                current = current.left
            else:
                current = current.right
        return None

    def _minimum(self, node: BSTNode) -> BSTNode:
        while node.left is not None:
            node = node.left
        return node

    def delete(self, value: int) -> None:
        z = self.find(value)
        if z is None:
            return

        if z.left is None or z.right is None:
            y = z
        else:
            y = self._minimum(z.right)

        if y.left is not None:
            x = y.left
        else:
            x = y.right

        if x is not None:
            x.parent = y.parent

        if y.parent is None:
            self.root = x
        elif y == y.parent.left:
            y.parent.left = x
        else:
            y.parent.right = x

        if y != z:
            z.value = y.value


def clone_bst(node: BSTNode | None, parent: BSTNode | None = None) -> BSTNode | None:
    if node is None:
        return None
    new_node = BSTNode(value=node.value, parent=parent)
    new_node.left = clone_bst(node.left, new_node)
    new_node.right = clone_bst(node.right, new_node)
    return new_node
