from gates.gate import Gate

class Source(Gate):
    def __init__(self, size):
        super().__init__(0, size, name='Source')
    
    def _init_state(self):
        return [Gate.DEFAULT_VALUE] * self._num_outputs

    def __call__(self, inputs, state=None):
        return state

    def serialize(self):
        return {'size': self._num_outputs}

    def deserialize(obj):
        return Source(**obj)