# infra/environments/dev/namespaces.tf
# Kubernetes namespaces defined as code.
# This ensures namespaces are recreated automatically if the cluster
# is destroyed and rebuilt — no manual kubectl commands needed.

resource "kubernetes_namespace" "ingestion" {
  metadata {
    name = "ingestion"
    labels = {
      environment = "dev"
      project     = "gridsense"
      layer       = "ingestion"
    }
  }
}

resource "kubernetes_namespace" "processing" {
  metadata {
    name = "processing"
    labels = {
      environment = "dev"
      project     = "gridsense"
      layer       = "processing"
    }
  }
}

resource "kubernetes_namespace" "storage" {
  metadata {
    name = "storage"
    labels = {
      environment = "dev"
      project     = "gridsense"
      layer       = "storage"
    }
  }
}

resource "kubernetes_namespace" "delivery" {
  metadata {
    name = "delivery"
    labels = {
      environment = "dev"
      project     = "gridsense"
      layer       = "delivery"
    }
  }
}

resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      environment = "dev"
      project     = "gridsense"
      layer       = "monitoring"
    }
  }
}