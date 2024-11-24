import random
import seed
import os
from typing import List  # Import List from typing module


priority_set = set()
queue_position = 0

# this is AI GENERATED CODE from claude
def sort_seeds(seed_queue: List[seed.Seed]):
    def seed_sort_key(seed: seed.Seed):
        # Create tuple for sorting
        return (-seed.favored, seed.exec_time * seed.file_size, seed.seed_id)
    
    # Sort the queue in-place using the custom key
    seed_queue.sort(key=seed_sort_key)
    return seed_queue

def select_next_seed(seed_queue: List[seed.Seed], num_branches):
    global queue_position, priority_set

    # Check if we need to start a new cycle
    if queue_position >= len(seed_queue):
        # Reset for new cycle
        priority_set.clear()
        queue_position = 0
        
        for seed in seed_queue:
            seed.unmark_visited()
            if seed.coverage >= num_branches:
                priority_set.add(seed)
                seed.mark_favored()
            else:
                seed.unmark_favored()
        
        seed_queue = sort_seeds(seed_queue)

    # 10% chance to take a random unvisited seed
    if random.random() < 0.1:
        # Get quick count of unvisited seeds
        unvisited_indices = [i for i in range(queue_position, len(seed_queue)) 
                           if not seed_queue[i].visited]
        if unvisited_indices:
            idx = random.choice(unvisited_indices)
            seed_queue[idx].mark_visited()
            return seed_queue[idx]

    # 90% chance: use the strategy
    # First check priority queue
    if priority_set:
        for i in range(queue_position, len(seed_queue)):
            if seed_queue[i].favored and not seed_queue[i].visited:
                priority_set.remove(i)
                seed_queue[i].mark_visited()
                queue_position = i + 1
                return seed_queue[i]

    # Then find next unvisited seed
    while queue_position < len(seed_queue):
        if not seed_queue[queue_position].visited:
            seed_queue[queue_position].mark_visited()
            selected = seed_queue[queue_position]
            queue_position += 1
            return selected
        queue_position += 1

    # If we somehow got here (shouldn't happen), restart cycle
    queue_position = len(seed_queue)  # This will trigger new cycle next time
    return seed_queue[0]


def get_power_schedule(seed, total_cal_us=0, total_cal_cycles=0, total_bitmap_size=0, total_bitmap_entries=0):
    # Base performance score
    perf_score = 100
    
    # Calculate averages
    if total_cal_cycles == 0:
        avg_exec_us = seed.exec_time  # Use seed's own time if no average available
    else:
        avg_exec_us = total_cal_us / total_cal_cycles
        
    if total_bitmap_entries == 0:
        avg_bitmap_size = seed.coverage  # Use seed's own coverage if no average available
    else:
        avg_bitmap_size = total_bitmap_size / total_bitmap_entries

    # Adjust score based on execution speed
    if seed.exec_time * 0.1 > avg_exec_us:
        perf_score = 10
    elif seed.exec_time * 0.25 > avg_exec_us:
        perf_score = 25
    elif seed.exec_time * 0.5 > avg_exec_us:
        perf_score = 50
    elif seed.exec_time * 0.75 > avg_exec_us:
        perf_score = 75
    elif seed.exec_time * 4 < avg_exec_us:
        perf_score = 300
    elif seed.exec_time * 3 < avg_exec_us:
        perf_score = 200
    elif seed.exec_time * 2 < avg_exec_us:
        perf_score = 150

    # Adjust score based on bitmap size (coverage)
    if seed.coverage * 0.3 > avg_bitmap_size:
        perf_score *= 3
    elif seed.coverage * 0.5 > avg_bitmap_size:
        perf_score *= 2
    elif seed.coverage * 0.75 > avg_bitmap_size:
        perf_score *= 1.5
    elif seed.coverage * 3 < avg_bitmap_size:
        perf_score *= 0.25
    elif seed.coverage * 2 < avg_bitmap_size:
        perf_score *= 0.5
    elif seed.coverage * 1.5 < avg_bitmap_size:
        perf_score *= 0.75

    # For handicap and depth adjustments, we'll need to add these fields to your Seed class
    # For now, we'll use a simplified version
    
    HAVOC_MAX_MULT = 200
    
    # Scale the perf_score to actual number of iterations
    # The division by 100 is to normalize the perf_score which started at base 100
    power = min(int((perf_score / 100)), HAVOC_MAX_MULT)
    
    # Ensure we always do at least one iteration
    return max(power, 1)

def calculate_statistics(seed_queue):
    total_cal_us = sum(seed.exec_time for seed in seed_queue)
    total_cal_cycles = len(seed_queue)
    total_bitmap_size = sum(seed.coverage for seed in seed_queue)
    total_bitmap_entries = len(seed_queue)
    
    return (total_cal_us, total_cal_cycles, total_bitmap_size, total_bitmap_entries)

