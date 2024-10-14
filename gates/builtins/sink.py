from gates.gate import Gate
import copy

class Sink(Gate):
    def __init__(self, dims, labels=None):
        super().__init__(dims, [], input_labels=labels, name='Sink')

    def _init_state(self):
        return super()._init_inputs()

    def __call__(self, inputs, state=None):
        for i, input in enumerate(inputs):
            state[i] = input
        return []
    
    def serialize(self):
        return {'dims': self._input_dims, 'labels': self._input_labels}

    def deserialize(obj):
        return Sink(**obj)
    
    def _duplicate(self):
        return Sink(
            copy.deepcopy(self._input_dims),
            labels=copy.deepcopy(self._input_labels)
        )

    def _duplicate_state(self, state):
        return copy.deepcopy(state)

    @property
    def dims(self):
        return self._input_dims

    @property
    def labels(self):
        return self._input_labels