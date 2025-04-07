import os
import re
import time
import requests
from prometheus_client import start_http_server, Gauge
from datetime import datetime

# Prometheus metric to track error occurrences based on the error message
error_message_gauge = Gauge('iis_error_message_count', 'Count of IIS error messages',
                            ['error_message', 'error_location', 'exception_type', 'error_line'])

# URL to the IIS error logs directory (HTTP)
log_directory_url = "C:/ErrorLog/Error/"

# Function to download the log file
def download_log_file(log_url):
    try:
        response = requests.get(log_url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text  # Return the content of the log file
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the log file: {e}")
        return None

# Function to parse the error logs and update Prometheus metrics
def parse_and_update_metrics():
    # Get the current date for the log file (formatted as '4/7/2025')
    current_date = datetime.now().strftime('%m/%d/%Y')

    # Construct the log file URL for today's date
    log_url = f"{log_directory_url}{current_date}.txt"

    # Download the log file content
    log_content = download_log_file(log_url)
    if log_content:
        # Define regex pattern to capture relevant fields
        error_pattern = re.compile(
            r"Error Written Date: (?P<date>[\d/]+\s[\d:]+)\s.*?"
            r"Error Line No : (?P<line>\w+)\s.*?"
            r"Error Message: (?P<message>.*?)\s*?"
            r"Exception Type: (?P<exception_type>.*?)\s*?"
            r"Error Location : (?P<location>.*?)\s*?"
        )

        # Find all matching error log entries
        matches = error_pattern.finditer(log_content)
        for match in matches:
            # Extract the matched groups (error details)
            error_message = match.group("message").strip()
            exception_type = match.group("exception_type").strip()
            error_location = match.group("location").strip()
            error_line = match.group("line").strip()

            # Update Prometheus gauge for this error message
            error_message_gauge.labels(
                error_message=error_message,
                error_location=error_location,
                exception_type=exception_type,
                error_line=error_line
            ).inc()

# Function to start the metrics server
def start_metrics_server():
    # Start the Prometheus metrics HTTP server on port 8000
    start_http_server(8000)
    print("Metrics server started on port 8000")

# Main function
def main():
    # Start the metrics server
    start_metrics_server()

    # Continuously parse and update metrics every 60 seconds
    while True:
        parse_and_update_metrics()
        time.sleep(60)  # Adjust the sleep time as needed (e.g., scrape logs every 60 seconds)

if __name__ == "__main__":
    main()
