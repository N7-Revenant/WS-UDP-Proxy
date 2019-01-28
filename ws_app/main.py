import random
import asyncio
import websockets


class Message:
    def __init__(self, mes_str=None):
        self.__mes_parts = dict()
        if mes_str:
            self.parse(mes_str)

    def assemble_request(self, client_id, message_id, text):
        self.__mes_parts = {
            'Type': 'Request',
            'Mod': 'WS_mark',
            'Client-ID': client_id,
            'Message-ID': message_id,
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


async def receiver(websocket):
    while True:
        raw_mes = await websocket.recv()
        print('Received:')
        print(f"{raw_mes}\n")

        mes = Message(raw_mes)
        if mes.get('Type') == 'Request':
            if mes.get('Mod') == 'WS_mark':
                await websocket.send(mes.assemble_response(' received'))
            else:
                print('Message has wrong mark in "Mod" field! Ignoring...')


async def hello():
    count = 300
    id = str(random.randint(10000, 99999))
    loop = asyncio.get_event_loop()
    async with websockets.connect('ws://localhost:8080') as websocket:
        task = loop.create_task(receiver(websocket))
        for i in range(count):
            mes = Message()
            print('Sending:')
            print(mes.assemble_request(id, str(i), 'Text'))
            await websocket.send(mes.assemble_request(id, str(i), 'Text'))
            await asyncio.sleep(1)
        task.cancel()

asyncio.get_event_loop().run_until_complete(hello())