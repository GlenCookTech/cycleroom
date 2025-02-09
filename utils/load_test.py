from locust import HttpUser, task, between

class GearLoadTest(HttpUser):
    wait_time = between(1, 3)

    @task
    def get_gear(self):
        self.client.get("/gear")
