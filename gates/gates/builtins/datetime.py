from gates.gate import Gate
import time

class Datetime(Gate):
    def __init__(self):
        super().__init__((), (64,), name='Datetime')

    def __call__(self, inputs, state=None):
        timestamp = [int(bit) for bit in bin(int(time.time()))[2:]]
        pad = [0]*(64 - len(timestamp))
        return [pad + timestamp]
    
    def deserialize(obj):
        return Datetime()
    
    def _duplicate(self):
        return Datetime()

    def _duplicate_state(self, state):
        return None