"""conftest.py for mission_graph tests.

Injects a minimal sys.modules stub for langchain_core.messages.utils before
any test module imports langgraph. This is required because langchain_core 1.4.0
ships without messages/utils.py, but langgraph 1.2.0's graph/message.py imports
AnyMessage, MessageLikeRepresentation, convert_to_messages, and
message_chunk_to_message from that module via the lazy __getattr__ mechanism.

This conftest runs at collection time (before any test file is imported), so
the stub is in place when mission_graph.py calls `from langgraph.graph import ...`.
"""
from __future__ import annotations
import sys
import types


def _inject_langchain_messages_utils_stub() -> None:
    """Register a minimal stub for langchain_core.messages.utils if missing."""
    stub_name = "langchain_core.messages.utils"
    if stub_name in sys.modules:
        return  # already injected or the real module exists

    stub = types.ModuleType(stub_name)
    stub.AnyMessage = object
    stub.MessageLikeRepresentation = object
    stub.convert_to_messages = lambda x, **kw: x if isinstance(x, list) else list(x)
    stub.message_chunk_to_message = lambda x: x
    stub.convert_to_openai_messages = lambda x, **kw: []
    stub.filter_messages = lambda x, **kw: x if isinstance(x, list) else []
    stub.get_buffer_string = lambda x, **kw: ""
    stub.merge_message_runs = lambda x, **kw: x if isinstance(x, list) else []
    stub.messages_from_dict = lambda x: []
    stub.trim_messages = lambda x, **kw: x if isinstance(x, list) else []
    stub._message_from_dict = lambda x: x
    sys.modules[stub_name] = stub


# Run at import time so it's ready before any test module is collected.
_inject_langchain_messages_utils_stub()
