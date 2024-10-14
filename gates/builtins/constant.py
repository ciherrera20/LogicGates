from gates.gate import Gate
import copy

class Constant(Gate):
    def __init__(self, dim, state=None):
        super().__init__([], [dim], name='Constant')
        if state is None:
            self._reset_state()
        else:
            self._state = state
    
    def _reset_state(self):
        state = []
        if self._output_dims[0] == 1:
            state.append(Gate.DEFAULT_VALUE)
        else:
            state.append([Gate.DEFAULT_VALUE] * self._output_dims[0])
        self._state = state

    def __call__(self, inputs, state=None):
        return self._state

    def serialize(self):
        return {'dim': self._output_dims[0], 'state': self._state}

    def deserialize(obj):
        return Constant(**obj)

    def get_state(self):
        return self._state
    
    def set_state(self, state):
        self._state = state

    def _duplicate(self):
        return Constant(
            self._output_dims[0],
            state=copy.deepcopy(self._state)
        )

    def _duplicate_state(self, state):
        return copy.deepcopy(state)

    @property
    def dims(self):
        return self._output_dims