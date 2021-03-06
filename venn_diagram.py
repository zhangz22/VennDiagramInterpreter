import sys
import numpy as np

import matplotlib.pyplot as plt
from matplotlib_venn import *

import expression_set

def hex_to_rgba(hex_):
    hex_ = hex_.lstrip('#')
    hlen = len(hex_)
    rgb = [int(hex_[i:i + hlen // 3], 16) / 255 for i in range(0, hlen, hlen // 3)]
    return tuple(rgb + [0])


venn = {
    2: {
        "venn": venn2,
        "circles": venn2_circles,
        "subsets": (1, 1, 0.5),
        'colors': list(map(hex_to_rgba, ["#ff7f7f", "#7fbf7f", "#d8ab7f"]))
    },
    3: {
        "venn": venn3,
        "circles": venn3_circles,
        "subsets": (1, 1, 0.5, 1, 0.5, 0.5, 0.1),
        "colors": list(
            map(hex_to_rgba, ["#ff7f7f", "#7fbf7f", "#7f7fff", "#d8ab7f",
                              "#d87fd8", "#7fabd8", "#b298b2"]))
    }
}


class VennDiagramPlt(object):
    def __init__(self, parent: expression_set.ExpressionSet):
        self.expression_set = parent
        self.venn_diagram = None  # The venn diagram objects

    def create_diagram(self, highlight_some=True):
        """
        This function displays the diagram according to the area codes generated in
        the expression set
        :param highlight_some: a flag to determine whether to highlight "Some"
                               premises using a background color
        """
        if len(self.expression_set.all_label) == 0 and len(
                self.expression_set.members) != 0:
            print("ERROR: need to parse the expressions first", file=sys.stderr)
            self.expression_set.parse_premises()

        # Create venn diagram basic structure
        labels = tuple(sorted(self.expression_set.members))
        if not 2 <= len(labels) <= 3:
            raise ValueError("ERROR: Currently only at two or three items can be "
                             "supported but got " + str(labels))
        colors = dict(zip(self.expression_set.all_label.keys(),
                          venn[len(self.expression_set)]["colors"]))

        # Draw the venn diagram in matplotlib
        plt.ion()
        c = venn[len(self.expression_set)]["circles"](
            subsets=venn[len(self.expression_set)]["subsets"])  # Edge
        self.venn_diagram = venn[len(self.expression_set)]["venn"](
            subsets=venn[len(self.expression_set)]["subsets"], set_labels=labels)
        for area_label, color in zip(self.expression_set.all_label,
                                     colors):  # Set areas to white
            self.venn_diagram.get_patch_by_id(
                self.expression_set.all_label[area_label]).set_alpha(1.0)
            self.venn_diagram.get_patch_by_id(
                self.expression_set.all_label[area_label]).set_facecolor("white")
            self.venn_diagram.get_patch_by_id(
                self.expression_set.all_label[area_label]).set_edgecolor(
                (0, 0, 0, 0))
            self.venn_diagram.get_label_by_id(
                self.expression_set.all_label[area_label]).set_text("")

        # Areas
        area_colors, texts = [], []

        def color_area(area_label: str):
            for exp in exps:
                area = self.venn_diagram.get_patch_by_id(
                    self.expression_set.all_label[area_label])
                area.set_alpha(1.0)
                area.set_facecolor(colors[area_label])
                area_colors.append(area)
                texts.append(str(exp))

        # Hightlight "Some" premises using a background color
        for area_label_pair, exps in self.expression_set.cross.items():
            if len(area_label_pair) == 2:
                self.mark_intersect(area_label_pair)
            if highlight_some:
                for area_label in area_label_pair:
                    color_area(area_label)

        # Disabled areas should be marked black
        for area_label, exps in self.expression_set.black.items():
            for exp in exps:
                area = self.venn_diagram.get_patch_by_id(
                    self.expression_set.all_label[area_label])
                area.set_alpha(1.0)
                area.set_facecolor('black')
                area_colors.append(area)
                texts.append(str(exp))

    def get_intersect_pos(self, areas: tuple):
        """
        :param areas: a pair of area labels (A,B)/(A,C)...
        :return: the position or rotation of a "X" symbol between these two areas on
                 the diagram
        """
        labels = tuple(sorted(self.expression_set.members))
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
        return get_center_pos(self.expression_set.all_label[areas[0]],
                              self.expression_set.all_label[areas[1]]), 0

    def mark_intersect(self, area_labels: tuple):
        """
        This function marks "X" symbol(s) on the edge line(s) between areas
        :param area_labels: labels of areas (A,B...)
        """
        if len(area_labels) < 2:
            return
        for i in range(len(area_labels)):
            for j in range(i + 1, len(area_labels)):
                pos, rot = self.get_intersect_pos((area_labels[i], area_labels[j]))
                size = (5 - len(self.expression_set.members)) * 7
                # If one of the area is black, move the cross
                if area_labels[i] in self.expression_set.black:
                    color = (1, 1, 0, 0.75)
                    pos2, rot2 = self.get_intersect_pos((area_labels[j], area_labels[j]))
                elif area_labels[j] in self.expression_set.black:
                    color = (1, 1, 0, 0.75)
                    pos2, rot2 = self.get_intersect_pos((area_labels[i], area_labels[i]))
                else:
                    color = "black"
                    pos2 = None
                if pos2 is not None:
                    plt.arrow(*(np.array(pos)+[0,0.03]), *((np.array(pos2)-np.array(pos))*0.5), head_width=0.02)
                    plt.annotate('X', xy=pos2, rotation=rot2, xytext=(0, 0),
                                 weight='bold', size=size, ha='center',
                                 textcoords='offset points')
                # Draw the cross on the diagram
                plt.annotate('X', xy=pos, rotation=rot, xytext=(0, 0), weight='bold',
                             size=size, color=color, ha='center',
                             textcoords='offset points')

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
                self.expression_set.all_label[area_label]).set_edgecolor(color)
            self.venn_diagram.get_patch_by_id(
                self.expression_set.all_label[area_label]).set_linewidth(2)
            self.venn_diagram.get_patch_by_id(
                self.expression_set.all_label[area_label]).set_hatch(pattern)

    def show_validatity(self, is_valid: bool):
        """
        This function displays the final conclusion on the diagram
        :param is_valid: the validatity of the argument
        """
        if is_valid:
            text = "  VALID ARGUMENT"
            color = hex_to_rgba("#228B22")
        else:
            text = "  INVALID ARGUMENT"
            color = hex_to_rgba("#8B0000")
        plt.annotate(text, xy=(0.5, 0.02), rotation=0, xytext=(0, 0),
                     xycoords='figure fraction',
                     size=22,
                     ha='center', textcoords='offset points')

    def show_argument(self, exp):
        """
        This function displays the expression being validated on the diagram
        :param exp: the argument being validated
        """
        plt.annotate(str(exp), xy=(0.5, 0.08), rotation=0, xytext=(0, 0),
                     xycoords='figure fraction',
                     size=13,
                     ha='center', textcoords='offset points')