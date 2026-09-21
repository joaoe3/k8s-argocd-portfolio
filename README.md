# Kubernetes + ArgoCD Portfolio Project

A small, hands-on project demonstrating Terraform, Kubernetes, and GitOps
workflows via ArgoCD — built end to end, AI assisted.

## What it does

A Flask application (AI-assisted), deployed to a local Kubernetes cluster, that queries the
cluster's own API (using RBAC-scoped permissions) and displays live pod and node
status on a simple dashboard. The entire deployment is managed via ArgoCD using
GitOps — changes flow through git, not manual `kubectl apply`.

## Architecture

```
Terraform ──► kind cluster (local Kubernetes in Docker)
                    │
                    ├── ArgoCD (watches this repo's k8s/ folder)
                    │       │
                    │       ▼
                    └── dashboard-app namespace
                            ├── ServiceAccount (least-privilege RBAC:
                            │     get/list on pods and nodes only)
                            ├── Deployment (dashboard-app, resource
                            │     requests/limits set)
                            └── Service (exposes the app internally)
```

**Architecture:**
- **Terraform** provisions the cluster itself — infrastructure as code, not a
  manually-run `kind create cluster` command, highly costumizable.
- **RBAC is scoped to exactly what the app needs** (`get`/`list` on `pods` and
  `nodes`, nothing else) — a `ClusterRole` is required here specifically because
  `Node` objects are cluster-scoped (not namespaced), and the app needs pod
  visibility across all namespaces, not just its own.
- **ArgoCD manages the application via GitOps**: git is the source of truth for
  what should be running. `syncPolicy.automated.selfHeal: true` means manual
  changes made directly to the cluster are automatically reverted —
  this was tested live by manually scaling the deployment to 3 replicas and
  watching ArgoCD revert it back to the 1 replica defined in git.
- **Images are pinned to specific version tags** (`v1`, not `latest`) so that
  deploying a new image version is a real, trackable git change that ArgoCD
  picks up and rolls out automatically, rather than an ambiguous tag that could
  silently point at different content over time.

## Components

```
terraform/cluster/     # Terraform config provisioning the local kind cluster
app/                    # Flask application source, Dockerfile
k8s/                    # Kubernetes manifests: namespace, ServiceAccount,
                        #   ClusterRole/ClusterRoleBinding, Deployment, Service
argocd/                 # ArgoCD Application manifest
scripts/                # Supporting Python health-check script
```

## Requirements

- Docker
- Terraform
- kubectl
- kind

## Running it locally

```bash
# 1. Provision the cluster
cd terraform/cluster
terraform init
terraform apply

# 2. Build and load the app image into the cluster
cd ../../app
docker build -t dashboard-app:v1 .
kind load docker-image dashboard-app:v1 --name portfolio-cluster

# 3. Install ArgoCD
kubectl create namespace argocd
kubectl create -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 4. Point ArgoCD at this repo
cd ..
kubectl apply -f argocd/application.yaml

# ArgoCD will now provision the namespace, RBAC, Deployment and Service
# automatically from the k8s/ folder — no manual kubectl apply needed for the app itself.

# 5. Access the dashboard
kubectl port-forward -n dashboard-app svc/dashboard-app-service 8080:80
# visit http://localhost:8080

# 6. Verify health
python3 scripts/healthcheck.py
```

## What I'd add with more time

- CI pipeline to build/push the image and bump the version tag automatically on merge
- NetworkPolicy restricting traffic into the `dashboard-app` namespace
- A second small app to demonstrate a shared "paved path" pattern across services
- TLS/ingress instead of port-forwarding for access

## What this demonstrates

- Infrastructure as code (Terraform) provisioning real infrastructure, not just
  application config
- Kubernetes fundamentals: namespaces, RBAC least-privilege, resource
  requests/limits, Services/label selectors
- GitOps in practice via ArgoCD, including verified drift detection and
  self-healing, not just installation
- Image versioning and reproducibility, and why `latest` tags are a real
  operational problem, learned by hitting the actual issue mid-build
- A working, genuinely useful supporting script with proper error handling
