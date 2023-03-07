from gates.gate import Gate

class Nand(Gate):
    def __init__(self):
        super().__init__((1, 1), (1,), name='NAND')

    def __call__(self, inputs, state=None):
        if type(inputs[0]) != int or type(inputs[0]) != int:
            return [None]
        else:
            return [int(not (inputs[0] and inputs[1]))]

    def deserialize(obj):
        return Nand()

    def _duplicate(self):
        return Nand()

    def _duplicate_state(self, state):
        return None