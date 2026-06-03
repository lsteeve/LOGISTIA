# Playbooks LOGISTIA

Ce dossier contient le point d'entrée Ansible du projet.

`logistia-site.yml` applique tous les rôles dans un ordre contrôlé.

## Ordre d'exécution

1. `logistia-common` — paquets de base et rsyslog sur toutes les machines
2. `logistia-hardening` — durcissement SSH et sysctl sur toutes les machines
3. `logistia-router` — NAT, nftables, WireGuard sur router-logistia
4. `logistia-app` — Nginx, Dolibarr, Traccar sur app-logistia
5. `logistia-db` — MariaDB sur db-logistia
6. `logistia-devops` — GitHub Runner, Terraform sur devops-logistia
7. `logistia-soc` — Wazuh, Prometheus, Grafana, Syslog sur soc-logistia
8. `logistia-ia` — Ollama, Mistral, logistia-analyzer sur ia-logistia
9. `logistia-backup` — rsync 3-2-1 sur backup-logistia
10. Vérification finale — qemu-guest-agent actif sur toutes les machines

## Pourquoi le routeur est configuré en premier

`router-logistia` fournit le NAT pour toutes les autres machines. Sans lui, les machines des VLANs internes ne peuvent pas accéder à Internet pour télécharger les paquets apt. Il est donc configuré avant les rôles applicatifs.

## Pourquoi `become: true`

Les rôles installent des paquets, modifient `/etc`, créent des utilisateurs et démarrent des services. Ces opérations nécessitent les droits root. `become: true` indique à Ansible d'élever les privilèges avec sudo.
