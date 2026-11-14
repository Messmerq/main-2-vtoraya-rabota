"""Tests for repository parsing, traversal and output."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from graph import ascii_tree, build_graph, reverse_dependencies, to_d2
from repository import PyPIRepository, TestRepository


class ProjectTests(unittest.TestCase):
    """Exercise cycles, shared dependencies and metadata handling."""

    def setUp(self):
        self.repo = TestRepository('examples/graph.json')
        self.graph = build_graph(self.repo, 'A')

    def test_graph_cycle_and_shared_node(self):
        self.assertEqual(set(self.graph), {'A', 'B', 'C', 'D'})
        self.assertEqual(self.graph['D'], ['A'])
        self.assertIn('already shown', ascii_tree(self.graph, 'A'))

    def test_reverse_transitive(self):
        self.assertEqual(reverse_dependencies(self.graph, 'D'),
                         ['A', 'B', 'C'])
        self.assertEqual(reverse_dependencies({'E': []}, 'E'), [])

    def test_d2_and_isolated_node(self):
        self.assertIn('"A" -> "B"', to_d2(self.graph))
        self.assertEqual(to_d2({'E': []}), '"E"')

    def test_invalid_test_graph(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as file:
            json.dump({'A': ['missing']}, file)
            file.flush()
            with self.assertRaises(ValueError):
                TestRepository(file.name)

    def test_pypi_metadata(self):
        requirements = ['Foo_Bar>=2', 'Dev; extra == "dev"']
        data = {'info': {'requires_dist': requirements}}
        response = io.BytesIO(json.dumps(data).encode())
        with patch('repository.urlopen', return_value=response):
            repo = PyPIRepository('https://pypi.org')
            self.assertEqual(repo.dependencies('x'), ['foo-bar'])


if __name__ == '__main__':
    unittest.main()
