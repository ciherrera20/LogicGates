import json
from Graph import DirectedGraph
from GateDefinition import GateDefinition
from Project import Project
from Reshaper import Reshaper
from Gate import Gate

class ProgramEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        # elif isinstance(obj, DirectedGraph):
        #     return obj._to_dict
        # elif isinstance(obj, GateDefinition):
        #     return {
        #         'name': obj._name,
        #         'gates': obj._gates,
        #         'gate_types': obj._gate_types,
        #         'connections': obj._connections
        #     }
        # elif isinstance(obj, Project):
        #     return {

        #     }
        return json.JSONEncoder.default(self, obj)

def json_program_obj_hook(dct):
    if isinstance(dct, dict):
        if '' in dct:
            return
    return dct