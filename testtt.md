from prometheus_client import start_http_server, Gauge
import time
import os
import re
from datetime import datetime

# Define Prometheus metrics
total_errors = Gauge('aspnet_total_errors', 'Total number of errors in ASP.NET app')
sql_errors = Gauge('aspnet_sql_errors', 'Number of SQL-related errors')
last_error_timestamp = Gauge('aspnet_last_error_timestamp', 'Timestamp of last logged error (Unix)')

LOG_FILE = r"C:\Logs\app_log.txt"  # Adjust to your actual path

def parse_error_log():
    if not os.path.exists(LOG_FILE):
        print(f"[ERROR] Log file not found: {LOG_FILE}")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log_data = f.read()

    # Regex to match individual exception blocks
    pattern = re.compile(r"--------Exception Details on\s+(.+?)\s*-+\s+Log Written Date:\s+(.+?)\s+Error Line No.+?Error Message:(.*?)\s+Exception Type:(.*?)\s+Error Location:(.*?)\s+Error Page Url", re.DOTALL)
    matches = pattern.findall(log_data)

    error_count = len(matches)
    sql_error_count = 0
    latest_ts = 0

    for match in matches:
        log_time = match[1].strip()
        try:
            ts = datetime.strptime(log_time, "%m/%d/%Y %I:%M:%S %p")
            latest_ts = max(latest_ts, int(ts.timestamp()))
        except Exception:
            pass

        error_message = match[2].lower()
        exception_type = match[3].lower()

        if "sql" in error_message or "sql" in exception_type:
            sql_error_count += 1

    # Set Prometheus metrics
    total_errors.set(error_count)
    sql_errors.set(sql_error_count)
    last_error_timestamp.set(latest_ts)

if __name__ == "__main__":
    print("[STARTING] IIS Error Exporter on port 9100...")
    start_http_server(9100)

    while True:
        parse_error_log()
        time.sleep(15)  # Adjust interval
