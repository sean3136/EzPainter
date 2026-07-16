from __future__ import annotations

from dataclasses import dataclass

RED = "red"
BLACK = "black"


@dataclass(eq=False)
class RedBlackNode:
    value: int
    color: str = RED

    left: RedBlackNode | None = None
    right: RedBlackNode | None = None
    parent: RedBlackNode | None = None


class RedBlackTree:
    def __init__(self) -> None:
        self.root: RedBlackNode | None = None

    def insert(self, value: int) -> None:
        node = RedBlackNode(value=value)

        parent: RedBlackNode | None = None
        current = self.root

        while current is not None:
            parent = current

            if value < current.value:
                current = current.left

            elif value > current.value:
                current = current.right

            else:
                return

        node.parent = parent

        if parent is None:
            self.root = node

        elif value < parent.value:
            parent.left = node

        else:
            parent.right = node

        self._fix_insert(node)

    def _rotate_left(
        self,
        node: RedBlackNode,
    ) -> None:
        pivot = node.right

        if pivot is None:
            return

        node.right = pivot.left

        if pivot.left is not None:
            pivot.left.parent = node

        pivot.parent = node.parent

        if node.parent is None:
            self.root = pivot

        elif node is node.parent.left:
            node.parent.left = pivot

        else:
            node.parent.right = pivot

        pivot.left = node
        node.parent = pivot

    def _rotate_right(
        self,
        node: RedBlackNode,
    ) -> None:
        pivot = node.left

        if pivot is None:
            return

        node.left = pivot.right

        if pivot.right is not None:
            pivot.right.parent = node

        pivot.parent = node.parent

        if node.parent is None:
            self.root = pivot

        elif node is node.parent.right:
            node.parent.right = pivot

        else:
            node.parent.left = pivot

        pivot.right = node
        node.parent = pivot

    def _fix_insert(
        self,
        node: RedBlackNode,
    ) -> None:
        while node.parent is not None and node.parent.color == RED:
            grandparent = node.parent.parent

            if grandparent is None:
                break

            if node.parent is grandparent.left:
                uncle = grandparent.right

                if uncle is not None and uncle.color == RED:
                    node.parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    node = grandparent

                else:
                    if node is node.parent.right:
                        node = node.parent
                        self._rotate_left(node)

                    if node.parent is not None:
                        node.parent.color = BLACK

                        grandparent = node.parent.parent

                        if grandparent is not None:
                            grandparent.color = RED
                            self._rotate_right(grandparent)

            else:
                uncle = grandparent.left

                if uncle is not None and uncle.color == RED:
                    node.parent.color = BLACK
                    uncle.color = BLACK
                    grandparent.color = RED
                    node = grandparent

                else:
                    if node is node.parent.left:
                        node = node.parent
                        self._rotate_right(node)

                    if node.parent is not None:
                        node.parent.color = BLACK

                        grandparent = node.parent.parent

                        if grandparent is not None:
                            grandparent.color = RED
                            self._rotate_left(grandparent)

        if self.root is not None:
            self.root.color = BLACK

    def find(self, value: int) -> RedBlackNode | None:
        current = self.root
        while current is not None:
            if value == current.value:
                return current
            elif value < current.value:
                current = current.left
            else:
                current = current.right
        return None

    def _minimum(self, node: RedBlackNode) -> RedBlackNode:
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

        x_parent = y.parent
        y_was_left = False
        if x_parent is not None:
            y_was_left = (y == x_parent.left)

        if x is not None:
            x.parent = x_parent

        if x_parent is None:
            self.root = x
        elif y == x_parent.left:
            x_parent.left = x
        else:
            x_parent.right = x

        y_color = y.color

        if y != z:
            z.value = y.value

        if y_color == BLACK:
            self._fix_delete(x, x_parent, y_was_left)

    def _fix_delete(
        self,
        x: RedBlackNode | None,
        x_parent: RedBlackNode | None,
        y_was_left: bool,
    ) -> None:
        is_left = y_was_left
        while x is not self.root and (x is None or x.color == BLACK):
            if is_left:
                w = x_parent.right
                if w is not None and w.color == RED:
                    w.color = BLACK
                    x_parent.color = RED
                    self._rotate_left(x_parent)
                    w = x_parent.right

                if (w is None or (w.left is None or w.left.color == BLACK)) and \
                   (w is None or (w.right is None or w.right.color == BLACK)):
                    if w is not None:
                        w.color = RED
                    x = x_parent
                    x_parent = x.parent
                    if x_parent is not None:
                        is_left = (x == x_parent.left)
                else:
                    if w is not None and (w.right is None or w.right.color == BLACK):
                        if w.left is not None:
                            w.left.color = BLACK
                        w.color = RED
                        self._rotate_right(w)
                        w = x_parent.right

                    if w is not None:
                        w.color = x_parent.color
                        if w.right is not None:
                            w.right.color = BLACK
                    x_parent.color = BLACK
                    self._rotate_left(x_parent)
                    x = self.root
                    break
            else:
                w = x_parent.left
                if w is not None and w.color == RED:
                    w.color = BLACK
                    x_parent.color = RED
                    self._rotate_right(x_parent)
                    w = x_parent.left

                if (w is None or (w.left is None or w.left.color == BLACK)) and \
                   (w is None or (w.right is None or w.right.color == BLACK)):
                    if w is not None:
                        w.color = RED
                    x = x_parent
                    x_parent = x.parent
                    if x_parent is not None:
                        is_left = (x == x_parent.left)
                else:
                    if w is not None and (w.left is None or w.left.color == BLACK):
                        if w.right is not None:
                            w.right.color = BLACK
                        w.color = RED
                        self._rotate_left(w)
                        w = x_parent.left

                    if w is not None:
                        w.color = x_parent.color
                        if w.left is not None:
                            w.left.color = BLACK
                    x_parent.color = BLACK
                    self._rotate_right(x_parent)
                    x = self.root
                    break

        if x is not None:
            x.color = BLACK


def clone_rb_tree(node: RedBlackNode | None, parent: RedBlackNode | None = None) -> RedBlackNode | None:
    if node is None:
        return None
    new_node = RedBlackNode(value=node.value, color=node.color, parent=parent)
    new_node.left = clone_rb_tree(node.left, new_node)
    new_node.right = clone_rb_tree(node.right, new_node)
    return new_node

