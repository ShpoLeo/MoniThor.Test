from locust import HttpUser, TaskSet, task, between
import json
import random

class UserBehavior(TaskSet):
    wait_time = between(1, 2)
    def on_start(self):
        """Executed when a Locust user starts (e.g., logs in)."""
        self.username = f"locust_user_{random.randint(1000, 9999)}"
        self.password = "password"
        self.login()

    def login(self):
        response = self.client.post("/BElogin", json={
            "username": self.username,
            "password": self.password
        })
        if response.status_code == 200:
            print("Login successful")
        else:
            print("Login failed")

    @task
    def add_new_domain(self):
        domain_name = "example.com"
        response = self.client.get(f"/BEadd_domain/{domain_name}/{self.username}")
        print(f"Add Domain Response: {response.status_code} - {response.text}")

    @task
    def upload_file(self):
        filename = "../testdata/Domains_for_upload.txt"
        response = self.client.get(f"/BEbulk_upload/{filename}/{self.username}")
        print(f"Bulk Upload Response: {response.status_code} - {response.text}")

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    
