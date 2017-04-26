import sys
import signal
import itertools
import time

from fp_growth import find_frequent_itemsets
from pprint import pprint
from timeout import timeout

"""Notes:

* Data is too big process all at once on a normal computer, hence we
  reduce the number of transactions first, only keeping results of a
  relavant airport

* Depending on airports selected the number of found frequent sets can
  vary a lot. E.g. for a support of 50, HKG will have 27 while FRA
  will have 6781 frequent sets.

   --> Solution: 
       Dynamically select mininal support. Just keep on increasing
       minimal support until we find less than e.g. 50 frequent
       sets. If the process takes to long, just abort and try

* Algorithm runs extemely slow if we do not remove duplicate flights
  WITHIN the transactions.

"""

######################################################################
### Initialization

# Preload all transactions to memory
transactions = []
with open("./flight_transactions") as f:
    for line in f:
        trans = line.split(",")
        trans = list(set(trans))                             # Remove duplicates
        trans = map(lambda x: set(x.split("->")), trans)     # Do not consider direction
        trans = map(lambda x: '-'.join(x), trans)
        transactions.append(trans)
        
def mine_frequent_set(trans, min_sup):
    # Need to turn generator to list
    return list(find_frequent_itemsets(trans, min_sup, True))

def get_frequent_sets(airport):
    # Filter out transactions that doesn't have the airport
    trans = filter(lambda x: airport in ' '.join(x), transactions)
    
    print("Process %s of transactions for %s" % (len(trans), airport))

    # Obscure data science voodoo
    min_sup = 20+len(trans)/10
    if min_sup > 100:
        min_sup = 100

    # Retry to find frequent sets by increasing min_sup until there is
    # no timeout nor too many results
    while True:
        res = timeout(mine_frequent_set, args = (trans, min_sup), timeout = 1, default = 'timeout')
        min_sup += 5
        
        if res == 'timeout':
            print 'Timeout, increase minimal support'
            continue

        # only keep sets with at least 3 items
        result = filter(lambda x: len(x[0]) > 2, res)
          
        # final set must include airport
        result = filter(lambda x: airport in ' '.join(x[0]), result) 

        if len(result) < 50:
            break

    result.sort(key=lambda x: x[1], reverse=True)
    return result

def __count_matches_in_frequent_set(frequent_set, pairs):
    counter = 0
    for s in frequent_set:
        for a1, a2 in pairs:
            if a1 in s and a2 in s:
                counter += 1
                break
    return counter

def __generate_suggestion(sets, airports):
    # split and flatten
    flat = []
    for s in sets:
        flat.extend(s.split('-'))

    suggestions = []
    for s in flat:
        if s not in airports:
            suggestions.append(s)

    return suggestions

def get_suggestion(homes, airports):
    print '\nMatched frequent sets:'
    pairs = list(itertools.combinations(airports, 2))

    relevant_frequent_sets = []
    suggestion = []
    
    for h in homes:
        
        res1, res2, res3 = [], [], []
        
        for freq, _ in get_frequent_sets(h):
            counter = __count_matches_in_frequent_set(freq, pairs)

            # Use multiple level of thresholds and later select the
            # one that has the least sets
            if counter > len(freq)-1:
                res1.append(freq)
            if counter > len(freq)-2:
                res2.append(freq)
            if counter > len(freq)-3:
                res2.append(freq)
                print freq
                
        # filter out empty sets
        res = filter(lambda x: len(x) != 0, (res1, res2, res3))
        
        # if has non-empty set, select the one with the smallest number of suggestion
        if res:
            min_set = min(res, key=len)[0]
            relevant_frequent_sets.append(min_set)
            suggestion.extend(min_set)


    suggestion = __generate_suggestion(suggestion, airports)

    return { 'relevant_frequent_sets': relevant_frequent_sets, 'iatas': suggestion }
