# K3s Installation with Helm, Monitoring, Loki Retention, and cert-manager

## 1. Purpose

This document explains how to install and configure a lightweight Kubernetes environment using K3s on a single VM.

It includes:

- K3s installation
- kubectl alias setup
- Helm installation
- Namespace setup
- cert-manager installation
- Prometheus + Grafana monitoring using kube-prometheus-stack
- Loki + Promtail logging
- Metrics and logs retention limits
- Auto-delete / cleanup configuration
- Basic verification commands
- Uninstall commands

---

## 2. Recommended VM

For a limited-resource single VM:

| Component | Recommended |
|---|---|
| VM Size | Azure B4ms or similar |
| CPU | 4 vCPU |
| RAM | 16 GB |
| OS | Ubuntu 22.04 / 24.04 LTS |
| Disk | Minimum 64 GB, recommended 128 GB |
| Kubernetes | K3s |
| Ingress | Traefik |
| Monitoring | kube-prometheus-stack |
| Logging | Loki + Promtail |
| TLS | cert-manager + Let's Encrypt |

---

## 3. Architecture

```text
Internet
   |
Domain DNS
   |
VM Public IP
   |
K3s Node
   |
Traefik Ingress Controller
   |
------------------------------------------------
|                    |                         |
Application Services Monitoring Stack          Logging Stack
Next.js / API / etc  Prometheus + Grafana      Loki + Promtail
                     Metrics Retention         Log Retention
                     Auto cleanup              Auto delete
```

---

## 4. Pre-Requisites

Login as root or a sudo user.

```bash
sudo apt update -y
sudo apt upgrade -y
```

Install required tools:

```bash
sudo apt install -y curl wget git unzip jq vim net-tools ca-certificates gnupg lsb-release
```

Disable swap:

```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab
```

Enable required kernel modules:

```bash
cat <<EOF | sudo tee /etc/modules-load.d/k3s.conf
br_netfilter
overlay
EOF

sudo modprobe br_netfilter
sudo modprobe overlay
```

Apply sysctl settings:

```bash
cat <<EOF | sudo tee /etc/sysctl.d/99-k3s.conf
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
net.ipv4.ip_forward=1
EOF

sudo sysctl --system
```

---

## 5. Install K3s

### Option A: Install K3s with default Traefik

Recommended for single VM.

```bash
curl -sfL https://get.k3s.io | sh -
```

Check service:

```bash
sudo systemctl status k3s
```

Check nodes:

```bash
sudo k3s kubectl get nodes
```

### Option B: Install K3s without Traefik

Use this only if you want to install NGINX Ingress separately.

```bash
curl -sfL https://get.k3s.io | sh -s - --disable traefik
```

For this document, Traefik is assumed to be enabled.

---

## 6. Configure kubectl

```bash
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config
chmod 600 ~/.kube/config
kubectl get nodes
```

---

## 7. Create kubectl Alias

```bash
echo "alias ku='kubectl'" >> ~/.bashrc
source ~/.bashrc
```

Test:

```bash
ku get nodes
ku get pods -A
```

Optional aliases:

```bash
cat <<'EOF' >> ~/.bashrc

# Kubernetes aliases
alias ku='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kga='kubectl get all'
alias kaf='kubectl apply -f'
alias kdf='kubectl delete -f'
alias kdesc='kubectl describe'
alias klogs='kubectl logs'
EOF

source ~/.bashrc
```

---

## 8. Verify K3s System Pods

```bash
ku get pods -A
ku get pods -n kube-system | grep traefik
ku get svc -n kube-system | grep traefik
```

---

## 9. Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

---

## 10. Create Namespaces

```bash
ku create namespace cert-manager
ku create namespace monitoring
ku create namespace logging
```

If already exists, ignore the error.

---

# PART 1: cert-manager Setup

## 11. Install cert-manager using Helm

```bash
helm repo add jetstack https://charts.jetstack.io
helm repo update

helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set crds.enabled=true
```

For older chart versions:

```bash
helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set installCRDs=true
```

Verify:

```bash
ku get pods -n cert-manager
```

Expected pods:

```text
cert-manager
cert-manager-cainjector
cert-manager-webhook
```

---

## 12. Create Let's Encrypt Production ClusterIssuer

Replace email address before applying.

```bash
mkdir -p ~/k3s-setup/cert-manager
nano ~/k3s-setup/cert-manager/cluster-issuer.yaml
```

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-production
spec:
  acme:
    email: admin@example.com
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-production-key
    solvers:
      - http01:
          ingress:
            class: traefik
```

Apply:

```bash
ku apply -f ~/k3s-setup/cert-manager/cluster-issuer.yaml
ku get clusterissuer
ku describe clusterissuer letsencrypt-production
```

---

## 13. Optional Let's Encrypt Staging ClusterIssuer

```bash
nano ~/k3s-setup/cert-manager/cluster-issuer-staging.yaml
```

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    email: admin@example.com
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-staging-key
    solvers:
      - http01:
          ingress:
            class: traefik
```

```bash
ku apply -f ~/k3s-setup/cert-manager/cluster-issuer-staging.yaml
```

---

# PART 2: Monitoring Setup with Prometheus and Grafana

## 14. Add Prometheus Helm Repo

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

---

## 15. Create kube-prometheus-stack Values File

```bash
mkdir -p ~/k3s-setup/monitoring
nano ~/k3s-setup/monitoring/kube-prometheus-values.yaml
```

```yaml
fullnameOverride: kube-prometheus-stack

grafana:
  enabled: true
  adminUser: admin
  adminPassword: "ChangeMeStrongPassword"

  persistence:
    enabled: true
    type: pvc
    size: 5Gi

  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

  service:
    type: ClusterIP

alertmanager:
  enabled: true
  alertmanagerSpec:
    retention: 72h
    storage:
      volumeClaimTemplate:
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 2Gi
    resources:
      requests:
        cpu: 50m
        memory: 128Mi
      limits:
        cpu: 200m
        memory: 256Mi

prometheus:
  enabled: true
  prometheusSpec:
    retention: 7d
    retentionSize: 8GB
    scrapeInterval: 30s
    evaluationInterval: 30s
    walCompression: true

    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 10Gi

    resources:
      requests:
        cpu: 200m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 2Gi

prometheusOperator:
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 300m
      memory: 384Mi

kube-state-metrics:
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      cpu: 200m
      memory: 256Mi

prometheus-node-exporter:
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 200m
      memory: 128Mi
```

Retention settings:

```yaml
prometheus:
  prometheusSpec:
    retention: 7d
    retentionSize: 8GB
```

---

## 16. Install Monitoring Stack

```bash
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f ~/k3s-setup/monitoring/kube-prometheus-values.yaml
```

Verify:

```bash
ku get pods -n monitoring
ku get svc -n monitoring
ku get pvc -n monitoring
```

---

## 17. Access Grafana Locally

```bash
ku port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

Open:

```text
http://localhost:3000
```

Login:

```text
Username: admin
Password: ChangeMeStrongPassword
```

---

## 18. Optional Grafana Ingress with TLS

```bash
nano ~/k3s-setup/monitoring/grafana-ingress.yaml
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana-ingress
  namespace: monitoring
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-production
spec:
  ingressClassName: traefik
  tls:
    - hosts:
        - grafana.example.com
      secretName: grafana-tls
  rules:
    - host: grafana.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: kube-prometheus-stack-grafana
                port:
                  number: 80
```

```bash
ku apply -f ~/k3s-setup/monitoring/grafana-ingress.yaml
ku get certificate -n monitoring
ku describe certificate grafana-tls -n monitoring
```

---

# PART 3: Loki Logging Setup

## 19. Add Grafana Helm Repo

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

---

## 20. Create Loki Values File with Retention and Auto Delete

```bash
mkdir -p ~/k3s-setup/logging
nano ~/k3s-setup/logging/loki-values.yaml
```

```yaml
deploymentMode: SingleBinary

loki:
  auth_enabled: false

  commonConfig:
    replication_factor: 1

  schemaConfig:
    configs:
      - from: "2024-04-01"
        store: tsdb
        object_store: filesystem
        schema: v13
        index:
          prefix: loki_index_
          period: 24h

  storage:
    type: filesystem

  limits_config:
    retention_period: 72h
    ingestion_rate_mb: 4
    ingestion_burst_size_mb: 8
    max_query_series: 5000
    reject_old_samples: true
    reject_old_samples_max_age: 168h

  compactor:
    working_directory: /var/loki/compactor
    retention_enabled: true
    retention_delete_delay: 2h
    retention_delete_worker_count: 50
    delete_request_store: filesystem

singleBinary:
  replicas: 1

  persistence:
    enabled: true
    size: 10Gi
    storageClass: local-path

  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 1Gi

read:
  replicas: 0

write:
  replicas: 0

backend:
  replicas: 0

gateway:
  enabled: false

chunksCache:
  enabled: false

resultsCache:
  enabled: false

test:
  enabled: false

monitoring:
  selfMonitoring:
    enabled: false
    grafanaAgent:
      installOperator: false

lokiCanary:
  enabled: false
```

Recommended Loki retention:

| Environment | Retention | PVC |
|---|---:|---:|
| Demo | 24h | 5Gi |
| Small app | 72h | 10Gi |
| Medium app | 7d | 20Gi |
| Production | 15d+ | External object storage |

---

## 21. Install Loki

```bash
helm upgrade --install loki grafana/loki \
  --namespace logging \
  -f ~/k3s-setup/logging/loki-values.yaml
```

Verify:

```bash
ku get pods -n logging
ku get svc -n logging
ku get pvc -n logging
```

---

## 22. Install Promtail

```bash
nano ~/k3s-setup/logging/promtail-values.yaml
```

```yaml
config:
  clients:
    - url: http://loki.logging.svc.cluster.local:3100/loki/api/v1/push

  snippets:
    pipelineStages:
      - cri: {}

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 200m
    memory: 256Mi

tolerations:
  - operator: Exists
```

Install:

```bash
helm upgrade --install promtail grafana/promtail \
  --namespace logging \
  -f ~/k3s-setup/logging/promtail-values.yaml
```

Verify:

```bash
ku get pods -n logging
```

---

## 23. Add Loki Datasource to Grafana

```bash
nano ~/k3s-setup/monitoring/grafana-loki-datasource.yaml
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-loki-datasource
  namespace: monitoring
  labels:
    grafana_datasource: "1"
data:
  loki-datasource.yaml: |-
    apiVersion: 1
    datasources:
      - name: Loki
        type: loki
        access: proxy
        url: http://loki.logging.svc.cluster.local:3100
        isDefault: false
```

```bash
ku apply -f ~/k3s-setup/monitoring/grafana-loki-datasource.yaml
ku rollout restart deployment kube-prometheus-stack-grafana -n monitoring
```

---

# PART 4: Auto Cleanup and Disk Protection

## 24. K3s Container Image Cleanup

Check disk:

```bash
df -h
sudo du -sh /var/lib/rancher/k3s
```

Manual cleanup:

```bash
sudo k3s crictl images
sudo k3s crictl rmi --prune
```

---

## 25. Create Weekly Image Cleanup CronJob on Host

```bash
sudo nano /usr/local/bin/k3s-image-cleanup.sh
```

```bash
#!/bin/bash
set -e

echo "Starting K3s image cleanup: $(date)"

k3s crictl rmi --prune || true

journalctl --vacuum-time=7d || true

echo "Cleanup completed: $(date)"
```

```bash
sudo chmod +x /usr/local/bin/k3s-image-cleanup.sh
sudo crontab -e
```

Add:

```cron
0 3 * * 0 /usr/local/bin/k3s-image-cleanup.sh >> /var/log/k3s-image-cleanup.log 2>&1
```

---

## 26. Limit systemd Journal Logs

```bash
sudo nano /etc/systemd/journald.conf
```

Set or update:

```ini
SystemMaxUse=1G
SystemKeepFree=2G
MaxRetentionSec=7day
```

Restart:

```bash
sudo systemctl restart systemd-journald
journalctl --disk-usage
```

---

# PART 5: Application Ingress Example with TLS

## 27. Example App Ingress

```bash
mkdir -p ~/k3s-setup/app
nano ~/k3s-setup/app/app-ingress.yaml
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  namespace: default
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-production
spec:
  ingressClassName: traefik
  tls:
    - hosts:
        - app.example.com
      secretName: app-tls
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 3000
```

```bash
ku apply -f ~/k3s-setup/app/app-ingress.yaml
ku get ingress
ku get certificate
ku describe certificate app-tls
```

---

# PART 6: Verification Commands

## Cluster

```bash
ku get nodes -o wide
ku get pods -A
ku get svc -A
ku get ingress -A
ku get pvc -A
```

## cert-manager

```bash
ku get pods -n cert-manager
ku get clusterissuer
ku get certificates -A
ku get certificaterequests -A
ku get orders -A
ku get challenges -A
```

## Monitoring

```bash
ku get pods -n monitoring
ku get svc -n monitoring
ku get pvc -n monitoring
```

Prometheus:

```bash
ku port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
```

Grafana:

```bash
ku port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
```

Alertmanager:

```bash
ku port-forward -n monitoring svc/kube-prometheus-stack-alertmanager 9093:9093
```

## Loki

```bash
ku get pods -n logging
ku get svc -n logging
ku get pvc -n logging
```

Port-forward Loki:

```bash
ku port-forward -n logging svc/loki 3100:3100
curl http://localhost:3100/ready
```

---

# PART 7: Test Logs in Grafana

In Grafana:

```text
Explore -> Select Loki datasource
```

Example LogQL queries:

```logql
{namespace="default"}
```

```logql
{namespace="monitoring"}
```

```logql
{app="your-app-name"}
```

---

# PART 8: Resource Planning for B4ms

| Component | CPU Request | Memory Request | PVC |
|---|---:|---:|---:|
| Prometheus | 200m | 512Mi | 10Gi |
| Grafana | 100m | 256Mi | 5Gi |
| Alertmanager | 50m | 128Mi | 2Gi |
| Loki | 100m | 256Mi | 10Gi |
| Promtail | 50m | 64Mi | No PVC |
| cert-manager | Default/small | Default/small | No PVC |

Total recommended storage:

```text
Prometheus: 10Gi
Grafana: 5Gi
Alertmanager: 2Gi
Loki: 10Gi
System + images: 30Gi+
```

Minimum VM disk:

```text
64Gi
```

Recommended VM disk:

```text
128Gi
```

---

# PART 9: Upgrade Commands

```bash
helm repo update
```

cert-manager:

```bash
helm upgrade cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set crds.enabled=true
```

Monitoring:

```bash
helm upgrade monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f ~/k3s-setup/monitoring/kube-prometheus-values.yaml
```

Loki:

```bash
helm upgrade loki grafana/loki \
  --namespace logging \
  -f ~/k3s-setup/logging/loki-values.yaml
```

Promtail:

```bash
helm upgrade promtail grafana/promtail \
  --namespace logging \
  -f ~/k3s-setup/logging/promtail-values.yaml
```

---

# PART 10: Uninstall Commands

Promtail:

```bash
helm uninstall promtail -n logging
```

Loki:

```bash
helm uninstall loki -n logging
ku delete pvc -n logging --all
```

Monitoring:

```bash
helm uninstall monitoring -n monitoring
ku delete pvc -n monitoring --all
```

cert-manager:

```bash
helm uninstall cert-manager -n cert-manager
```

Delete cert-manager CRDs only if you are sure:

```bash
ku delete crd \
  certificaterequests.cert-manager.io \
  certificates.cert-manager.io \
  challenges.acme.cert-manager.io \
  clusterissuers.cert-manager.io \
  issuers.cert-manager.io \
  orders.acme.cert-manager.io
```

Uninstall K3s:

```bash
/usr/local/bin/k3s-uninstall.sh
```

---

# PART 11: Troubleshooting

## Pods Pending

```bash
ku describe pod <pod-name> -n <namespace>
ku get pvc -A
ku get storageclass
```

K3s default storage class is usually:

```text
local-path
```

## Certificate Not Issuing

```bash
ku describe certificate <cert-name> -n <namespace>
ku get challenges -A
ku describe challenge <challenge-name> -n <namespace>
ku logs -n cert-manager deploy/cert-manager
```

Common issues:

- Domain DNS not pointing to VM public IP
- Port 80 not open
- Port 443 not open
- Wrong ingressClassName
- Wrong ClusterIssuer name

## Loki Retention Not Working

```bash
ku logs -n logging -l app.kubernetes.io/name=loki
helm get values loki -n logging
```

Required settings:

```yaml
limits_config:
  retention_period: 72h

compactor:
  retention_enabled: true
```

Retention is not instant. Loki first removes index entries and then deletes chunks after the configured delay.

## Prometheus PVC Filling

```bash
ku get pvc -n monitoring
helm get values monitoring -n monitoring
```

Recommended:

```yaml
prometheus:
  prometheusSpec:
    retention: 7d
    retentionSize: 8GB
```

If PVC is still full, reduce:

```yaml
retention: 3d
retentionSize: 5GB
```

Then upgrade:

```bash
helm upgrade monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f ~/k3s-setup/monitoring/kube-prometheus-values.yaml
```

## Node Disk Full

```bash
df -h
sudo du -sh /var/lib/rancher/k3s
sudo du -sh /var/log
journalctl --disk-usage
sudo k3s crictl rmi --prune
sudo journalctl --vacuum-time=7d
```

---

# PART 12: Recommended Final Setup

For a single VM setup:

```text
K3s: enabled
Traefik: enabled
Helm: enabled
cert-manager: enabled
Prometheus retention: 7 days
Prometheus retention size: 8GB
Prometheus PVC: 10Gi
Grafana PVC: 5Gi
Loki retention: 72 hours
Loki PVC: 10Gi
Promtail: enabled
Weekly image cleanup: enabled
Journal retention: 7 days
```

This gives:

- Kubernetes rollout and rollback
- Auto-healing
- Helm deployment support
- Metrics monitoring
- Log collection
- Automatic old log cleanup
- Automatic metrics retention
- TLS certificates using cert-manager
