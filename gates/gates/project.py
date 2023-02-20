from gates.utils.graph import DirectedGraph
from gates.utils.serialize import ProgramEncoder
from gates.builtins import Nand, Reshaper, Sink, Source
from gates.gate_definition import GateDefinition
import json

class Project:
    BUILTIN_GATES = ['NAND', 'Source', 'Sink', 'Reshaper']

    def __init__(self, name):
        self.name = name
        self._definitions = {
            'NAND': Nand,
            'Source': Source,
            'Sink': Sink,
            'Reshaper': Reshaper
        }
        self._dependency_graph = DirectedGraph()
        for name in self._definitions.keys():
            self._dependency_graph.add_vertex(name)
    
    def get_gate_names(self):
        return self._definitions.keys()

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
            raise ValueError('{} does not exist'.format(name))
        elif name in Project.BUILTIN_GATES:
            raise ValueError('Cannot delete {}'.format(name))
        else:
            predecessors = self._dependency_graph.get_direct_predecessors(name)
            if len(predecessors) != 0:
                if not force:
                    raise Warning('Other definitions depend on {}'.format(name))

            # Remove all instances of the deleted definition from the definitions that depended on it
            for predecessor in predecessors:
                self._definitions[predecessor].remove_gate_type(name)
            del self._definitions[name]
            self._dependency_graph.remove_vertex(name)
    
    def rename_definition(self, name, new_name):
        '''
        Rename a definition
        '''
        if name not in self._definitions:
            raise ValueError('{} does not exist'.format(name))
        elif name in Project.BUILTIN_GATES:
            raise ValueError('Cannot rename {}'.format(name))
        elif new_name in self._definitions:
            raise ValueError('{} already exists'.format(new_name))
        else:
            definition = self._definitions[name]

            # Replace the old name with the new one in the definitions that depend on it
            predecessors = self._dependency_graph.get_direct_predecessors(name)
            for predecessor in predecessors:
                pred_definition = self._definitions[predecessor]

                # Replace the name of each gate
                for gate_uid in pred_definition._gate_types[name]:
                    pred_definition._gates[gate_uid]._name = new_name

                # Replace the name used by the predecessor definition
                pred_definition._gate_types[new_name] = pred_definition._gate_types[name]
                del pred_definition._gate_types[name]
            self._definitions[new_name] = self._definitions[name]
            del self._definitions[name]

            # This is the disgusting part where we have to replace the vertex in the dependency graph with a new one with the new name
            successors = self._dependency_graph.get_direct_successors(name)
            self._dependency_graph.add_vertex(new_name)
            for predecessor in predecessors:
                self._dependency_graph.add_edge(predecessor, new_name)
            for successor in successors:
                self._dependency_graph.add_edge(new_name, successor)
            self._dependency_graph.remove_vertex(name)

            # Finally, set the definition's name to the new name
            definition._name = new_name

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
            'name': self.name,
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
    
    def save(self, dir):
        with open(dir, 'w') as f:
            json.dump(self.serialize(), f, cls=ProgramEncoder, indent=4)
    
    def load(dir):
        with open(dir, 'r') as f:
            return Project.deserialize(json.load(f))