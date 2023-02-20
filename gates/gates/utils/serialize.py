import json

class ProgramEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def json_program_obj_hook(dct):
    if isinstance(dct, dict):
        if '' in dct:
            return
    return dct