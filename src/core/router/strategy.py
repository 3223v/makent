class RoundRobinStrategy(Strategy):
    def __init__(self):
        self.index = 0

    def select(self, clients, **kwargs):
        client = clients[self.index]
        self.index = (self.index + 1) % len(clients)
        return client