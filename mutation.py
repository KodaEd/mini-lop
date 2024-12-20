import random
import struct
import os

class SpliceMutator:
    def __init__(self, havoc_mutator=None):
        self.havoc_mutator = havoc_mutator or HavocMutator()
        
    def mutate(self, seed, queue, conf):
        # Get list of other valid seeds (excluding current seed)
        other_seeds = [s for s in queue if s.path != seed.path and os.path.exists(s.path)]
        if not other_seeds:
            return None
            
        # Read current seed data
        try:
            with open(seed.path, 'rb') as f:
                data1 = bytearray(f.read())
        except (IOError, OSError):
            return None
            
        if len(data1) < 2:  # Need at least 2 bytes to splice
            return None
            
        # Choose just one other seed randomly
        other_seed = random.choice(other_seeds)
        try:
            with open(other_seed.path, 'rb') as f:
                data2 = bytearray(f.read())
                
            if len(data2) < 2:
                return None
                
            # Split both files at their midpoints
            split1 = len(data1) // 2
            split2 = len(data2) // 2
            
            # Create new test input by combining first half of data1 with second half of data2
            spliced_data = data1[:split1] + data2[split2:]
            
            # Write spliced data to temporary file for havoc mutation
            with open(conf['current_input'], 'wb') as f:
                f.write(spliced_data)
            
            # Apply havoc mutation to the spliced data
            temp_seed = type('Seed', (), {'path': conf['current_input']})
            self.havoc_mutator.mutate(conf, temp_seed, queue)
            
            # Read back the havoc-mutated data
            with open(conf['current_input'], 'rb') as f:
                mutated_data = bytearray(f.read())
                
            return mutated_data
                
        except (IOError, OSError):
            return None

class DeterministicMutator:
    def __init__(self):
        self.INTERESTING_8 = [-128, -1, 0, 1, 16, 32, 64, 100, 127]
        self.INTERESTING_16 = [-32768, -129, 128, 255, 256, 512, 1000, 1024, 4096, 32767]
        self.INTERESTING_32 = [-2147483648, -100663046, -32769, 32768, 65535, 65536, 100663045, 2147483647]
        self.min_ratio = 0.05

    def mutate(self, conf, seed, queue=None, mutation_type=None):
        with open(seed.path, 'rb') as f:
            data = bytearray(f.read())
            
        if not data:
            return None

        if mutation_type is None:
            mutations = ['flip', 'bit_flip', 'splice', 'byte_flip', 'arithmetic', 
                        'interesting_value', 'chunk_replacement', 'duplicate_chunk']
        else:
            mutations = [mutation_type]
            
        for mutation in mutations:
            if mutation == 'flip':
                data = self._flip_mutation(data)
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
            elif mutation == 'splice' and queue:
                spliced = self._splice_mutation(data, seed, queue)
                if spliced:
                    data = spliced

        with open(conf['current_input'], 'wb') as f:
            f.write(data)
            
        return data

    def _single_bit_flip(self, data):
        if not data:
            return data
        pos = random.randint(0, len(data) - 1)
        bit = random.randint(0, 7)
        data[pos] ^= (1 << bit)
        return data

    def _single_byte_flip(self, data):
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

    def _flip_mutation(self, data):
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

class HavocMutator:
    def __init__(self, max_mutations=6):
        self.max_mutations = max_mutations
        self.deterministic_mutator = DeterministicMutator()
        
    def mutate(self, conf, seed, queue=None):
        mutations = ['bit_flip', 'byte_flip', 'arithmetic', 
                    'interesting_value', 'chunk_replacement', 'duplicate_chunk']
        
        num_mutations = random.randint(1, self.max_mutations)
        
        with open(seed.path, 'rb') as f:
            data = bytearray(f.read())
        
        temp_path = conf['current_input']
        temp_conf = {'current_input': temp_path}
        temp_seed = type('Seed', (), {'path': temp_path})
        
        with open(temp_path, 'wb') as f:
            f.write(data)
            
        for _ in range(num_mutations):
            mutation_type = random.choice(mutations)
            result = self.deterministic_mutator.mutate(temp_conf, temp_seed, queue, mutation_type)
            if result is None:
                break
                
        return True

def havoc_mutation(conf, seed, queue=None):
    strategy_roll = random.random()
    mutator = DeterministicMutator()
    havoc = HavocMutator()
    splice = SpliceMutator(havoc)
    
    if strategy_roll < 0.90:  # 90% chance for single deterministic mutation
        weighted_mutations = [
            ('flip', 4),
            ('splice', 5 if queue and len(queue) > 1 else 0),
            ('splice_havoc', 1 if queue and len(queue) > 1 else 0),
            ('bit_flip', 1),
            ('byte_flip', 1),
            ('arithmetic', 1),
            ('interesting_value', 1),
            ('chunk_replacement', 1),
            ('duplicate_chunk', 1)
        ]
        
        possible_mutations = [m for m in weighted_mutations if m[1] > 0]
        total_weight = sum(m[1] for m in possible_mutations)
        
        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for mutation_type, weight in possible_mutations:
            current_weight += weight
            if r <= current_weight:
                if mutation_type == 'splice_havoc':
                    # Handle splice mutation
                    result = splice.mutate(seed, queue, conf)
                    if result is None:
                        # If splice fails, return None or could try havoc
                        return None
                    return result
                else:
                    return mutator.mutate(conf, seed, queue, mutation_type)
    
    else:  # 10% chance for havoc
        return havoc.mutate(conf, seed, queue)