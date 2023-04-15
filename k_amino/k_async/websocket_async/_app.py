import inspect
import selectors
import sys
import threading
import time
import traceback
import asyncio

from . import _logging
from ._abnf import ABNF
from ._url import parse_url
from ._core import WebSocket, getdefaulttimeout
from ._exceptions import *

"""
_app.py
websocket - WebSocket client library for Python

Copyright 2022 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

__all__ = ["WebSocketApp"]

RECONNECT = 0


def setReconnect(reconnectInterval):
    global RECONNECT
    RECONNECT = reconnectInterval


class DispatcherBase:
    """
    DispatcherBase
    """
    def __init__(self, app, ping_timeout):
        self.app = app
        self.ping_timeout = ping_timeout

    async def timeout(self, seconds, callback):
        await asyncio.sleep(seconds)
        await callback()

    async def reconnect(self, seconds, reconnector):
        try:
            _logging.info("reconnect() - retrying in %s seconds [%s frames in stack]" % (seconds, len(inspect.stack())))
            await asyncio.sleep(seconds)
            await reconnector(reconnecting=True)
        except KeyboardInterrupt as e:
            _logging.info("User exited %s" % (e,))


class Dispatcher(DispatcherBase):
    """
    Dispatcher
    """
    async def read(self, sock, read_callback, check_callback):
        while self.app.keep_running:
            sel = selectors.DefaultSelector()
            sel.register(self.app.sock.sock, selectors.EVENT_READ)

            r = sel.select(self.ping_timeout)
            if r:
                if not await read_callback():
                    break
            check_callback()
            sel.close()


class SSLDispatcher(DispatcherBase):
    """
    SSLDispatcher
    """
    async def read(self, sock, read_callback, check_callback):
        while self.app.keep_running:
            r = self.select()
            if r:
                if not await read_callback():
                    break
            check_callback()

    def select(self):
        sock = self.app.sock.sock
        if sock.pending():
            return [sock,]

        sel = selectors.DefaultSelector()
        sel.register(sock, selectors.EVENT_READ)

        r = sel.select(self.ping_timeout)
        sel.close()

        if len(r) > 0:
            return r[0][0]


class WrappedDispatcher:
    """
    WrappedDispatcher
    """
    def __init__(self, app, ping_timeout, dispatcher):
        self.app = app
        self.ping_timeout = ping_timeout
        self.dispatcher = dispatcher
        dispatcher.signal(2, dispatcher.abort)  # keyboard interrupt

    async def read(self, sock, read_callback, check_callback):
        await self.dispatcher.read(sock, read_callback)
        self.ping_timeout and self.timeout(self.ping_timeout, check_callback)

    async def timeout(self, seconds, callback):
        await self.dispatcher.timeout(seconds, callback)

    async def reconnect(self, seconds, reconnector):
        await self.timeout(seconds, reconnector)


class WebSocketApp:
    """
    Higher level of APIs are provided. The interface is like JavaScript WebSocket object.
    """

    def __init__(self, url, header=None,
                 on_open=None, on_message=None, on_error=None,
                 on_close=None, on_ping=None, on_pong=None,
                 on_cont_message=None,
                 keep_running=True, get_mask_key=None, cookie=None,
                 subprotocols=None,
                 on_data=None,
                 socket=None):
        """
        WebSocketApp initialization

        Parameters
        ----------
        url: str
            Websocket url.
        header: list or dict
            Custom header for websocket handshake.
        on_open: function
            Callback object which is called at opening websocket.
            on_open has one argument.
            The 1st argument is this class object.
        on_message: function
            Callback object which is called when received data.
            on_message has 2 arguments.
            The 1st argument is this class object.
            The 2nd argument is utf-8 data received from the server.
        on_error: function
            Callback object which is called when we get error.
            on_error has 2 arguments.
            The 1st argument is this class object.
            The 2nd argument is exception object.
        on_close: function
            Callback object which is called when connection is closed.
            on_close has 3 arguments.
            The 1st argument is this class object.
            The 2nd argument is close_status_code.
            The 3rd argument is close_msg.
        on_cont_message: function
            Callback object which is called when a continuation
            frame is received.
            on_cont_message has 3 arguments.
            The 1st argument is this class object.
            The 2nd argument is utf-8 string which we get from the server.
            The 3rd argument is continue flag. if 0, the data continue
            to next frame data
        on_data: function
            Callback object which is called when a message received.
            This is called before on_message or on_cont_message,
            and then on_message or on_cont_message is called.
            on_data has 4 argument.
            The 1st argument is this class object.
            The 2nd argument is utf-8 string which we get from the server.
            The 3rd argument is data type. ABNF.OPCODE_TEXT or ABNF.OPCODE_BINARY will be came.
            The 4th argument is continue flag. If 0, the data continue
        keep_running: bool
            This parameter is obsolete and ignored.
        get_mask_key: function
            A callable function to get new mask keys, see the
            WebSocket.set_mask_key's docstring for more information.
        cookie: str
            Cookie value.
        subprotocols: list
            List of available sub protocols. Default is None.
        socket: socket
            Pre-initialized stream socket.
        """
        self.url = url
        self.header = header if header is not None else []
        self.cookie = cookie

        self.on_open = on_open
        self.on_message = on_message
        self.on_data = on_data
        self.on_error = on_error
        self.on_close = on_close
        self.on_ping = on_ping
        self.on_pong = on_pong
        self.on_cont_message = on_cont_message
        self.keep_running = False
        self.get_mask_key = get_mask_key
        self.sock = None
        self.last_ping_tm = 0
        self.last_pong_tm = 0
        self.ping_thread = None
        self.stop_ping = None
        self.ping_interval = 0
        self.ping_timeout = None
        self.ping_payload = ""
        self.subprotocols = subprotocols
        self.prepared_socket = socket
        self.has_errored = False

    async def send(self, data, opcode=ABNF.OPCODE_TEXT):
        """
        send message

        Parameters
        ----------
        data: str
            Message to send. If you set opcode to OPCODE_TEXT,
            data must be utf-8 string or unicode.
        opcode: int
            Operation code of data. Default is OPCODE_TEXT.
        """

        if not self.sock or await self.sock.send(data, opcode) == 0:
            raise WebSocketConnectionClosedException(
                "Connection is already closed.")

    async def close(self, **kwargs):
        """
        Close websocket connection.
        """
        self.keep_running = False
        if self.sock:
            await self.sock.close(**kwargs)
            self.sock = None

    def _start_async_ping_thread(self):
        self.last_ping_tm = self.last_pong_tm = 0
        self.stop_ping = threading.Event()

        self.ping_loop = asyncio.new_event_loop()

        self.ping_thread = threading.Thread(target=self.ping_loop.run_forever)
        self.ping_thread.daemon = True
        self.ping_thread.start()

    def _stop_ping_thread(self):
        self.ping_loop.call_soon_threadsafe(self.ping_loop.stop)

        if self.stop_ping:
            self.stop_ping.set()

        if self.ping_thread and self.ping_thread.is_alive():
            self.ping_thread.join(3)

        self.last_ping_tm = self.last_pong_tm = 0

    def submit_async(self, awaitable):
        return asyncio.run_coroutine_threadsafe(awaitable, self.ping_loop)

    def _start_ping_thread(self):
        self._start_async_ping_thread()
        self.submit_async(self._send_ping())

    async def _send_ping(self):
        if self.stop_ping.wait(self.ping_interval):
            return

        while not self.stop_ping.wait(self.ping_interval):
            if self.sock:
                self.last_ping_tm = time.time()
                try:
                    _logging.debug("Sending ping")
                    await self.sock.ping(self.ping_payload)
                except Exception as ex:
                    _logging.debug("Failed to send ping: %s", ex)

        self._stop_ping_thread()

    async def run_forever(self, sockopt=None, sslopt=None,
                    ping_interval=0, ping_timeout=None,
                    ping_payload="",
                    http_proxy_host=None, http_proxy_port=None,
                    http_no_proxy=None, http_proxy_auth=None,
                    http_proxy_timeout=None,
                    skip_utf8_validation=False,
                    host=None, origin=None, dispatcher=None,
                    suppress_origin=False, proxy_type=None, reconnect=None,
                    do_reconnect=True):
        """
        Run event loop for WebSocket framework.

        This loop is an infinite loop and is alive while websocket is available.

        Parameters
        ----------
        sockopt: tuple
            Values for socket.setsockopt.
            sockopt must be tuple
            and each element is argument of sock.setsockopt.
        sslopt: dict
            Optional dict object for ssl socket option.
        ping_interval: int or float
            Automatically send "ping" command
            every specified period (in seconds).
            If set to 0, no ping is sent periodically.
        ping_timeout: int or float
            Timeout (in seconds) if the pong message is not received.
        ping_payload: str
            Payload message to send with each ping.
        http_proxy_host: str
            HTTP proxy host name.
        http_proxy_port: int or str
            HTTP proxy port. If not set, set to 80.
        http_no_proxy: list
            Whitelisted host names that don't use the proxy.
        http_proxy_timeout: int or float
            HTTP proxy timeout, default is 60 sec as per python-socks.
        http_proxy_auth: tuple
            HTTP proxy auth information. tuple of username and password. Default is None.
        skip_utf8_validation: bool
            skip utf8 validation.
        host: str
            update host header.
        origin: str
            update origin header.
        dispatcher: Dispatcher object
            customize reading data from socket.
        suppress_origin: bool
            suppress outputting origin header.
        proxy_type: str
            type of proxy from: http, socks4, socks4a, socks5, socks5h
        reconnect: int
            delay interval when reconnecting

        Returns
        -------
        teardown: bool
            False if the `WebSocketApp` is closed or caught KeyboardInterrupt,
            True if any other exception was raised during a loop.
        """

        if reconnect is None:
            reconnect = RECONNECT

        if ping_timeout is not None and ping_timeout <= 0:
            raise WebSocketException("Ensure ping_timeout > 0")

        if ping_interval is not None and ping_interval < 0:
            raise WebSocketException("Ensure ping_interval >= 0")

        if ping_timeout and ping_interval and ping_interval <= ping_timeout:
            raise WebSocketException("Ensure ping_interval > ping_timeout")

        if not sockopt:
            sockopt = []

        if not sslopt:
            sslopt = {}

        if self.sock:
            raise WebSocketException("socket is already opened")

        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.ping_payload = ping_payload
        self.keep_running = True

        async def teardown(close_frame=None):
            """
            Tears down the connection.

            Parameters
            ----------
            close_frame: ABNF frame
                If close_frame is set, the on_close handler is invoked
                with the statusCode and reason from the provided frame.
            """

            self._stop_ping_thread()
            self.keep_running = False

            if self.sock:
                await self.sock.close()

            close_status_code, close_reason = self._get_close_args(
                close_frame if close_frame else None)

            self.sock = None

            # Finally call the callback AFTER all teardown is complete
            await self._callback(self.on_close, close_status_code, close_reason)

        async def setSock(reconnecting=False):
            if reconnecting and self.sock:
                await self.sock.shutdown()

            self.sock = WebSocket(
                self.get_mask_key, sockopt=sockopt, sslopt=sslopt,
                fire_cont_frame=self.on_cont_message is not None,
                skip_utf8_validation=skip_utf8_validation,
                enable_multithread=True)

            self.sock.settimeout(getdefaulttimeout())
            try:
                await self.sock.connect(
                    self.url, header=self.header, cookie=self.cookie,
                    http_proxy_host=http_proxy_host,
                    http_proxy_port=http_proxy_port, http_no_proxy=http_no_proxy,
                    http_proxy_auth=http_proxy_auth, http_proxy_timeout=http_proxy_timeout,
                    subprotocols=self.subprotocols,
                    host=host, origin=origin, suppress_origin=suppress_origin,
                    proxy_type=proxy_type, socket=self.prepared_socket)

                _logging.info("Websocket connected")

                if self.ping_interval:
                    self._start_ping_thread()

                await self._callback(self.on_open)
                await dispatcher.read(self.sock.sock, read, check)

            except (WebSocketConnectionClosedException, ConnectionRefusedError, KeyboardInterrupt, SystemExit, Exception) as e:
                await handleDisconnect(e, reconnecting)

        async def read():
            if not self.keep_running:
                return await teardown()
            try:
                op_code, frame = await self.sock.recv_data_frame(True)
            except (WebSocketConnectionClosedException, KeyboardInterrupt) as e:
                if custom_dispatcher:
                    return await handleDisconnect(e)
                else:
                    raise e
            if op_code == ABNF.OPCODE_CLOSE:
                return await teardown(frame)

            elif op_code == ABNF.OPCODE_PING:
                await self._callback(self.on_ping, frame.data)

            elif op_code == ABNF.OPCODE_PONG:
                self.last_pong_tm = time.time()
                await self._callback(self.on_pong, frame.data)

            elif op_code == ABNF.OPCODE_CONT and self.on_cont_message:
                await self._callback(self.on_data, frame.data,
                    frame.opcode, frame.fin)
                await self._callback(self.on_cont_message,
                    frame.data, frame.fin)

            else:
                data = frame.data
                if op_code == ABNF.OPCODE_TEXT and not skip_utf8_validation:
                    data = data.decode("utf-8")

                await self._callback(self.on_data, data, frame.opcode, True)
                await self._callback(self.on_message, data)

            return True

        def check():
            if (self.ping_timeout):
                has_timeout_expired = time.time() - self.last_ping_tm > self.ping_timeout
                has_pong_not_arrived_after_last_ping = self.last_pong_tm - self.last_ping_tm < 0
                has_pong_arrived_too_late = self.last_pong_tm - self.last_ping_tm > self.ping_timeout

                if (self.last_ping_tm and
                        has_timeout_expired and
                        (has_pong_not_arrived_after_last_ping or has_pong_arrived_too_late)):
                    raise WebSocketTimeoutException("ping/pong timed out")
            return True

        async def handleDisconnect(e, reconnecting=False):
            self.has_errored = True
            self._stop_ping_thread()

            if not reconnecting:
                await self._callback(self.on_error, e)
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                await teardown()
                # Propagate further
                raise
            if reconnect or True:
                _logging.info("%s - reconnect" % e)
                if custom_dispatcher:
                    _logging.debug("Calling custom dispatcher reconnect [%s frames in stack]" % len(inspect.stack()))
                    await dispatcher.reconnect(reconnect, setSock)
            else:
                _logging.error("%s - goodbye" % e)
                # print("WEBSOCKET", type(e), e)
                await teardown()

        custom_dispatcher = bool(dispatcher)
        dispatcher = self.create_dispatcher(ping_timeout, dispatcher, parse_url(self.url)[3])

        await setSock(do_reconnect)

        if not custom_dispatcher and reconnect:
            while self.keep_running:
                _logging.debug("Calling dispatcher reconnect [%s frames in stack]" % len(inspect.stack()))
                await dispatcher.reconnect(reconnect, setSock)

        return self.has_errored

    def create_dispatcher(self, ping_timeout, dispatcher=None, is_ssl=False):
        if dispatcher:  # If custom dispatcher is set, use WrappedDispatcher
            return WrappedDispatcher(self, ping_timeout, dispatcher)
        timeout = ping_timeout or 10
        if is_ssl:
            return SSLDispatcher(self, timeout)

        return Dispatcher(self, timeout)

    def _get_close_args(self, close_frame):
        """
        _get_close_args extracts the close code and reason from the close body
        if it exists (RFC6455 says WebSocket Connection Close Code is optional)
        """
        # Need to catch the case where close_frame is None
        # Otherwise the following if statement causes an error
        if not self.on_close or not close_frame:
            return [None, None]

        # Extract close frame status code
        if close_frame.data and len(close_frame.data) >= 2:
            close_status_code = 256 * close_frame.data[0] + close_frame.data[1]
            reason = close_frame.data[2:].decode('utf-8')
            return [close_status_code, reason]
        else:
            # Most likely reached this because len(close_frame_data.data) < 2
            return [None, None]

    async def _callback(self, callback, *args):
        none = type(None)
        if isinstance(callback, none):
            return

        if callback and callable(callback):
            try:
                await callback(self, *args)

            except Exception as e:
                _logging.error("error from callback {}: {}".format(callback, e))
                # print(type(e), e, callback)
                if self.on_error:
                    await self.on_error(self, [e, callback.__name__])
