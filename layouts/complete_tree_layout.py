from models.heap import HeapNode


def calculate_complete_tree_positions(
    root: HeapNode | None,
    horizontal_gap: float = 80.0,
    vertical_gap: float = 100.0,
) -> dict[HeapNode, tuple[float, float]]:
    positions: dict[HeapNode, tuple[float, float]] = {}
    if root is None:
        return positions

    def get_depth(node: HeapNode | None) -> int:
        if node is None:
            return 0
        return 1 + max(get_depth(node.left), get_depth(node.right))

    depth = get_depth(root)

    positions[root] = (0.0, 0.0)
    queue = [root]
    level_map = {root: 0}

    while queue:
        node = queue.pop(0)
        curr_level = level_map[node]
        curr_x, curr_y = positions[node]

        if curr_level < depth - 1:
            spacing = horizontal_gap * (2 ** (depth - 2 - curr_level))
        else:
            spacing = horizontal_gap

        if node.left is not None:
            positions[node.left] = (curr_x - spacing / 2, curr_y + vertical_gap)
            level_map[node.left] = curr_level + 1
            queue.append(node.left)

        if node.right is not None:
            positions[node.right] = (curr_x + spacing / 2, curr_y + vertical_gap)
            level_map[node.right] = curr_level + 1
            queue.append(node.right)

    return positions
