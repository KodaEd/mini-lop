I used 8 types of mutations, i just named it all deterministic without it actually being, just easier to diff from havoc.

['trim', 'splice', 'bit_flip', 'byte_flip', 'arithmetic', 'interesting_value', 'chunk_replacement', 'duplicate_chunk']

In the deterministic class, the trim and splice is weighted higher to have a better chance of being picked as those are "more effective". These mutations only change a single part of the file.

THere is only a 10% chance of using a havoc mutation, and then randomly apply mutations from the deterministic class and hope for some change.

To be frank alot of this was generated using piepie but under my supervision as it was alot of boilerplate code. The main logic was made by me though.

