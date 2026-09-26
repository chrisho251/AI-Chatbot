"""Load test for the target of 10 concurrent students. Owned by Lane D.

Each simulated student sends a question to the gateway ask endpoint and reads the answer stream to
the end. Locust reports the time until the stream ends and the failures. Latency to the first token
and throughput come from the Performance dashboard, which records them in the api service.
Run it with uvx locust and this file against a stack with the gpu profile, 10 users, and the
gateway address as host. LOAD_TEST_TOKEN holds the bearer token of a test student from Keycloak.
"""

import os
import random

from locust import HttpUser, between, task

QUESTIONS = (
    "How do I compute a 95 percent confidence interval for a mean?",
    "What is the difference between a t test and a z test?",
    "How do I read a p value in a regression output?",
    "Now do the same with a sample of 40 values.",
)


class Student(HttpUser):
    wait_time = between(5, 15)

    @task
    def ask(self) -> None:
        headers = {"authorization": f"Bearer {os.environ['LOAD_TEST_TOKEN']}"}
        form = {"question": random.choice(QUESTIONS)}
        with self.client.post(
            "/v1/ask", data=form, headers=headers, stream=True, catch_response=True, name="ask"
        ) as response:
            for _line in response.iter_lines():
                pass
            if response.status_code != 200:
                response.failure(f"status {response.status_code}")
