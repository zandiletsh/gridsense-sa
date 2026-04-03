# infra/environments/dev/outputs.tf
# Exposes important values from modules so we can reference them easily

# ── VPC Outputs ────────────────────────────────────────────────────
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

# ── EKS Outputs ────────────────────────────────────────────────────
output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

# ── MSK Outputs ────────────────────────────────────────────────────
output "msk_bootstrap_brokers" {
  description = "Kafka plaintext broker connection string"
  value       = module.msk.bootstrap_brokers
}

output "msk_bootstrap_brokers_tls" {
  description = "Kafka TLS broker connection string"
  value       = module.msk.bootstrap_brokers_tls
}

output "msk_zookeeper_connect" {
  description = "ZooKeeper connection string"
  value       = module.msk.zookeeper_connect_string
}