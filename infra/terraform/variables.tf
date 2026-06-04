variable "proxmox_url" {
  description = "URL de l'API Proxmox"
  type        = string
}

variable "proxmox_user" {
  description = "Compte Terraform Proxmox — terraform-logistia@pve"
  type        = string
}

variable "proxmox_token" {
  description = "Valeur du token logistia-token"
  type        = string
  sensitive   = true
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
  description = "Cle publique logistia_ed25519 injectee par cloud-init"
  type        = string
  sensitive   = true
}

variable "vmid_start" {
  description = "Base des VMIDs LOGISTIA"
  type        = number
  default     = 100
}
