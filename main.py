import os
import sys

import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from expression import Expression
from expression_set import ExpressionSet


# Always compare different sets TODO
# TODO move the X once X is on a border with black
# tODO conclusion/validity


class VennGUI(object):
    def __init__(self):
        self.filename = ""
        self.filepath = ""
        self.collect = None
        self.root = None
        self.fig = None
        self.msg_text = None
        self.msg_label = None
        self.premises_box = None
        self.show_btn = None
        self.is_definite_highlight = None
        self.is_possible_highlight = None
        self.eval_box = None
        self.set_up()

    def run(self, argv):
        """
        :param argv: arguments for running the program
                     Usage: main.py <-f filename>
        """
        if len(argv) > 1:
            for i in range(1, len(argv)):
                if argv[i] == "-f":
                    if i+1 >= len(argv):
                        print("ERROR: Invalid arguments."
                              "Usage: main.py <-f filename>", file=sys.stderr)
                        sys.exit(1)
                    self.filepath = argv[i+1]
                    self.load(new_file=False)
        self.root.mainloop()

    def set_up(self):
        # Set up the venn
        self.collect = ExpressionSet()

        # Set up GUI
        self.root = tk.Tk()
        self.root.title("Venn Diagram Interpreter")
        tk.Grid.rowconfigure(self.root, 0, weight=1)
        tk.Grid.columnconfigure(self.root, 0, weight=1)
        self.fig = plt.figure(1)

        canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        plot_widget = canvas.get_tk_widget()

        # The main panel
        plot_widget.grid(row=0, column=0, columnspan=2,
                         sticky=tk.N + tk.S + tk.E + tk.W)

        # ---------------------------- Premises --------------------------------
        # Message
        self.msg_text = tk.StringVar()
        self.msg_label = tk.Label(self.root, textvariable=self.msg_text)
        self.msg_label.grid(row=1, sticky="w", columnspan=2)

        # Premises input box
        tk.Label(self.root,
                 text="Sytnax: (Use quote or a newline to separate)").grid(
            row=2, sticky="w", columnspan=2)
        tk.Label(self.root,
                 text="\tSet (total 3 at most): The name of the set, "
                      "use a quote(\"\") if it contains multiple words").grid(
            row=3, sticky="w", columnspan=2)
        tk.Label(self.root,
                 text="\tExpression: <All/Some> A's are <(not)> B's").grid(
            row=4, sticky="w", columnspan=2)
        tk.Label(self.root, text="Enter the premises:").grid(row=6, sticky="w",
                                                             columnspan=2)

        PREMISE_BOX_HEIGHT = 4
        FIRST_ROW_OF_PREMISE_BOX = 3 + PREMISE_BOX_HEIGHT
        self.premises_box = ScrolledText(self.root, height=PREMISE_BOX_HEIGHT)
        self.premises_box.grid(row=FIRST_ROW_OF_PREMISE_BOX, column=0, sticky="nsew",
                               rowspan=PREMISE_BOX_HEIGHT)

        def premises_modified(event):
            curr_title = self.root.title()
            if self.premises_box.edit_modified():
                if not curr_title.startswith("*"):
                    self.root.title("*" + curr_title)
            else:
                curr_title = curr_title[1:] if curr_title[0] == '*' else curr_title
                self.root.title(curr_title)

        self.premises_box.bind("<<Modified>>", premises_modified)

        def focus_next_widget(event):
            event.widget.tk_focusNext().focus()
            return "break"

        self.premises_box.bind("<Tab>", focus_next_widget)

        self.show_btn = tk.Button(self.root, text="Show diagram",
                                  command=self.show_diagram)
        self.show_btn.grid(row=FIRST_ROW_OF_PREMISE_BOX + 1, column=1,
                           sticky=tk.W + tk.E, rowspan=1)
        self.show_btn.bind("<Return>", lambda e: self.show_btn.invoke())
        self.premises_box.bind("<Control-Return>", lambda e: self.show_btn.invoke())

        clear_btn = tk.Button(self.root, text="Clear", command=self.clear)
        clear_btn.grid(row=FIRST_ROW_OF_PREMISE_BOX + 2, column=1,
                       sticky=tk.W + tk.E, rowspan=1)
        clear_btn.bind("<Return>", lambda e: clear_btn.invoke())

        # load_btn = tk.Button(self.root, text="Load", command=load)
        # load_btn.grid(row=3, column=1)
        #
        # save_btn = tk.Button(self.root, text="Save", command=save_as)
        # save_btn.grid(row=4, column=1)

        self.is_possible_highlight = tk.IntVar()
        poss_check = tk.Checkbutton(self.root,
                                    text="Use color shadow to highlight \"Some\" statements.",
                                    variable=self.is_possible_highlight)
        poss_check.grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT,
                        column=0)
        poss_check.toggle()

        # self.is_definite_highlight = tk.IntVar()
        # def_check = tk.Checkbutton(self.root,
        #                            text="Use color shadow to highlight \"All\" statements.",
        #                            variable=self.is_definite_highlight)
        # def_check.grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT + 1,
        #                column=0)

        # Input box
        tk.Label(self.root, text="Enter the expression you want to evaluate:").grid(
            row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT + 2, sticky="w",
            columnspan=2)

        self.eval_box = tk.Entry(self.root)
        self.eval_box.grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT + 3,
                           column=0, sticky="ew")
        self.eval_box.bind("<Return>", lambda e: self.update_diagram())

        eval_btn = tk.Button(self.root, text="Evaluate", command=self.update_diagram)
        eval_btn.grid(row=FIRST_ROW_OF_PREMISE_BOX + PREMISE_BOX_HEIGHT + 3,
                      column=1)
        eval_btn.bind("<Return>", lambda e: eval_btn.invoke())

        # Menu bar
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="\tNew         ", accelerator="        Ctrl+N",
                             command=self.new_file)
        self.root.bind('<Control-n>', lambda e: self.new_file())
        filemenu.add_command(label="\tOpen...     ", accelerator="        Ctrl+O",
                             command=self.load)
        self.root.bind('<Control-o>', lambda e: self.load())
        filemenu.add_command(label="\tSave        ", accelerator="        Ctrl+S",
                             command=self.save)
        self.root.bind('<Control-s>', lambda e: self.save())
        filemenu.add_command(label="\tSave As...  ", accelerator="Ctrl+Shift+S",
                             command=self.save_as)
        self.root.bind('<Control-Shift-s>', lambda e: self.save_as())
        filemenu.add_separator()
        filemenu.add_command(label="\tExit", command=quit)
        menubar.add_cascade(label="File", menu=filemenu)

        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.add_command(label="\tUndo", accelerator="Ctrl+Z",
                             command=lambda: self.root.focus_get().event_generate(
                                 '<<Undo>>'))
        editmenu.add_separator()
        editmenu.add_command(label="\tCut", accelerator="Ctrl+X",
                             command=lambda: self.root.focus_get().event_generate(
                                 '<<Cut>>'))
        editmenu.add_command(label="\tCopy", accelerator="Ctrl+C",
                             command=lambda: self.root.focus_get().event_generate(
                                 '<<Copy>>'))
        editmenu.add_command(label="\tPaste", accelerator="Ctrl+V",
                             command=lambda: self.root.focus_get().event_generate(
                                 '<<Paste>>'))
        editmenu.add_separator()
        editmenu.add_command(label="\tSelect All", accelerator="Ctrl+A",
                             command=lambda: self.root.focus_get().event_generate(
                                 '<<SelectAll>>'))
        menubar.add_cascade(label="Edit", menu=editmenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help Index")
        helpmenu.add_command(label="About...")
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.root.config(menu=menubar)
        self.root.protocol("WM_DELETE_WINDOW", quit)

    # Update button
    def show_diagram(self):
        plt.clf()
        self.msg_text.set("")
        # Create the ExpressionSet object
        self.collect = ExpressionSet()
        if self.premises_box.get("1.0", tk.END) == "":
            return
        try:
            self.collect.premises(self.premises_box.get("1.0", tk.END).replace(';', '\n'))
        except NameError as e:
            self.msg_text.set(str(e))
            self.msg_label.configure(foreground="red")
        except TypeError as e:
            print(e, file=sys.stderr)
            pass
        except ValueError as e:
            self.msg_text.set(str(e))
            self.msg_label.configure(foreground="red")
            return
        except SyntaxError as e:
            self.msg_text.set(str(e))
            self.msg_label.configure(foreground="red")
            return
        if self.collect.empty() or len(self.collect) == 1:
            return
        self.collect.parse_premises()
        self.collect.display_diagram(
            highlight_some=bool(self.is_possible_highlight.get()))
        self.fig.canvas.flush_events()
        self.fig.canvas.draw()

    # Update button
    def update_diagram(self):
        self.show_diagram()
        if self.collect.empty():
            self.msg_text.set("The diagram is empty!")
            self.msg_label.configure(foreground="red")
            return
        if self.eval_box.get() == "":
            return
        try:
            ret, must, reason = self.collect.evaluate(
                Expression(self.eval_box.get()), show=True)
            self.msg_text.set(reason)
            if ret:
                if must:
                    self.msg_label.configure(foreground="green")
                else:
                    self.msg_label.configure(foreground="yellowgreen")
            else:
                if must:
                    self.msg_label.configure(foreground="red")
                else:
                    self.msg_label.configure(foreground="darkorange")
            self.fig.canvas.flush_events()
            self.fig.canvas.draw()
        except SyntaxError as e:
            self.msg_text.set(str(e))
            self.msg_label.configure(foreground="red")

    # Load button
    filetypes = (("Venn Diagram file (*.venn)", "*.venn"),
                 ("Normal text file (*.txt)", "*.txt"),
                 ("All types (*.*)", "*.*"))

    def load(self, new_file=True):
        if new_file:
            self.filepath = tk.filedialog.askopenfilename(
                defaultextension=".venn", filetypes=VennGUI.filetypes)
        if self.filepath == "":
            return
        if not os.path.exists(self.filepath):
            print("ERROR File \"{}\" does not exist.".format(self.filepath),
                  file=sys.stderr)
            return
        self.filename = os.path.basename(self.filepath)
        with open(self.filepath, 'r', encoding='utf8') as f:
            text = f.read()
        self.premises_box.delete('1.0', tk.END)
        self.premises_box.insert(tk.INSERT, text)
        self.premises_box.edit_modified(False)
        self.show_btn.invoke()
        self.msg_text.set("Successfully load from file \"{}\"".format(self.filename))
        self.msg_label.configure(foreground="green")
        self.root.title(self.filename + " - Venn Diagram Interpreter")

    def save_as(self, new_file=True):
        if new_file or self.filepath == "" or self.filename == "":
            self.filepath = tk.filedialog.asksaveasfilename(
                defaultextension=".venn", filetypes=VennGUI.filetypes)
            if self.filepath == "":
                return
            self.filename = os.path.basename(self.filepath)
        with open(self.filepath, "w", encoding='utf8') as text_file:
            text_file.write(self.premises_box.get("1.0", tk.END))
        self.msg_text.set("Successfully saved file \"{}\"".format(self.filename))
        self.msg_label.configure(foreground="green")
        self.root.title(self.filename + " - Venn Diagram Interpreter")

    def save(self):
        if self.filename == "":
            self.save_as()
        self.save_as(new_file=False)

    def clear(self):
        self.premises_box.delete('1.0', tk.END)
        self.msg_text.set("")
        self.eval_box.delete(0, tk.END)
        plt.clf()

    def new_file(self):
        if self.premises_box.edit_modified():
            save_before_new = tk.messagebox.askyesnocancel(
                "Venn Diagram Interpreter", "Do you want to save the changes?")
            if save_before_new is None:
                return
            if save_before_new:
                self.save()
        self.clear()
        self.premises_box.edit_modified(False)
        self.filename = ""
        self.filepath = ""
        self.root.title("Venn Diagram Interpreter")

    def quit(self):
        if self.premises_box.edit_modified():
            save_before_exit = tk.messagebox.askyesnocancel(
                "Venn Diagram Interpreter", "Do you want to save the changes?")
            if save_before_exit is None:
                return
            if save_before_exit:
                self.save()
        self.root.quit()


if __name__ == '__main__':
    gui = VennGUI()
    gui.run(sys.argv)

    # All A's are B's
    # All B's are C's
    # Some C's are A's may be wrong if ABC is
    # All C are not A may be false

    # All A's are B's
    # Some C's are A's

    # Some C's are B's <- True

    # If I want to know a SOME there must be an X