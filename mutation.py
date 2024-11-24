import random
import struct
import os

class DeterministicMutator:
    def __init__(self):
        self.INTERESTING_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
        self.INTERESTING_16 = [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
        self.INTERESTING_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]
        self.min_ratio = 0.05

    def mutate(self, conf, seed, queue=None, mutation_type=None):
        """
        Performs a single mutation of specified type, or one of each type if None.
        """
        with open(seed.path, 'rb') as f:
            data = bytearray(f.read())
            
        if not data:
            return None

        if mutation_type is None:
            # Apply each mutation type once
            mutations = ['trim', 'splice', 'bit_flip', 'byte_flip', 'arithmetic', 
                        'interesting_value', 'chunk_replacement', 'duplicate_chunk']
        else:
            mutations = [mutation_type]
            
        for mutation in mutations:
            if mutation == 'trim':
                data = self._trim_mutation(data)
            elif mutation == 'splice' and queue:
                spliced = self._splice_mutation(data, seed, queue)
                if spliced:
                    data = spliced
            elif mutation == 'bit_flip':
                data = self._single_bit_flip(data)
            elif mutation == 'byte_flip':
                data = self._single_byte_flip(data)
            elif mutation == 'arithmetic':
                data = self._single_arithmetic(data)
            elif mutation == 'interesting_value':
                data = self._single_interesting_value(data)
            elif mutation == 'chunk_replacement':
                data = self._single_chunk_replacement(data)
            elif mutation == 'duplicate_chunk':
                data = self._single_chunk_duplicate(data)

        with open(conf['current_input'], 'wb') as f:
            f.write(data)
            
        return data

    def _single_bit_flip(self, data):
        """Single bit flip at random position"""
        if not data:
            return data
        pos = random.randint(0, len(data) - 1)
        bit = random.randint(0, 7)
        data[pos] ^= (1 << bit)
        return data

    def _single_byte_flip(self, data):
        """Single byte flip with random size"""
        if not data:
            return data
        size = random.choice([1, 2, 4])
        if len(data) < size:
            size = len(data)
        pos = random.randint(0, len(data) - size)
        for i in range(size):
            data[pos + i] ^= 0xFF
        return data

    def _single_arithmetic(self, data):
        """Single arithmetic operation at random position"""
        if len(data) < 2:
            return data
        sizes = [(2, 'h'), (4, 'i'), (8, 'q')]
        size, fmt = random.choice(sizes)
        if len(data) < size:
            return data
        
        pos = random.randint(0, len(data) - size)
        try:
            value = struct.unpack('<' + fmt, data[pos:pos + size])[0]
            delta = random.randint(-35, 35)
            if delta != 0:
                new_value = value + delta
                data[pos:pos + size] = struct.pack('<' + fmt, new_value)
        except struct.error:
            pass
        return data

    def _single_interesting_value(self, data):
        """Single interesting value insertion"""
        if not data:
            return data
        interesting_sets = [
            (1, self.INTERESTING_8),
            (2, self.INTERESTING_16),
            (4, self.INTERESTING_32)
        ]
        size, values = random.choice(interesting_sets)
        if len(data) < size:
            return data
            
        pos = random.randint(0, len(data) - size)
        value = random.choice(values)
        try:
            if size == 1:
                data[pos] = value & 0xFF
            elif size == 2:
                data[pos:pos + 2] = struct.pack('<h', value)
            elif size == 4:
                data[pos:pos + 4] = struct.pack('<i', value)
        except struct.error:
            pass
        return data

    def _single_chunk_replacement(self, data):
        """Single chunk replacement"""
        if len(data) < 4:
            return data
        chunk_size = random.choice([2, 4, 8])
        if len(data) < chunk_size * 2:
            return data
            
        pos1 = random.randint(0, len(data) - chunk_size)
        pos2 = random.randint(0, len(data) - chunk_size)
        
        chunk1 = data[pos1:pos1 + chunk_size]
        chunk2 = data[pos2:pos2 + chunk_size]
        data[pos1:pos1 + chunk_size] = chunk2
        data[pos2:pos2 + chunk_size] = chunk1
        return data

    def _single_chunk_duplicate(self, data):
        """Single chunk duplication"""
        if len(data) < 2:
            return data
        chunk_size = random.choice([1, 2, 4, 8])
        if len(data) < chunk_size:
            return data
            
        src_pos = random.randint(0, len(data) - chunk_size)
        dst_pos = random.randint(0, len(data))
        
        chunk = data[src_pos:src_pos + chunk_size]
        data[dst_pos:dst_pos] = chunk
        return data

    def _trim_mutation(self, data):
        """Simplified trim that removes one chunk"""
        if len(data) < 4:
            return data
        
        chunk_size = random.choice([1, 2, 4, 8, 16, 32, 64, 128])
        if len(data) < chunk_size * 2:
            return data
            
        pos = random.randint(0, len(data) - chunk_size)
        if len(data) - chunk_size < len(data) * self.min_ratio:
            return data
            
        return data[:pos] + data[pos + chunk_size:]

    def _splice_mutation(self, data, seed, queue):
        """Simple splice between two inputs"""
        if len(data) < 2:
            return None
            
        other_seeds = [s for s in queue if s.path != seed.path and os.path.exists(s.path)]
        if not other_seeds:
            return None
            
        other_seed = random.choice(other_seeds)
        try:
            with open(other_seed.path, 'rb') as f:
                other_data = bytearray(f.read())
                
            if len(other_data) < 2:
                return None
                
            curr_split = random.randint(1, len(data) - 1)
            other_split = random.randint(1, len(other_data) - 1)
            
            return data[:curr_split] + other_data[other_split:]
        except (IOError, OSError):
            return None

class HavocMutator:
    def __init__(self, max_mutations=6):
        self.max_mutations = max_mutations
        self.deterministic_mutator = DeterministicMutator()
        
    def mutate(self, conf, seed, queue=None):
        """
        Applies multiple random mutations one after another
        """
        mutations = ['bit_flip', 'byte_flip', 'arithmetic', 
                    'interesting_value', 'chunk_replacement', 'duplicate_chunk']
        
        # Pick how many mutations to apply
        num_mutations = random.randint(1, self.max_mutations)
        
        # Start with original data
        with open(seed.path, 'rb') as f:
            data = bytearray(f.read())
        
        # Create temporary file for intermediate mutations
        temp_path = conf['current_input']
        temp_conf = {'current_input': temp_path}
        temp_seed = type('Seed', (), {'path': temp_path})
        
        # Write initial data
        with open(temp_path, 'wb') as f:
            f.write(data)
            
        # Apply random mutations sequentially
        for _ in range(num_mutations):
            mutation_type = random.choice(mutations)
            result = self.deterministic_mutator.mutate(temp_conf, temp_seed, queue, mutation_type)
            if result is None:
                break
                
        return True

def havoc_mutation(conf, seed, queue=None):
    """
    Main mutation function with priorities:
    - For deterministic (90%): Pick one of trim, splice, or single deterministic mutation
    - For havoc (10%): Apply multiple random deterministic mutations
    """
    strategy_roll = random.random()
    mutator = DeterministicMutator()
    
    if strategy_roll < 0.90:  # 90% chance for single deterministic mutation
        # First try trim if not done
        if not hasattr(seed, 'trimmed'):
            seed.trimmed = True
            return mutator.mutate(conf, seed, queue, 'trim')
            
        # Then try splice if possible
        if queue and len(queue) > 1 and random.random() < 0.33:  # 33% chance for splice when possible
            return mutator.mutate(conf, seed, queue, 'splice')
            
        # Otherwise pick one deterministic mutation
        mutations = ['bit_flip', 'byte_flip', 'arithmetic', 
                    'interesting_value', 'chunk_replacement', 'duplicate_chunk']
        selected_mutation = random.choice(mutations)
        return mutator.mutate(conf, seed, queue, selected_mutation)
    
    else:  # 10% chance for havoc
        havoc = HavocMutator()
        return havoc.mutate(conf, seed, queue)