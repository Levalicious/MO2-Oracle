
def inversion(x: list[bytes]) -> set[tuple[bytes, bytes]]:
    oset: set[tuple[bytes, bytes]] = set()
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            if x[i] > x[j]:
                oset.add((x[i], x[j]))
    return oset