from ducktools.classbuilder.prefab import Prefab, Attribute, SlotFields


class TestConstructionForms:
    """
    Test the 3 different ways of constructing prefabs
    """
    def test_attributes(self):
        class Ex(Prefab):
            a = Attribute()
            b = Attribute(default=1)

        # Slotted by default
        assert "__slots__" in vars(Ex)
        assert isinstance(Ex.__slots__, dict)

        ex = Ex(1, 2)
        assert ex.a == 1
        assert ex.b == 2

    def test_annotations(self):
        class Ex(Prefab):
            a: int
            b: int = 1

        assert "__slots__" in vars(Ex)
        assert isinstance(Ex.__slots__, dict)

        ex = Ex(1, 2)
        assert ex.a == 1
        assert ex.b == 2

    def test_slots(self):
        class Ex(Prefab):
            __slots__ = SlotFields(
                a=Attribute(),
                b=1
            )

        assert "__slots__" in vars(Ex)
        assert isinstance(Ex.__slots__, dict)

        ex = Ex(1, 2)
        assert ex.a == 1
        assert ex.b == 2


class TestClassArguments:
    def test_slots(self):
        class Ex(Prefab, slots=True):
            a: int
            b: int = 1

        assert "__slots__" in vars(Ex)

        class Ex(Prefab, slots=False):
            a: int
            b: int = 1

        assert "__slots__" not in vars(Ex)
