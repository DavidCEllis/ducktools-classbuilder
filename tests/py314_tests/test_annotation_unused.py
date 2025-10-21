# Test that in 3.14 under ignore_annotations that annotations are not evaluated
from ducktools.classbuilder.prefab import prefab, Prefab, attribute


class FailureIfEvaluated:
    def __init__(self):
        self.evaluation_attempted = False

    def __getattr__(self, name):
        self.evaluation_attempted = True
        return None


def test_evaluated():
    dont_eval = FailureIfEvaluated()

    # Test evaluated if normally used
    @prefab
    class Example:
        a: dont_eval.trigger = attribute(default=42)  # type: ignore

    assert dont_eval.evaluation_attempted == True

    dont_eval == FailureIfEvaluated()

    class Example(Prefab):
        a: dont_eval.trigger = attribute(default=42)  # type: ignore

    assert dont_eval.evaluation_attempted == True


def test_not_evaluated():
    dont_eval = FailureIfEvaluated()

    # Test not evaluated if ignore_annotations=True
    @prefab(ignore_annotations=True)
    class Example:
        a: dont_eval.trigger = attribute(default=42)  # type: ignore

    assert dont_eval.evaluation_attempted == False

    dont_eval = FailureIfEvaluated()

    assert Example().a == 42


    class Example(Prefab, ignore_annotations=True):
        a: dont_eval.trigger = attribute(default=42)  # type: ignore

    assert dont_eval.evaluation_attempted == False

    assert Example().a ==  42