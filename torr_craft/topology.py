"""Topology rules for vacuum schematics."""

from typing import Dict, Iterable, Tuple

Edge = Tuple[str, str]


def unisolated_chamber_pair(component_types: Dict[str, str], edges: Iterable[Edge]):
    """Return two chambers reachable without crossing a gate valve, if any.

    A gate valve is an isolating boundary. Removing every gate valve from the
    graph must leave at most one chamber in each connected component.
    """
    parent = {}

    def find(node):
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for source, target in edges:
        if component_types.get(source) == "gate" or component_types.get(target) == "gate":
            continue
        union(source, target)

    by_root = {}
    for object_id, device_type in component_types.items():
        if device_type == "chamber":
            by_root.setdefault(find(object_id), []).append(object_id)

    for chambers in by_root.values():
        if len(chambers) >= 2:
            return chambers[0], chambers[1]
    return None
