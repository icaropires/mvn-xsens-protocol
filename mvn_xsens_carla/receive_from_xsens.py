#!/usr/bin/env python3.6

import socket
import struct
from collections import namedtuple

UDP_IP = "0.0.0.0"
UDP_PORT = 8000
CHUNK_SIZE = 1500  # MTU

MsgType = namedtuple('MsgType', 'name code fmt size')

# (segment id, x, y, z, rotation x, rotation y, rotation z)
poseEuler = MsgType('poseEuler', '01', '>Iffffff', 28)

msg_types = {
   poseEuler.code: poseEuler
}

for _, msg_type in msg_types.items():
    assert struct.calcsize(msg_type.fmt) == msg_type.size


class Header:
    '''(id string, sample counter, datagram counter, nº items, time code, char id, future use)'''

    fmt = '>6sIBBIB7x'
    size = 24

    def __init__(self, data):
        assert struct.calcsize(self.fmt) == self.size

        (self.id, self.sample_counter, self.datagram_counter,
         self.n_items, self.time_code, self.char_id, *_) = struct.unpack(self.fmt, data)

        self.msg_type_code = self.id[-2:].decode()

    def _is_last_datagram(self):
        return bool(self.datagram_counter & 2**7)  # First bit of byte


def get_msg(sock):
    chunk, _ = sock.recvfrom(CHUNK_SIZE)

    pos = Header.size
    header = Header(chunk[0:pos])

    items = []
    for _ in range(header.n_items):
        try:
            msg_type = msg_types[header.msg_type_code]
        except KeyError:
            raise NotImplementedError(
                f"Message type '{header.msg_type_code}' not implemented yet!"
            )

        data = chunk[pos:pos+msg_type.size]
        item = struct.unpack(msg_type.fmt, data)

        pos += msg_type.size
        items.append(item)

    return [header] + items


def get_ready_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    return sock


def write_records_to_file():
    sock = get_ready_socket()

    with open('positions.csv', 'w') as f:
        f.write('segment_id,x,y,z,rotation_x,rotation_y,rotation_z\n')

        while True:
            header, *items = get_msg(sock)

            if header.msg_type_code == poseEuler.code:
                f.write(
                    '\n'.join(
                        ','.join(map(str, item)) for item in items
                    ) + '\n'
                )

                print(f'Recorded {len(items)} items!')


def get_data():
    sock = get_ready_socket()

    while True:
        data = get_msg(sock)

        if not data:
            raise StopIteration()

        yield data


if __name__ == '__main__':
    write_records_to_file()
