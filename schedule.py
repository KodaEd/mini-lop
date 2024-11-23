import random

dictionary = {}

def select_next_seed(seed_queue):
    # this is a dummy implementation, it just randomly selects a seed
    # TODO: implement the "favor" feature of AFL
    

    selected = random.choice(seed_queue)

    return selected


# get the power schedule (# of new test inputs to generate for a seed)
def get_power_schedule(seed):
    # this is a dummy implementation, it just returns a random number
    # TODO: implement the power schedule similar to AFL (should consider the coverage, and execution time)
    return random.randint(1, 10)

