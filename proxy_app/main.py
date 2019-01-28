import ssl
import signal
import asyncio

from aiohttp import web, WSMsgType

from converter import Converter


class Vars:
    Converter = None


class UDPEndpointProtocol:
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        Vars.Converter.process_udp_message(data.decode())

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        print("Connection closed")

    async def send(self, message):
        print('Sending:\n' + message + '\n')
        self.transport.sendto(message.encode())


async def udp_client():
    _loop = asyncio.get_event_loop()

    transport, protocol = await _loop.create_datagram_endpoint(
        lambda: UDPEndpointProtocol(),
        remote_addr=('127.0.0.1', 9999))
    Vars.Converter.add_udp_endpoint(transport, protocol)


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            Vars.Converter.process_ws_message(msg.data, ws)

        elif msg.type == WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())
    print('websocket connection closed')
    return ws


async def run_apps(_app):
    _app.add_routes([web.get('/', websocket_handler, ),
                     web.static('/static', './static', show_index=True)])

    runner = web.AppRunner(_app)
    await runner.setup()

    ws_endpoint = web.TCPSite(runner, 'localhost', 8080)
    await ws_endpoint.start()

    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain('./ssl/localhost.crt', './ssl/localhost.key')
    wss_endpoint = web.TCPSite(runner, 'localhost', 8443, ssl_context=context)
    await wss_endpoint.start()


def main():
    Vars.Converter = Converter()

    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, loop.stop)

    loop.create_task(udp_client())

    app = web.Application()
    loop.create_task(run_apps(app))

    loop.run_forever()


if __name__ == '__main__':
    main()

