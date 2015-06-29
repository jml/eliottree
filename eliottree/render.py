from datetime import datetime

from tree_format import format_tree


DEFAULT_IGNORED_KEYS = set([
    u'action_status', u'action_type', u'task_level', u'task_uuid'])


def _format_value(value, encoding):
    """
    Format a value for a task tree.
    """
    if isinstance(value, datetime):
        return value.isoformat(' ').encode(encoding)
    elif isinstance(value, unicode):
        return value.encode(encoding)
    elif isinstance(value, str):
        # We guess bytes values are UTF-8.
        return value.decode('utf-8', 'replace').encode(encoding)
    return repr(value).decode('utf-8', 'replace').encode(encoding)


def _truncate_value(value, limit):
    """
    Truncate values longer than ``limit``.
    """
    values = value.split('\n')
    value = values[0]
    if len(value) > limit or len(values) > 1:
        return '{} [...]'.format(value[:limit])
    return value


class _Node(object):

    def __init__(self, node):
        self._node = node

    def render(self, encoding, field_limit):
        return self._node.name.encode(encoding)

    def children(self, ignored_task_keys):
        task = self._node.task
        children = []
        if task is not None:
            children.extend([
                _Field(k, v)
                for (k, v) in task.items()
                if k not in ignored_task_keys
            ])
        children.extend(map(_Node, self._node.children()))
        return children


class _Field(object):

    def __init__(self, key, value):
        self._key = key
        self._value = value

    def render(self, encoding, field_limit):
        key = self._key.encode(encoding)
        if getattr(self._value, 'items', None):
            return key

        # XXX: Doesn't handle multi-line output
        _value = _format_value(self._value, encoding)
        if field_limit:
            _value = _truncate_value(_value, field_limit)
        return '{key}: {value}'.format(
            key=key,
            value=_value,
        )

    def children(self, ignored_task_keys):
        items = getattr(self._value, 'items', None)
        if not items:
            return []
        return [
            _Field(k, v) for (k, v) in items()
            if k not in ignored_task_keys
        ]


def render_task_nodes(write, nodes, field_limit, ignored_task_keys=None,
                      encoding='utf-8'):
    """
    Render a tree of task nodes as an ``ASCII`` tree.

    :type write: ``callable`` taking a single ``bytes`` argument
    :param write: Callable to write the output.

    :type nodes: ``list`` of ``(unicode, _TaskNode)``.
    :param nodes: List of pairs of task UUID and task nodes, as obtained
        from ``Tree.nodes``.

    :type field_limit: ``int``
    :param field_limit: Length at which to begin truncating, ``0`` means no
        truncation.

    :type ignored_task_keys: ``set`` of ``unicode``
    :param ignored_task_keys: Set of task key names to ignore.

    :type encoding: ``bytes``
    :param encoding: Encoding to use when rendering.
    """
    if ignored_task_keys is None:
        ignored_task_keys = DEFAULT_IGNORED_KEYS
    for task_uuid, node in nodes:
        write(format_tree(
            _Node(node),
            format_node=lambda node: node.render(encoding, field_limit),
            get_children=lambda node: node.children(ignored_task_keys)))
        write('\n')


__all__ = ['render_task_nodes']
