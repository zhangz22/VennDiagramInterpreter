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
            ret += "not "
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
        prime = 31
        result = 1
        result = prime * result + hash(self.name) if self.name is not None else 0
        result = prime * result + hash(self.some) if self.some is not None else 0
        result = prime * result + hash(self.all) if self.all is not None else 0
        result = prime * result + hash(self.neg) if self.neg is not None else 0
        return result


class Expression(object):
    def __init__(self, expression: str):
        try:
            self.lhs, self.rhs = Expression.parse(expression)
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

        lhs, rhs = Token(exp_list[0:aux]), Token(exp_list[aux+1:])
        if lhs.neg or rhs.all or rhs.some:
            raise SyntaxError("Invalid expression \"" + exp + "\"")
        if lhs.name == rhs.name:
            raise SyntaxError("Invalid expression with identical set name \"{}\"".format(lhs.name))
        return lhs, rhs

    def __str__(self):
        return str(self.lhs) + " are " + str(self.rhs)

    def __contains__(self, key):
        if isinstance(key, str):
            return key == self.lhs.name or key == self.rhs.name
        elif isinstance(key, Token):
            return key == self.lhs or key == self.rhs
        else:
            return False

    def __eq__(self, other):
        if other is self:
            return True
        if not isinstance(other, Expression):
            return False
        return self.lhs == other.lhs and self.rhs == other.rhs

    def __hash__(self):
        prime = 31
        result = 1
        result = prime * result + hash(self.lhs) if self.lhs is not None else 0
        result = prime * result + hash(self.rhs) if self.lhs is not None else 0
        return result
