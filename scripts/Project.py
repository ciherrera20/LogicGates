from Graph import DirectedGraph
from Nand import Nand
from Source import Source
from Sink import Sink
from Reshaper import Reshaper
from GateDefinition import GateDefinition

class Project:
    BUILTIN_GATES = ['NAND', 'Source', 'Sink', 'Reshaper']

    def __init__(self, name):
        self._name = name
        self._definitions = {
            'NAND': Nand,
            'Source': Source,
            'Sink': Sink,
            'Reshaper': Reshaper
        }
        self._dependency_graph = DirectedGraph()
        for name in self._definitions.keys():
            self._dependency_graph.add_vertex(name)
    
    def define(self, num_inputs, num_outputs, name):
        if name in self._definitions:
            raise ValueError('{} already exists'.format(name))
        self._dependency_graph.add_vertex(name)
        definition = GateDefinition(num_inputs, num_outputs, name, self)
        self._definitions[name] = definition
        return definition

    def delete_definition(self, name, force=False):
        '''
        Attempt to delete the given definition
        '''
        if name not in self._definitions:
            raise ValueError('{} does not exit'.format(name))
        elif name in Project.BUILTIN_GATES:
            raise ValueError('Cannot delete {}'.format(name))
        else:
            predecessors = self._dependency_graph.get_direct_predecessors(name)
            if len(predecessors) != 0:
                if not force:
                    raise ValueError('Other definitions depend on {}'.format(name))
            for predecessor in predecessors:
                self._definitions[predecessor].remove_gate_type(name)
            del self._definitions[name]

    def _check_dependency(self, from_type, to_type):
        return self._dependency_graph.check_edge(from_type, to_type)
    
    def _add_dependency(self, from_type, to_type):
        self._dependency_graph.add_edge(from_type, to_type)

    def _remove_dependency(self, from_type, to_type):
        self._dependency_graph.remove_edge(from_type, to_type)
    
    def serialize(self):
        definitions = {}
        for name, definition in self._definitions.items():
            if isinstance(definition, GateDefinition):
                definitions[name] = definition.serialize()
        
        return {
            'name': name,
            'definitions': definitions,
            'dependency_graph': self._dependency_graph.serialize()
        }

    def deserialize(obj):
        project = Project(obj['name'])
        dependency_graph = DirectedGraph.deserialize(obj['dependency_graph'])
        order = dependency_graph.get_order('NAND')[0]
        gates = {}
        for gate_type in reversed(order):
            if gate_type not in project._definitions:
                project._dependency_graph.add_vertex(gate_type)
                definition = GateDefinition.deserialize(obj['definitions'][gate_type], project, gates)
                project._definitions[gate_type] = definition
        return project