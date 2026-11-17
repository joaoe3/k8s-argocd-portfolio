# Kubernetes + ArgoCD Portfolio Project

A small, hands-on project demonstrating Terraform, Kubernetes, GitOps via ArgoCD,
and a security-first CI pipeline — built end to end, AI assisted.

## What it does

A Flask application (AI-assisted), deployed to a local Kubernetes cluster, that queries the
cluster's own API (using RBAC-scoped permissions) and displays live pod and node
status on a simple dashboard. The entire deployment is managed via ArgoCD using
GitOps — changes flow through git, not manual `kubectl apply`.

## Architecture

```
Pull request ──► GitHub Actions: commit lint, image build, Trivy scan
                                   │ (merge to main)
                                   ▼
Terraform ──► kind cluster (local Kubernetes in Docker)
                    │
                    ├── ArgoCD (watches this repo's k8s/ folder)
                    │       │
                    │       ▼
                    └── dashboard-app namespace  (Pod Security: restricted)
                            ├── ServiceAccount (read-only RBAC:
                            │     get/list on pods and nodes)
                            ├── Deployment (non-root, read-only root filesystem,
                            │     all capabilities dropped, requests/limits set)
                            └── Service (exposes the app internally)
```

**Architecture:**
- **Terraform** provisions the cluster itself — infrastructure as code, not a
  manually-run `kind create cluster` command, highly customizable.
- **RBAC is read-only and scoped to the API calls the app makes.** A `ClusterRole`
  is required here specifically because `Node` objects are cluster-scoped (not
  namespaced), and the app lists pods across all namespaces, not just its own.
- **ArgoCD manages the application via GitOps**: git is the source of truth for
  what should be running. `syncPolicy.automated.selfHeal: true` means manual
  changes made directly to the cluster are automatically reverted —
  this was tested live by manually scaling the deployment to 3 replicas and
  watching ArgoCD revert it back to the 1 replica defined in git.
- **Images are pinned to specific version tags** (`v2`, not `latest`) so that
  deploying a new image version is a real, trackable git change that ArgoCD
  picks up and rolls out automatically, rather than an ambiguous tag that could
  silently point at different content over time.

## Security

### CI pipeline (every pull request)
- **Commit lint** enforces Conventional Commit PR titles.
- **Image build** proves the image builds on every change to `app/`.
- **Trivy image scan** fails the PR on any HIGH or CRITICAL vulnerability that
  has a fix available.
- **The scanner itself is pinned by commit SHA**, not by tag. In March 2026 the
  Trivy GitHub Action's version tags were hijacked in a supply-chain attack
  (GHSA-69fq-xp46-6x23); a tag can be moved, a commit SHA cannot.
- **Least-privilege CI token**: the workflow runs with `permissions: contents: read`.
- **Exceptions are documented, not silenced**: `.trivyignore` holds a single,
  justified, expiring exception (a setuptools CVE that only matches pip's
  vendored `pkg_resources`, not the vulnerable code path).

### Dependencies
- `app/requirements.in` lists only the direct dependencies (`flask`,
  `kubernetes`); `pip-compile` generates the fully pinned `requirements.txt`,
  with a `# via` note explaining why each package is there.
- The image patches OS packages and pip's bundled libraries at build time.

### Workload hardening
- The image runs as an **unprivileged user** (`USER 10001`).
- The pod runs with `runAsNonRoot`, `allowPrivilegeEscalation: false`, a
  **read-only root filesystem** (with an `emptyDir` for `/tmp`), **all Linux
  capabilities dropped**, and the `RuntimeDefault` seccomp profile.
- The namespace **enforces the Pod Security Standard `restricted`**, so the
  cluster itself rejects workloads that don't meet it:

```
$ kubectl run evil --image=nginx -n dashboard-app --privileged
Error from server (Forbidden): pods "evil" is forbidden: violates PodSecurity "restricted:latest":
privileged (container "evil" must not set securityContext.privileged=true),
allowPrivilegeEscalation != false (...), unrestricted capabilities (...),
runAsNonRoot != true (...), seccompProfile (...)
```

### Secrets hygiene
- The generated kubeconfig is git-ignored (it was once committed by mistake
  and has since been untracked).

## Components

```
terraform/cluster/     # Terraform config provisioning the local kind cluster
app/                    # Flask application, Dockerfile, requirements.in / .txt
k8s/                    # Kubernetes manifests: namespace (Pod Security labels),
                        #   ServiceAccount, ClusterRole/ClusterRoleBinding,
                        #   Deployment, Service
argocd/                 # ArgoCD Application manifest
scripts/                # Supporting Python health-check script
.github/workflows/      # CI: commit lint, image build + Trivy scan
.trivyignore            # Documented, expiring scanner exceptions
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
docker build -t dashboard-app:v2 .
kind load docker-image dashboard-app:v2 --name portfolio-cluster

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

**Updating dependencies:** edit `app/requirements.in`, then run
`pip-compile --strip-extras -o app/requirements.txt app/requirements.in`
(add `--upgrade` to bump everything).

## What I'd add with more time

- Push the image to GHCR and bump the version tag automatically on merge
- NetworkPolicies: default deny, then allow only ingress to the app, DNS and the API server
- Tighter RBAC: nodes cluster-wide, pods only in specific namespaces via RoleBindings
- Image signing (cosign) and admission control (Kyverno) so only signed images run
- Prometheus and Grafana for metrics
- TLS/ingress instead of port-forwarding for access

## What this demonstrates

- Infrastructure as code (Terraform) provisioning real infrastructure, not just
  application config
- Kubernetes fundamentals: namespaces, RBAC least-privilege, resource
  requests/limits, Services/label selectors
- Kubernetes security in practice: non-root workloads, `securityContext`
  hardening, and Pod Security Standards enforced by the cluster
- Shift-left security: vulnerability scanning as a merge gate, supply-chain
  awareness (SHA-pinned actions), and documented exceptions instead of ignored findings
- GitOps in practice via ArgoCD, including verified drift detection and
  self-healing, not just installation
- Image versioning and reproducibility, and why `latest` tags are a real
  operational problem, learned by hitting the actual issue mid-build
- A working, genuinely useful supporting script with proper error handling