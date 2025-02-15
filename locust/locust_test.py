from locust import HttpUser, task, between
import random
import json

class UserBehavior(HttpUser):
    wait_time = between(1, 2)
    
    def load_domains_from_file(self):
        """Load domains from the test file"""
        try:
            with open('./testdata/domain_test.txt', 'r') as file:
                domains = [line.strip() for line in file if line.strip()]
            print(f"Loaded {len(domains)} domains from file")
            return domains
        except Exception as e:
            print(f"Error loading domains: {e}")
            return []
        
    def on_start(self):
        """Setup and login before starting tests"""
        self.username = f"locust_user_{random.randint(1,500)}"
        self.client.post("/BEregister", data={
            "username": self.username,
            "password": "password"
        })
        self.login()
        self.domains = self.load_domains_from_file()
        print(f"User {self.username} initialized with {len(self.domains)} domains")
    
    def login(self):
        response = self.client.post("/BElogin", data={
            "username": self.username,
            "password": "password"
        })

    @task
    def single_domain_check(self):
        """Test checking a single domain"""
        print(f"User {self.username} starting single check of {self.domains[0]}")
        response = self.client.post("/BEadd_domain", json={
            "domain": self.domains[0]
        })
        print(f"Single check completed for {self.username}. Status: {response.status_code}")

    # @task
    # def bulk_domain_check(self):
    #     """Test checking all domains from file"""
    #     print(f"User {self.username} starting bulk check of {len(self.domains)} domains")
    #     response = self.client.post("/BEbulk_upload", json={
    #         "domains": self.domains
    #     })
    #     print(f"Bulk check completed for {self.username}. Status: {response.status_code}")