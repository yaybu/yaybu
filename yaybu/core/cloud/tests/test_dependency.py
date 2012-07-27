
from yaybu.core.cloud import dependency
import unittest

class TestDependency(unittest.TestCase):
    
    def test_resolution(self):
        # a-> b -> c
        #       -> d
        #       -> i -> j
        #  -> e
        #  -> f -> d
        #  -> g -> h
        #  -> g -> b
        graph = dependency.Graph()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("b", "i")
        graph.add_edge("i", "j")
        graph.add_edge("a", "e")
        graph.add_edge("a", "f")
        graph.add_edge("a", "g")
        graph.add_edge("f", "d")
        graph.add_edge("g", "h")
        graph.add_edge("g", "b")
        resolved = graph.resolve()
        self.assertEqual(resolved, ['c', 'j', 'i', 'b', 'e', 'd', 'f', 'h', 'g', 'a'])
        
    def test_circular(self):
        graph = dependency.Graph()
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("c", "a")
        self.assertRaises(dependency.CircularReferenceError, graph.resolve)
        
    def test_unlinked_graphs(self):
        graph = dependency.Graph()
        graph.add_edge("a", "b")
        graph.add_edge("c", "d")
        resolved = graph.resolve()
        self.assertEqual(resolved, ['b', 'a', 'd', 'c'])
        
    def test_no_graph(self):
        graph = dependency.Graph()
        graph.add_node("a")
        graph.add_node("b")
        resolved = graph.resolve()
        self.assertEqual(resolved, ['a', 'b'])
        
        


        
        