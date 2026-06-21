# 📈 Equity Trading App: Developer Onboarding Guide

Welcome to the Equity Trading App repository! This guide will help you operate our local Kubernetes (k3d) environment.

Our infrastructure strictly follows a **GitOps** methodology. Every component of our infrastructure is declarative and version-controlled. You **do not** need to manually modify Kubernetes manifests or understand Helm to run this locally; you just need to use the provided scripts.

---

## 🚀 1. Activating the Observability Stack

To conserve local system resources, the comprehensive observability stack (Loki, Promtail, Prometheus, Grafana) is disabled by default.

To toggle the logging and metrics environment, run the provided bash scripts from the **root of the repository**:

* **Enable Logging and Monitoring:**

    ```bash
    ./logs_up.sh
    ```

* **Disable Logging and Monitoring:**

    ```bash
    ./logs_down.sh
    ```

> ⚠️ **IMPORTANT: BE PATIENT!** > After running `./logs_up.sh`, it takes about **1 to 2 minutes** for the GitOps controllers to reconcile, pull the necessary images, initialize the Loki database, and start the Grafana web server. If the page doesn't load immediately, grab a coffee and wait for the pods to spin up!

---

## 📊 2. Accessing & Using Grafana

Once the cluster is up, Grafana is accessible via your browser. Because of how our local Traefik load balancer is configured, you must specify **port 8080**.

* **URL:** `http://grafana.localhost:8080`
* **Username:** `admin`
* **Password:** `Rust!`

Navigate to **Dashboards -> FastAPI Developer Dashboard** (or k3d Stats) to view the live log feeds and cluster statistics.

### Reading The Dashboard

Our dashboard features both live application logs and core infrastructure metrics side-by-side:

* **Active FastAPI Nodes:** Displays the true, currently running pod count requested by the HPA.
* **FastAPI Total CPU Utilization (%):** Displays the raw CPU percentage relative to the resource requests. *(Note: We use the `irate()` function here, meaning this instantly reflects high-traffic spikes without artificial smoothing.)*
* **CPU Usage per Pod (Cores):** A live line-graph tracking exactly which containers are absorbing traffic.

*(Note: When you first generate a log locally, it might take 5–10 seconds for Promtail to detect the new file in the host-mapped volume and push it to Grafana. Subsequent logs will appear instantly).*

---

## 📝 3. Writing Your Logs (Strict Conventions)

Our logging pipeline uses Promtail (via host-mapped volume mounts) to watch the `logs/` folder at the root of this repository. To ensure your logs appear correctly on the dashboard panels, you **must** follow these two rules:

### Rule 1: The Folder Structure (The `app` tag)

You must use one of the pre-configured subfolders inside the root `logs/` directory. Promtail reads this folder name and turns it into the `{app}` label in Grafana.

✅ **ALLOWED FOLDERS:**

* `logs/FastAPI/app.log`
* `logs/Postgres/db.log`
* `logs/Redis/cache.log`
* `logs/Streamlit/ui.log`

❌ **DO NOT DO THIS:**

* `logs/fastapi_app.log` *(Will not get tagged correctly!)*
* `logs/my_custom_folder/app.log` *(Will not show up on the dashboard!)*

### Rule 2: The Log Format (The `level` tag)

Our pipeline uses Regex to extract the severity level from your log text. Your logs **must** start with a bracketed timestamp, followed by a space, followed by an uppercase level (`INFO`, `WARNING`, `ERROR`), and a colon.

**Required Format:**
`[YYYY-MM-DD HH:MM:SS] LEVEL: Message`

**Example (Python Logbook):**
If you are working on the FastAPI or Streamlit services, configure your FileHandler format string exactly like this:

```python
import logbook
from pathlib import Path

# 1. Point to your specific subfolder!
LOG_FILE = Path("../../logs/FastAPI/app.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# 2. Use this exact format string
file_handler = logbook.FileHandler(
    LOG_FILE, 
    level='INFO', 
    format_string='[{record.time:%Y-%m-%d %H:%M:%S}] {record.level_name}: {record.channel}: {record.message}'
)
file_handler.push_application()
```

---

## 🏗 4. Technical Architecture Overview

* **Backend:** FastAPI (Python) - Configured with aggressive Horizontal Pod Autoscaling (HPA).
* **Frontend:** Streamlit.
* **Data Layer:** Redis (Streams for high-speed ingestion) and PostgreSQL (persistent records).
* **Workers:** Rust (`trade-writer.rs`) for compiled-level Redis-to-PostgreSQL synchronization.

---
---

## 🦊 5. Important Notice for Max: GitOps and Locust Load Testing

Hey Max! As you configure or execute load tests against the FastAPI backend using Locust, please adhere to our architectural standards.

### GitOps Principles

We utilize **Flux** for GitOps operations. The `main` branch of this GitHub repository is the absolute source of truth for the cluster's state. Any manual, imperative changes (e.g., using `kubectl edit` or temporary UI workarounds) will be detected as configuration drift and immediately overwritten by Flux controllers.

We enforce a **Fork-and-PR** workflow:

1. Fork the repository.
2. Implement declarative changes to the source code or manifests.
3. Submit a Pull Request.

### Updating and Testing `locustfile.py`

Locust is deployed via our GitOps pipeline and is strictly maintained at 1 replica. The load-testing script (`locustfile.py`) is injected into the Locust Pod via a dynamically generated ConfigMap.

To update and test your load-testing scripts locally without conflicting with Flux, utilize the provided deployment script:

1. **Modify the Script:** Make your required changes to `backend/Locust/locustfile.py`.
2. **Execute the Reload Script:** From the repository root, run:

    ```bash
    ./locust_reload.sh
    ```

3. **Validate:** This script synchronizes your local code changes with the cluster and forces a rollout of the Locust Pod, allowing you to immediately validate your updated load profiles.
