#!/bin/bash

# Path to certificates inside the container
CERT_PATH="/etc/nginx/certs"

# Warning threshold in days
THRESHOLD=30

echo "=== SSL Certificate Expiry Check ==="
echo "Checking certificates in $CERT_PATH ..."

# Loop through all domain folders
for domain_dir in "$CERT_PATH"/*; do
  if [ -d "$domain_dir" ]; then
    domain=$(basename "$domain_dir")
    cert_file="$domain_dir/cert.pem"

    if [ ! -f "$cert_file" ]; then
      echo "[WARNING] Certificate not found for $domain"
      continue
    fi

    # Get expiration date
    expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
    expiry_seconds=$(date -d "$expiry_date" +%s)
    now_seconds=$(date +%s)
    days_left=$(( (expiry_seconds - now_seconds) / 86400 ))

    if [ "$days_left" -le "$THRESHOLD" ]; then
      echo "[ALERT] Certificate for $domain expires in $days_left days!"
    else
      echo "[OK] Certificate for $domain expires in $days_left days."
    fi
  fi
done
echo "=== Check Complete ==="

____________________________________________________________________________________


#docker cp ssl_watch.sh nginx-proxy-letsencrypt:/ssl_watch.sh
#docker exec -it nginx-proxy-letsencrypt chmod +x /ssl_watch.sh
#docker exec -it nginx-proxy-letsencrypt /ssl_watch.sh

