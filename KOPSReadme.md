Here is your **ready-to-copy `README.md` file content** 👇
You can directly save this as `README.md` in your GitHub repo.

---

````markdown
# 🚀 KOPS – Kubernetes Cluster Setup & Practice Notes

## 📚 Lesson Name: KOPS (Kubernetes Operations)

This repository contains my hands-on practice notes for creating and managing a Kubernetes cluster using **KOPS on AWS**, along with deployments, services, ingress, TLS setup, and troubleshooting.

---

# 🧠 1. What is KOPS?

KOPS (Kubernetes Operations) is a tool used to create, manage, upgrade, and delete production-grade Kubernetes clusters on cloud providers like AWS.

It uses:
- S3 bucket as state store
- EC2 instances for nodes
- Route53 for DNS (optional)
- IAM roles for access control

---

# 🏗 2. Cluster Setup Process (Step-by-Step)

## 🔹 Step 1: Generate SSH Key

```bash
ssh-keygen
cd ~/.ssh
ls -al
````

Used by KOPS to access worker nodes.

---

## 🔹 Step 2: Install KOPS

```bash
cd /usr/local/bin/
wget https://github.com/kubernetes/kops/releases/download/v1.34.1/kops-linux-amd64
mv kops-linux-amd64 kops
chmod +x kops
kops version
```

---

## 🔹 Step 3: Install Kubectl

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
kubectl version
```

---

## 🔹 Step 4: Create Cluster (Dry Run)

```bash
kops create cluster \
--name=ragav.space \
--state=s3://ragavs3space \
--zones=us-east-1a,us-east-1b \
--node-count=2 \
--control-plane-count=1 \
--node-size=t3.medium \
--control-plane-size=t3.medium \
--ssh-public-key ~/.ssh/id_ed25519.pub \
--dns-zone=ragav.space \
--dry-run --output yaml > cluster.yml
```

---

## 🔹 Step 5: Create Cluster from YAML

```bash
kops create -f cluster.yml
kops update cluster --name ragav.space --yes --admin
kops validate cluster --wait 10m
```

---

## 🔹 Step 6: Delete Cluster

```bash
kops delete -f cluster.yml --yes
```

---

# 📦 3. Basic Kubernetes Commands

```bash
kubectl cluster-info
kubectl get nodes -o wide
kubectl get pods
kubectl get pods -n kube-system
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl exec -it <pod> -- bash
```

---

# 🚀 4. Application Deployment

## 🔹 Create Deployment

```bash
kubectl create deployment app1 \
--image kiran2361993/kubegame:v2 \
--replicas 3 \
--dry-run -o yaml
```

---

## 🔹 Apply YAML Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app1
  template:
    metadata:
      labels:
        app: app1
    spec:
      containers:
      - name: app1
        image: kiran2361993/kubegame:v2
```

```bash
kubectl apply -f deployment.yml
```

---

# ❤️ 5. Health Checks

## 🔹 Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /index.html
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 10
```

Used to check if pod is ready to receive traffic.

---

## 🔹 Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 80
  initialDelaySeconds: 15
  periodSeconds: 20
```

Used to restart container if unhealthy.

---

# 🌐 6. Service Exposure

## ClusterIP

```bash
kubectl expose deployment app1 --port 80 --type ClusterIP
```

## NodePort

```bash
kubectl expose deployment app1 --port 80 --target-port 80 --type=NodePort
```

## LoadBalancer

```bash
kubectl expose deployment app1 --port 80 --target-port 80 --type=LoadBalancer
```

---

# 🔐 7. TLS Secret Creation

```bash
kubectl create secret tls nginx-tls-default \
--key="tls.key" \
--cert="tls.crt"
```

Verify:

```bash
kubectl get secrets
kubectl describe secret nginx-tls-default
```

---

# 🌍 8. Install Ingress Controller (AWS)

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.3.1/deploy/static/provider/aws/deploy.yaml
```

Check:

```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
kubectl get ingress
```

---

# 🛠 9. Troubleshooting Commands

```bash
kubectl describe pod <pod>
kubectl logs <pod>
kubectl exec -it <pod> -- bash
kubectl explain pod
kubectl get pods -o wide
kubectl get svc -o wide
```

---

# 🎯 Interview Questions & Answers

## 1. What is KOPS?

KOPS is a tool used to create and manage production-grade Kubernetes clusters on AWS.

## 2. Why does KOPS use S3?

S3 is used as a state store to maintain cluster configuration and metadata.

## 3. Difference between Readiness and Liveness Probe?

* Readiness → Checks if pod is ready to serve traffic.
* Liveness → Restarts container if unhealthy.

## 4. Difference between NodePort and LoadBalancer?

* NodePort → Exposes service on node IP + static port.
* LoadBalancer → Creates cloud provider load balancer.

## 5. What happens if Liveness probe fails?

Kubernetes restarts the container.

## 6. How to debug a crashing pod?

* kubectl describe pod
* kubectl logs
* kubectl exec into container

## 7. What is kube-system namespace?

Namespace containing core Kubernetes components like API server, scheduler, controller manager.

## 8. What is ClusterIP?

Default service type that exposes service internally within cluster.

---

# 🧪 Scenario-Based Questions

## Scenario 1:

Pod is running but service is not accessible externally.

**Troubleshooting:**

* Check service type (ClusterIP/NodePort/LoadBalancer)
* kubectl get svc -o wide
* Check security groups
* Verify targetPort mapping

---

## Scenario 2:

Pod is restarting continuously.

**Troubleshooting:**

* kubectl describe pod
* kubectl logs
* Check Liveness probe configuration
* Check resource limits

---

## Scenario 3:

Ingress is not routing traffic.

**Troubleshooting:**

* kubectl get ingress
* kubectl describe ingress
* Check ingress controller pod
* Validate TLS secret

---

## Scenario 4:

Cluster creation stuck in validating state.

**Troubleshooting:**

* kops validate cluster
* Check EC2 instances
* Check IAM permissions
* Verify S3 state store

---

# 📈 Learning Outcomes

✔ Kubernetes Cluster Lifecycle
✔ KOPS Configuration
✔ Deployment & Service Management
✔ Ingress & TLS Setup
✔ Health Probes
✔ Troubleshooting Real-Time Issues

---

# 🚀 Level Achieved

This practice covers:

* Intermediate Kubernetes
* Cluster Administration
* DevOps Real-Time Troubleshooting
* Production-Grade Setup Concepts

---

# 📌 Next Learning Goals

* Helm Charts
* HPA (Horizontal Pod Autoscaler)
* RBAC
* Monitoring with Prometheus & Grafana
* CI/CD Integration with Kubernetes

---

**Author:** Ragavan
**Role:** DevOps Engineer
**Focus:** Kubernetes | Cloud | Automation | CI/CD

```
