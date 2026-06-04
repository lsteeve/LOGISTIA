output "router_logistia_ip" {
  value       = module.router_logistia.ip
  description = "router-logistia — NAT nftables VLAN"
}

output "app_logistia_ip" {
  value       = module.app_logistia.ip
  description = "app-logistia — Nginx Dolibarr Traccar"
}

output "db_logistia_ip" {
  value       = module.db_logistia.ip
  description = "db-logistia — MariaDB VLAN Data"
}

output "devops_logistia_ip" {
  value       = module.devops_logistia.ip
  description = "devops-logistia — GitHub Runner Terraform Ansible"
}

output "soc_logistia_ip" {
  value       = module.soc_logistia.ip
  description = "soc-logistia — Wazuh Prometheus Grafana Syslog"
}

output "ia_logistia_ip" {
  value       = module.ia_logistia.ip
  description = "ia-logistia — Ollama Mistral Isolation Forest"
}

output "backup_logistia_ip" {
  value       = module.backup_logistia.ip
  description = "backup-logistia — rsync PBS 3-2-1"
}
