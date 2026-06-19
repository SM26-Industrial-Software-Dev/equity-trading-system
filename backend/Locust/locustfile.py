from locust import HttpUser, task, between

class EquityTradingUser(HttpUser):
    wait_time = between(1, 3)

    @task(3) # The '3' makes it 3x more likely to run this task
    def load_docs(self):
        self.client.get("/docs")

    @task(2)
    def check_positions(self):
        # This will likely return a 401, but it generates awesome error rate metrics!
        self.client.get("/positions") 

    @task(1)
    def attempt_login(self):
        self.client.post("/login", json={"username": "test", "password": "password"})
