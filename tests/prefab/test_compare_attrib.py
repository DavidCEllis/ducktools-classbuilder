from ducktools.classbuilder.prefab import prefab, attribute


def test_compare_false():
    @prefab
    class CompareClass:
        x = attribute()
        y = attribute(compare=False)

    ex1 = CompareClass(1, 1)
    ex2 = CompareClass(1, 1)
    ex3 = CompareClass(1, 2)
    ex4 = CompareClass(2, 2)

    assert ex1 == ex2
    assert ex1 == ex3
    assert ex1 != ex4
