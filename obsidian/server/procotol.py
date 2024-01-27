import importlib.util
import importlib
import socket
import struct

orjson_exists = importlib.util.find_spec("orjson")
result = orjson_exists is not None

if result:
    json = importlib.import_module('orjson')
else:
    json = importlib.import_module('json')

class MCProcotol:

    def __init__(self, port=25565) -> None:
        self.address = "0.0.0.0"

    async def __pack_variant(d: int) -> bytes:
        b = b''
        while True:
            byte = d & 0x7f
            d >>= 7
            b += struct.pack()