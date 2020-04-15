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
        self.highlight = {}      # A dictionary containing area code -> list of expressions
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
            raise ValueError("ERROR: Unknown type inserted.")
        if len(self.members) > 3:
            print(self.members, file=sys.stderr)
            raise ValueError("ERROR: Only two or three items can be supported!")

    def parse(self):
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
            for area_label in self.label_id:
                if exp.symbol1.neg ^ (exp.symbol1.token in area_label):
                    # TODO is "not all A is B" or "not some A is B" supported?
                    # Some A is B
                    if exp.symbol1.some:
                        # The XOR operator here means if symbol2 is negated, find
                        # the area that does not contain symbol2
                        if exp.symbol2.neg ^ (exp.symbol2.token in area_label):
                            if area_label not in self.highlight:
                                self.highlight[area_label] = []
                            self.highlight[area_label].append(exp)
                    # All A is B
                    elif exp.symbol1.all:
                        # The XOR operator here means if symbol2 is negated, find
                        # the area that does contain symbol2
                        if exp.symbol2.neg == (exp.symbol2.token in area_label):
                            if area_label not in self.disable:
                                self.disable[area_label] = []
                            self.disable[area_label].append(exp)

    def show(self, highlight=True):
        """
        This function evaluates all expressions stored in the current set.
        Then it displays the diagram
        """
        if len(self.label_id) == 0 and len(self.members) != 0:
            print("ERROR: need to parse the expressions first", file=sys.stderr)
            self.parse()

        plt.ion()

        # Create venn diagram
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

        # Draw the venn diagram
        c = circles(subsets=subsets)
        self.diagram = venn(subsets=subsets, set_labels=labels)

        for area_label, color in zip(self.label_id, colors):
            self.diagram.get_patch_by_id(self.label_id[area_label]).set_alpha(1.0)
            self.diagram.get_patch_by_id(self.label_id[area_label]).set_facecolor("white")
            self.diagram.get_patch_by_id(self.label_id[area_label]).set_edgecolor((0,0,0,0))
            self.diagram.get_label_by_id(self.label_id[area_label]).set_text("")

        # Legends
        area_colors, texts = [], []
        if highlight:
            for area_label, exps in self.highlight.items():
                for exp in exps:
                    area = self.diagram.get_patch_by_id(self.label_id[area_label])
                    area.set_facecolor(colors[area_label])
                    area_colors.append(area)
                    texts.append(str(exp))
        for area_label, exps in self.disable.items():
            for exp in exps:
                area = self.diagram.get_patch_by_id(self.label_id[area_label])
                area.set_facecolor('black')
                area_colors.append(area)
                texts.append(str(exp))

        # Display the diagram
        # self.fig.legend(handles=area_colors, labels=texts) #,
        # loc='center left',
        # bbox_to_anchor=(1, 0.5))
        # plt.show(block=True)

    def evaluate(self, exp: Expression, show=False):
        print("Evaluating " + str(exp))
        expression_area = set()
        for area_label in self.label_id:
            if exp.symbol1.neg ^ (exp.symbol1.token in area_label):
                # TODO is "not all A is B" or "not some A is B" supported?
                # Some A is B
                if exp.symbol1.some:
                    # The XOR operator here means if symbol2 is negated, find
                    # the area that does not contain symbol2
                    if exp.symbol2.neg ^ (exp.symbol2.token in area_label):
                        expression_area.add(area_label)
                # All A is B
                ## TODO still problem here
                elif exp.symbol1.all:
                    # The XOR operator here means if symbol2 is negated, find
                    # the area that does contain symbol2
                    if exp.symbol2.neg == (exp.symbol2.token in area_label):
                        expression_area.add(area_label)
        valid_area = expression_area - set(self.disable.keys())

        if show:
            if len(valid_area) == 0:
                for area_label in expression_area:
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_edgecolor("red")
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_linewidth(2)
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_hatch('///')
            else:
                for area_label in valid_area:
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_edgecolor("green")
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_linewidth(2)
                    self.diagram.get_patch_by_id(
                        self.label_id[area_label]).set_hatch('xxx')

        if len(valid_area) == 0:
            print("Evaluation failed")
            return False, valid_area
        else:
            print("Evaluation successful")
            print(valid_area)
            return True, valid_area