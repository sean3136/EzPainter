from __future__ import annotations


class HeapNode:
    def __init__(self, value: int) -> None:
        self.value = value
        self.left: HeapNode | None = None
        self.right: HeapNode | None = None
        self.parent: HeapNode | None = None


class Heap:
    def __init__(self, is_min_heap: bool = True) -> None:
        self.is_min_heap = is_min_heap
        self.nodes: list[HeapNode] = []

    def insert(self, value: int) -> None:
        node = HeapNode(value)
        self.nodes.append(node)
        self._bubble_up(len(self.nodes) - 1)

    def extract_root(self) -> int | None:
        if not self.nodes:
            return None
        root_val = self.nodes[0].value
        if len(self.nodes) == 1:
            self.nodes.pop()
        else:
            self.nodes[0] = self.nodes.pop()
            self._bubble_down(0)
        return root_val

    def delete(self, value: int) -> None:
        idx = -1
        for i, node in enumerate(self.nodes):
            if node.value == value:
                idx = i
                break
        if idx == -1:
            return

        if idx == len(self.nodes) - 1:
            self.nodes.pop()
        else:
            self.nodes[idx] = self.nodes.pop()
            self._bubble_up(idx)
            self._bubble_down(idx)

    def _less(self, a: int, b: int) -> bool:
        if self.is_min_heap:
            return a < b
        else:
            return a > b

    def _bubble_up(self, idx: int) -> None:
        while idx > 0:
            parent_idx = (idx - 1) // 2
            if self._less(self.nodes[idx].value, self.nodes[parent_idx].value):
                self.nodes[idx], self.nodes[parent_idx] = self.nodes[parent_idx], self.nodes[idx]
                idx = parent_idx
            else:
                break

    def _bubble_down(self, idx: int) -> None:
        n = len(self.nodes)
        while True:
            left_idx = 2 * idx + 1
            right_idx = 2 * idx + 2
            target_idx = idx

            if left_idx < n and self._less(self.nodes[left_idx].value, self.nodes[target_idx].value):
                target_idx = left_idx

            if right_idx < n and self._less(self.nodes[right_idx].value, self.nodes[target_idx].value):
                target_idx = right_idx

            if target_idx != idx:
                self.nodes[idx], self.nodes[target_idx] = self.nodes[target_idx], self.nodes[idx]
                idx = target_idx
            else:
                break

    def rebuild_tree(self) -> HeapNode | None:
        n = len(self.nodes)
        if n == 0:
            return None
        for i in range(n):
            node = self.nodes[i]
            left_idx = 2 * i + 1
            right_idx = 2 * i + 2

            node.left = self.nodes[left_idx] if left_idx < n else None
            node.right = self.nodes[right_idx] if right_idx < n else None

            if node.left is not None:
                node.left.parent = node
            if node.right is not None:
                node.right.parent = node
        self.nodes[0].parent = None
        return self.nodes[0]


def clone_heap(heap: Heap) -> Heap:
    new_heap = Heap(is_min_heap=heap.is_min_heap)
    new_heap.nodes = [HeapNode(node.value) for node in heap.nodes]
    new_heap.rebuild_tree()
    return new_heap
