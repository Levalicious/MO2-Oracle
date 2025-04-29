from plugin_oracle.util.ml.bernoulli import Bernoulli

class Mod:
    def __init__(self, hash: bytes) -> None:
        self.hash: bytes = hash
        self.hind: int = int.from_bytes(hash, 'little')
        self.name: str = self.hash.hex()
        self.dist: Bernoulli = Bernoulli()
    
    def __hash__(self) -> int:
        return self.hash.__hash__()