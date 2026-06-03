# Rôles Ansible LOGISTIA

Ce dossier contient les rôles applicatifs du projet.

Chaque rôle a une responsabilité unique et correspond à une machine ou une fonction précise de l'infrastructure LOGISTIA.

## Rôles du projet

| Rôle | Machine cible | Responsabilité |
|------|---------------|----------------|
| `logistia-common` | toutes | paquets de base, rsyslog vers soc-logistia |
| `logistia-hardening` | toutes | SSH, sysctl, auditd |
| `logistia-router` | router-logistia | NAT, nftables, WireGuard, interfaces VLAN |
| `logistia-app` | app-logistia | Nginx HTTPS, Dolibarr ERP, Traccar IoT |
| `logistia-db` | db-logistia | MariaDB, base logistia-dolibarr |
| `logistia-devops` | devops-logistia | GitHub Runner, Terraform, Ansible |
| `logistia-soc` | soc-logistia | Wazuh Manager, Prometheus, Grafana, Syslog-ng |
| `logistia-ia` | ia-logistia | Ollama, Mistral, logistia-analyzer.py |
| `logistia-backup` | backup-logistia | rsync 3-2-1, cron quotidien |

## Structure d'un rôle

Chaque rôle contient :

- `tasks/main.yml` — tâches à appliquer sur la machine cible
- `handlers/main.yml` — redémarrages de services déclenchés par les tâches

Les handlers ne s'exécutent que si la tâche associée a modifié quelque chose. Cela évite de redémarrer un service dont la configuration n'a pas changé.

## Idempotence

Les modules Ansible sont idempotents. Une tâche peut être rejouée sans refaire inutilement la même action. Relancer `logistia-site.yml` sur une infrastructure déjà configurée ne cause aucun effet de bord.
