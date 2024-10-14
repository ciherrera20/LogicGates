from collections import deque
from gates.utils.orderedset import OrderedSet
import math

class DirectedGraph():
    '''
    Directed Graph represented using adjacency lists implemented via dicts and sets.
    '''
    def __init__(self):
        '''
        Create a directed graph
        '''
        self._from_dict = {}  # For each vertex, stores the set of vertices to which there are outgoing edges
        self._to_dict = {}    # For each vertex, stores the set of vertices from which there are incoming edges
    
    def add_vertex(self, v):
        '''
        Add vertex v to the graph if it is not already in it
        Runtime: O(1)
        '''
        if v not in self._from_dict and v not in self._to_dict:
            self._from_dict[v] = OrderedSet()
            self._to_dict[v] = OrderedSet()
    
    def remove_vertex(self, v):
        '''
        Remove vertex v from the graph
        Runtime: O(|V|)
            Run time is proportional to the number of edges
            that v has. The worst case is v is connected to
            every other vertex.
        '''
        for w in self._from_dict[v]:
            self._to_dict[w].discard(v)
        for w in self._to_dict[v]:
            self._from_dict[w].discard(v)
        del self._from_dict[v]
        del self._to_dict[v]
    
    def check_edge(self, v, w):
        '''
        Check whether an edge from v to w is or would be part of a cycle
        Return True if yes, False otherwise
        '''
        # Check whether v is any of w's successors
        stack = deque([w])
        visited = OrderedSet()
        while len(stack) != 0:
            x = stack.pop()
            if x == v:
                return True
            elif x not in visited:
                for successor in self.get_direct_successors(x):
                    stack.append(successor)
                visited.add(x)
        return False

    def add_edge(self, v, w):
        '''
        Add an edge going from v to w
        Runtime: O(1)
        '''
        self._from_dict[v].add(w)
        self._to_dict[w].add(v)

    def remove_edge(self, v, w):
        '''
        If an edge exists from v to w, remove it
        Runtime: O(1)
        '''
        self._from_dict[v].discard(w)
        self._to_dict[w].discard(v)
    
    def get_shortest_paths(self, source):
        '''
        Get the lengths of the shortest path from the given
        source vertex to every other vertex.

        Runtime: O(|V|)
        '''
        # Perform a breadth first search
        lengths = {source: 0}
        queue = deque([source])
        while len(queue) != 0:
            v = queue.pop()
            for w in self._from_dict[v]:
                if w not in lengths:
                    lengths[w] = lengths[v] + 1
                    queue.appendleft(w)
        
        for v in self._from_dict:
            if v not in lengths:
                lengths[v] = math.inf
        return lengths
    
    def get_strongly_connected_components(self):
        '''
        Implements Tarjan's strongly connected components
        algorithm: https://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
        Returns components in topologically sorted order

        Runtime: O(|V| + |E|)
        '''
        unvisited = OrderedSet([v for v in self._from_dict])
        stack = deque()
        vertex_dict = {}
        index = 0
        sc_components = []
        dag_edges = []

        # Helper function to perform depth first search
        def helper(v):
            nonlocal index
            stack.append(v)
            vertex_dict[v] = (index, index, True, None)  # Hold index, lowlink, onstack status, and component index
            index += 1

            # Visit every vertex that v has an edge going to
            for w in self._from_dict[v]:
                was_unvisited = False
                if w in unvisited:
                    unvisited.discard(w)
                    helper(w)
                    was_unvisited = True

                # Update lowlink value depending on whether w was already visited and on the stack
                v_index, v_lowlink, _, _ = vertex_dict[v]
                w_index, w_lowlink, w_onstack, _ = vertex_dict[w]
                if was_unvisited:
                    vertex_dict[v] = (v_index, min(v_lowlink, w_lowlink), True, None)
                elif w_onstack:
                    vertex_dict[v] = (v_index, min(v_lowlink, w_index), True, None)
                else:
                    dag_edges.append((v, w))

            # Pop vertices into a component
            v_index, v_lowlink, _, _ = vertex_dict[v]
            if v_index == v_lowlink:
                comp_index = len(sc_components)
                component = OrderedSet()

                # Pop from the stack until the popped vertex is the current vertex
                w = stack.pop()
                w_index, w_lowlink, _, _ = vertex_dict[w]
                vertex_dict[w] = (w_index, w_lowlink, False, comp_index)
                component.add(w)
                while w != v:
                    w = stack.pop()
                    w_index, w_lowlink, _, _ = vertex_dict[w]
                    vertex_dict[w] = (w_index, w_lowlink, False, comp_index)
                    component.add(w)
                sc_components.insert(0, component)

        # Ensure that every vertex is put into a component
        while len(unvisited) != 0:
            v = unvisited.pop()
            helper(v)
        
        # Turn the graph into a DAG
        # dag = DirectedGraph()
        # for i in range(len(sc_components)):
        #     dag.add_vertex(i)
        # for v, w in dag_edges:
        #     _, _, _, v_comp = vertex_dict[v]
        #     _, _, _, w_comp = vertex_dict[w]
        #     dag.add_edge(v_comp, w_comp)

        # Return components
        return sc_components

    def get_order(self, source, flattened=True):
        '''
        Get an order for the graph that respects dependencies given a source
        Also return a list of vertices whose outgoing edges were cut to create the order

        Runtime: O(|V|^2+|E|^2)
            Worst-case occurs when the graph is complete,
            i.e. every vertex has an edge going to and from
            every other vertex. In that case, each
            recursive call adds a single vertex to the
            final order and performs Tarjan's algorithm on
            the graph formed by the remaining vertices.
        '''
        # order, cut_vertices = [], OrderedSet()
        order, cut_edges = [], OrderedSet()
        shortest_paths = self.get_shortest_paths(source)
        for component in self.get_strongly_connected_components():
            if len(component) == 1:
                v = list(component)[0]
                order.append(v)
                if v in self._to_dict[v]:
                    # cut_vertices.add(v)
                    cut_edges.add((v, v))
            else:
                g = DirectedGraph()
                source = None
                for v in component:
                    if source is None or shortest_paths[v] < shortest_paths[source]:
                        source = v
                    g.add_vertex(v)
                
                for w in component:
                    for v in self._to_dict[w]:
                        if v in component:
                            if w is not source:
                                g.add_edge(v, w)
                            else:
                                # cut_vertices.add(v)
                                cut_edges.add((v, w))
                
                # rec_order, rec_cut_vertices = g.get_order(source)
                rec_order, rec_cut_edges = g.get_order(source)
                if flattened:
                    order += rec_order
                else:
                    order.append(rec_order)
                # cut_vertices = cut_vertices.union(rec_cut_vertices)
                cut_edges = cut_edges.union(rec_cut_edges)
        # return order, cut_vertices
        return order, cut_edges

    def remove_cycles(self, source):
        '''
        Use the cut_edges returned by get_order to remove cycles
        '''
        order, cut_edges = self.get_order(source)
        acyclic = DirectedGraph.deserialize(self.serialize())
        for (v, w) in cut_edges:
            acyclic.remove_edge(v, w)
        return acyclic, order

    def get_layers(self, source):
        '''
        Put the vertices into layers
        '''
        acyclic, order = self.remove_cycles(source)

        # Create a dictionary to hold the rank values for each node
        rank = {}
        # Initialize the rank of each node to zero
        for v in acyclic._from_dict.keys():
            rank[v] = 0

        # Iterate over the nodes in topological order
        for i, w in enumerate(order):
            # Find the maximum rank of the predecessors of the current node
            max_rank = -1

            # Keep the source always below every other node, even if they are at the same layer
            predecessors = acyclic.get_direct_predecessors(w)
            if i == 1:
                predecessors.add(source)
            for v in predecessors:
                if rank[v] > max_rank:
                    max_rank = rank[v]
            # Set the rank of the current node to one more than the maximum rank
            rank[w] = max_rank + 1

        return rank

    def get_direct_successors(self, v):
        '''
        Get the direct successors of v
        '''
        return OrderedSet([w for w in self._from_dict[v]])
    
    def get_direct_predecessors(self, v):
        '''
        Get the direct predecessors of v
        '''
        return OrderedSet([w for w in self._to_dict[v]])
    
    def get_all_successors(self, v):
        '''
        Get all successors of v
        '''
        old_v = v

        # Perform a breadth first search
        successors = OrderedSet([v])
        queue = deque([v])
        while len(queue) != 0:
            v = queue.pop()
            for w in self._from_dict[v]:
                if w not in successors:
                    successors.add(w)
                    queue.appendleft(w)
        
        # Remove the source vertex from the list and return
        successors.remove(old_v)
        return successors

    def get_all_predecessors(self, v):
        '''
        Get all predecessors of v
        '''
        old_v = v

        # Perform a breadth first search
        predecessors = OrderedSet([v])
        queue = deque([v])
        while len(queue) != 0:
            v = queue.pop()
            for w in self._to_dict[v]:
                if w not in predecessors:
                    predecessors.add(w)
                    queue.appendleft(w)
        
        # Remove the source vertex from the list and return
        predecessors.remove(old_v)
        return predecessors

    def serialize(self):
        return self._from_dict
    
    def deserialize(obj):
        graph = DirectedGraph()
        for v in obj.keys():
            graph.add_vertex(v)
        for v, ws in obj.items():
            for w in ws:
                graph.add_edge(v, w)
        return graph

    def __str__(self):
        '''
        Print a simplified representation of the directed graph
        '''
        s = '{'
        if len(self._from_dict) != 0:
            for v in self._from_dict:
                s += '{}: '.format(v) + '{'
                if len(self._from_dict[v]) != 0:
                    for w in self._from_dict[v]:
                        s += '{}, '.format(w)
                    s = s[:-2]
                s += '},\n '
            s = s[:-3]
        s += '}'
        return s

if __name__ == '__main__':
    g = DirectedGraph()
    g.add_vertex('A')
    g.add_vertex('B')
    g.add_vertex('C')
    g.add_vertex('D')
    g.add_vertex('E')
    g.add_vertex('F')
    g.add_vertex('G')
    g.add_vertex('H')
    g.add_edge('A', 'E')
    g.add_edge('B', 'A')
    g.add_edge('C', 'B')
    g.add_edge('C', 'D')
    g.add_edge('D', 'C')
    g.add_edge('E', 'B')
    g.add_edge('F', 'B')
    g.add_edge('F', 'E')
    g.add_edge('F', 'G')
    g.add_edge('G', 'C')
    g.add_edge('G', 'F')
    g.add_edge('H', 'D')
    g.add_edge('H', 'G')
    g.add_edge('H', 'H')

    g1 = DirectedGraph()
    g1.add_vertex('A')
    g1.add_vertex('B')
    g1.add_vertex('C')
    g1.add_vertex('D')
    g1.add_edge('A', 'B')
    g1.add_edge('B', 'C')
    g1.add_edge('C', 'D')
    g1.add_edge('D', 'B')
    g1.add_edge('D', 'C')