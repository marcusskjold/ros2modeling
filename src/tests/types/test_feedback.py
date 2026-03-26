from roserer.types import Feedback

def test_feedback_add() -> None:
    f1 = Feedback()
    f1.errors.append("A")
    f1.warnings.append("C")
    f2 = Feedback()
    f2.errors.append("B")
    f2.warnings.append("D")
    f3 = f1 + f2
    assert f3.errors == ["A", "B"]
    assert f3.warnings == ["C", "D"]
