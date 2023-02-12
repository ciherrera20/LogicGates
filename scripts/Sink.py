from Gate import Gate

class Sink(Gate):
    def __init__(self, size):
        super().__init__(size, 0, name='Sink')
    
    def _init_state(self):
        return [Gate.DEFAULT_VALUE] * self._num_inputs

    def __call__(self, inputs, state=None):
        for i, input in enumerate(inputs):
            state[i] = input
        return None
    
    def serialize(self):
        return {'size': self._num_inputs}

    def deserialize(obj):
        return Sink(**obj)