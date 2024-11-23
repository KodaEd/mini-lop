import random
import struct
import os

class HavocMutator:
    def __init__(self, max_mutations=6):
        self.max_mutations = max_mutations
        
        self.INTERESTING_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
        self.INTERESTING_16 = [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
        self.INTERESTING_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]
    
    def mutate(self, conf, seed, queue=None):
        """
        Main mutation function with splice support.
        queue: List of all available seeds
        """
        # Decide whether to do splice mutation (15% chance)
        if queue and len(queue) > 1 and random.random() < 0.15:
            data = self._splice_mutation(seed, queue)
        else:
            with open(seed.path, 'rb') as f:
                data = bytearray(f.read())
        
        if not data or len(data) == 0:
            return
        
        # Apply havoc mutations
        num_mutations = random.randint(1, self.max_mutations)
        for _ in range(num_mutations):
            mutation_choice = random.randint(0, 6)
            
            if mutation_choice == 0:
                self._bit_flip_mutation(data)
            elif mutation_choice == 1:
                self._byte_flip_mutation(data)
            elif mutation_choice == 2:
                self._arithmetic_mutation(data)
            elif mutation_choice == 3:
                self._interesting_value_mutation(data)
            elif mutation_choice == 4:
                self._chunk_replacement_mutation(data)
            elif mutation_choice == 5:
                if len(data) > 0:
                    pos = random.randint(0, len(data) - 1)
                    data[pos] = random.randint(0, 255)
            elif mutation_choice == 6:
                self._duplicate_chunk_mutation(data)

        with open(conf['current_input'], 'wb') as f:
            f.write(data)

    def _splice_mutation(self, seed, queue):
        """
        Implements the splice mutation operation:
        1. Select another random seed from the queue
        2. Split both seeds at random points
        3. Combine first half of current seed with second half of other seed
        """
        # Get current seed content
        with open(seed.path, 'rb') as f:
            curr_data = bytearray(f.read())
        
        if len(curr_data) < 2:  # Too small to splice
            return curr_data
            
        # Select another seed that's not the current one and exists
        other_seeds = [s for s in queue if s.path != seed.path and os.path.exists(s.path)]
        if not other_seeds:
            return curr_data
            
        other_seed = random.choice(other_seeds)
        
        try:
            with open(other_seed.path, 'rb') as f:
                other_data = bytearray(f.read())
                
            if len(other_data) < 2:  # Too small to splice
                return curr_data
                
            # Select random split points for both seeds
            curr_split = random.randint(1, len(curr_data) - 1)
            other_split = random.randint(1, len(other_data) - 1)
            
            # Combine the halves
            spliced_data = curr_data[:curr_split] + other_data[other_split:]
            
            return spliced_data
        except (IOError, OSError):  # Handle potential file access errors
            return curr_data

    def _bit_flip_mutation(self, data):
        if len(data) == 0:
            return
            
        byte_pos = random.randint(0, len(data) - 1)
        num_bits = random.choice([1, 2, 4])
        bit_offset = random.randint(0, 7 - (num_bits - 1))
        
        mask = ((1 << num_bits) - 1) << bit_offset
        original_byte = data[byte_pos]
        flipped_byte = original_byte ^ mask
        
        data[byte_pos] = flipped_byte & 0xFF

    def _bit_flip_mutation(self, data):
        if len(data) == 0:
            return
            
        # Choose random byte position
        byte_pos = random.randint(0, len(data) - 1)
        
        # Choose number of consecutive bits to flip (1, 2, or 4)
        num_bits = random.choice([1, 2, 4])
        
        # Choose random starting bit within the byte
        bit_offset = random.randint(0, 7 - (num_bits - 1))
        
        # Create and apply mask
        mask = ((1 << num_bits) - 1) << bit_offset
        original_byte = data[byte_pos]
        flipped_byte = original_byte ^ mask
        
        # Ensure the result is within valid byte range
        data[byte_pos] = flipped_byte & 0xFF

    def _byte_flip_mutation(self, data):
        if len(data) == 0:
            return
            
        num_bytes = random.choice([1, 2, 4])
        if len(data) < num_bytes:
            num_bytes = len(data)
            
        pos = random.randint(0, len(data) - num_bytes)
        
        for i in range(num_bytes):
            data[pos + i] ^= 0xFF

    def _arithmetic_mutation(self, data):
        if len(data) < 2:
            return
            
        sizes = [(2, 'h'), (4, 'i'), (8, 'q')]
        size, fmt = random.choice(sizes)
        
        if len(data) < size:
            return
            
        pos = random.randint(0, len(data) - size)
        
        try:
            value = struct.unpack('<' + fmt, data[pos:pos + size])[0]
            delta = random.randint(-35, 35)
            
            if random.random() < 0.5:
                value += delta
            else:
                value -= delta
                
            data[pos:pos + size] = struct.pack('<' + fmt, value)
        except struct.error:
            return

    def _interesting_value_mutation(self, data):
        if len(data) < 2:
            return
            
        sizes = [(1, self.INTERESTING_8), 
                (2, self.INTERESTING_16), 
                (4, self.INTERESTING_32)]
        size, interesting_vals = random.choice(sizes)
        
        if len(data) < size:
            return
            
        pos = random.randint(0, len(data) - size)
        value = random.choice(interesting_vals)
        
        try:
            if size == 1:
                data[pos] = value & 0xFF
            elif size == 2:
                data[pos:pos + 2] = struct.pack('<h', value)
            elif size == 4:
                data[pos:pos + 4] = struct.pack('<i', value)
        except struct.error:
            return

    def _chunk_replacement_mutation(self, data):
        if len(data) < 4:
            return
            
        chunk_size = random.randint(1, min(8, len(data) // 2))
        pos1 = random.randint(0, len(data) - chunk_size)
        pos2 = random.randint(0, len(data) - chunk_size)
        
        chunk1 = data[pos1:pos1 + chunk_size]
        chunk2 = data[pos2:pos2 + chunk_size]
        
        data[pos1:pos1 + chunk_size] = chunk2
        data[pos2:pos2 + chunk_size] = chunk1

    def _duplicate_chunk_mutation(self, data):
        if len(data) < 2:
            return
            
        chunk_size = random.randint(1, min(8, len(data)))
        src_pos = random.randint(0, len(data) - chunk_size)
        dst_pos = random.randint(0, len(data))
        
        chunk = data[src_pos:src_pos + chunk_size]
        data[dst_pos:dst_pos] = chunk

def havoc_mutation(conf, seed, queue=None):
    """
    Updated havoc_mutation function that accepts a queue parameter
    """
    mutator = HavocMutator()
    mutator.mutate(conf, seed, queue)