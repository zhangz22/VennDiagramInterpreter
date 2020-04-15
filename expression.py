import re


class Token(object):
    def __init__(self, exp_list):
        """
        throw a SyntaxError if the expression is Syntax Incorrect
        :param exp_list: could be [<(some/all/not)>, <name>'s]
        """
        if not 0 < len(exp_list) <= 2:
            raise SyntaxError("Invalid expression")

        # Name of the set
        name_string = exp_list[-1]
        self.name = name_string.strip("\'s").upper()

        # Keywords
        # TODO should "not all A is B" or "not some A is B" supported?
        loc = 0
        if exp_list[loc] == "not":
            self.neg = True
            loc += 1
        else:
            self.neg = False

        if exp_list[loc] == "some":
            self.some, self.all = True, False
            # No more tokens
            if loc + 1 < len(exp_list) - 1:
                raise SyntaxError("Invalid expression with unrecognizable token \"{}\" after \"some\"".format(exp_list[loc + 1]))
        elif exp_list[loc] == "all":
            self.some, self.all = False, True
            # No more tokens
            if loc + 1 < len(exp_list) - 1:
                raise SyntaxError("Invalid expression with unrecognizable token \"{}\" after \"all\"".format(exp_list[loc + 1]))
        else:
            self.some, self.all = False, False
            if exp_list[loc] != name_string:
                raise SyntaxError("Invalid expression with unrecognizable token \"{}\"".format(exp_list[loc]))

    def __str__(self):
        ret = ""
        if self.neg:
            ret += "Not "
        if self.some:
            ret += "some " if ret != "" else "Some "
        elif self.all:
            ret += "all " if ret != "" else "All "
        return ret + self.name + "\'s"

    def __eq__(self, other):
        if other is self:
            return True
        if not isinstance(other, Token):
            return False
        return self.name == other.name and self.some == other.some and \
               self.all == other.all and self.neg == other.neg

    def __hash__(self):
        return hash((self.name, self.some, self.all, self.neg))


class Expression(object):
    def __init__(self, expression: str):
        try:
            self.symbol1, self.symbol2 = Expression.parse(expression)
        except SyntaxError as e:
            raise e
        self.to_string = expression

    @staticmethod
    def parse(exp: str):
        """
        throw a SyntaxError if the expression is Syntax Incorrect
        :param exp: the string needed to be parsed
        :return: two Token objects
        """
        exp_list = re.findall("(?:\".*?\"|\S)+", exp.lower())
        # AUX
        if "are" in exp_list:
            aux = exp_list.index("are")
        elif "is" in exp_list:
            aux = exp_list.index("is")
        else:
            raise SyntaxError("Invalid expression \"" + exp + "\": no relation found.")

        symbol1, symbol2 = Token(exp_list[0:aux]), Token(exp_list[aux+1:])
        if symbol1.neg or symbol2.all or symbol2.some:
            raise SyntaxError("Invalid expression \"" + exp + "\"")
        if symbol1.name == symbol2.name:
            raise SyntaxError("Invalid expression with identical set name \"{}\"".format(symbol1))
        return symbol1, symbol2

    def __str__(self):
        return str(self.symbol1) + "'s are " + str(self.symbol2) + "'s"

    def __contains__(self, key):
        if isinstance(key, str):
            return key == self.symbol1.name or key == self.symbol2.name
        elif isinstance(key, Token):
            return key == self.symbol1 or key == self.symbol2
        else:
            return False

    def __eq__(self, other):
        if other is self:
            return True
        if not isinstance(other, Expression):
            return False
        return self.symbol1 == other.symbol1 and self.symbol2 == other.symbol2

    def __hash__(self):
        prime = 31
        result = 1
        result = prime * result + hash(self.symbol1)
        result = prime * result + hash(self.symbol2)
        return result
