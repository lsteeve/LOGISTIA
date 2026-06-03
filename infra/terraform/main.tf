terraform {
  backend "local" {}

  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.46"
    }
  }
}

provider "proxmox" {
  endpoint  = var.proxmox_url
  api_token = "${var.proxmox_user}=${var.proxmox_token}"
  insecure  = true

  ssh {
    agent    = false
    username = "root"
    password = var.proxmox_ssh_password
  }
}

resource "proxmox_virtual_environment_file" "logistia_cloudinit" {
  content_type = "snippets"
  datastore_id = "local"
  node_name    = var.proxmox_node

  source_raw {
    data      = file("${path.module}/cloudinit/logistia-cloudinit.yaml")
    file_name = "logistia-cloudinit.yaml"
  }
}

module "router_logistia" {
  source      = "./modules/logistia-vm"
  name        = "router-logistia"
  node_name   = var.proxmox_node
  vmid        = var.vmid_start + 1
  cores       = 2
  memory      = 2048
  disk_size   = 20
  datastore   = var.proxmox_storage
  bridge      = "vmbr0"
  ip          = "192.168.10.151/24"
  gateway     = "192.168.10.254"
  ssh_key     = var.ssh_public_key
  userdata_id = proxmox_virtual_environment_file.logistia_cloudinit.id
  extra_nets  = ["vmbr1", "vmbr2", "vmbr3", "vmbr4", "vmbr5", "vmbr6"]
}

module "app_logistia" {
  source      = "./modules/logistia-vm"
  name        = "app-logistia"
  node_name   = var.proxmox_node
  vmid        = var.vmid_start + 2
  cores       = 2
  memory      = 4096
  disk_size   = 30
  datastore   = var.proxmox_storage
  bridge      = "vmbr1"
  ip          = "10.10.10.10/24"
  gateway     = "10.10.10.1"
  ssh_key     = var.ssh_public_key
  userdata_id = proxmox_virtual_environment_file.logistia_cloudinit.id
  extra_nets  = []
}

module "db_logistia" {
  source      = "./modules/logistia-vm"
  name        = "db-logistia"
  node_name   = var.proxmox_node
  vmid        = var.vmid_start + 3
  cores       = 2
  memory      = 4096
  disk_size   = 40
  datastore   = var.proxmox_storage
  bridge      = "vmbr2"
  ip          = "10.20.20.10/24"
  gateway     = "10.20.20.1"
  ssh_key     = var.ssh_public_key
  userdata_id = proxmox_virtual_environment_file.logistia_cloudinit.id
  extra_nets  = []
}

module "devops_logistia" {
  source      = "./modules/logistia-vm"
  name        = "devops-logistia"
  node_name   = var.proxmox_node
  vmid        = var.vmid_start + 4
  cores       = 2
  memory      = 4096
  disk_size   = 30
  datastore   = var.proxmox_storage
  bridge      = "vmbr3"
  ip          = "10.30.30.10/24"
  gateway     = "10.30.30.1"
  ssh_key     = var.ssh_public_key
  userdata_id = proxmox_virtual_environment_file.logistia_cloudinit.id
  extra_nets  = []
}

module "soc_logistia" {
  source      = "./modules/logistia-vm"
  name        = "soc-logistia"
  node_name   = var.proxmox_node
  vmid        = var.vmid_start + 5
  cores       = 2
  memory      = 12288
  disk_size   = 60
  datastore   = var.proxmox_storage
  bridge      = "vmbr4"
  ip          = "10.40.40.10/24"
  gateway     = "10.40.40.1"
  ssh_key     = var.ssh_public_key
  userdata_id = proxmox_virtual_environment_file.logistia_cloudinit.id
  extra_nets  = []
}

module "ia_logistia" {
  source      = "./modules/logistia-vm"
  name        = "ia-logistia"
  node_name   = var.proxmox_node
  vmid        = var.vmid_start + 6
  cores       = 2
  memory      = 12288
  disk_size   = 40
  datastore   = var.proxmox_storage
  bridge      = "vmbr5"
  ip          = "10.50.50.10/24"
  gateway     = "10.50.50.1"
  ssh_key     = var.ssh_public_key
  userdata_id = proxmox_virtual_environment_file.logistia_cloudinit.id
  extra_nets  = []
}

module "backup_logistia" {
  source      = "./modules/logistia-vm"
  name        = "backup-logistia"
  node_name   = var.proxmox_node
  vmid        = var.vmid_start + 7
  cores       = 1
  memory      = 2048
  disk_size   = 100
  datastore   = var.proxmox_storage
  bridge      = "vmbr6"
  ip          = "10.60.60.10/24"
  gateway     = "10.60.60.1"
  ssh_key     = var.ssh_public_key
  userdata_id = proxmox_virtual_environment_file.logistia_cloudinit.id
  extra_nets  = []
}
