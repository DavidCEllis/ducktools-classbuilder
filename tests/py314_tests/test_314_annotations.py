from annotationlib import Format

from ducktools.classbuilder.annotations.annotations_314 import _call_annotate_forwardrefs


from unittest.mock import MagicMock, call


def test_user_annotate_called_with_forwardref():
    def annotate(format, /):
        if format == Format.VALUE_WITH_FAKE_GLOBALS:
            raise NotImplementedError(format)
        return {}

    annotate_mock = MagicMock(wraps=annotate)

    _call_annotate_forwardrefs(annotate_mock)

    first_call = call(Format.VALUE_WITH_FAKE_GLOBALS)
    second_call = call(Format.FORWARDREF)

    annotate_mock.assert_has_calls([first_call, second_call])
