from Gate import Gate

class Reshaper(Gate):
    def __init__(self, input_dims, output_dims):
        if sum(input_dims) != sum(output_dims):
            raise ValueError('Mismatched input and output dimensions')
        self._input_dims = input_dims
        self._output_dims = output_dims
        super().__init__(len(input_dims), len(output_dims), name='Reshaper')

    def _init_inputs(self):
        inputs = []
        for input_dim in self._input_dims:
            if input_dim == 1:
                inputs.append(Gate.DEFAULT_VALUE)
            else:
                inputs.append([Gate.DEFAULT_VALUE] * input_dim)
        return inputs

    def _init_state(self):
        return None

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
        return {'input_dims': self._input_dims, 'output_dims': self._output_dims}
    
    def deserialize(obj):
        return Reshaper(**obj)