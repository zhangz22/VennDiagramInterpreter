import sys

import numpy as np

from expression import Expression, Token
import matplotlib.pyplot as plt
from matplotlib_venn import *


def hex_to_rgba(hex):
    hex = hex.lstrip('#')
    hlen = len(hex)
    rgb = [int(hex[i:i + hlen // 3], 16) / 255 for i in range(0, hlen, hlen // 3)]
    return tuple(rgb + [0])


venn = {
    2: {
        "venn": venn2,
        "circles": venn2_circles,
        "subsets": (1, 1, 0.5),
        'colors':  list(map(hex_to_rgba, ["#ff7f7f", "#7fbf7f", "#d8ab7f"]))
        },
    3: {
        "venn": venn3,
        "circles": venn3_circles,
        "subsets": (1, 1, 0.5, 1, 0.5, 0.5, 0.1),
        "colors":  list(map(hex_to_rgba, ["#ff7f7f", "#7fbf7f", "#7f7fff", "#d8ab7f",
                                          "#d87fd8", "#7fabd8", "#b298b2"]))
    }
}


class ExpressionSet(object):
    def __init__(self):
        self.relations = set()  # A set of Expression objects
        self.members = set()  # A set of strings representing members (A,B,C...)
        self.label_id = {}  # A set of all labels in the diagram (A,B,AB...)
        self.crosses = {}  # A dictionary containing tuple of area code -> list of expressions that is emphasized by "Some" statements
        self.black = {}
        self.venn_diagram = None  # The venn diagram objects

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
        :return: true if the diagram contains no sets or relations
        """
        return len(self.members) == 0 and len(self.relations) == 0

    def __len__(self):
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
            self.members.add(exp.symbol1.name)
            self.members.add(exp.symbol2.name)
        elif isinstance(exp, str):
            self.members.add(Token(exp).name)
        else:
            raise TypeError("ERROR: Unknown type inserted.")
        if len(self.members) > 3:
            raise ValueError("ERROR: Only two or three sets can be supported but "
                             "the program got " + str(self.members))

    def premises(self, premises):
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
        This function evaluates the validity of a single expression and returns two sets
        containing the area labels to prove/disprove the statement
        :param exp:
        :return: support: a tuple contains all area labels that can prove this statement
                 against: a set contains all area labels that can refute this statement

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
        for area_label in self.label_id:
            if exp.symbol1.name in area_label:
                if exp.symbol1.some:
                    # Some A is B -> There must be an AB
                    # Find the areas that contains symbol2 (e.g. AB)
                    # The XOR operator here means if symbol2 is negated, find
                    # the area that does not contain symbol2
                    if exp.symbol2.neg ^ (exp.symbol2.name in area_label):
                        # Check for AB
                        support.add(area_label)
                elif exp.symbol1.all:
                    # All A is B -> There must not be an A or B (only AB, B)
                    # Find the areas that does not contain symbol2 (e.g. B)
                    # The == operator here means if symbol2 is negated, find
                    # the area that does contain symbol2
                    if exp.symbol2.neg ^ (exp.symbol2.name not in area_label):
                        # Check for A
                        against.add(area_label)
                    elif exp.symbol2.neg ^ (exp.symbol2.name in area_label):
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
        else:
            raise ValueError("ERROR: Currently only at two or three items can be "
                             "supported but got " + str(labels))

        # Parse relations
        for exp in self.relations:
            support, against = self.parse(exp)
            if exp.symbol1.some:
                # At this time, in the tuple support (X,Y), then at least one of them
                # should exist. We should mark an X between these two areas
                # all_crosses is a dictionary { tuple of area labels -> expression }
                if support not in self.crosses:
                    self.crosses[support] = []
                self.crosses[support].append(exp)
            if exp.symbol1.all:
                # if support not in self.possible_all:
                #     self.possible_all[support] = []
                # self.possible_all[support].append(exp)
                # Any of the labels in the set against should be disabled
                for area_label in against:
                    if area_label not in self.black:
                        self.black[area_label] = []
                    self.black[area_label].append(exp)

    def get_all_possible_area(self):
        """
        :return: a list of sets of area labels where each set represents that at
                 least one of the area in the diagram is true
        """
        all_possible_combines = list(
            map(lambda x: set(x) - self.black.keys(), self.crosses.keys()))
        return all_possible_combines

    def is_area_definite(self, target: set):
        """
        :param target: a large area being checked composed by small areas represented
                       by labels in the set
        :return: True if this area is sure to be TRUE
        """
        # TODO Add symbol 1
        all_possible_combines = self.get_all_possible_area()
        for area in all_possible_combines:
            if area.issubset(target):
                return True
        return False

    results = {
        "TRUE": {"validity": True, "must": True, "color": "green", "pattern": "///",
                 "reason": "This is a TRUE statement. The green shadow in the diagram shows all valid areas."},
        "MAYBE TRUE": {"validity": True, "must": False, "color": "green", "pattern": "..",
                       "reason": "This statement may be TRUE but not necessarily TRUE.\n The green shadow in the diagram shows areas satisfies the expression but they may be empty."},
        "NO TRUE": {"validity": False, "must": True, "color": "red", "pattern": "xxx",
                  "reason": "This is a FALSE statement. The red shadow in the diagram shows all areas that fits the statement, but they are all invalid."},
        "FALSE": {"validity": False, "must": True, "color": "red", "pattern": "xxx",
                  "reason": "This is a FALSE statement. The red shadow in the diagram shows all areas that refutes the statement."},
        "MAYBE FALSE": {"validity": False, "must": False, "color": "red", "pattern": "+",
                        "reason": "This statement may be FALSE but not necessarily FALSE.\n The red shadow in the diagram shows all areas that refutes the statement but they may be empty."}
    }

    def evaluate(self, exp: Expression, show=False):
        """
        This function evaluates the validity of a statement and displays it on the diagram
        :param exp: the expression being validated
        :param show: a flag represents if the result should be displayed on the diagram
        :return: <if the expression could be TRUE>, <if the expression must be TRUE>, reason stated by a string
        """
        # Unknown set names
        if exp.symbol1.name not in self.members or exp.symbol2.name not in self.members:
            unknown = {exp.symbol1.name, exp.symbol2.name} - self.members
            return False, True, "Set name(s) not found: " + str(unknown).strip("{").strip("}")

        # Get area code results for the expression being validated
        support, against = self.parse(exp)
        valid_support_area = set(support) - set(self.black.keys())
        valid_against_area = against - set(self.black.keys())

        # Conclusion
        if exp.symbol1.some:
            # Definitely true -> support should cover an X
            # Possibly true -> support covers part of an X / support are all unknown
            # Definitely false -> support are all black
            if len(valid_support_area) == 0:
                result = "NO TRUE"
            elif self.is_area_definite(valid_support_area):
                result = "TRUE"
            else:
                result = "MAYBE TRUE"
        else:
            # Definitely false -> at least one of against is not black
            # Possibly false -> again covers part of an X / support are all unknown
            # Definitely true -> has valid support area
            ## TODO add symbol1 to definite
            if len(valid_support_area) > 0: # TODO add is_area_definite
                result = "TRUE"
            elif self.is_area_definite(valid_against_area):
                result = "FALSE"
            else:
                result = "MAYBE FALSE"

        if show:
            if result == "NO TRUE":
                marked = set(support)
            elif result == "TRUE" or result == "MAYBE TRUE":
                marked = set(valid_support_area)
            else:
                marked = against
            self.mark_area(marked, color=ExpressionSet.results[result]["color"], pattern=ExpressionSet.results[result]["pattern"])
            self.show_validatity(ExpressionSet.results[result]["validity"] and ExpressionSet.results[result]["must"])

        return ExpressionSet.results[result]["validity"], ExpressionSet.results[result]["must"], ExpressionSet.results[result]["reason"]


    # ===============================================================================
    # VISUALIZATION RELATED FUNCTIONS
    # ===============================================================================
    def display_diagram(self, highlight_some=True):
        """
        This function displays the diagram according to the area codes generated by
        create_diagram() function.
        :param highlight_some: a flag to determine whether to highlight "Some"
                               premises using a background color
        """
        if len(self.label_id) == 0 and len(self.members) != 0:
            print("ERROR: need to parse the expressions first", file=sys.stderr)
            self.parse_premises()

        # Create venn diagram basic structure
        labels = tuple(sorted(self.members))
        if not 2 <= len(labels) <= 3:
            raise ValueError("ERROR: Currently only at two or three items can be "
                             "supported but got " + str(labels))
        colors = dict(zip(self.label_id.keys(), venn[len(self)]["colors"]))

        # Draw the venn diagram in matplotlib
        plt.ion()
        c = venn[len(self)]["circles"](subsets=venn[len(self)]["subsets"])  # Edge
        self.venn_diagram = venn[len(self)]["venn"](subsets=venn[len(self)]["subsets"], set_labels=labels)
        for area_label, color in zip(self.label_id, colors):  # Set areas to white
            self.venn_diagram.get_patch_by_id(self.label_id[area_label]).set_alpha(1.0)
            self.venn_diagram.get_patch_by_id(
                self.label_id[area_label]).set_facecolor("white")
            self.venn_diagram.get_patch_by_id(
                self.label_id[area_label]).set_edgecolor((0, 0, 0, 0))
            self.venn_diagram.get_label_by_id(self.label_id[area_label]).set_text("")

        # Areas
        area_colors, texts = [], []

        def color_area(area_label: str):
            for exp in exps:
                area = self.venn_diagram.get_patch_by_id(self.label_id[area_label])
                area.set_alpha(1.0)
                area.set_facecolor(colors[area_label])
                area_colors.append(area)
                texts.append(str(exp))

        # Hightlight "All" premises using a background color
        # if highlight_all:
        #     for area_label_tuple, exps in self.possible_all.items():
        #         for area_label in area_label_tuple:
        #             color_area(area_label)

        # Hightlight "Some" premises using a background color
        for area_label_pair, exps in self.crosses.items():
            if len(area_label_pair) == 2:
                self.mark_intersect(area_label_pair)
            if highlight_some:
                for area_label in area_label_pair:
                    color_area(area_label)

        # Disabled areas should be marked black
        for area_label, exps in self.black.items():
            for exp in exps:
                area = self.venn_diagram.get_patch_by_id(self.label_id[area_label])
                area.set_alpha(1.0)
                area.set_facecolor('black')
                area_colors.append(area)
                texts.append(str(exp))

        # Display the legend
        # self.fig.legend(handles=area_colors, labels=texts) #,
        # loc='center left',
        # bbox_to_anchor=(1, 0.5))

    def get_intersect_pos(self, areas: tuple):
        """
        :param areas: a pair of area labels (A,B)/(A,C)...
        :return: the position or rotation of a "X" symbol between these two areas on
                 the diagram
        """
        labels = tuple(sorted(self.members))
        get_center_pos = lambda id1, id2: \
            (np.array(self.venn_diagram.get_label_by_id(id1).get_position()) +
             np.array(self.venn_diagram.get_label_by_id(id2).get_position())) / 2
        if len(labels) == 2:
            A, B = labels[0], labels[1]
            if areas == (A, A + B) or areas == (A + B, A):
                pos = get_center_pos('100', '110')
                pos[0] *= 0.9;
                pos[1] *= 0.8
                rot = 0
                return pos, rot
            elif areas == (B, A + B) or areas == (A + B, B):
                pos = get_center_pos('010', '110')
                pos[0] *= 0.9;
                pos[1] *= 0.8
                rot = 0
                return pos, rot
        elif len(labels) == 3:
            A, B, C = labels[0], labels[1], labels[2]
            if areas == (A, A + B) or areas == (A + B, A):
                pos = get_center_pos('100', '110')
                pos[0] *= 0.63
                rot = 165
                return pos, rot
            elif areas == (B, A + B) or areas == (A + B, B):
                pos = get_center_pos('010', '110')
                pos[0] *= 0.6
                rot = 15
                return pos, rot
            elif areas == (A, A + C) or areas == (A + C, A):
                pos = get_center_pos('100', '101')
                pos[0] *= 0.95;
                pos[1] *= -0.8
                rot = 45
                return pos, rot
            elif areas == (B, B + C) or areas == (B + C, B):
                pos = get_center_pos('010', '011')
                pos[0] *= 0.95;
                pos[1] *= -0.6
                rot = 135
                return pos, rot
            elif areas == (C, A + C) or areas == (A + C, C):
                pos = get_center_pos('001', '101')
                pos[0] *= 1.45;
                pos[1] *= 0.85
                rot = 10
                return pos, rot
            elif areas == (C, B + C) or areas == (B + C, C):
                pos = get_center_pos('001', '011')
                pos[0] *= 1.45;
                pos[1] *= 0.82
                rot = 170
                return pos, rot
            elif areas == (A + B, A + B + C) or areas == (A + B + C, A + B):
                pos = get_center_pos('110', '111')
                pos[1] *= 0.8;
                rot = 0
                return pos, rot
            elif areas == (A + C, A + B + C) or areas == (A + B + C, A + C):
                pos = get_center_pos('011', '111')
                pos[0] *= -0.9;
                pos[1] *= 1.4
                rot = 125
                return pos, rot
            elif areas == (B + C, A + B + C) or areas == (A + B + C, B + C):
                pos = get_center_pos('101', '111')
                pos[0] *= -1;
                pos[1] *= 1.4
                rot = 55
                return pos, rot
        return get_center_pos(self.label_id[areas[0]],
                              self.label_id[areas[1]]), 0

    def mark_intersect(self, area_labels: tuple):
        """
        This function marks "X" symbol(s) on the edge line(s) between areas
        :param area_labels: labels of areas (A,B...)
        """
        if len(area_labels) < 2:
            return
        for i in range(len(area_labels)):
            for j in range(i + 1, len(area_labels)):
                pos, rot = self.get_intersect_pos(
                    (area_labels[i], area_labels[j]))
                size = (5 - len(self.members)) * 7
                plt.annotate('X', xy=pos, rotation=rot, xytext=(0, 0),
                             weight='bold',
                             size=size,
                             ha='center', textcoords='offset points')

    def mark_area(self, area: set, color="red", pattern='xxx'):
        """
        This function marks area(s) in the diagram with a edge color and a hatch
        texture
        :param area: a set containing all area labels
        :param color: the edge color
        :param pattern: the texture of shadow
                        'xxx' for definitely false
                        '+' for possibly false
                        '///' for definitely true
                        '..' for possibly true
        """
        for area_label in area:
            self.venn_diagram.get_patch_by_id(
                self.label_id[area_label]).set_edgecolor(color)
            self.venn_diagram.get_patch_by_id(
                self.label_id[area_label]).set_linewidth(2)
            self.venn_diagram.get_patch_by_id(
                self.label_id[area_label]).set_hatch(pattern)

    def show_validatity(self, is_valid: bool):
        if is_valid:
            text = "  VALID ARGUMENT"
            color = hex_to_rgba("#228B22")
        else:
            text = "  INVALID ARGUMENT"
            color = hex_to_rgba("#8B0000")
        plt.annotate(text, xy=(0.5, 0.02), rotation=0, xytext=(0, 0),
                     xycoords='figure fraction',
                     size=25,
                     ha='center', textcoords='offset points')

