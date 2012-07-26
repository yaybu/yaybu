
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

class IslandError(GraphError):
    pass
        
class Graph:
    
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
            if n.ref is ref:
                return n
        node = Node(ref)
        self.nodes.append(node)
        return node
        
    def add_edge(self, from_, to):
        from_node = self.get_node(from_)
        to_node = self.get_node(to)
        from_node.add_edge(to_node)
        
    def resolve(self):
        resolved = []
        self.dep_resolve(self.nodes[0], resolved, [])
        for n in self.nodes:
            if n not in resolved:
                raise IslandError("Some nodes not connected to resolved graph")
        return [n.ref for n in resolved]
        