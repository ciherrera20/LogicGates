from gates.utils.graph import DirectedGraph
from gates.utils.serialize import ProgramEncoder
from gates.builtins import Nand, Reshaper, Sink, Source, Datetime, Constant
from gates.gate_definition import GateDefinition
import json

class Project:
    BUILTIN_GATES = ['NAND', 'Reshaper', 'Constant', 'Datetime', 'Source', 'Sink']

    def __init__(self, name):
        self.name = name
        self._definitions = {
            'NAND': Nand,
            'Reshaper': Reshaper,
            'Constant': Constant,
            'Datetime': Datetime,
            'Source': Source,
            'Sink': Sink
        }
        self._dependency_graph = DirectedGraph()
        for name in self._definitions.keys():
            self._dependency_graph.add_vertex(name)
    
    def get_gate_names(self):
        return self._definitions.keys()

    def define(self, name, input_dims=[], output_dims=[], input_labels=None, output_labels=None):
        if name in self._definitions:
            raise ValueError('{} already exists'.format(name))
        self._dependency_graph.add_vertex(name)
        definition = GateDefinition(input_dims, output_dims, name, self, input_labels=input_labels, output_labels=output_labels)
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
    
    def _get_dependencies(self, definition):
        return [self._definitions[successor] for successor in self._dependency_graph.get_direct_successors(definition._name)]
    
    def _get_dependees(self, definition):
        return [self._definitions[predecessor] for predecessor in self._dependency_graph.get_direct_predecessors(definition._name)]

    def _run_on_dependees(self, definition, proc, acc=[]):
        '''
        Run the function proc on all dependees of the given definition
        '''
        for dependee in self._get_dependees(definition):
            proc(dependee, acc + [definition])
            self._run_on_dependees(dependee, proc, acc + [definition])

    def _inserted_input(self, definition, idx):
        for dependee in self._get_dependees(definition):
            dependee._inserted_input(definition, idx)

    def _inserted_output(self, definition, idx):
        def helper(definition, acc):
            definition._inserted_output(acc, idx)
        self._run_on_dependees(definition, helper)

    def _removed_input(self, definition, idx):
        for dependee in self._get_dependees(definition):
            dependee._removed_input(definition, idx)

    def _removed_output(self, definition, idx):
        def helper(definition, acc):
            definition._removed_output(acc, idx)
        self._run_on_dependees(definition, helper)
    
    def _remove_uid(self, definition, uid):
        def helper(definition, acc):
            definition._remove_uid(acc, uid)
        self._run_on_dependees(definition, helper)

    def repair_instances(self, definition):
        def helper(definition, acc):
            definition._repair_instances(acc)
        self._run_on_dependees(definition, helper)

    def __getitem__(self, *args, **kwargs):
        return self._definitions.__getitem__(*args, **kwargs)

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

    def deserialize(obj, gates={}):
        project = Project(obj['name'])
        dependency_graph = DirectedGraph.deserialize(obj['dependency_graph'])
        order = dependency_graph.get_order('NAND')[0]
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