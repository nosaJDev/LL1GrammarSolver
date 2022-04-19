
# This is an attempt to create sets that follow a fixed point logic,
# making them perfect for LL(1) parsers
import sys

class FPset:

    def __init__(self, name):

        # Give a name to the set
        self.name = name

        # What elements are on the set
        self.elems = set()

        # Wether the set changed recently
        self.changed = True

        # On which events does the set participate 
        self.events = set()

    def contains(self,elem):

        # Checks if the set contains a specific element
        return elem in self.elems

    def add(self, elem):

        # Adds an element to the set
        if self.contains(elem):
            return

        self.elems.add(elem)
        self.changed = True

    def __str__(self):
        return str(self.elems)


# This is an event that can change a set based on others
class FPevent:

    def __init__(self,name, assertions, outcomes):

        # Set the name of the set
        self.name = name

        # Wether this event must be rechecked
        self.pending = True

        # Which things must be true for it to happen
        # In the form of tupples (set, 'c' , 'element') The set must contain the element
        self.assertions = assertions

        # What will happen if the assertions are true
        # In the form of tupples (set1, 'a', set2) Add the contents of set2 to set1
        self.outcomes = outcomes

        # Add the event to the appopriate sets based on the rules and outcomes
        for theset,_,_ in assertions:
            theset.events.add(self)
        for _,_,theset in outcomes:
            if type(theset) != str:
                theset.events.add(self)

    def play(self):

        # Plays out the rule, checks all the assertions etc..
        #print("Playing event",self.assertions,self.outcomes)


        # Reset the pending flag
        self.pending = False

        # Check all the assertions
        for assertion in self.assertions:
            
            # Unpack first
            theset, op, elem = assertion
            
            # Then check that it is true
            if op == 'c':
                if not theset.contains(elem):
                    # Assertion failed
                    return

        # If all the assertions pass, make the changes
        for outcome in self.outcomes:
            # Unpack first
            set1, op, set2 = outcome

            # Make the change
            if op == 'a':
                for el in set2.elems:
                    if el != 'ε':
                        set1.add(el)
            elif op == 'as':
                set1.add(set2)
            
            # Reset the rules that are affected
            if set1.changed:
                set1.changed = False
                for ev in set1.events:
                    ev.pending = True


# This class will collect and play all FPevents until there are no changes left
class FPplayer:


    def __init__(self, events):

        # Write all the events in
        self.events = events

    def play(self):

        # Play all the events until no event is pending
        still_pending = True
        while still_pending:

            # Reset the still pending events
            still_pending = False

            # Play the events
            for ev in self.events:
                if ev.pending:
                    ev.play()
                    still_pending = True


# Context free grammar parser
class CFG:

    def __init__(self, filename):

        # Parse the file of the grammar
        file = open(filename, 'r',encoding='utf-8')
        file_contents = file.read()
        file.close()

        # Split into lines
        file_lines = file_contents.split('\n')

        # Set of symbols, non-terminals and terminals
        self.symbols = set()
        self.terminals = set()
        self.nonterminals = set()

        # Create a list of the rules
        self.rules = []

        # Parse the lines
        for line in file_lines:
            
            # Skip the comments
            if line[0] == '#':
                continue

            # Split the line into its elements
            elems = line.split()

            # Create a rule based on the line
            self.rules.append((elems[0],tuple(elems[2:])))

            # Parse through the elements
            for i in range(len(elems)):
                
                # Skip the arrow symbol
                if i == 1:
                    continue
                
                # Get and add the symbol
                sym = elems[i]
                self.symbols.add(sym)

                # Add the first symbol to the non-terminals
                if i == 0:
                    self.nonterminals.add(sym)
        
        # Find out which symbols are terminals
        for sym in self.symbols:
            if sym not in self.nonterminals:
                self.terminals.add(sym)

    def print_info(self):
        # Prints the context free grammar
        
        # First print the non-terminals
        print("Non-terminal symbols:",self.nonterminals)

        # Then print the terminals
        safe_terminals = {x for x in self.terminals if x != 'ε'}
        print("Terminal symbols:",safe_terminals)

    
        # Finally print the rules
        for r in self.rules:

            # Print the rule
            self.print_rule(r)

    def print_rule(self,rule,end='\n',start_p = -1, end_p = -1):
        print(self.string_rule(rule,end,start_p,end_p),end='')

    def string_rule(self,rule,end='\n',start_p = -1, end_p = -1):
        
        # Make the initial string
        res = ""

        # For printing parentheses
        at = 0

        # Print the start of the rule
        if at == start_p:
            res += "["
        res += rule[0]+(']' if at == end_p else "")+" => "
        at += 1
        
        # Print the follow-up
        for rest in rule[1]:
            if at == start_p:
                res += "["
            res += rest+(']' if at == end_p else "")+" "
            at += 1

        # A final case for parentheses
        if end_p >= at:
            res += "...ε] "
        res += end
            
        return res


def get_FFFplus(cfg):
    # This function accepts a context free grammar and with the help of fixed point
    # sets, it constructs FIRST, FOLLOW and FIRST+ sets for every symbol in the grammar

    # First, create the appropriate dictionaries for the sets you will be making
    sets = {
        'first':{},
        'follow':{},
        'first+':{}
    }

    # Create an FPplayer to store all the possible events
    myevents = []

    # Create sets for all the symbols of the grammar
    for sym in cfg.symbols:
        
        # Create the set
        sets['first'][sym] = FPset("FIRST("+sym+")")

        # If the symbol is non-terminal, add it to the set
        if sym in cfg.terminals:
            sets['first'][sym].add(sym)
        else:
            # Create a follow set if it's non terminal
            sets['follow'][sym] = FPset("FOLLOW("+sym+")")

    # Then, according to the grammar rules, create appropriate events for the first sets
    for fsym, following in cfg.rules:

        # Add events for every possible following
        for i in range(len(following)+1):

            # Add assertions for the previous symbols
            assertions = []

            # Variables for printing the logic
            print()
            cfg.print_rule((fsym,following),'\n',0,i+1)
            has_assertions = False
            word = "if"

            for ssym in following[:i]:

                # Print one step of the assertions
                print(word,sets['first'][ssym].name,'contains','ε')
                word = 'and'
                has_assertions = True

                assertions.append((sets['first'][ssym],'c','ε'))
            
            # Print the outcomes
            if has_assertions:
                print('then',end=" ")

            # Add the outcome
            outcome = None
            if i == len(following) or following[i] == 'ε':
                outcome = (sets['first'][fsym],'as','ε')
                print(outcome[0].name,"gets the element ε")
            else:
                outcome = (sets['first'][fsym],'a',sets['first'][following[i]])
                print(outcome[0].name,"gets the elements of",outcome[2].name)

            # Create the event
            myevents.append(FPevent("-",assertions.copy(),[outcome]))

            # Stop if you encountered a terminal
            if i < len(following) and following[i] in cfg.terminals:
                break

    # Then, create follow events for non-terminal symbols
    sets['follow'][cfg.rules[0][0]].add("$")
    for fsym, following in cfg.rules:

        print('f',(fsym,following))

        # Loop through the rule to find non-terminals
        for i in range(len(following)):
            
            # Check if you encountered a non-terminal
            rsym = following[i]
            if rsym not in cfg.nonterminals:
                continue

            # If it is a non-terminal, loop through the rest to create events
            for j in range(i+1, len(following)+1):

                # Add assertions for the previous symbols
                assertions = []
                
                # Variables for printing the logic
                print()
                cfg.print_rule((fsym,following),'\n',i+1,j+1)
                has_assertions = False
                word = "if"

                for ssym in following[i+1:j]:

                    # Print one assertion
                    print(word, sets['first'][ssym].name,'contains','ε')
                    has_assertions = True
                    word = "and"

                    assertions.append((sets['first'][ssym],'c','ε'))
                
                # Add the outcome
                outcome = None
                if j == len(following):
                    outcome = (sets['follow'][rsym],'a',sets['follow'][fsym])
                else:
                    outcome = (sets['follow'][rsym],'a',sets['first'][following[j]])
                
                # Print the outcome
                if has_assertions:
                    print("then",end=" ")
                print(outcome[0].name,"gets the elements of",outcome[2].name)

                # Create the event
                myevents.append(FPevent("-",assertions.copy(),[outcome]))

                # Stop early if you encounter a terminal
                if j < len(following) and following[j] in cfg.terminals:
                    break

    # Finally, create first+ sets and appropriate rules
    for rule in cfg.rules:

        # Create a set for this specific rule
        rname = cfg.string_rule(rule,'')
        sets['first+'][rule] = FPset("FIRST+("+rname[0:-1]+")")

        # Loop through the rule
        fsym, following = rule
        for i in range(len(following)+1):

            # Add variables for printing assertions
            print()
            cfg.print_rule((fsym,following),'\n',0,i+1)
            has_assertions = False
            word = "if"

            # Add assertions for the previous symbols
            assertions = []
            for ssym in following[:i]:

                # Print one step of the assertions
                print(word,sets['first'][ssym].name,'contains','ε')
                word = 'and'
                has_assertions = True

                assertions.append((sets['first'][ssym],'c','ε'))
            
            # Add the outcome
            outcome = None
            if i == len(following) or following[i] == 'ε':
                outcome = (sets['first+'][rule],'a',sets['follow'][fsym])
            else:
                outcome = (sets['first+'][rule],'a',sets['first'][following[i]])

            # Print the outcome
            if has_assertions:
                print("then",end=" ")
            print(outcome[0].name,"gets the elements of",outcome[2].name)


            # Create the event
            myevents.append(FPevent("-",assertions.copy(),[outcome]))

            # Stop early if you encounter terminal
            if i < len(following) and following[i] in cfg.terminals:
                break

    # Add a player and play out the rules
    myplayer = FPplayer(myevents)
    myplayer.play()

    # Remove terminals from the first sets
    #for elem in [x for x in sets['first'] if x in cfg.terminals]:
    #    sets['first'].pop(elem)

    # Add a new line to finish
    print()

    # Return the sets
    return sets



def main():

    # Find the filename from the arguments
    if len(sys.argv) < 2:
        print("Usage: python ll1.py <filename>")
        return

    # Load the grammar and print it
    myCFG = CFG(sys.argv[1])
    myCFG.print_info()
    res = get_FFFplus(myCFG)
    for label in res:
        for label2 in res[label]:
            print(res[label][label2].name,"=",str(res[label][label2]))
        print()
    


if __name__ == "__main__":
    main()