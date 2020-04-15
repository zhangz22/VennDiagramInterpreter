import unittest

from expression import Expression
from expression_set import ExpressionSet
import matplotlib.pyplot as plt

TRUE = (True, True)
MAYBE_TRUE = (True, False)
FALSE = (False, True)
MAYBE_FALSE = (False, False)


class VennDiagramTestCase(unittest.TestCase):
    SHOW_BY_DEFAULT = True

    def simple_test(self, premises, exp, expected, show=SHOW_BY_DEFAULT):
        s = ExpressionSet()
        s.add_premises(premises)
        s.parse_premises()
        if show:
            s.display_diagram()
        ret = s.evaluate(Expression(exp), show=show)
        if show:
            plt.show()
        self.assertEqual((ret[0], ret[1]), expected)

    def test_some_some(self):
        # If I want to know a SOME argument there must be an X in my covered area
        premises = """Some A's are B's\n
                      Some B's are C's"""
        exp = "Some A's are C's"
        self.simple_test(premises, exp, MAYBE_TRUE)

    def test_all_all(self):
        premises = """All A's are B's\n
                      All B's are C's"""
        exp = "All A's are C's"
        self.simple_test(premises, exp, TRUE, show=False)

    def test_all_all_not(self):
        premises = """All A's are B's\n
                      All B's are C's"""
        exp = "All A's are not C's"
        self.simple_test(premises, exp, FALSE, show=False)

    def test_all_all_not_2(self):
        premises = """All A's are B's\n
                      All B's are C's"""
        exp = "All C's are not A's"
        self.simple_test(premises, exp, MAYBE_TRUE, show=False)

    def test_all_some(self):
        premises = """All A's are B's\n
                      All B's are C's"""
        exp = "Some A's are C's"
        self.simple_test(premises, exp, MAYBE_TRUE)

    def test_all_some_some(self):
        premises = """All A's are B's\n
                      Some C's are A's"""
        exp = "Some C's are B's"
        self.simple_test(premises, exp, TRUE, show=True)

    def test_cross(self):
        premises = """All B's are A's\n
                      Some C's are B's"""
        exp = "Some C's are A's"
        self.simple_test(premises, exp, TRUE, show=True)

    def test_cross2(self):
        premises = """All A's are C's\n
                      Some A's are B's"""
        exp = "Some C's are A's"
        self.simple_test(premises, exp, TRUE, show=True)

    def test_double_cross(self):
        premises = """All A's are B's\n
                      Some B's are C's\n
                      Some A's are C's"""
        exp = "Some A's are C's"
        self.simple_test(premises, exp, TRUE, show=True)

    def test_premises_conflict(self):
        premises = """All B's are not A's\n
                      Some B's are A's\n
                      Some B's are C's\n
                      Some C's are A's\n
                      Some C's are not B's\n
                      Some A's are C's"""
        exp = "Some A's are C's"
        try:
            self.simple_test(premises, exp, TRUE, show=True)
        except ValueError as e:
            self.assertEqual(str(e),
                             "Error: conflicts happens between [\"Some B's are A's\"]"
                             " and [\"All B's are not A's\"]", "Error message")


if __name__ == '__main__':
    unittest.main()
