from gates.gate import Gate

class Reshaper(Gate):
    def __init__(self, input_dims, output_dims, input_labels=None, output_labels=None):
        if sum(input_dims) != sum(output_dims):
            raise ValueError('Mismatched input and output dimensions')
        super().__init__(input_dims, output_dims, input_labels, output_labels, name='Reshaper')

    def __call__(self, inputs, state=None):
        flattened_inputs = []
        for i, input in enumerate(inputs):
            if self._input_dims[i] == 1:
                flattened_inputs.append(input)
            else:
                flattened_inputs += input

        i = 0
        outputs = []
        for output_dim in self._output_dims:
            if output_dim == 1:
                outputs.append(flattened_inputs[i])
            else:
                outputs.append(flattened_inputs[i:i+output_dim])
            i += output_dim
        
        return outputs

    def serialize(self):
        return {
            'input_dims': self._input_dims,
            'output_dims': self._output_dims,
            'input_labels': self._input_labels,
            'output_labels': self._output_labels
        }
    
    def deserialize(obj):
        return Reshaper(**obj)
    
    def _duplicate(self):
        return Reshaper(
            self._input_dims,
            self._output_dims,
            input_labels=self._input_labels,
            output_labels=self._output_labels
        )

    def _duplicate_state(self, state):
        return None