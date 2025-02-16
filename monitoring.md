from prometheus_client import start_http_server, Gauge
import time
import os

ERROR_LOG_PATH = r"C:\inetpub\logs\Error\*.txt"
ERROR_COUNT = Gauge('iis_error_count', 'Number of errors in IIS logs')

def count_errors():
    error_count = 0
    for log_file in glob.glob(ERROR_LOG_PATH):
        with open(log_file, 'r') as f:
            for line in f:
                if "error" in line.lower():  # Adjust this condition based on your log format
                    error_count += 1
    ERROR_COUNT.set(error_count)

if __name__ == '__main__':
    start_http_server(8000)  # Expose metrics on port 8000
    while True:
        count_errors()
        time.sleep(60)  # Check logs every 60 seconds
		
Prometheus yaml		
		
		scrape_configs:
  - job_name: 'iis_error_metrics'
    static_configs:
      - targets: ['<iis-server>:8000']



You need to install the prometheus_client library to create and expose metrics.

bash
Copy
pip install prometheus_client
Step 2: Write a Python Script to Expose Metrics
Create a Python script (app.py) that simulates an application generating metrics. This script will:

Create a counter metric for tracking the number of requests.

Create a gauge metric for tracking the number of errors.

Expose these metrics over HTTP for Prometheus to scrape.

python
Copy
from prometheus_client import start_http_server, Counter, Gauge
import random
import time

# Create metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total number of requests')
ERROR_COUNT = Gauge('app_errors_total', 'Total number of errors')

def simulate_application():
    """Simulate an application that generates metrics."""
    while True:
        # Simulate a request
        REQUEST_COUNT.inc()  # Increment the request counter

        # Simulate an error (randomly)
        if random.random() < 0.2:  # 20% chance of an error
            ERROR_COUNT.inc()  # Increment the error gauge

        # Wait for a while before the next request
        time.sleep(5)

if __name__ == '__main__':
    # Start the HTTP server to expose metrics on port 8000
    start_http_server(8000)
    print("Metrics server started on port 8000")

    # Simulate the application
    simulate_application()
Step 3: Run the Python Script
Run the script to start the application and expose metrics:

bash
Copy
python app.py
The script will start an HTTP server on port 8000 and expose the metrics at the /metrics endpoint. You can view the metrics by visiting:

Copy
http://localhost:8000/metrics
You should see output like this:

Copy
# HELP app_requests_total Total number of requests
# TYPE app_requests_total counter
app_requests_total 10.0

# HELP app_errors_total Total number of errors
# TYPE app_errors_total gauge
app_errors_total 2.0
Step 4: Configure Prometheus to Scrape the Metrics
Now, configure Prometheus to scrape the metrics exposed by the Python script.

Download and Install Prometheus:

Download Prometheus from the official website.

Extract the files and navigate to the Prometheus directory.

Edit the Prometheus Configuration:

Open the prometheus.yml file in a text editor.

Add a new job to scrape the metrics from the Python script:

yaml
Copy
global:
  scrape_interval: 15s  # How often to scrape targets

scrape_configs:
  - job_name: 'python_app'
    static_configs:
      - targets: ['localhost:8000']  # Replace with your server IP if running remotely
Start Prometheus:

Run Prometheus using the following command:

bash
Copy
./prometheus --config.file=prometheus.yml
Copy
Access the Prometheus Web UI:

Open your browser and go to http://localhost:9090.

In the "Expression" box, enter app_requests_total or app_errors_total to query the metrics.

Step 5: Visualize Metrics in Grafana
If you want to visualize the metrics in Grafana:

Install Grafana:

Download and install Grafana from the official website.

Add Prometheus as a Data Source:

Open Grafana in your browser (http://localhost:3000).

Go to Configuration > Data Sources.

Add a new data source and select Prometheus.

Set the URL to http://localhost:9090 (or your Prometheus server address).

Create a Dashboard:

Go to Create > Dashboard.

Add a new panel and use the query app_requests_total or app_errors_total to visualize the metrics.

Step 6: Add Alerting (Optional)
You can configure alerting in Prometheus to notify you when certain conditions are met (e.g., too many errors).

Edit prometheus.yml:
Add an alerting rule:

yaml
Copy
rule_files:
  - alerts.yml
Create alerts.yml:
Define an alert rule:

yaml
Copy
groups:
  - name: example
    rules:
      - alert: HighErrorRate
        expr: app_errors_total > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "The error count is above 5."
Reload Prometheus:
Send a SIGHUP signal to Prometheus or restart it to apply the new configuration.

Configure Alertmanager:
Set up Alertmanager to handle alerts (e.g., send emails or Slack notifications).