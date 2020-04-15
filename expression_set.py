import sys

from expression import Expression
import matplotlib.pyplot as plt
from matplotlib_venn import *


def hex_to_rgba(hex):
    hex = hex.lstrip('#')
    hlen = len(hex)
    rgb = [int(hex[i:i+hlen//3], 16)/255 for i in range(0, hlen, hlen//3)]
    return tuple(rgb + [0])

class ExpressionSet(object):
    def __init__(self):
        self.relations = set()   # A set of Expression objects
        self.members = set()     # A set of strings representing members (A,B,C...)
        self.label_id = {}       # A set of all labels in the diagram (A,B,AB...)
        self.possible = {}      # A dictionary containing area code -> list of expressions that is emphasized by "Some" statements
        self.definite = {}      # A dictionary containing area code -> list of expressions that is emphasized by "All" statements
        self.disable = {}
        self.diagram = None     # The venn diagram objects

    def __contains__(self, key):
        if isinstance(key, str):
            return key in self.members
        elif isinstance(key, Expression):
            return key in self.relations
        else:
            return False

    def __str__(self):
        ret = ""
        for i in sorted(self.members):
            ret += str(i) + " {"
            for j in self.relations:
                if i in j:
                    ret += "<" + str(j) + ">, "
            ret += "}\n"
        return ret

    def empty(self):
        return len(self.members) == 0

    def append(self, exp: Expression):
        if isinstance(exp, Expression):
            self.relations.add(exp)
            self.members.add(exp.symbol1.token)
            self.members.add(exp.symbol2.token)
        elif isinstance(exp, str):
            self.members.add(exp)
        else:
            raise TypeError("ERROR: Unknown type inserted.")
        if len(self.members) > 3:
            print(self.members, file=sys.stderr)
            raise ValueError("ERROR: Only two or three sets can be supported but "
                             "the program got " + str(self.members))

    def parse(self, exp: Expression):
        """
        This function evaluates the validity of a single expression and returns two sets
        containing the area labels to prove/disprove the statement
        :param exp:
        :return: support: a set contains all area labels that can prove this statement
                 against: a set contains all area labels that can refute this statement

        For statements:
                         |              support                     |        against
        -----------------|------------------------------------------|----------------------------------------
         Some A is B     | find if there is some area AB            |          {}
         Some A is not B | find if there is some area A (without B) |          {}
         All A is B      | find if there is some area AB            | find if there is some area A (without B)
         All A is not B  | find if there is some area A (without B) | find if there is some area AB
        -----------------|------------------------------------------|----------------------------------------

        """
        support = set()
        against = set()
        for area_label in self.label_id:
            if exp.symbol1.token in area_label:
                # TODO should "not all A is B" or "not some A is B" supported?
                if exp.symbol1.some:
                    # Some A is B -> There must be an AB
                    # Find the areas that contains symbol2 (e.g. AB)
                    # The XOR operator here means if symbol2 is negated, find
                    # the area that does not contain symbol2
                        if exp.symbol2.neg ^ (exp.symbol2.token in area_label):
                            # Check for AB
                            support.add(area_label)
                elif exp.symbol1.all:
                    # All A is B -> There must not be an A or B (only AB, B)
                    # Find the areas that does not contain symbol2 (e.g. B)
                    # The == operator here means if symbol2 is negated, find
                    # the area that does contain symbol2
                    if exp.symbol2.neg ^ (exp.symbol2.token not in area_label):
                        # Check for A
                        against.add(area_label)
                    elif exp.symbol2.neg ^ (exp.symbol2.token in area_label):
                        # Check for AB
                        support.add(area_label)
        return support, against

    def create_diagram(self):
        """
        This function parses all pre-conditions added to this diagram and generates
        corresponding area codes (highlighted by "Some" statements and disabled by
        "Not" statements
        """
        # Create venn diagram
        labels = tuple(sorted(self.members))
        if len(labels) == 2:
            self.label_id = {labels[0]: "10",  # A (left)
                             labels[1]: "01",  # B (right)
                             labels[0] + labels[1]: "11"}  # A ∩ B
        elif len(labels) == 3:
            self.label_id = {labels[0]: '100',  # A (up-left)
                             labels[1]: '010',  # B (up-right)
                             labels[2]: '001',  # C (down)
                             labels[0] + labels[1]: '110',  # A ∩ B
                             labels[0] + labels[2]: '101',  # A ∩ C
                             labels[1] + labels[2]: '011',  # B ∩ C
                             labels[0] + labels[1] + labels[2]: '111'}  # A ∩ B ∩ C

        # Parse relations
        for exp in self.relations:
            support, against = self.parse(exp)
            if exp.symbol1.some:
                for area_label in support:
                    if area_label not in self.possible:
                        self.possible[area_label] = []
                    self.possible[area_label].append(exp)
            if exp.symbol1.all:
                for area_label in support:
                    if area_label not in self.possible:
                        self.definite[area_label] = []
                    self.definite[area_label].append(exp)
                for area_label in against:
                    if area_label not in self.disable:
                        self.disable[area_label] = []
                    self.disable[area_label].append(exp)

    def display_diagram(self, highlight=True):
        """
        This function displays the diagram according to the area codes generated by
        create_diagram() function.
        :param highlight: a flag to determine whether to highlight "Some" preconditions
                          using a background color
        """
        if len(self.label_id) == 0 and len(self.members) != 0:
            print("ERROR: need to parse the expressions first", file=sys.stderr)
            self.parse()

        # Create venn diagram basic structure
        labels = tuple(sorted(self.members))
        if len(labels) == 2:
            venn = venn2
            circles = venn2_circles
            subsets = (1, 1, 0.5)
            colors = ["#ff7f7f", "#7fbf7f", "#d8ab7f"]
        elif len(labels) == 3:
            venn = venn3
            circles = venn3_circles
            subsets = (1, 1, 0.5, 1, 0.5, 0.5, 0.1)
            colors = ["#ff7f7f", "#7fbf7f", "#7f7fff", "#d8ab7f", "#d87fd8",
                      "#7fabd8", "#b298b2"]
        else:
            raise ValueError(
                "ERROR: Currently only at two or three items can be supported but got " + str(labels))
        colors = dict(zip(self.label_id.keys(), list(map(hex_to_rgba, colors))))

        # Draw the venn diagram in matplotlib
        plt.ion()
        c = circles(subsets=subsets)   # border
        self.diagram = venn(subsets=subsets, set_labels=labels)
        for area_label, color in zip(self.label_id, colors): # Set areas to white
            self.diagram.get_patch_by_id(self.label_id[area_label]).set_alpha(1.0)
            self.diagram.get_patch_by_id(self.label_id[area_label]).set_facecolor("white")
            self.diagram.get_patch_by_id(self.label_id[area_label]).set_edgecolor((0,0,0,0))
            self.diagram.get_label_by_id(self.label_id[area_label]).set_text("")

        # Areas
        area_colors, texts = [], []
        if highlight:
            # Hightlight "Some" preconditions using a background color
            for area_label, exps in self.possible.items():
                for exp in exps:
                    area = self.diagram.get_patch_by_id(self.label_id[area_label])
                    area.set_facecolor(colors[area_label])
                    area_colors.append(area)
                    texts.append(str(exp))
        # Disable areas should be marked black
        for area_label, exps in self.disable.items():
            for exp in exps:
                area = self.diagram.get_patch_by_id(self.label_id[area_label])
                area.set_facecolor('black')
                area_colors.append(area)
                texts.append(str(exp))

        # Display the legend
        # self.fig.legend(handles=area_colors, labels=texts) #,
        # loc='center left',
        # bbox_to_anchor=(1, 0.5))

    def evaluate(self, exp: Expression, show=False, print_log=False):
        """
        This function evaluates the validity of a statement and displays it on the diagram
        :param exp:
        :param show:
        :param log:
        :return:
        """
        support_area, against_area = self.parse(exp)
        valid_support_area = support_area - set(self.disable.keys())
        valid_against_area = against_area - set(self.disable.keys())

        def mark_green(area: set):
            if show:
                for area_label in area:
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_edgecolor("green")
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_linewidth(2)
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_hatch('xxx')

        def mark_red(area: set):
            if show:
                for area_label in area:
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_edgecolor("red")
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_linewidth(2)
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_hatch('///')

        def log(*arg):
            if (print_log):
                print(arg)

        if exp.symbol1.some:
            # Some A is B
            if len(valid_support_area) != 0:
                # There is some area AB that can prove this statement
                definite_support_area = valid_support_area.intersection(self.definite.keys())
                if len(definite_support_area) > 0:
                    mark_green(definite_support_area)
                    # if len(valid_support_area - self.possible.keys()) == 0:
                    return True, "This is a TRUE statement. The green shadow in the diagram shows all valid areas."
                else:
                    mark_green(valid_support_area)
                    return False, "This statement may be TRUE but not necessarily TRUE.\n The green shadow in the diagram shows areas satisfies the expression but they may be empty."
            else:
                # There is some area AB that can prove this statement but are disabled
                mark_red(support_area)
                return False, "This is a FALSE statement. The red shadow in the diagram shows all areas that fits the statement, but they are all invalid."
        elif exp.symbol1.all and exp.symbol1.token == exp.symbol2.token:
            if not exp.symbol2.neg:
                # All A is A
                if exp in self:
                    mark_green(support_area)
                    return True, "This is a TRUE statement. The green shadow in the diagram shows all valid areas."
                else:
                    mark_red(support_area)
                    return False, "This is a FALSE statement. The red shadow in the diagram shows all areas that fits the statement, but they are all invalid."
                pass
            else:
                # All A is not A
                if exp in self:
                    mark_green(support_area)
                    return True, "This is a TRUE statement. The green shadow in the diagram shows all valid areas."
                else:
                    mark_red(support_area)
                    return False, "This is a FALSE statement. The red shadow in the diagram shows all areas that fits the statement, but they are all invalid."
                pass
        elif exp.symbol1.all:
            # All A is B
            if len(valid_against_area) != 0:
                definite_against_area = valid_against_area.intersection(self.definite.keys())
                if len(definite_against_area) > 0:
                    mark_red(definite_against_area)
                    return False, "This is a FALSE statement. The red shadow in the diagram shows all areas that refutes the statement."
                else:
                    mark_red(valid_against_area)
                    return False, "This statement may be FALSE but not necessarily FALSE.\n The red shadow in the diagram shows all areas that refutes the statement but they may be empty."
            else:
                if len(valid_support_area) != 0:
                    mark_green(valid_support_area)
                    return True, "This is a TRUE statement. The green shadow in the diagram shows all valid areas."
                else:
                    mark_red(support_area)
                    return False, "This is a FALSE statement. The red shadow in the diagram shows all areas that fits the statement, but they are all invalid."



