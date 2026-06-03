variable "proxmox_url" {
  description = "URL de l'API Proxmox"
  type        = string
  default     = "https://192.168.10.150:8006"
}

variable "proxmox_user" {
  description = "Compte Terraform Proxmox"
  type        = string
  default     = "terraform-logistia@pve"
}

variable "proxmox_token" {
  description = "Valeur du token API logistia-token"
  type        = string
  sensitive   = true
}

variable "proxmox_ssh_password" {
  description = "Mot de passe SSH root Proxmox pour upload cloud-init"
  type        = string
  sensitive   = true
  default     = ""
}

variable "proxmox_node" {
  description = "Nom du noeud Proxmox cible"
  type        = string
  default     = "PVE"
}

variable "proxmox_storage" {
  description = "Stockage Proxmox pour les disques"
  type        = string
  default     = "local-lvm"
}

variable "ssh_public_key" {
  description = "Cle SSH publique logistia injectee par cloud-init"
  type        = string
  sensitive   = true
}

variable "vmid_start" {
  description = "Base des VMIDs LOGISTIA"
  type        = number
  default     = 100
}
