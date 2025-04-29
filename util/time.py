import time
from time import time_ns
from typing import Callable

def now() -> int:
    return time_ns() // 1000000

def sleep(ms: int) -> None:
    time.sleep(ms / 1000)

def crloop(rate: int, f: Callable[[int], bool], ) -> None:
    t1 = now()
    it = 0
    running = True
    while running:
        running = f(it)

        t2 = now()
        rest = rate - (t2 - t1)
        if rest < 0: 
            behind = -rest
            rest = rate - behind % rate
            lost = behind + rest
            t1 += lost
            it += lost // rate
        sleep(rest)
        t1 += rate
        it += 1