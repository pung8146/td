import ctypes
import json
import platform
import os


class Tdlib:
    def __init__(self, lib_path):
        self.tdjson = ctypes.CDLL(lib_path)

        self.tdjson.td_json_client_create.restype = ctypes.c_void_p
        self.client = self.tdjson.td_json_client_create()

        self.tdjson.td_json_client_send.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.tdjson.td_json_client_receive.argtypes = [ctypes.c_void_p, ctypes.c_double]
        self.tdjson.td_json_client_receive.restype = ctypes.c_char_p
        self.tdjson.td_json_client_execute.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        self.tdjson.td_json_client_execute.restype = ctypes.c_char_p
        self.tdjson.td_json_client_destroy.argtypes = [ctypes.c_void_p]

    def send(self, query):
        self.tdjson.td_json_client_send(self.client, json.dumps(query).encode('utf-8'))

    def receive(self):
        result = self.tdjson.td_json_client_receive(self.client, 1.0)
        if result:
            return json.loads(result.decode('utf-8'))
        return None

    def execute(self, query):
        result = self.tdjson.td_json_client_execute(self.client, json.dumps(query).encode('utf-8'))
        if result:
            return json.loads(result.decode('utf-8'))
        return None

    def destroy(self):
        self.tdjson.td_json_client_destroy(self.client)


def create():
    system = platform.system()
    if system == "Darwin":
        lib_path = os.path.abspath("example/python/libtdjson.dylib")
    elif system == "Linux":
        lib_path = os.path.abspath("example/python/libtdjson.so")
    else:
        raise RuntimeError("Unsupported OS")

    return Tdlib(lib_path)
