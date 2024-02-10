import socket
import struct

import orjson
import minecraft_data


class MCProcotol:
    def __init__(
        self, address: str = "0.0.0.0", port: int = 25565, version="1.16.5"
    ) -> None:
        self.address = address
        self.port = port
        self.mcd = minecraft_data(version)
        self.maxPlayers = 20
        self.motd = "A Minecraft Server"

    async def __pack_variant(self, d: int) -> bytes:
        b = b""
        while True:
            byte = d & 0x7F
            d >>= 7
            b += struct.pack("B", byte | (0x80 if d > 0 else 0))

            if d == 0:
                break
        return b

    async def __unpack_varint_socket(self, sock: socket.socket) -> int:
        data = 0
        for i in range(5):
            o = sock.recv(1)

            if len(o) == 0:
                break

            byte = ord(o)
            data |= (byte & 0x7F) << 7 * i

            if not byte & 0x80:
                break

        return data

    async def __read_long_data(self, sock: socket.socket, size: int) -> bytearray:
        data = bytearray()

        while len(data) < size:
            data += bytearray(sock.recv(size - len(data)))

        return data

    async def __status(self, sock: socket.socket):
        status = {
            "version": {"name": self.mcd.version, "protocol": self.mcd.protocol},
            "players": {"max": self.maxPlayers, "online": 0},
            "description": {"text": self.motd},
        }
        await self.send(sock, status)

    async def handle_client(self, sock: socket.socket, addr: str):
        packet_len = await self.__unpack_varint_socket(sock)
        data = await self.__read_long_data(sock, packet_len)

        if data[-1] == 1:
            await self.__status(sock)
        elif data[-1] == 2:
            await self.login(sock)

    async def send(self, sock: socket.socket, json_data: dict):
        response = orjson.dumps(json_data)
        response = await self.__pack_variant(len(response)) + response
        response = await self.__pack_variant(0x00) + response
        response = await self.__pack_variant(len(response)) + response

        sock.send(response)

    async def login(self, sock: socket.socket):
        login = {"text": "Hello, world!"}
        await self.send(sock, login)

    async def start(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setblocking(False)
        self.server.bind((self.address, self.port))
        self.server.listen()
        try:
            while True:
                try:
                    sock, addr = self.server.accept()
                except Exception as e:
                    if e.args[0] == 10035:
                        continue
                await self.handle_client(sock, addr)
        except KeyboardInterrupt:
            pass
        finally:
            self.server.close()
