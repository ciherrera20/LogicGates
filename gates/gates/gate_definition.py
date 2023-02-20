from gates.gate import Gate
from gates.builtins import Sink, Source
from gates.utils import DirectedGraph, hybridmethod
from collections import deque

class CompoundGate(Gate):
    def __init__(self, definition):
        self._definition = definition
        super().__init__(definition._num_inputs, definition._num_outputs, name=definition._name)

    def _init_state(self):
        return self._definition._init_state()
    
    def __call__(self, inputs, state=None):
        return self._definition._process_state(inputs, state=state)

    def serialize_state(self, state):
        return self._definition.serialize_state(state)
    
    def deserialize(obj):
        return 

class GateDefinition:
    '''
    Represents the definition for a custom gate. Instances of custom gates are of type CompoundGate.
    '''
    _num_definitions = 0

    def __init__(self, num_inputs, num_outputs, name, project):
        self._num_inputs = num_inputs
        self._num_outputs = num_outputs
        self._name = name
        self._project = project

        # Maintain the internal connections between gates
        self._graph = DirectedGraph()  # Gates (specifically their uids) are vertices and any connections are edges
        self._gates = {}               # Indexed by the gate's uid. Stores the gate objects
        self._gate_types = {}          # Indexed by a string (the gate type). Stores a set of ints (the uids)
        self._connections = {}         # Indexed by a pair of uids (from, to). Stores a set of output index, input index tuples

        # Maintain the definition's state
        self._state = {}

        # Represents the input (source) and output (sink) to the overall gate
        self._source = Source(num_inputs)
        self._sink = Sink(num_outputs)
        self.add_gate(self._source)
        self.add_gate(self._sink)

        # The order to evaluate the internal gates in
        self._order = None      # A list of gate uids representing the evaluation order
        self._cut_gates = None  # A set of gate uids corresponding to gates whose outputs should be saved
        self._reorder = True    # Flag set whenever the graph representing the definition's internal structure changes
        # TODO: look into refactoring the directed graph code to update the order instead of recomputing it

    def add_gate(self, gate):
        '''
        Add a gate to the definition
        '''
        if gate._uid in self._gates:
            raise ValueError('{} is already in the definition'.format(gate))
        
        # Update dependency graph if necessary
        if gate._name not in self._gate_types:
            if self._project._check_dependency(self._name, gate._name):
                raise ValueError('Recursive definition: {} depends on {}'.format(gate._name, self._name))
            self._project._add_dependency(self._name, gate._name)
            self._gate_types[gate._name] = {gate._uid}
        else:
            self._gate_types[gate._name].add(gate._uid)

        # Add gate
        self._graph.add_vertex(gate._uid)
        self._gates[gate._uid] = gate

        # Update definition's state
        if gate == self._source:
            self._state['inputs'] = gate._init_state()
        elif gate == self._sink:
            self._state['outputs'] = gate._init_state()
        else:
            gate_state = gate._init_state()
            # if gate_state is not None:
            self._state[gate._uid] = (gate_state, gate(gate._init_inputs(), gate_state))
    
    def remove_gate(self, gate):
        '''
        Remove a gate and all its connections from a definition
        '''
        if gate._uid not in self._gates:
            raise ValueError('{} is not in the definition'.format(gate))

        # Update dependency graph if necessary
        self._gate_types[gate._name].discard(gate._uid)
        if len(self._gate_types[gate._name]) == 0:
            del self._gate_types[gate._name]
            self._project._remove_dependency(self._name, gate._name)

        # Remove from connections
        for predecessor in self._graph.get_direct_predecessors(gate._uid):
            self._reorder = True  # Edge has been deleted
            del self._connections[predecessor, gate._uid]

        # Remove to connections
        for successor in self._graph.get_direct_successors(gate._uid):
            self._reorder = True  # Edge has been deleted
            
            # If the gate had a connection to itself then we can't delete it again
            if (gate._uid, successor) in self._connections:
                del self._connections[gate._uid, successor]
        
        # Remove the gate from the graph
        self._graph.remove_vertex(gate._uid)
        del self._gates[gate._uid]

        # Update definition's state
        if gate._uid in self._state:
            del self._state[gate._uid]

    def remove_gate_type(self, name):
        gate_uids = list(self._gate_types[name])
        for gate_uid in gate_uids:
            self.remove_gate(self._gates[gate_uid])

    def _validate_from_pair(self, from_pair):
        from_gate, output_idx = from_pair
        if from_gate._uid not in self._gates:
            raise ValueError('{} is not in the definition'.format(from_gate))
        if output_idx >= from_gate._num_outputs:
            raise ValueError('Invalid output index {} for {}'.format(output_idx, from_gate))
    
    def _validate_to_pair(self, to_pair):
        input_idx, to_gate = to_pair
        if to_gate._uid not in self._gates:
            raise ValueError('{} is not in the definition'.format(to_gate))
        if input_idx >= to_gate._num_inputs:
            raise ValueError('Invalid input index {} for {}'.format(input_idx, to_gate))

    def add_connection(self, from_pair, to_pair):
        '''
        Add a connection from a gate to a gate if it does not already exist
        params:
            from_pair   Tuple containing the gate providing a singal and its output index
            to_pair     Tuple containing an input index for the gate accepting a signal
        '''
        self._validate_from_pair(from_pair)
        self._validate_to_pair(to_pair)

        # Unpack input pairs
        from_gate, output_idx = from_pair
        input_idx, to_gate = to_pair

        # If a connection between the two gates does not yet exist, create it
        key = (from_gate._uid, to_gate._uid)
        if key not in self._connections:
            self._reorder = True  # Edge has been created
            self._graph.add_edge(*key)
            self._connections[key] = set()

        # Add the output index and input index to the connection
        self._connections[key].add((output_idx, input_idx))

    def remove_connection(self, from_pair, to_pair):
        '''
        Remove a connection from a gate to a gate if it does not already exist
        params:
            from_pair   Tuple containing the gate providing a singal and its output index
            to_pair     Tuple containing an input index for the gate accepting a signal
        '''
        self._validate_from_pair(from_pair)
        self._validate_to_pair(to_pair)

        # Unpack input pairs
        from_gate, output_idx = from_pair
        input_idx, to_gate = to_pair

        # Remove the output index and input index from the connection
        key = (from_gate._uid, to_gate._uid)
        self._connections[key].discard((output_idx, input_idx))

        # If the connection between the two gates no longer connects any outputs to inputs, delete it
        if len(self._connections[key]) == 0:
            self._reorder = True  # Edge has been deleted
            del self._connections[key]
            self._graph.remove_edge(*key)
    
    def clear_gate_input(self, to_pair):
        '''
        params:
            to_pair     Tuple containing an input index for the gate accepting a signal
        '''
        self._validate_to_pair(to_pair)

        to_idx, to_gate = to_pair
        for predecessor in self._graph.get_direct_predecessors(to_gate._uid):
            key = predecessor, to_gate._uid

            # Remove connections using the output specified
            for output_idx, input_idx in self._connections[key]:
                if input_idx == to_idx:
                    self._connections[key].discard((output_idx, input_idx))
            
            # If the connection between the two gates no longer connects any outputs to inputs, delete it
            if len(self._connections[key]) == 0:
                self._reorder = True  # Edge has been deleted
                del self._connections[key]

    def clear_gate_output(self, from_pair):
        '''
        Remove all connections from a gate's outputs
        params:
            from_pair   Tuple containing the gate providing a singal and its output index
        '''
        self._validate_from_pair(from_pair)

        from_gate, from_idx = from_pair
        for successor in self._graph.get_direct_successors(from_gate._uid):
            key = from_gate._uid, successor

            # Remove connections using the input specified
            for output_idx, input_idx in self._connections[key]:
                if output_idx == from_idx:
                    self._connections[key].discard((output_idx, input_idx))
            
            # If the connection between the two gates no longer connects any outputs to inputs, delete it
            if len(self._connections[key]) == 0:
                self._reorder = True  # Edge has been deleted
                del self._connections[key]

    def tie_input_to(self, source_idx, to_pair):
        '''
        Tie one of the definition's inputs to a gate's input
        params:
            source_idx  The definition's input index
            to_pair     Tuple containing an input index for the gate accepting a signal
        '''
        self.add_connection((self._source, source_idx), to_pair)
    
    def remove_input_to(self, source_idx, to_pair):
        '''
        Remove the connection from one of the definition's inputs to a gate's input
        params:
            source_idx  The definition's input index
            to_pair     Tuple containing an input index for the gate accepting a signal
        '''
        self.remove_connection((self._source, source_idx), to_pair)
    
    def clear_input(self, sink_idx):
        '''
        Remove all connections from one of the definition's inputs
        '''
        self.clear_gate_output((self._sink, sink_idx))

    def tie_output_to(self, from_pair, sink_idx):
        '''
        Tie a gate's output to one of the definition's outputs
        params:
            from_pair   Tuple containing the gate providing a singal and its output index
            sink_idx    The definition's output index
        '''
        self.add_connection(from_pair, (sink_idx, self._sink))

    def remove_output_to(self, from_pair, sink_idx):
        '''
        Remove the connection from a gate's output to one of the definition's outputs
        params:
            from_pair   Tuple containing the gate providing a singal and its output index
            sink_idx    The definition's output index
        '''
        self.remove_connection(from_pair, (sink_idx, self._sink))

    def clear_output(self, source_idx):
        '''
        Remove all connections from one of the definition's outputs
        '''
        self.clear_gate_input((source_idx, self._source))

    def insert_input(self, idx):
        '''
        Insert a new input for the definition at idx
        All inputs greater than or equal to idx are shifted over by one
        '''
        if idx > self._num_inputs:
            raise ValueError('Invalid insertion index: {}'.format(idx))

        # Create new source gate
        new_source = Source(self._num_inputs + 1)
        self.add_gate(new_source)

        # Move all connections from old source gate to the new one
        for successor_uid in self._graph.get_direct_successors(self._source._uid):
            successor = self._gates[successor_uid]
            for output_idx, input_idx in self._connections[self._source._uid, successor_uid]:
                if output_idx >= idx:
                    output_idx += 1
                self.add_connection((new_source, output_idx), (input_idx, successor))

        # Replace old source with the new source
        self.remove_gate(self._source)
        self._source = new_source
        self._num_inputs += 1
    
        # Update definition's state
        self._inputs.insert(idx, Gate.DEFAULT_VALUE)

    def insert_output(self, idx):
        '''
        Insert a new output for the definition at idx
        All outputs greater than or equal to idx are shifted over by one
        '''
        if idx > self._num_outputs:
            raise ValueError('Invalid insertion index: {}'.format(idx))

        # Create new sink gate
        new_sink = Sink(self._num_outputs + 1)
        self.add_gate(new_sink)

        # Move all connections from old sink gate to the new one
        for predecessor_uid in self._graph.get_direct_predecessors(self._sink._uid):
            predecessor = self._gates[predecessor_uid]
            for output_idx, input_idx in self._connections[predecessor_uid, self._sink._uid]:
                if input_idx >= idx:
                    input_idx += 1
                self.add_connection((predecessor, output_idx), (input_idx, new_sink))
        self.remove_gate(self._sink)
        
        # Replace the old sink with the new sink
        self._sink = new_sink
        self._num_outputs += 1

        # Update defintion's state
        self._outputs.insert(idx, Gate.DEFAULT_VALUE)
    
    def append_input(self):
        '''
        Add a new input to the definition at the end of the current inputs
        '''
        self.insert_input(self._num_inputs)
    
    def append_output(self):
        '''
        Add a new output to the definition at the end of the current outputs
        '''
        self.insert_output(self._num_outputs)

    def swap_inputs(self, idx0, idx1):
        '''
        Swap two of the definition's inputs
        '''
        if idx0 >= self._num_inputs:
            raise ValueError('First given swap index is invalid: {}'.format(idx0))
        if idx1 >= self._num_inputs:
            raise ValueError('Second given swap index is invalid: {}'.format(idx1))
        
        # Swap connections from idx0 to idx1 and vice versa
        for successor_uid in self._graph.get_direct_successors(self._source._uid):
            key = (self._source._uid, successor_uid)
            new_connections = set()
            for output_idx, input_idx in self._connections[key]:
                if output_idx == idx0:
                    output_idx = idx1
                elif output_idx == idx1:
                    output_idx = idx0
                new_connections.add((output_idx, input_idx))
            self._connections[key] = new_connections
        
        # Update definition's state
        input0, input1 = self._state['inputs'][idx0], self._state['inputs'][idx1]
        self._state['inputs'][idx0], self._state['inputs'][idx1] = input1, input0
    
    def swap_outputs(self, idx0, idx1):
        '''
        Swap two of the definition's outputs
        '''
        if idx0 >= self._num_outputs:
            raise ValueError('First given swap index is invalid: {}'.format(idx0))
        if idx1 >= self._num_outputs:
            raise ValueError('Second given swap index is invalid: {}'.format(idx1))

        # Swap connections from idx0 to idx1 and vice versa
        for predecessor_uid in self._graph.get_direct_predecessors(self._sink._uid):
            key = (predecessor_uid, self._source._uid)
            new_connections = set()
            for output_idx, input_idx in self._connections[key]:
                if input_idx == idx0:
                    input_idx = idx1
                elif input_idx == idx1:
                    input_idx = idx0
                new_connections.add((output_idx, input_idx))
            self._connections[key] = new_connections
        
        # Update definition's state
        output0, output1 = self._state['outputs'][idx0], self._state['outputs'][idx1]
        self._state['outputs'][idx0], self._state['outputs'][idx1] = output1, output0

    def remove_input(self, idx):
        '''
        Remove one of the definition's inputs
        '''
        if idx >= self._num_inputs:
            raise ValueError('Input index is invalid: {}'.format(idx))

        # Create new source gate
        new_source = Source(self._num_inputs - 1)
        self.add_gate(new_source)

        # Move all connections from old source gate to the new one
        for successor_uid in self._graph.get_direct_successors(self._source._uid):
            successor = self._gates[successor_uid]
            for output_idx, input_idx in self._connections[self._source._uid, successor_uid]:
                if output_idx > idx:
                    output_idx -= 1
                elif output_idx == idx:
                    continue
                self.add_connection((new_source, output_idx), (input_idx, successor))
        self.remove_gate(self._source)
        
        # Replace the old source with the new source
        self._source = new_source
        self._num_inputs -= 1

        # Update definition's state
        self._state['inputs'].remove(idx)

    def remove_output(self, idx):
        '''
        Remove one of the definition's outputs
        '''
        if idx >= self._num_outputs:
            raise ValueError('Output index is invalid: {}'.format(idx))

        # Create new sink gate
        new_sink = Sink(self._num_outputs - 1)
        self.add_gate(new_sink)

        # Move all connections from old sink gate to the new one
        for predecessor_uid in self._graph.get_direct_predecessors(self._sink._uid):
            predecessor = self._gates[predecessor_uid]
            for output_idx, input_idx in self._connections[predecessor_uid, self._sink._uid]:
                if input_idx > idx:
                    input_idx -= 1
                elif input_idx == idx:
                    continue
                self.add_connection((predecessor, output_idx), (input_idx, new_sink))
        self.remove_gate(self._sink)
        
        # Replace the old sink with the new sink
        self._sink = new_sink
        self._num_outputs -= 1

        # Update definition's state
        self._state['outputs'].remove(idx)

    def pop_input(self):
        '''
        Remove the definition's last input
        '''
        if self._num_inputs == 0:
            raise ValueError('Cannot pop an input because the number of inputs is 0')
        self.remove_input(self._num_inputs - 1)

    def pop_output(self):
        '''
        Remove the definition's last output
        '''
        if self._num_outputs == 0:
            raise ValueError('Cannot pop an input because the number of inputs is 0')
        self.remove_output(self._num_outputs - 1)

    def _init_inputs(self):
        return self._source._init_state()

    def _update_order(self):
        # Compute a new evaluation order if necessary
        if self._reorder:
            self._order, self._cut_gates = self._graph.get_order(self._source._uid)
            self._reorder = False

    def _init_state(self):
        '''
        Initialize a state
        '''
        self._update_order()

        # Store the states for each gate in the definition if needed
        state = {}
        for gate_uid, gate in self._gates.items():
            if gate_uid != self._source._uid and gate_uid != self._sink._uid:
                # We only need to store a gate's state if it is not None or if it is a cut gate
                gate_state = gate._init_state()
                if gate_state is not None or gate_uid in self._cut_gates:
                    state[gate_uid] = (gate_state, gate(gate._init_inputs(), gate_state))
        
        # Return None if this gate does not need to store a state
        if len(state) == 0:
            return None
        return state

    def _process_state(self, inputs, state=None):
        '''
        Process a given state
        '''
        self._update_order()

        # Replace None with an empty dict to make it easier to work with
        if state is None:
            state = {}

        # Evaluate each gate to compute the final output
        # outputs = None
        outputs = {self._source._uid: inputs}
        for gate_uid in self._order:
            # Skip over the rest of the code for the source since we don't need to do any computation for it
            if gate_uid == self._source._uid:
                continue

            # Retrieve the gate
            gate = self._gates[gate_uid]

            # Get the inputs to the gate from its predecessors
            gate_inputs = gate._init_inputs()
            for predecessor_uid in self._graph.get_direct_predecessors(gate_uid):
                for output_idx, input_idx in self._connections[predecessor_uid, gate_uid]:
                    if predecessor_uid in outputs:
                        gate_inputs[input_idx] = outputs[predecessor_uid][output_idx]
                    elif predecessor_uid in state:
                        gate_inputs[input_idx] = state[predecessor_uid][1][output_idx]
                    else:
                        raise ValueError('Invalid state')

            # Save outputs
            if gate_uid == self._sink._uid:
                outputs['final'] = gate_inputs
            else:
                # Update state if necessary
                if gate_uid in state:
                    gate_state = state[gate_uid][0]
                    gate_outputs = gate(gate_inputs, gate_state)
                    state[gate_uid] = (gate_state, gate_outputs)
                else:
                    gate_outputs = gate(gate_inputs)
                outputs[gate_uid] = gate_outputs
        return outputs['final']

    def tick(self):
        self._state['outputs'] = self._process_state(self._state['inputs'], self._state)

    def serialize(self):
        # Serialize gates
        gates = {}
        for uid, gate in self._gates.items():
            if gate != self._source and gate != self._sink:
                serialized_gate = gate.serialize()
                if serialized_gate is not None:
                    gates[uid] = serialized_gate
        
        # Reformat connection for serialization
        connections = {}
        for (from_uid, to_uid), pairs in self._connections.items():
            if from_uid not in connections:
                connections[from_uid] = {}
            connections[from_uid][to_uid] = pairs

        # Create serializable object
        obj = {
            'name': self._name,
            'num_inputs': self._num_inputs,
            'num_outputs': self._num_outputs,
            'source': self._source._uid,
            'sink': self._sink._uid,
            'gates': gates,
            'gate_types': self._gate_types,
            'connections': connections,
            'state': self.serialize_state(self._state)
        }
        return obj

    def serialize_state(self, state):
        if state is None:
            return None

        obj = {}
        for key, value in state.items():
            if type(key) == int:
                obj[key] = (self._gates[key].serialize_state(value[0]), value[1])
            else:
                obj[key] = value
        return obj
    
    @hybridmethod
    @staticmethod
    def deserialize_state(obj, gates, project):
        state = {
            'inputs': obj['inputs'],
            'outputs': obj['outputs']
        }
        for key, value in obj.items():
            if type(key) == int:
                gate_state, gate_outputs = value
                gate = gates[key]
                definition = project._definitions[gate._name]
                state[gate._uid] = definition.deserialize_state(gate_state), gate_outputs
        return state

    @deserialize_state.instancemethod
    def deserialize_state(self, obj):
        if obj is None:
            return None

        state = {}
        for gate_uid, (gate_state, gate_outputs) in obj.items():
            gate = self._gates[gate_uid]
            definition = self._project._definitions[gate._name]
            state[gate_uid] = definition.deserialize_state(gate_state), gate_outputs
        return state

    @hybridmethod
    @staticmethod
    def deserialize(obj, project, gates):
        '''
        Deserialize a definition
        '''
        source_uid, sink_uid = obj['source'], obj['sink']
        definition = GateDefinition(obj['num_inputs'], obj['num_outputs'], obj['name'], project)

        # Create gates
        for gate_type, uids in obj['gate_types'].items():
            for uid in uids:
                if uid == source_uid:
                    gates[uid] = definition._source
                elif uid == sink_uid:
                    gates[uid] = definition._sink
                else:
                    serialized_gate = obj['gates'].get(uid, obj['gates'].get(str(uid), None))
                    gate = project._definitions[gate_type].deserialize(serialized_gate)
                    gates[uid] = gate
                    definition.add_gate(gate)

        # Add connections
        for from_uid, value in obj['connections'].items():
            from_gate = gates[int(from_uid)]
            for to_uid, pairs in value.items():
                to_gate = gates[int(to_uid)]
                for pair in pairs:
                    output_idx, input_idx = pair
                    definition.add_connection((from_gate, output_idx), (input_idx, to_gate))
        
        # Create a new state object where old gate uids are replaced with new ones
        state = {}
        stack = deque([(obj['state'], state)])
        while len(stack) != 0:
            old_state, new_state = stack.pop()
            for key, value in old_state.items():
                if type(key) == int:
                    if type(value[0]) == dict:
                        new_value = ({}, value[1])
                        stack.append((value[0], new_value[0]))
                    else:
                        new_value = value
                    new_state[gates[key]._uid] = new_value
                else:
                    new_state[key] = value

        # Deserialize state
        definition._state = GateDefinition.deserialize_state(state, definition._gates, project)
        return definition

    @deserialize.instancemethod
    def deserialize(self, obj):
        '''
        Deserialize a gate
        '''
        return self()

    def __call__(self):
        return CompoundGate(self)
    
    def __str__(self):
        name = self._name
        if name is None:
            name = 'Gate'
        s = ''
        if self._num_inputs > 0:
            s += '{} \u2192 '.format(self._state['inputs'])
        s += '{} Definition'.format(name)
        if self._num_outputs > 0:
            s += ' \u2192 {}'.format(self._state['outputs'])
        return s