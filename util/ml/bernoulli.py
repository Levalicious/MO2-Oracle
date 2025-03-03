from math import gcd, log2

class Bernoulli:
    def __init__(self) -> None:
        self.C = [0] * 2
        self.P = [0.5] * 2
        self.H: float = -1

    def observe(self, v: bool) -> None:
        self.C[0] += v
        self.C[1] += 1
        self.update()
    
    def update(self) -> None:
        if self.P[1] == 0:
            return
        self.P[0] = self.C[0] / self.C[1]
        self.P[1] = 1 - self.P[0]
        self.H = -sum(p * log2(p) for p in self.P if p > 0)