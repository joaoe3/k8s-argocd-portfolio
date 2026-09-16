# Kubernetes + ArgoCD Portfolio Project

A small, hands-on project demonstrating Terraform, Kubernetes, and GitOps workflows via ArgoCD.

**Status: in progress** — building incrementally, day by day. See below for current state.

## What this project does (once complete)

1. **Terraform** provisions a local Kubernetes cluster (`kind`)
2. A simple application is deployed to it, following proper resource limits and health check conventions
3. **ArgoCD** takes over management of that deployment via GitOps — changes flow through git, not manual `kubectl apply`
4. A small **Python** utility supports the setup (health check or manifest validation)

## Why

Built to deepen hands-on Kubernetes and ArgoCD experience through direct practice, rather than tutorial-following alone.

## Progress

- [x] **Day 1** — Terraform provisions a local `kind` cluster (`terraform/cluster/`)
- [ ] **Day 2** — Deploy a simple application manually (Deployment, Service, ConfigMap, resource limits)
- [ ] **Day 3** — Install ArgoCD, migrate the app to GitOps-managed deployment
- [ ] **Day 4** — Full documentation, architecture overview, supporting Python script

## Structure

```
terraform/
  cluster/          # Terraform config provisioning the local kind cluster
```

*(structure will grow as the project progresses)*

## Requirements

- Docker
- Terraform
- kubectl
- kind

## Usage (current state)

```bash
cd terraform/cluster
terraform init
terraform apply
kubectl cluster-info --context kind-portfolio-cluster
kubectl get nodes
```
