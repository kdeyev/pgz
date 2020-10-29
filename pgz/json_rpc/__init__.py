# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import

from asyncio import AbstractEventLoop, ensure_future
from uuid import uuid4
from functools import wraps
from operator import methodcaller
from typing import (
    Dict,
    List,
    Union,
    Optional,
    Any,
)

from .variants import JSON_RPC_VERSION, ErrorCode, Success, AsyncResultsResolver
from ._error import create_error_response, code_to_response, as_failed


class Evaluator:
    """ TODO: split async evaluation """

    def __init__(self, rpc_stack: Dict, loop: Optional[AbstractEventLoop]):
        self._rpc_stack = rpc_stack
        self._loop = loop

    def _call(self, id, name, params: Union[List, Dict]) -> Dict:
        """
        JSON-RPC supports positional arguments and named arguments.
        """
        from inspect import signature

        if name not in self._rpc_stack:
            return as_failed(id, ErrorCode.METHOD_NOT_FOUND)

        function = self._rpc_stack[name]
        parameter_spec = signature(function).parameters

        result = None
        if isinstance(params, List):
            if len(params) != len(parameter_spec):
                return as_failed(id, ErrorCode.INVALID_PARAMS)

            result = function(*params)

        elif isinstance(params, Dict):
            if set(params.keys()) != set(parameter_spec.keys()):
                return as_failed(id, ErrorCode.INVALID_PARAMS)

            result = function(**params)

        else:
            return as_failed(id, ErrorCode.INVALID_REQUEST)

        return Success(id, result)

    def _eval(self, jsonrpc, method, id=None, params=None):
        if params is None:
            params = []

        try:
            return self._call(id, method, params)
        except Exception as e:
            return as_failed(id, ErrorCode.UNEXPECTED_ERROR, str(e))

    def do(self, request):
        if isinstance(request, Dict):
            result = self._eval(**request)
            return result.to_response()

        if isinstance(request, List):
            results = (self._eval(**r) for r in request)
            responses = map(methodcaller("to_response"), results)
            return [r for r in responses if r]

        assert False, f"Invalid request {request}"


class AsyncEvaluator(Evaluator):
    def do(self, request):
        if isinstance(request, Dict):
            result = self._eval(**request)
            return result.resolve_async(self._loop).to_response()

        if isinstance(request, List):
            results = AsyncResultsResolver([self._eval(**r) for r in request], self._loop)
            return results.to_response()

        assert False, f"Invalid request {request}"


class Registrator:
    """
    Decorator class instance to register functions as Remote procedure.

    In default, rpc method name will be the name of function.
    First argument would be a name of the method.

    Example:

    >>> register = Registrator()

    >>> @register
    ... def func_x(a, b, c):
    ...     pass
    ...

    >>> @register('named')
    ... def func_named(a, b, c):
    ...     pass
    ...
    """

    def __init__(self, loop=None):
        self._rpc_stack = {}
        self._loop = loop
        if loop:
            self._evaluator = AsyncEvaluator(self._rpc_stack, self._loop)
        else:
            self._evaluator = Evaluator(self._rpc_stack, self._loop)

    def _set_rpc(self, name, func):
        self._rpc_stack[name] = func
        return func

    def register(self, target):
        if isinstance(target, str):

            # call as decorator with argument
            def decorate(func):
                return self._set_rpc(target, func)

            return decorate

        else:
            # call as normal decorator
            func = target
            return self._set_rpc(func.__name__, func)

    def __call__(self, request):
        return self.register(request)

    def dispatch(self, request):
        """
        Dispatcher for rpc request.
        Receive a JSON-rpc request then returns a result.
        The request must be follows JSON-rpc protocol.  Basically a dict but it can be a list if it is batch.
        """
        return self._evaluator.do(request)
