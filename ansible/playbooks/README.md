# Playbooks LOGISTIA

## Ordre d'exécution de logistia-site.yml

1. `logistia-common` — paquets de base et rsyslog sur toutes les machines
2. `logistia-hardening` — durcissement SSH, sysctl, auditd sur toutes les machines
3. `logistia-router` — NAT, nftables, interfaces VLAN sur router-logistia
4. `logistia-app` — Nginx, Dolibarr, Traccar sur app-logistia
5. `logistia-db` — MariaDB sur db-logistia
6. `logistia-devops` — GitHub Runner, Terraform sur devops-logistia
7. `logistia-soc` — Wazuh, Prometheus, Grafana, Syslog-ng sur soc-logistia
8. `logistia-ia` — Ollama, Mistral, logistia-scanner sur ia-logistia
9. `logistia-backup` — rsync, PBS sur backup-logistia
10. Vérification finale — qemu-guest-agent actif sur toutes les machines

## Pourquoi le routeur est configuré en premier

`router-logistia` fournit le NAT pour toutes les autres machines. Sans lui, les machines des VLANs internes ne peuvent pas accéder à Internet pour télécharger les paquets apt.

## Pourquoi `become: true`

Les rôles installent des paquets, modifient `/etc` et démarrent des services. Ces opérations nécessitent les droits root via sudo.
