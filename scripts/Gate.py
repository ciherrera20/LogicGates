from abc import ABC, abstractmethod

class Gate(ABC):
    DEFAULT_VALUE = 0
    _num_gates = 0

    def __init__(self, num_inputs, num_outputs, name=None):
        self._num_inputs = num_inputs
        self._num_outputs = num_outputs
        self._name = name

        # Assign a unique ID to each gate
        self._uid = Gate._num_gates
        Gate._num_gates += 1

    def _init_inputs(self):
        '''
        Return an initial input for the gate
        '''
        return [Gate.DEFAULT_VALUE] * self._num_inputs

    @abstractmethod
    def _init_state(self):
        '''
        Return an initial state for the gate
        '''
        pass

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

    def __repr__(self):
        name = self._name
        if name is None:
            name = 'Gate'
        return '<{}({}, {}) at {}>'.format(name, self._num_inputs, self._num_outputs, hex(id(self)))
    
    def __str__(self):
        name = self._name
        if name is None:
            name = 'Gate'
        s = ''
        inputs = self._init_inputs()
        if self._num_inputs > 0:
            s += '{} \u2192 '.format(inputs)
        s += name
        if self._num_outputs > 0:
            s += ' \u2192 {}'.format(self(inputs, self._init_state()))
        return s