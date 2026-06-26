import time
from contextlib import contextmanager


class Timer:
    """
    Utility class for measuring execution time in milliseconds.
    Useful for pipeline profiling (ZIP processing, LLM calls, etc.)
    """

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()
        return self

    def stop(self):
        self.end_time = time.time()
        return self

    def duration_ms(self):
        if self.start_time is None or self.end_time is None:
            return 0
        return round((self.end_time - self.start_time) * 1000, 2)


# =========================================
# CONTEXT MANAGER VERSION (BEST PRACTICE)
# =========================================

@contextmanager
def timer(name: str = "block"):
    """
    Context manager for measuring execution time.
    Example usage:

    with timer("zip_extraction") as t:
        ...
    """

    start = time.time()
    yield
    end = time.time()

    duration = round((end - start) * 1000, 2)

    print(f"[TIMER] {name}: {duration} ms")