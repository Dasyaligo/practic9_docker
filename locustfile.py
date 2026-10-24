import os
import random
from faker import Faker
from locust import HttpUser, TaskSet, SequentialTaskSet, task, between

fake = Faker("ru_RU")
BASE_CAR_IDS = [1, 2, 3, 4, 5, 6, 7]

class CatalogTasks(TaskSet):

    @task(5)
    def health_check(self):
        self.client.get("/api/health", name="GET /api/health")

    @task(5)
    def list_cars(self):
        self.client.get("/api/cars", name="GET /api/cars")

    @task(5)
    def search_cars(self):
        query = random.choice(["Class", "GL", "E", "S", "V", "AMG"])
        self.client.get("/api/cars", params={"q": query}, name="GET /api/cars?q=...")

    @task(5)
    def sort_cars(self):
        order = random.choice(["asc", "desc"])
        self.client.get("/api/cars", params={"order": order}, name="GET /api/cars?order=...")

    @task(5)
    def car_details(self):
        car_id = random.choice(BASE_CAR_IDS)
        with self.client.get(f"/api/cars/{car_id}", name="GET /api/cars/[id]", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Ожидался статус 200, получен {response.status_code}")

    @task(5)
    def get_stats(self):
        self.client.get("/api/stats", name="GET /api/stats")

    @task(1)
    def create_order(self):
        car_id = random.choice(BASE_CAR_IDS)
        payload = {
            "car_id": car_id,
            "quantity": 1,
            "customer": {
                "name": fake.name(),
                "email": fake.email(),
                "phone": fake.phone_number()
            }
        }
        with self.client.post("/api/orders", json=payload, name="POST /api/orders", catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"Неожиданный статус: {response.status_code}")

    @task(1)
    def submit_feedback(self):
        payload = {
            "name": fake.name(),
            "message": fake.sentence(nb_words=8),
            "rating": random.randint(3, 5)
        }
        with self.client.post("/api/feedback", json=payload, name="POST /api/feedback", catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Неожиданный статус: {response.status_code}")


class SequentialBrowseFlow(SequentialTaskSet):
    

    @task
    def open_catalog(self):
        self.client.get("/api/cars", name="SEQ GET /api/cars")

    @task
    def open_random_car(self):
        car_id = random.choice(BASE_CAR_IDS)
        self.client.get(f"/api/cars/{car_id}", name="SEQ GET /api/cars/[id]")

    @task
    def read_stats(self):
        self.client.get("/api/stats", name="SEQ GET /api/stats")


class AutoSalonUser(HttpUser):
    host = os.getenv("TARGET_HOST", "http://127.0.0.1:5000")
    wait_time = between(1, 3)
    tasks = {CatalogTasks: 20, SequentialBrowseFlow: 1}
