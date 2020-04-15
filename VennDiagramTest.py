import unittest

from expression import Expression
from expression_set import ExpressionSet
import matplotlib.pyplot as plt

TRUE = (True, True)
MAYBE_TRUE = (True, False)
FALSE = (False, True)
MAYBE_FALSE = (False, False)


class VennDiagramTestCase(unittest.TestCase):
    def simple_test(self, premises, exp, expected, show=False):
        s = ExpressionSet()
        s.premises(premises)
        s.parse_premises()
        if show:
            s.display_diagram()
        ret = s.evaluate(Expression(exp), show=show)
        if show:
            plt.show()
        self.assertEqual((ret[0], ret[1]), expected)

    def test_some_some(self):
        premises = """Some A's are B's\n
                      Some B's are C's"""
        exp = "Some A's are C's"
        self.simple_test(premises, exp, MAYBE_TRUE)

    def test_all_all(self):
        premises = """All A's are B's\n
                      All B's are C's"""
        exp = "All A's are C's"
        self.simple_test(premises, exp, TRUE)

    def test_all_some(self):
        premises = """All A's are B's\n
                      All B's are C's"""
        exp = "Some A's are C's"
        self.simple_test(premises, exp, MAYBE_TRUE)


if __name__ == '__main__':
    unittest.main()
