import unittest

from expression import Expression
from expression_set import ExpressionSet
import matplotlib.pyplot as plt


class MyTestCase(unittest.TestCase):
    def test_something(self):
        s = ExpressionSet()
        s.append(Expression("Some A's are B's"))
        s.append(Expression("Some B's are C's"))
        s.parse_premises()
        s.display_diagram()
        ret = s.evaluate(Expression("Some A's are C's"), show=True)
        plt.show()
        self.assertEqual(ret, False)


if __name__ == '__main__':
    unittest.main()
