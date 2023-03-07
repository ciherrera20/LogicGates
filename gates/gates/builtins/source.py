from gates.gate import Gate
import copy

class Source(Gate):
    def __init__(self, dims, labels=None):
        super().__init__([], dims, output_labels=labels, name='Source')
    
    def _init_state(self):
        state = []
        for output_dim in self._output_dims:
            if output_dim == 1:
                state.append(Gate.DEFAULT_VALUE)
            else:
                state.append([Gate.DEFAULT_VALUE] * output_dim)
        return state

    def __call__(self, inputs, state=None):
        return state

    def serialize(self):
        return {'dims': self._output_dims, 'labels': self._output_labels}

    def deserialize(obj):
        return Source(**obj)

    def _duplicate(self):
        return Source(
            copy.deepcopy(self._input_dims),
            labels=copy.deepcopy(self._input_labels)
        )

    def _duplicate_state(self, state):
        return None

    @property
    def dims(self):
        return self._output_dims
    
    @property
    def labels(self):
        return self._output_labels