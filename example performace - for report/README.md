# AInterview – Performance Testing with Locust

A concise guide to run load/performance tests using **Locust**.

---

## Prerequisites
- Python 3.10+
- Install Locust:
  ```bash
  pip install locust
  ```
- API Gateway running on cloud or locally at `http://127.0.0.1:8003`

  Quick check:
  ```bash
  curl <api_gateway_url>/health
  
  curl http://127.0.0.1:8003/health
  ```

---

## Files
- Place `locustfile.py` in the project root (or any path you prefer).
-   You can pass the host/url via **CLI** (recommended):
    ```bash
    --host=http://127.0.0.1:8003
    ```
    ...or set the host in code:
    ```python
    # inside locustfile.py
    class AInterviewUser(HttpUser):
        host = "http://127.0.0.1:8003"
    ```


---

## Running with the Web UI
1. Launch Locust:
   ```bash
   locust -f locustfile.py --host=http://127.0.0.1:8003
   ```
2. Open **http://localhost:8089** in your browser.
3. Fill in:
   - **Number of users to simulate** – total concurrent users.
   - **Spawn rate** – how many users to start per second.
4. Click **Start swarming** and observe results.
5. You should get "DONE!!!" msg for every virtual user that finished. Once they all did you can see the results at the browser or press <kbd>Ctrl+C</kbd> to get CLI like in the JPEG files in this folder.

---

## Headless runs (for scripts/CI) + CSV output
Examples:
```bash
# 1) 2 minutes, 5 users, spawn rate 1, export CSV
locust -f locustfile.py --host=http://127.0.0.1:8003 \
  --headless -u 5 -r 1 -t 2m --csv=run_u5

# 2) 2 minutes, 10 users
locust -f locustfile.py --host=http://127.0.0.1:8003 \
  --headless -u 10 -r 2 -t 2m --csv=run_u10
```
CSV files (e.g., `run_u5_stats.csv`) will be written to the current directory.

---

## Tips & Troubleshooting
- Ensure `--host` is set and up; otherwise, requests will fail.
- The Locust script creates a **unique `user_id` per virtual user**.
- To reduce external AI traffic, use a **minimal interview flow** or a local **AI stub** for `/get-hint`/`/submit`/`/give-up` during performance tests.


---
## Good luck!
