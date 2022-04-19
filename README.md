# LL1GrammarSolver
A small tool that parses a CFG and calculates FIRST, FOLLOW and FIRST+ sets, while also briefly describing the logic behind the results.

The grammar is given through a grammar file that consists of lines corresponding to rules.
A rule has the following syntax:
[NON-TERMINAL] => [(NON-)TERMINAL1] [(NON-)TERMINAL2] ...
[NON-TERMINAL] => ε

There is no need to declare which symbols are terminal or not. Every symbol that does have a rule is
considered non-terminal, and all the others are considered terminal. The symbol ε is considered an
empty string and must be found alone at the right side of a rule and never at the left side.

Grammar files support comment lines, every comment line must start with #.

Usage:
Run the command 'python ll1.py [grammar-file-location]' and the results will be printed in the terminal.
