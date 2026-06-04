# Rôles Ansible LOGISTIA

| Rôle | Machine | Responsabilité |
|------|---------|----------------|
| `logistia-common` | toutes | paquets de base, rsyslog |
| `logistia-hardening` | toutes | SSH, sysctl, auditd |
| `logistia-router` | router-logistia | NAT, nftables, VLAN |
| `logistia-app` | app-logistia | Nginx, Dolibarr, Traccar |
| `logistia-db` | db-logistia | MariaDB, base logistia-dolibarr |
| `logistia-devops` | devops-logistia | GitHub Runner, Terraform |
| `logistia-soc` | soc-logistia | Wazuh, Prometheus, Grafana, Syslog |
| `logistia-ia` | ia-logistia | Ollama, Mistral, logistia-scanner |
| `logistia-backup` | backup-logistia | rsync, PBS, cron |

## Structure d'un rôle

```
logistia-xxx/
  tasks/main.yml    — tâches à appliquer
  handlers/main.yml — redémarrages de services
```

Les handlers ne s'exécutent que si la tâche associée a modifié quelque chose.

## Idempotence

Tous les modules Ansible utilisés sont idempotents. Rejouer `logistia-site.yml` sur une infrastructure déjà configurée ne cause aucun effet de bord.
