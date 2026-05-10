##########################################################
# 0. プロバイダー設定
##########################################################
provider "google" {
  project = var.project_id
  region  = var.region
}

##########################################################
# 1. Cloud Logging 設定
##########################################################

# ログ集積用データセット
resource "google_bigquery_dataset" "log_dataset" {
  dataset_id = var.dataset_id
  location   = var.region
}

resource "google_logging_project_sink" "my_logging_sink" {
  name        = "my-log-sink"
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${var.dataset_id}"
  filter      = "jsonPayload.request_id:*"
}

# 権限付与
resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = google_logging_project_sink.my_logging_sink.writer_identity
}

##########################################################
# 2. VPCネットワーク
##########################################################
resource "google_compute_network" "vpc_network" {
  name                    = "ocr-vpc"
  auto_create_subnetworks = false
}

##########################################################
# 3. サブネット
##########################################################
resource "google_compute_subnetwork" "ocr_subnet" {
  name          = "ocr-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc_network.id

  secondary_ip_range {
    range_name    = "pod-ranges"
    ip_cidr_range = "192.168.16.0/20"
  }
  secondary_ip_range {
    range_name    = "services-ranges"
    ip_cidr_range = "192.168.32.0/20"
  }
}

##########################################################
# 4. GKEクラスター
##########################################################
resource "google_container_cluster" "primary" {
  name     = "ocr-cluster"
  location = "${var.region}-a" # リージョンに -a を付与してゾーン指定
  deletion_protection = false

  network    = google_compute_network.vpc_network.name
  subnetwork = google_compute_subnetwork.ocr_subnet.name

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "pod-ranges"
    services_secondary_range_name = "services-ranges"
  }
}

##########################################################
# 5. オートスケーリング対応ノードプール
##########################################################
resource "google_container_node_pool" "primary_nodes_hpa" {
  name       = "ocr-node-pool-hpa"
  location   = google_container_cluster.primary.location
  cluster    = google_container_cluster.primary.name
  
  initial_node_count = 1
  autoscaling {
    min_node_count = 1
    max_node_count = 6
  }

  node_config {
    spot         = true
    machine_type = "e2-standard-2" # 2CPU/8GBメモリ
    
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

##########################################################
# 6. Artifact Registry
##########################################################
resource "google_artifact_registry_repository" "ocr_repo" {
  location      = var.region
  repository_id = "ocr-images"
  format        = "DOCKER"
}

##########################################################
# 7. 出力
##########################################################
output "repository_url" {
  value = "${google_artifact_registry_repository.ocr_repo.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.ocr_repo.repository_id}"
}
