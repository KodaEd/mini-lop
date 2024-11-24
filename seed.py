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

    def __str__(self):
        # Create status indicators
        status = []
        if self.favored:
            status.append("favored")
        if self.visited:
            status.append("visited")
        
        # Format execution time to be readable (in milliseconds)
        exec_time_ms = f"{self.exec_time:.2f}ms"
        
        # Format file size to be readable (in bytes/KB/MB as appropriate)
        if self.file_size < 1024:
            size_str = f"{self.file_size}B"
        elif self.file_size < 1024 * 1024:
            size_str = f"{self.file_size/1024:.1f}KB"
        else:
            size_str = f"{self.file_size/(1024*1024):.1f}MB"
        
        # Build the string representation
        return (f"Seed[{self.seed_id}] "
                f"path='{self.path}' "
                f"size={size_str} "
                f"exec_time={exec_time_ms} "
                f"coverage={self.coverage} "
                f"status=[{', '.join(status)}]")
