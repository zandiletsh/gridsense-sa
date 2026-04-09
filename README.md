# GridSense SA — National Energy Intelligence Platform

> Real-time load shedding intelligence platform built on AWS, processing live Eskom data through an event-driven microservices architecture.

[![Deploy GridSense Services](https://github.com/zandiletsh/gridsense-sa/actions/workflows/deploy.yaml/badge.svg)](https://github.com/zandiletsh/gridsense-sa/actions/workflows/deploy.yaml)

---

## Overview

GridSense SA solves a real problem faced by 60 million South Africans — unpredictable load shedding. The platform ingests live data from the EskomSePush API, validates and streams it through Apache Kafka, and serves it through a REST API with sub-second response times.

Built as a learning project to achieve globally competitive cloud engineering skills.

---

## Architecture
EskomSePush API
↓ (every 5 minutes)
Eskom Ingestor (Python/Kubernetes)
↓
Kafka Topic: eskom.generation.raw (MSK)
↓
Data Validator (Python/Kubernetes)
↓
Kafka Topic: eskom.generation.validated
↓
API Gateway (FastAPI/Kubernetes)
↓
REST API consumers

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Cloud | AWS (EKS, MSK, ECR, VPC) |
| Infrastructure as Code | Terraform |
| Container Orchestration | Kubernetes (EKS 1.30) |
| Event Streaming | Apache Kafka (MSK 3.5.1) |
| Microservices | Python 3.11 |
| API Framework | FastAPI |
| Observability | Prometheus + Grafana |
| CI/CD | GitHub Actions |
| Container Registry | Amazon ECR |

---

## Services

### Eskom Ingestor
Polls the EskomSePush API every 5 minutes and publishes structured events to Kafka.
- Retry logic with exponential backoff (tenacity)
- Pydantic data validation
- Structured JSON logging (structlog)
- Graceful shutdown handling

### Data Validator
Consumes raw events from Kafka, applies 7 validation rules, and routes to validated or dead-letter topics.
- Validates: required fields, stage range (0-8), timestamp freshness (30min), future events, known sources
- Dead-letter queue for invalid events
- Consumer group offset tracking

### API Gateway
FastAPI application serving real-time load shedding data.
- `GET /api/v1/status` — current national load shedding stage
- `GET /api/v1/status/summary` — simplified status for mobile clients
- `GET /api/v1/health` — Kubernetes liveness probe
- `GET /api/docs` — auto-generated Swagger documentation
- 2 replicas across availability zones

---

## Infrastructure

### AWS Resources
- **VPC** — Custom VPC with public/private subnets across 2 AZs
- **EKS** — Managed Kubernetes cluster (v1.30) with 2x t3.medium nodes
- **MSK** — Managed Kafka cluster (v3.5.1) with 2x kafka.t3.small brokers
- **ECR** — Private container registry for all service images
- **NAT Gateway** — Outbound internet for private subnet resources

### Kafka Topics
| Topic | Purpose |
|-------|---------|
| eskom.generation.raw | Raw unvalidated events from ESP API |
| eskom.generation.validated | Clean validated events |
| eskom.generation.deadletter | Failed validation events |
| weather.readings.raw | Weather data (future) |
| municipality.schedules.parsed | Area schedules (future) |
| user.reports.validated | Crowdsourced reports (future) |
| predictions.stage.forecast | ML predictions (future) |
| alerts.triggered | Alert events (future) |

---

## Getting Started

### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform >= 1.6
- kubectl
- Helm >= 3.14
- Docker Desktop

### Deploy Infrastructure
```bash
cd infra/environments/dev
terraform init
terraform apply
```

### Configure kubectl
```bash
aws eks update-kubeconfig --region us-east-1 --name gridsense-dev
```

### Create Kafka Topics
```bash
kubectl run kafka-client --image=confluentinc/cp-kafka:7.5.0 \
  --namespace=ingestion --restart=Never --command -- sleep infinity

# Create topics (see scripts/create-topics.sh)
```

### Deploy Services
```bash
# Create secrets first
kubectl create secret generic eskom-ingestor-secrets \
  --namespace=ingestion \
  --from-literal=ESKOMSEPUSH_API_TOKEN=<your-token> \
  --from-literal=KAFKA_BOOTSTRAP_SERVERS=<broker-addresses>

# Deploy all services
kubectl apply -f services/eskom-ingestor/helm/templates/
kubectl apply -f services/data-validator/helm/templates/
kubectl apply -f services/api-gateway/helm/templates/
```

### Access the API
```bash
kubectl port-forward service/api-gateway 8080:80 -n delivery
curl http://localhost:8080/api/v1/status
```

### Access Grafana
```bash
kubectl port-forward service/monitoring-grafana 3000:80 -n monitoring
# Open http://localhost:3000
```

---

## CI/CD

Every push to `main` triggers the GitHub Actions pipeline:

1. **Detect changes** — identifies which services were modified
2. **Build** — Docker image built and tagged with git SHA
3. **Push** — image pushed to Amazon ECR
4. **Deploy** — Kubernetes deployment updated and rollout verified

Only modified services are rebuilt and redeployed.

---

## Cost Management

Estimated daily cost while active: **~$7.65/day**

| Resource | Cost/day |
|----------|---------|
| EKS Control Plane | $2.40 |
| 2x t3.medium nodes | $2.02 |
| MSK 2x kafka.t3.small | $2.16 |
| NAT Gateway | $1.08 |

Destroy expensive resources when not working:
```bash
terraform destroy \
  -target=module.msk.aws_msk_cluster.main \
  -target=module.eks.aws_eks_node_group.main \
  -target=module.eks.aws_eks_cluster.main \
  -target=module.vpc.aws_nat_gateway.main \
  -target=module.vpc.aws_eip.nat
```

---

## Project Structure
gridsense-sa/
├── infra/
│   ├── environments/
│   │   └── dev/          # Dev environment Terraform config
│   ├── modules/
│   │   ├── eks/          # EKS cluster module
│   │   ├── msk/          # MSK Kafka module
│   │   └── vpc/          # VPC networking module
│   └── global/           # Global resources (ECR)
├── services/
│   ├── eskom-ingestor/   # Kafka producer — ESP API polling
│   ├── data-validator/   # Kafka consumer — event validation
│   └── api-gateway/      # FastAPI REST API
└── .github/
└── workflows/
└── deploy.yaml   # CI/CD pipeline

---

## Author

**Zandile Tshabalala** — Cloud Engineer
- GitHub: [@zandiletsh](https://github.com/zandiletsh)
