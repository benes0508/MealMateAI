from locust import HttpUser, task, between
import uuid


class AInterviewUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.user_id = "performance-"+str(uuid.uuid4())

        with self.client.post("/start-interview", json={
            "user_id": self.user_id,
            "mode": "written",
            "company": "Google",
            "role": "Software Engineer",
            "country": "Israel"
        }, catch_response=True) as resp:
            if resp.status_code == 200:
                question = resp.json().get("question", {})
                print(f"start interview: {question.get('slug', 'no slug')}")
                self.current_question = question.get("slug", "two-sum")
            else:
                resp.failure(f"Failed to start interview - {resp.status_code} {resp.text}")
                self.current_question = "two-sum"  # fallback

    @task
    def interview_flow(self):
        if not hasattr(self, "already_ran"):
            self.already_ran = True
            for i in range(10):
                if i%4 == 0:
                    # hint
                    with self.client.post("/get-hint", json={
                        "name": self.current_question,
                        "reason": "not understanding the question"
                    }) as resp:
                        if resp.status_code == 200:
                            print(f"good hint: {resp.json().get('hint', 'No hint provided') != 'No hint provided'}")
                        else:
                            print(f"get-hint fail : {resp.status_code} {resp.text}")
                

                if i%4 == 1:
                    # skip
                    with self.client.post("/skip-question", json={
                        "user_id": self.user_id
                    }) as resp:
                        if resp.status_code == 200:
                            question = resp.json().get("question", {})
                            print(f"skip: {question.get('slug', 'no slug')}")
                            self.current_question = question.get("slug", "two-sum")
                        else:
                            print("Failed to skip question")
                            self.current_question = "two-sum"  # fallback
                else:
                    #submit
                    with self.client.post("/submit", json={
                        "name": self.current_question,
                        "language": "python",
                        "user_code": "print('Hello World')"
                    }) as resp:
                        if resp.status_code == 200:
                            print(f"good submit: {resp.json().get('status', 'No status provided') != 'No status provided'}")
                        else:
                            print(f"submit fail : {resp.status_code} {resp.text}")

                    # give-up
                    with self.client.post("/give-up", json={
                        "slug": self.current_question,
                        "language": "python",
                        "name": self.current_question,
                        "what_was_hard": "can't solve"
                    }) as resp:
                        if resp.status_code == 200:
                            h = resp.json().get('help', 'No help provided')
                            print(f"good giveup: {h if h != 'No help provided' else False}")
                        else:
                            print(f"give-up fail : {resp.status_code} {resp.text}")

                    # next-question
                    with self.client.post("/next-question", json={
                        "user_id": self.user_id
                    }) as resp:
                        if resp.status_code == 200:
                            question = resp.json().get("question", {})
                            print(f"next: {question.get('slug', 'no slug')}")
                            self.current_question = question.get("slug", "two-sum")
                        else:
                            resp.failure("No more questions or error")
                            break
            print(f"_____\nDONE!!!")

