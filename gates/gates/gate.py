from abc import ABC, abstractmethod

class Gate(ABC):
    DEFAULT_VALUE = 0
    _num_gates = 0

    def __init__(self, input_dims, output_dims, input_labels=None, output_labels=None, name=None):
        self._input_dims = input_dims
        self._output_dims = output_dims

        # Default input labels to empty strings
        if input_labels is None:
            input_labels = ['',] * len(input_dims)
        self._input_labels = input_labels

        # Default output labels to empty strings
        if output_labels is None:
            output_labels = ['',] * len(output_dims)
        self._output_labels = output_labels

        self._name = name

        # Assign a unique ID to each gate
        self._uid = Gate._num_gates
        Gate._num_gates += 1

    def _init_inputs(self):
        '''
        Return an initial input for the gate
        '''
        inputs = []
        for input_dim in self._input_dims:
            if input_dim == 1:
                inputs.append(Gate.DEFAULT_VALUE)
            else:
                inputs.append([Gate.DEFAULT_VALUE] * input_dim)
        return inputs

    def _init_state(self):
        '''
        Return an initial state for the gate
        '''
        return None

    @abstractmethod
    def __call__(self, inputs, state=None):
        '''
        Implement whatever computation the gate performs using the inputs and its state
        '''
        pass

    def serialize(self):
        return None

    def serialize_state(self, state):
        '''
        Serialize the gate's state
        '''
        return state

    def deserialize_state(obj):
        '''
        Deserialize the gate's state
        '''
        return obj
    
    @abstractmethod
    def deserialize(obj):
        '''
        Deserialize the gate
        '''
        pass

    @abstractmethod
    def _duplicate(self):
        '''
        Create a duplicate of the gate
        '''
        pass
    
    @abstractmethod
    def _duplicate_state(self, state):
        '''
        Create a duplicate of the gate's state
        '''
        return self.deserialize_state(self.serialize_state(state))

    @property
    def name(self):
        return self._name
    
    @property
    def uid(self):
        return self._uid

    @property
    def input_dims(self):
        return tuple(self._input_dims)

    @property
    def output_dims(self):
        return tuple(self._output_dims)

    @property
    def input_labels(self):
        return tuple(self._input_labels)

    @property
    def output_labels(self):
        return tuple(self._output_labels)

    def __repr__(self):
        name = self._name
        if name is None:
            name = 'Gate'
        return '<{}({}, {}) at {}>'.format(name, self._input_dims, self._output_dims, hex(id(self)))
    
    def __str__(self):
        name = self._name
        if name is None:
            name = 'Gate'
        s = ''
        inputs = self._init_inputs()
        if len(self._input_dims) > 0:
            str_inputs = []
            for dim, input in zip(self._input_dims, inputs):
                if dim == 1:
                    str_inputs.append(str(input))
                else:
                    str_inputs.append(''.join([str(i) for i in input]))
            s += '{} \u2192 '.format(', '.join(str_inputs))
        s += name
        if len(self._output_dims) > 0:
            outputs = self(inputs, self._init_state())
            str_outputs = []
            for dim, output in zip(self._output_dims, outputs):
                if dim == 1:
                    str_outputs.append(str(output))
                else:
                    str_outputs.append(''.join([str(i) for i in output]))
            s += ' \u2192 {}'.format(', '.join(str_outputs))
        return s