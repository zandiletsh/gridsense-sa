variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for Kafka brokers"
  type        = list(string)
}

variable "kafka_version" {
  description = "Kafka version"
  type        = string
  default     = "3.5.1"
}

variable "number_of_brokers" {
  description = "Number of Kafka broker nodes"
  type        = number
  default     = 2
}

variable "broker_instance_type" {
  description = "Instance type for Kafka brokers"
  type        = string
  default     = "kafka.t3.small"
}

variable "broker_volume_size" {
  description = "EBS volume size in GB per broker"
  type        = number
  default     = 20
}

variable "eks_security_group_id" {
  description = "Security group ID of the EKS cluster"
  type        = string
}
