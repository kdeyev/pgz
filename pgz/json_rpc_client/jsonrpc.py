import random
import sys
import json
import functools
import collections

import requests


class JSONRPCError(Exception):
    """Root exception for all errors related to this library"""


class TransportError(JSONRPCError):
    """An error occurred while performing a connection to the server"""

    def __init__(self, message, cause=None, server_response=None):
        self.message = message
        self.cause = cause
        self.server_response = server_response

    def __str__(self):
        return self.message


class ProtocolError(JSONRPCError):
    """An error occurred while dealing with the JSON-RPC protocol"""

    def __init__(self, message, server_data=None, server_response=None):
        self.message = message
        self.server_data = server_data  # the deserialized server data
        self.server_response = server_response

    def __str__(self):
        return self.message


class Server(object):
    """A connection to a HTTP JSON-RPC server, backed by requests"""

    def __init__(self, url, session=None, **requests_kwargs):
        self.session = session or requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json-rpc',
        })
        self.request = functools.partial(self.session.post, url, **requests_kwargs)

    def send_request(self, method_name, is_notification, params):
        """Issue the HTTP request to the server and return the method result (if not a notification)"""
        request_body = self.serialize(method_name, params, is_notification)
        try:
            response = self.request(data=request_body)
        except requests.RequestException as requests_exception:
            raise TransportError('Error calling method %r' % method_name, cause=requests_exception)

        if response.status_code != requests.codes.ok:
            raise TransportError('Got non-200 response from server, status code: %s' % response.status_code,
                                 server_response=response)

        if not is_notification:
            return self.parse_response(response)

    @staticmethod
    def parse_response(response):
        """Parse the data returned by the server according to the JSON-RPC spec. Try to be liberal in what we accept."""
        try:
            server_data = response.json()
        except ValueError as value_error:
            raise ProtocolError('Cannot deserialize response body: %s' % value_error, server_response=response)

        if not isinstance(server_data, dict):
            raise ProtocolError('Response is not a dictionary', server_response=response, server_data=server_data)

        if server_data.get('error'):
            code = server_data['error'].get('code', '')
            message = server_data['error'].get('message', '')
            raise ProtocolError('Error: %s %s' % (code, message), server_response=response, server_data=server_data)
        elif 'result' not in server_data:
            raise ProtocolError('Response without a result field', server_response=response, server_data=server_data)
        else:
            return server_data['result']

    @staticmethod
    def dumps(data):
        """Override this method to customize the serialization process (eg. datetime handling)"""
        return json.dumps(data)

    def serialize(self, method_name, params, is_notification):
        """Generate the raw JSON message to be sent to the server"""
        data = {'jsonrpc': '2.0', 'method': method_name}
        if params:
            data['params'] = params
        if not is_notification:
            # some JSON-RPC servers complain when receiving str(uuid.uuid4()). Let's pick something simpler.
            data['id'] = random.randint(1, sys.maxsize)
        return self.dumps(data)

    def __getattr__(self, method_name):
        return Method(self.__request, method_name)

    def __request(self, method_name, args=None, kwargs=None):
        """Perform the actual RPC call. If _notification=True, send a notification and don't wait for a response"""
        is_notification = kwargs.pop('_notification', False)
        if args and kwargs:
            raise ProtocolError('JSON-RPC spec forbids mixing arguments and keyword arguments')

        # from the specs:
        # "If resent, parameters for the rpc call MUST be provided as a Structured value.
        #  Either by-position through an Array or by-name through an Object."
        if len(args) == 1 and isinstance(args[0], collections.Mapping):
            args = dict(args[0])

        return self.send_request(method_name, is_notification, args or kwargs)


class Method(object):
    def __init__(self, request_method, method_name):
        if method_name.startswith("_"):  # prevent rpc-calls for private methods
            raise AttributeError("invalid attribute '%s'" % method_name)
        self.__request_method = request_method
        self.__method_name = method_name

    def __getattr__(self, method_name):
        if method_name.startswith("_"):  # prevent rpc-calls for private methods
            raise AttributeError("invalid attribute '%s'" % method_name)
        return Method(self.__request_method, "%s.%s" % (self.__method_name, method_name))

    def __call__(self, *args, **kwargs):
        return self.__request_method(self.__method_name, args, kwargs)
