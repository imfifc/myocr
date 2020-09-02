from contextlib import contextmanager

from ocr_structuring.core.utils.node_item import NodeItem
from .config import variables

_CURRENT_CONTEXT_STACK = []


def get_debug_context() -> "DebugContext":
    assert len(
        _CURRENT_CONTEXT_STACK
    ), "get_debug_context has to be called inside a 'with EventStorage(...)' context!"
    return _CURRENT_CONTEXT_STACK[-1]


class DebugContext:
    def __init__(self):
        self._prefixes = []
        # self._current_prefix = ""

    def __enter__(self):
        _CURRENT_CONTEXT_STACK.append(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert _CURRENT_CONTEXT_STACK[-1] == self
        _CURRENT_CONTEXT_STACK.pop()

    @property
    def _current_prefix(self):
        return "/".join(self._prefixes)

    @contextmanager
    def name_scope(self, name):
        """
        Yields:
            A context within which all the events added to this storage
            will be prefixed by the name scope.
        """
        self._prefixes.append(name)
        yield
        self._prefixes.pop(-1)

    def add_nodes(self, name, node_items: [NodeItem], desc=""):
        if len(node_items) == 0:
            return

        variables.add_nodes(
            f"{self._current_prefix}/{name}",
            f"{self._current_prefix}/{name}",
            node_items,
            desc,
        )
