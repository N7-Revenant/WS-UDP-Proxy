import asyncio


class Message:
    def __init__(self, mes_str=None):
        self.__mes_parts = dict()
        if mes_str:
            self.parse(mes_str)

    def assemble_message(self):
        msg = ''
        for item in self.__mes_parts.items():
            msg += '%s:%s\n' % item
        return msg

    def generate_answer(self, text):
        self.__mes_parts['Type'] = 'Answer'
        self.__mes_parts['Text'] += text
        return self.assemble_message()

    def parse(self, message):
        msg_lines = message.strip().split('\n')
        for line in msg_lines:
            parts = line.split(':', 1)
            self.__mes_parts[parts[0]] = parts[1]

    def get(self, key):
        return self.__mes_parts.get(key)

    def set(self, key, value):
        self.__mes_parts[key] = value


class Converter:
    def __init__(self, loop=asyncio.get_event_loop()):
        self.__loop = loop

        self.__udp_endpoint = None
        self.__udp_transport = None

        self.__ws_clients = dict()

    def __send_via_udp(self, mes):
        if self.__udp_endpoint:
            self.__loop.create_task(self.__udp_endpoint.send(mes))
        else:
            print('No UDP Endpoint!')

    def process_ws_message(self, msg, ws_connection):
        ws_mes = Message(msg)
        if ws_mes.get('Type') == 'Request':
            self.__ws_clients[ws_mes.get('Client-ID')] = {
                'ws_connection': ws_connection
            }
        ws_mes.set('Mod', 'UDP_mark')
        self.__send_via_udp(ws_mes.assemble_message())

    def process_udp_message(self, msg):
        print("Received:\n" + msg + '\n')
        udp_mes = Message(msg)
        client = udp_mes.get('Client-ID')
        if client in self.__ws_clients and not self.__ws_clients[client]['ws_connection'].closed:
            if self.__ws_clients[client]['ws_connection'].closed:
                print('Connection no longer active!')
            else:
                print('Active WS connection!')
                udp_mes.set('Mod', 'WS_mark')
                sender = self.__ws_clients[client]['ws_connection'].send_str
                self.__loop.create_task(sender(udp_mes.assemble_message()))
        else:
            print('Connection not found in registrations!')
            fail_mes = udp_mes.generate_answer("/can't be proxied")
            self.__loop.create_task(self.__udp_endpoint.send(fail_mes))

    def add_udp_endpoint(self, transport, protocol):
        self.__udp_transport = transport
        self.__udp_endpoint = protocol
