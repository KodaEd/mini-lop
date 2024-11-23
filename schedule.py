import random
import seed

priority_set = set()
queue_position = 0

def select_next_seed(seed_queue: list[seed.Seed], num_branches):
    # this is a dummy implementation, it just randomly selects a seed
    # TODO: implement the "favor" feature of AFL
    
    global queue_position, priority_set

    # check if there is still priority
    if len(priority_set) > 0:
        # find the next priority
        for index in range(queue_position, len(seed_queue)):
            if seed_queue[index].favored and not seed_queue[index].visited:
                priority_set.remove(index)
                return seed_queue[index]
        
    # should already exited if priority exists
    
    # find the first unvisited seed
    while queue_position < len(seed_queue) and seed_queue[queue_position].visited:
        queue_position += 1
    
    # just checking that it hasnt exited the cycle
    if queue_position < len(seed_queue):
        return seed_queue[queue_position]

    # okay now should be new cycle

    return selected


# get the power schedule (# of new test inputs to generate for a seed)
def get_power_schedule(seed):
    # this is a dummy implementation, it just returns a random number
    # TODO: implement the power schedule similar to AFL (should consider the coverage, and execution time)
    return random.randint(1, 10)

