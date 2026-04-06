# infra/environments/dev/main.tf
# This is the dev environment. It calls modules and passes
# environment-specific values to them.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }

  backend "s3" {
    bucket         = "gridsense-terraform-state-173679718835"
    key            = "environments/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "gridsense-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      module.eks.cluster_name,
      "--region",
      "us-east-1"
    ]
  }
}

# ── VPC ────────────────────────────────────────────────────────────
module "vpc" {
  source = "../../modules/vpc"

  project_name         = "gridsense"
  environment          = "dev"
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = ["us-east-1a", "us-east-1b"]
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.3.0/24", "10.0.4.0/24"]
}

# ── EKS Cluster ────────────────────────────────────────────────────
module "eks" {
  source = "../../modules/eks"

  project_name       = "gridsense"
  environment        = "dev"
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  kubernetes_version = "1.30"
  node_instance_type = "t3.medium"
  node_desired_size  = 2
  node_min_size      = 1
  node_max_size      = 4
}

# ── MSK Kafka ──────────────────────────────────────────────────────
module "msk" {
  source = "../../modules/msk"

  project_name          = "gridsense"
  environment           = "dev"
  vpc_id                = module.vpc.vpc_id
  vpc_cidr              = "10.0.0.0/16"
  private_subnet_ids    = module.vpc.private_subnet_ids
  kafka_version         = "3.5.1"
  number_of_brokers     = 2
  broker_instance_type  = "kafka.t3.small"
  broker_volume_size    = 20
  eks_security_group_id = module.eks.cluster_security_group_id
}
