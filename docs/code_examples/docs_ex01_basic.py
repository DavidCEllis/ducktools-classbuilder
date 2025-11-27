from ducktools.classbuilder.prefab import Prefab, attribute

class Slotted(Prefab):
    the_answer: int = 42
    the_question: str = attribute(
        default="What do you get if you multiply six by nine?",
        doc="Life the universe and everything",
    )

ex = Slotted()
print(ex)
print(ex.__slots__)
help(Slotted)
