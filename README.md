# VennDiagramInterpreter
### Overview
This is my undergraduate thesis. A simple program to validate some logic argument using
the venn diagram

### Environment installation
```
conda install numpy
conda install matplotlib
conda install matplotlib-venn
```
Or if the system does not have ```conda```, then
```
pip install numpy
pip install matplotlib
pip install matplotlib-venn
```

### How to use: 
```
usage: venn_gui.py [-h] [-f F] [-e EVAL] [--no_window]

optional arguments:
  -h, --help            show this help message and exit
  -f F                  Read premises from local file
  -e EVAL, --eval EVAL  The argument being validated
  --no_window           Get the result immediately without showing the
                        interactive window (Note: only works in an IDE)
```
- filename: if specified, the program will read from the file automatically at startup.
- eval: if specified, the program will automatically validate the argument

### Local file usage:
The file should contains all premises in logic arguments. 

### Syntax
The logic argument could be:
- Set (total 3 at most): The name of the set, use a quote("") if it contains multiple words
- Expression: <All/Some> A's are <(not)> B's
  <br> if the set name in the expression is not specified elsewhere, it will be added 
  automatically

Each element is separated by newline characters.

### Examples
```
cat example/example1.venn
```
A <br>
B <br>
Some A's are B's <br>
Some B's are C's <br>
C <br>
```
python venn_gui.py -f example/example1.venn --eval "Some A's are C's"
```
![exampl1](example/example1.png)
<br>
<br>
```
cat example/example1.venn
```
All A's are B's <br>
All B's are C's <br>
```
python venn_gui.py -f example/example2.venn --eval "All A's are C's" --no_window
```
![exampl1](example/example2_no_window.png)