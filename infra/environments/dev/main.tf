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
  kubernetes_version = "1.29"
  node_instance_type = "t3.medium"
  node_desired_size  = 2
  node_min_size      = 1
  node_max_size      = 4
}