import sys
import signal
import itertools
import time

from fp_growth import find_frequent_itemsets
from pprint import pprint
import multiprocessing as mp

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

# Preload all transactions to memory
transactions = []
with open("./flight_transactions") as f:
    for line in f:
        trans = line.split(",")
        trans = list(set(trans))                             # Remove duplicates
        # trans = filter(lambda x: airport in x, trans)
        trans = map(lambda x: set(x.split("->")), trans)     # Do not consider direction
        trans = map(lambda x: '-'.join(x), trans)
        transactions.append(trans)
        
def timeout(func, args = (), kwds = {}, timeout = 1, default = None):
    pool = mp.Pool(processes = 1)
    result = pool.apply_async(func, args = args, kwds = kwds)
    try:
        val = result.get(timeout = timeout)
    except mp.TimeoutError:
        pool.terminate()
        return default
    else:
        pool.close()
        pool.join()
        return val

def mine_frequent_set(trans, min_sup):
    # Need to turn generator to list
    return list(find_frequent_itemsets(trans, min_sup, True))

def get_frequent_sets(airport):
    trans = filter(lambda x: airport in ' '.join(x), transactions)  # Filter out one airport
    print("Process %s of transactions for %s" % (len(transactions), airport))

    # Obscure data science voodoo
    min_sup = 20+len(trans)/10
    if min_sup > 100:
        min_sup = 100

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
            
        print("%s sets found for minimal support of %s, too many, higher support" % (len(result), min_sup))


    result.sort(key=lambda x: x[1], reverse=True)
    # pprint(result)

    # print("Done\n")
    # print("%s frequent sets found with minimal support of %s in %s transactions" % (len(result), round(min_sup, 2), len(trans)))

    return result

def get_suggestion(homes, airports):
    print '\nMatched frequent sets:'
    pairs = list(itertools.combinations(airports, 2))
    # airports = filter(lambda x: x not in homes, airports)

    res1, res2, res3 = [], [], []
    for h in homes:
        for freq, _ in get_frequent_sets(h):
            counter = 0

            for s in freq:
                for a1, a2 in pairs:
                    if a1 in s and a2 in s:
                        counter += 1
                        break

            if counter > len(freq)-1:
                res1.append(freq)
            if counter > len(freq)-2:
                res2.append(freq)
            if counter > len(freq)-3:
                res2.append(freq)
                print freq

    return min(filter(lambda x: len(x) != 0, (res1, res2, res3)), key=len)
