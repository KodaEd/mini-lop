class Seed:
    def __init__(self, path, seed_id, coverage, exec_time, file_size):
        self.path = path
        self.seed_id = seed_id
        self.coverage = coverage
        self.exec_time = exec_time
        self.visited = True
        self.file_size = file_size
        # by default, a seed is not marked as favored
        self.favored = 0

    def mark_visited(self):
        self.visited = True

    def unmark_visited(self):
        self.visited = False


    def mark_favored(self):
        self.favored = 1

    def unmark_favored(self):
        self.favored = 0
