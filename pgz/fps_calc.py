class FPSCalc:
    def __init__(self, size=100) -> None:
        self.vals = []
        self.size = size
        self.counter = 0

    def push(self, value):
        self.counter += 1
        self.vals.append(value)
        if len(self.vals) > self.size:
            self.vals.pop(0)

    def aver(self):
        self.counter = 0
        return sum(self.vals) / len(self.vals)
