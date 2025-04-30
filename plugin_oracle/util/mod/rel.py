from plugin_oracle.util.ml.bernoulli import Bernoulli

class Relation:
    def __init__(self) -> None:
        self.dist: Bernoulli = Bernoulli()