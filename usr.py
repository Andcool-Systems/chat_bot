import time

class User:
    def __init__(self):
        self.client_id = 0
        self.last_time = time.time()

    def create_pipe(self, client_id):
        self.client_id = client_id
    