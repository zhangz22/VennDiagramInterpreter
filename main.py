import os
import sys

import numpy as np
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

import matplotlib

from expression import Expression
from expression_set import ExpressionSet

matplotlib.use('TkAgg')

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

"""
All A's are B's
Some C's are B's
Some B's are not A's
All C's are not A's

Some C's are not A's
"""

"""
A
B
Some A's are B's
Some B's are C's
"""

filename = ""
filepath = ""

# Update button
def show_diagram():
    global collect
    plt.clf()
    msg_test.set("")
    collect = ExpressionSet()
    if premises_box.get("1.0", tk.END) == "":
        return
    for line in premises_box.get("1.0", tk.END).replace(';', '\n').split('\n'):
        line = line.strip()
        if line == "": continue
        try:
            if len(line) == 1:
                collect.append(line)  # Collection
            else:
                collect.append(Expression(line))  # Expression
        except NameError as e:
            msg_test.set(str(e))
            msg_label.configure(foreground="red")
        except TypeError as e:
            print(e, file=sys.stderr)
            pass
        except ValueError as e:
            msg_test.set(str(e))
            msg_label.configure(foreground="red")
            return
    if collect.empty():
        return
    collect.create_diagram()
    collect.display_diagram(possible=bool(is_possible_highlight.get()), definite=bool(is_definite_highlight.get()))
    fig.canvas.flush_events()
    fig.canvas.draw()


# Update button
def update_diagram():
    global collect
    global msg_label
    show_diagram()
    if collect.empty():
        msg_test.set("The diagram is empty!")
        msg_label.configure(foreground="red")
        return
    if eval_box.get() == "":
        return
    ret, must, reason = collect.evaluate(Expression(eval_box.get()), show=True)
    msg_test.set(reason)
    if ret:
        if must:
            msg_label.configure(foreground="green")
        else:
            msg_label.configure(foreground="yellowgreen")
    else:
        if must:
            msg_label.configure(foreground="red")
        else:
            msg_label.configure(foreground="darkorange")
    fig.canvas.flush_events()
    fig.canvas.draw()


# Load button
filetypes = (("Venn Diagram file (*.venn)", "*.venn"), ("Normal text file (*.txt)", "*.txt"), ("All types (*.*)", "*.*"))


def load(new_file=True):
    global filename
    global filepath
    if new_file:
        filepath = tk.filedialog.askopenfilename(defaultextension=".venn", filetypes=filetypes)
        if filepath == "":
            return
        if not os.path.exists(filepath):
            print("ERROR File \"{}\" does not exist.".format(filepath),
                  file=sys.stderr)
            return
    filename = os.path.basename(filepath)
    with open(filepath, 'r', encoding='utf8') as f:
        text = f.read()
    premises_box.delete('1.0', tk.END)
    premises_box.insert(tk.INSERT, text)
    show_btn.invoke()
    msg_test.set("Successfully load from file \"{}\"".format(filename))
    msg_label.configure(foreground="green")
    root.title(filename + " - Venn Diagram Interpreter")


def save_as(new_file=True):
    global filename
    global filepath
    if new_file or filename == "":
        filepath = tk.filedialog.asksaveasfilename(defaultextension=".venn", filetypes=filetypes)
        if filepath == "":
            return
        filename = os.path.basename(filepath)
    with open(filepath, "w", encoding='utf8') as text_file:
        text_file.write(premises_box.get("1.0", tk.END))
    msg_test.set("Successfully saved file \"{}\"".format(filename))
    msg_label.configure(foreground="green")
    root.title(filename + " - Venn Diagram Interpreter")


def save():
    global filename
    global filepath
    if filename == "":
        save_as()
    save_as(new_file=False)


def clear():
    global filename
    global filepath
    premises_box.delete('1.0', tk.END)
    msg_test.set("")
    eval_box.delete(0, tk.END)
    plt.clf()
    filename = ""
    filepath = ""
    root.title("Venn Diagram Interpreter")


if __name__ == "__main__":
    # Set up the venn
    collect = ExpressionSet()

    # Set up GUI
    root = tk.Tk()
    root.title("Venn Diagram Interpreter")
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 0, weight=1)
    fig = plt.figure(1)

    canvas = FigureCanvasTkAgg(fig, master=root)
    plot_widget = canvas.get_tk_widget()

    # The main panel
    plot_widget.grid(row=0, column=0, columnspan=2, sticky=tk.N+tk.S+tk.E+tk.W)

    # ------------------------------ Preconditions ----------------------------------
    # Message
    msg_test = tk.StringVar()
    msg_label = tk.Label(root, textvariable=msg_test)
    msg_label.grid(row=1, sticky="w", columnspan=2)

    # Premises input box
    tk.Label(root, text="Sytnax:").grid(row=2, sticky="w", columnspan=2)
    tk.Label(root, text="     Set (total 3 at most): A single letter followed by a newline or semicolon").grid(row=3, sticky="w", columnspan=2)
    tk.Label(root, text="     Expression: <All/Some> A's are <(not)> B's").grid(row=4, sticky="w", columnspan=2)
    tk.Label(root, text="Enter the premises:").grid(row=6, sticky="w", columnspan=2)

    PREMISE_BOX_HEIGHT = 4
    FIRST_ROW_OF_PREMISE_BOX = 3 + PREMISE_BOX_HEIGHT
    premises_box = ScrolledText(root, height=PREMISE_BOX_HEIGHT)
    premises_box.grid(row=FIRST_ROW_OF_PREMISE_BOX, column=0, sticky="nsew", rowspan=PREMISE_BOX_HEIGHT)

    show_btn = tk.Button(root, text="Show diagram", command=show_diagram)
    show_btn.grid(row=FIRST_ROW_OF_PREMISE_BOX + 1, column=1, sticky=tk.W + tk.E, rowspan=1)

    clear_btn = tk.Button(root, text="Clear", command=clear)
    clear_btn.grid(row=FIRST_ROW_OF_PREMISE_BOX + 2, column=1, sticky=tk.W + tk.E, rowspan=1)

    # load_btn = tk.Button(root, text="Load", command=load)
    # load_btn.grid(row=3, column=1)
    #
    # save_btn = tk.Button(root, text="Save", command=save_as)
    # save_btn.grid(row=4, column=1)

    is_possible_highlight = tk.IntVar()
    possible_checkbox = tk.Checkbutton(root, text="Use color shadow to highlight \"Some\" statements.", variable=is_possible_highlight)
    possible_checkbox.grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT, column=0)
    possible_checkbox.toggle()

    is_definite_highlight = tk.IntVar()
    definite_checkbox = tk.Checkbutton(root, text="Use color shadow to highlight \"All\" statements.", variable=is_definite_highlight)
    definite_checkbox.grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT+1, column=0)

    # Input box
    tk.Label(root, text="Enter the expressions you want to evaluate:").grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT + 2, sticky="w", columnspan=2)

    eval_box = tk.Entry(root)
    eval_box.grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT + 3, column=0, sticky="ew")

    tk.Button(root, text="Evaluate", command=update_diagram).grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT + 3, column=1)

    # Menu bar
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="New         ", command=clear)
    filemenu.add_command(label="Open        ", command=load)
    filemenu.add_command(label="Save        ", command=save)
    filemenu.add_command(label="Save As     ", command=save_as)
    filemenu.add_separator()
    filemenu.add_command(label="Exit        ", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)

    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help Index")
    helpmenu.add_command(label="About...")
    menubar.add_cascade(label="Help", menu=helpmenu)

    root.config(menu=menubar)

    # Arguments
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        load(new_file=False)

    # Basic window
    def on_closing():
        if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.quit()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()