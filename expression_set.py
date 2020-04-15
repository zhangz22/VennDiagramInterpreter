from expression import Expression, Token

results = {
    "TRUE": {"validity": True, "must": True, "color": "green", "pattern": "///",
             "reason": "This is a TRUE statement. The green shadow in the "
                       "diagram shows all valid areas."},
    "MAYBE TRUE": {"validity": True, "must": False,
                   "color": "green", "pattern": "..",
                   "reason": "This statement may be TRUE but not necessarily "
                             "TRUE.\n The green shadow in the diagram shows "
                             "areas satisfies the expression but they may be "
                             "empty."},
    "NO TRUE": {"validity": False, "must": True,
                "color": "red", "pattern": "xxx",
                "reason": "This is a FALSE statement. The red shadow in the "
                          "diagram shows all areas that fits the statement, "
                          "but they are all invalid."},
    "FALSE": {"validity": False, "must": True, "color": "red", "pattern": "xxx",
              "reason": "This is a FALSE statement. The red shadow in the "
                        "diagram shows all areas that refutes the statement."},
    "MAYBE FALSE": {"validity": False, "must": False,
                    "color": "red", "pattern": "+",
                    "reason": "This statement may be FALSE but not necessarily "
                              "FALSE.\n The red shadow in the diagram shows "
                              "all areas that refutes the statement but they "
                              "may be empty."}
}


class ExpressionSet(object):
    def __init__(self):
        self.relations = set()  # A set of Expression objects
        self.members = set()  # A set of strings representing members (A,B,C...)
        # all_label is a dict of all labels in the diagram -> the patch id
        # {A,B,AB... -> "100", "010", "110"...}
        self.all_label = dict()
        # cross is a dictionary containing tuple of area labels-> list of expressions
        # that is emphasized by "Some" arguments. At least one area in each tuple
        # should be TRUE
        # {(AB,ABC) -> Some A's are B's ...}
        self.cross = dict()
        # black is a containing area labels -> list of expressions that is generated
        # by "All" arguments. None of the area in this set can be TRUE
        # {A -> All A's are B's,  AC -> All A's are B's... }
        self.black = dict()
        # The venn diagram plot
        import venn_diagram
        self.venn_diagram = venn_diagram.VennDiagramPlt(self)

    def __contains__(self, key):
        """
        :param key: item being checked. Either the name of a set or an Expression
        :return: true if the diagram contains the key
        """
        if isinstance(key, str):
            return key in self.members
        elif isinstance(key, Expression):
            return key in self.relations
        else:
            return False

    def __str__(self):
        """
        :return: str(self)
        """
        ret = ""
        for i in sorted(self.members):
            ret += str(i) + " {"
            for j in self.relations:
                if i in j:
                    ret += "<" + str(j) + ">, "
            ret += "}\n"
        return ret

    def empty(self):
        """
        :return: true if the diagram contains no sets or relations or false otherwise
        """
        return len(self.members) == 0 and len(self.relations) == 0

    def __len__(self):
        """
        :return: the number of sets
        """
        return len(self.members)

    def append(self, exp):
        """
        Add a expression (relation between sets) or a set to the diagram
        throw a SyntaxError if the expression is Syntax Incorrect
        throw a TypeError if the item being added has an incompatible type
        throw a ValueError if the diagram would contain more than three sets
        :param exp: (str): the name of a set
                    (Expression): a relation between sets
        """
        if isinstance(exp, Expression):
            self.relations.add(exp)
            self.members.add(exp.lhs.name)
            self.members.add(exp.rhs.name)
        elif isinstance(exp, str):
            self.members.add(Token(exp).name)
        else:
            raise TypeError("ERROR: Unknown type inserted.")
        if len(self.members) > 3:
            raise ValueError("ERROR: Only two or three sets can be supported but "
                             "the program got " + str(self.members))

    def premises(self, premises: str):
        """
        Parse a paragraph of premises and add expressions (relation between sets) or
        set names to the diagram
        throw a SyntaxError if the expression is Syntax Incorrect
        throw a TypeError if the item being added has an incompatible type
        throw a ValueError if the diagram would contain more than three sets
        :param premises: (str):  a paragraph contains set names or relations between
                                 sets, separated by newline character
        """
        for line in premises.split("\n"):
            line = line.strip()
            if line == "": continue
            if "are" in line or "is" in line:
                self.append(Expression(line))  # self.collection
            else:
                self.append(line)  # Expression

    # LOGIC RELATED FUNCTIONS
    def parse(self, exp: Expression):
        """
        This function evaluates the validity of a single expression and returns two
        sets containing the area labels to prove/disprove the statement
        :param exp:
        :return: support: a tuple contains all area labels that can prove the argument
                 against: a set contains all area labels that can refute the argument

        For statements:
                         | support:                       | against:
        -----------------|--------------------------------|--------------------------
                         | one of them should exist       |
         Some A is B     | (AB, ABC)                      |   {}
         Some A is not B | (A, AC)                        |   {}
                         | some or none of them may exist | none of them should exist
         All A is B      | (AB, ABC)                      | {A, AC}
         All A is not B  | (A, AC)                        | {AB, ABC}
        -----------------|--------------------------------|--------------------------
        """
        support = set()
        against = set()
        for area_label in self.all_label:
            if exp.lhs.name in area_label:
                if exp.lhs.some:
                    # Some A is B -> There must be an AB
                    # Find the areas that contains rhs (e.g. AB)
                    # The XOR operator here means if rhs is negated, find
                    # the area that does not contain rhs
                    if exp.rhs.neg ^ (exp.rhs.name in area_label):
                        # Check for AB
                        support.add(area_label)
                elif exp.lhs.all:
                    # All A is B -> There must not be an A or B (only AB, B)
                    # Find the areas that does not contain rhs (e.g. B)
                    # The == operator here means if rhs is negated, find
                    # the area that does contain rhs
                    if exp.rhs.neg ^ (exp.rhs.name not in area_label):
                        # Check for A
                        against.add(area_label)
                    elif exp.rhs.neg ^ (exp.rhs.name in area_label):
                        # Check for AB
                        support.add(area_label)
        return tuple(sorted(support)), against

    def parse_premises(self):
        """
        This function parses all pre-conditions added to this diagram and generates
        corresponding area codes (highlighted by "Some" statements and disabled by
        "Not" statements
        """
        # Create venn diagram
        labels = tuple(sorted(self.members))
        if len(labels) == 2:
            self.all_label = {labels[0]: "10",  # A (left)
                              labels[1]: "01",  # B (right)
                             labels[0] + labels[1]: "11"}  # A ∩ B
        elif len(labels) == 3:
            self.all_label = {labels[0]: '100',  # A (up-left)
                              labels[1]: '010',  # B (up-right)
                              labels[2]: '001',  # C (down)
                             labels[0] + labels[1]: '110',  # A ∩ B
                             labels[0] + labels[2]: '101',  # A ∩ C
                             labels[1] + labels[2]: '011',  # B ∩ C
                             labels[0] + labels[1] + labels[2]: '111'}  # A ∩ B ∩ C
        else:
            raise ValueError("ERROR: Currently only at two or three items can be "
                             "supported but got " + str(labels))

        # Parse relations
        for exp in self.relations:
            support, against = self.parse(exp)
            if exp.lhs.some:
                # At this time, in the tuple support (X,Y), then at least one of them
                # should exist. We should mark an X between these two areas
                # all_crosses is a dictionary { tuple of area labels -> expression }
                if support not in self.cross:
                    self.cross[support] = []
                self.cross[support].append(exp)
            if exp.lhs.all:
                # if support not in self.possible_all:
                #     self.possible_all[support] = []
                # self.possible_all[support].append(exp)
                # Any of the labels in the set against should be disabled
                for area_label in against:
                    if area_label not in self.black:
                        self.black[area_label] = []
                    self.black[area_label].append(exp)

    def is_area_definite(self, target: set, lhs: Token):
        """
        :param target: a large area being checked composed by small areas represented
                       by labels in the set
        :return: True if this area is sure to be TRUE
        """
        all_possible_combines = set(self.cross.keys())
        # Add symbol 1 of the All argument
        if lhs.all:
            lhs_circle = []
            for area_label in self.all_label:
                if lhs.name in area_label:
                    lhs_circle.append(area_label)
            all_possible_combines.add(tuple(lhs_circle))
        # For each cross in the diagram, remove the black part from it
        all_possible_combines = list(map(lambda x: set(x) - self.black.keys(),
                                         all_possible_combines))
        # If the target area covers            
        for area in all_possible_combines:
            if area.issubset(target):
                return True
        return False

    def evaluate(self, exp: Expression, show=False):
        """
        This function evaluates the validity of an argument
        :param exp: the expression being validated
        :param show: if the result should be displayed on the diagram
        :return: <if the expression could be TRUE>, <if the expression must be TRUE>,
                reason stated by a string
        """
        # Unknown set names
        if exp.lhs.name not in self.members or exp.rhs.name not in self.members:
            unknown = {exp.lhs.name, exp.rhs.name} - self.members
            return False, True, "Set name(s) not found: "+str(unknown).strip("{").strip("}")

        # Get area code results for the expression being validated
        support, against = self.parse(exp)
        valid_support_area = set(support) - set(self.black.keys())
        valid_against_area = against - set(self.black.keys())

        # Conclusion
        if exp.lhs.some:
            # Definitely true -> support should cover an X
            # Possibly true -> support covers part of an X / support are all unknown
            # Definitely false -> support are all black
            if len(valid_support_area) == 0:
                result = "NO TRUE"
            elif self.is_area_definite(valid_support_area, exp.lhs):
                result = "TRUE"
            else:
                result = "MAYBE TRUE"
        else:
            # Definitely false -> at least one of against is not black
            # Possibly false -> again covers part of an X / support are all unknown
            # Definitely true -> has valid support area
            if self.is_area_definite(valid_support_area, exp.lhs):
                result = "TRUE"
            elif self.is_area_definite(valid_against_area, exp.lhs):
                result = "FALSE"
            elif not self.is_area_definite(valid_support_area, exp.lhs):
                result = "MAYBE TRUE"
            else:
                result = "MAYBE FALSE"

        if show:
            if result == "NO TRUE":
                marked = set(support)
            elif result == "TRUE" or result == "MAYBE TRUE":
                marked = set(valid_support_area)
            else:
                marked = against
            self.venn_diagram.mark_area(marked,
                                        color=results[result]["color"],
                                        pattern=results[result]["pattern"])
            self.venn_diagram.show_validatity(results[result]["validity"] and results[result]["must"])

        return results[result]["validity"], results[result]["must"], results[result]["reason"]

    def display_diagram(self, highlight_some=True):
        self.venn_diagram.display_diagram(highlight_some)