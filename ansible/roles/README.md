# Les rôles Ansible — LOGISTIA

Un **rôle** Ansible regroupe toutes les tâches nécessaires pour configurer une fonction précise. LOGISTIA compte **13 rôles**. Certains s'appliquent à toutes les machines (rôles transverses), d'autres à une machine précise (rôles applicatifs).

## Rôles transverses (appliqués à toutes les machines)

| Rôle | Fonction |
|------|----------|
| **logistia-common** | Paquets de base, agent QEMU, configuration système commune, envoi des journaux vers le SOC. Répare aussi automatiquement un gestionnaire de paquets interrompu. |
| **logistia-hardening** | Durcissement de sécurité : configuration SSH, paramètres système sécurisés, journalisation d'audit. |
| **logistia-wazuh-agent** | Installe et enregistre l'agent Wazuh sur chaque machine (sauf le SOC), afin qu'elle remonte ses journaux au SIEM. |

## Rôles d'infrastructure

| Rôle | Machine | Fonction |
|------|---------|----------|
| **logistia-router** | router-logistia | Configure les interfaces VLAN, le NAT et le pare-feu nftables (filtrage inter-VLAN). Rend le routage persistant aux redémarrages. |
| **logistia-backup** | backup-logistia | Met en place les sauvegardes (Proxmox Backup Server, stratégie 3-2-1). |

## Rôles applicatifs

| Rôle | Machine | Fonction |
|------|---------|----------|
| **logistia-app** | app-logistia | Serveur web : Nginx (HTTPS), ERP Dolibarr, suivi GPS Traccar. Journalise l'activité réseau applicative. |
| **logistia-db** | db-logistia | Base de données MariaDB. |
| **logistia-devops** | devops-logistia | Runner GitHub Actions self-hosted et outils d'automatisation (Terraform, Ansible). |

## Rôles du SOC et de la sécurité

| Rôle | Machine | Fonction |
|------|---------|----------|
| **logistia-soc** | soc-logistia | Cœur du SOC : installe le SIEM Wazuh (manager, indexer, tableau de bord), la supervision (Prometheus, Grafana), les règles de détection personnalisées, la synchronisation avec MISP, la réponse automatique (Active Response) et le scanner IA. |
| **logistia-misp** | misp-logistia | MISP : base de renseignement sur les menaces (Threat Intelligence). |
| **logistia-cortex** | cortex-logistia | Cortex : analyse automatisée d'observables. |
| **logistia-thehive** | thehive-logistia | TheHive : gestion et suivi des incidents de sécurité. |

## Rôle de l'intelligence artificielle

| Rôle | Machine | Fonction |
|------|---------|----------|
| **logistia-ia** | ia-logistia | Installe Ollama et télécharge le modèle d'IA local (phi3), qui sert de moteur d'analyse aux incidents détectés par le SOC. |

## Comment les rôles travaillent ensemble

Les rôles ne sont pas indépendants : ils forment un ensemble cohérent.

- Les rôles **transverses** préparent chaque machine et installent l'agent Wazuh qui **remonte les journaux au SOC**.
- Le rôle **logistia-soc** centralise ces journaux, détecte les menaces, et fait appel au **modèle d'IA** (installé par **logistia-ia**) pour analyser les incidents.
- Les rôles **misp / cortex / thehive** apportent le renseignement et l'investigation.
- Le rôle **logistia-router** garantit que seuls les flux nécessaires circulent entre ces différentes zones.

Le fonctionnement complet de cette chaîne est décrit dans [docs/SOC-SOAR.md](../../docs/SOC-SOAR.md).
