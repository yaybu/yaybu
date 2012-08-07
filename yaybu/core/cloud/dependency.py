
""" Dependency graph """

import itertools

class Node:
    def __init__(self, ref):
        self.ref = ref
        self.edges = []
        
    def add_edge(self, node):
        self.edges.append(node)
        
class GraphError(Exception):
    pass

class CircularReferenceError(GraphError):
    pass

class Graph:
    
    """ Represents a depency graph. Seems to cope ok with multiple unlinked graphs. """
    
    def __init__(self):
        self.nodes = []
        
    def dep_resolve(self, node, resolved, unresolved):
        unresolved.append(node)
        for edge in node.edges:
            if edge not in resolved:
                if edge in unresolved:
                    raise CircularReferenceError("Circular reference detected from %r to %r" % (node.ref, edge.ref))
                self.dep_resolve(edge, resolved, unresolved)
        resolved.append(node)
        unresolved.remove(node)
        
    def get_node(self, ref):
        for n in self.nodes:
            if n.ref == ref:
                return n
        node = Node(ref)
        self.nodes.append(node)
        return node
        
    def add_edge(self, from_, to):
        from_node = self.get_node(from_)
        to_node = self.get_node(to)
        from_node.add_edge(to_node)
        
    def add_node(self, node):
        """ Add a node without creating an edge. """
        # a side effect of getting a node is to add it if necessary
        self.get_node(node)
        
    def resolve(self):
        resolved = []
        island = []
        for n in self.nodes:
            if n not in resolved:
                self.dep_resolve(n, resolved, [])
        return [n.ref for n in resolved]
    
    