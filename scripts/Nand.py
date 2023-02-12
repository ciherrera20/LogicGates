from Gate import Gate

class Nand(Gate):
    def __init__(self):
        super().__init__(2, 1, name='NAND')

    def _init_state(self):
        return None

    def __call__(self, inputs, state=None):
        if type(inputs[0]) != int or type(inputs[0]) != int:
            return [None]
        else:
            return [int(not (inputs[0] and inputs[1]))]
    
    def deserialize(obj):
        return Nand()