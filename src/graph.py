"""Dependency graph traversal and textual renderers."""


def build_graph(repository, root):
    """Build the reachable graph using recursive depth-first search."""
    graph = {}

    def visit(node):
        if node in graph:
            return
        graph[node] = list(repository.dependencies(node))
        for dependency in graph[node]:
            visit(dependency)

    visit(root)
    return graph


def reverse_dependencies(graph, target):
    """Find reachable nodes that directly or indirectly depend on target."""
    reverse = {node: [] for node in graph}
    for node, dependencies in graph.items():
        for dep in dependencies:
            reverse.setdefault(dep, []).append(node)
    if target not in reverse:
        raise ValueError(f'package not found in graph: {target}')
    result = build_graph(_MappingRepository(reverse), target)
    return sorted(node for node in result if node != target)


class _MappingRepository:
    def __init__(self, graph):
        self.graph = graph

    def dependencies(self, node):
        """Return dependencies from an in-memory adjacency list."""
        return self.graph[node]


def ascii_tree(graph, root):
    """Render a tree with cycle and repeated-node markers."""
    lines = [root]
    expanded = {root}

    def visit(node, prefix):
        children = graph[node]
        for index, child in enumerate(children):
            last = index == len(children) - 1
            branch = '`-- ' if last else '|-- '
            repeated = child in expanded
            suffix = ' (already shown)' if repeated else ''
            lines.append(prefix + branch + child + suffix)
            if not repeated:
                expanded.add(child)
                visit(child, prefix + ('    ' if last else '|   '))

    visit(root, '')
    return '\n'.join(lines)


def to_d2(graph):
    """Render graph in D2, quoting identifiers and including isolated nodes."""
    import json
    lines = [json.dumps(node) for node in graph]
    for node, dependencies in graph.items():
        for dep in dependencies:
            lines.append(f'{json.dumps(node)} -> {json.dumps(dep)}')
    return '\n'.join(lines)
