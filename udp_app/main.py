import random
import asyncio


class Vars:
    Transport = None
    Protocol = None


class Message:
    def __init__(self, mes_str=None):
        self.__mes_parts = dict()
        if mes_str:
            self.parse(mes_str)

    def assemble_request(self, client_id, text):
        self.__mes_parts = {
            'Type': 'Request',
            'Mod': 'UDP_mark',
            'Client-ID': client_id,
            'Message-ID': str(random.randint(100000000, 9999999999)),
            'Text': text
        }
        return self.__assemble_message()

    def assemble_response(self, text):
        self.__mes_parts['Type'] = 'Answer'
        self.__mes_parts['Text'] += text
        return self.__assemble_message()

    def __assemble_message(self):
        msg = ''
        for item in self.__mes_parts.items():
            msg += '%s:%s\n' % item
        return msg

    def parse(self, message):
        msg_lines = message.strip().split('\n')
        for line in msg_lines:
            parts = line.split(':', 1)
            self.__mes_parts[parts[0]] = parts[1]

    def get(self, key):
        return self.__mes_parts.get(key)

    def set(self, key, value):
        self.__mes_parts[key] = value


async def udp_message(message, delay, addr):
    await asyncio.sleep(delay)
    print('Send %r to %s' % (message, addr))
    Vars.Transport.sendto(message.encode(), addr)


class EchoServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode()
        print('Received %r from %s' % (message, addr))
        mes = Message(message)
        if mes.get('Type') == 'Request':
            if mes.get('Mod') == 'UDP_mark':
                result = mes.assemble_response('/answer')
                print('Send %r to %s' % (result, addr))
                self.transport.sendto(result.encode(), addr)

                rand_mes = Message()
                delay = random.randint(1, 5)
                loop.create_task(udp_message(rand_mes.assemble_request(mes.get('Client-ID'),
                                                                       'Random'), delay, addr))


async def main():
    try:
        print("Starting UDP server")
        _loop = asyncio.get_event_loop()
        Vars.Transport, Vars.Protocol = await _loop.create_datagram_endpoint(
            lambda: EchoServerProtocol(),
            local_addr=('127.0.0.1', 9999))
    except KeyboardInterrupt:
        print("Stopping UDP server")

loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
