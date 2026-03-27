#This file creates the S3 bucket and DynaminDB table
#that Terraform uses to store its state remotely

terraform {
    required_version = ">= 1.5.0"

    required_providers {
      aws = {
        source = "hashicorp/aws"
        version = "~> 5.0"
      }
    }

     # Add this block — tells Terraform to store state in S3
  backend "s3" {
    bucket         = "gridsense-terraform-state-173679718835"
    key            = "global/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "gridsense-terraform-locks"
    encrypt        = true
}
}

provider "aws" {
    region = "us-east-1"
}

#____S3 Bucket__________________________________________________________________________________________________________________________________________________________________________
#This bucket stores the terraform.tfstate file all environments.
#Versioning is enabled so we can recover from accidental state corruption.

resource "aws_s3_bucket" "terraform_state" {
    bucket = "gridsense-terraform-state-173679718835"

    lifecycle {
        prevent_destroy = true
    }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
    bucket = aws_s3_bucket.terraform_state.id

    versioning_configuration {
        status = "Enabled"
    }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
    bucket = aws_s3_bucket.terraform_state.id

    rule {
        apply_server_side_encryption_by_default {
          sse_algorithm = "AES256"
        }
    }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
    bucket = aws_s3_bucket.terraform_state.id

    block_public_acls = true
    block_public_policy = true
    ignore_public_acls = true
    restrict_public_buckets = true
  
}

#--DynanoDB Table-------------------------------------------------------------------------------------------------------------------------------------------------------------------
#This table acts as a lock. When a terraform apply starts,
# it writes a record here. If another apply tries to run at the 
# same time, it sees the lock and waits.

resource "aws_dynamodb_table" "terraform_locks" {
    name = "gridsense-terraform-locks"
    billing_mode = "PAY_PER_REQUEST"
    hash_key = "LockID"

    attribute {
      name = "LockID"
      type ="S"
    }
}