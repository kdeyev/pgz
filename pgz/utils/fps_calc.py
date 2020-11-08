from typing import List


class FPSCalc:
    def __init__(self, size: int = 100) -> None:
        self.vals: List[float] = []
        self.size = size
        self.counter: int = 0

    def push(self, value: float) -> None:
        self.counter += 1
        self.vals.append(value)
        if len(self.vals) > self.size:
            self.vals.pop(0)

    def aver(self) -> float:
        self.counter = 0
        return sum(self.vals) / len(self.vals)
