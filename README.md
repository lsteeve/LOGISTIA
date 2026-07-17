# LOGISTIA — Infrastructure SOC / SOAR as Code

Plateforme SOC (Security Operations Center) complète, déployée en **Infrastructure as Code**
sur Proxmox, combinant SIEM, CTI et SOAR avec automatisation Terraform + Ansible et
pipeline CI/CD GitHub Actions.

> Projet Mastère ISRC — Centre de formation Laser

---

## Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Chaîne de détection et réponse](#chaîne-de-détection-et-réponse)
- [Déploiement](#déploiement)
- [Structure du dépôt](#structure-du-dépôt)
- [Sécurité](#sécurité)

---

## Vue d'ensemble

LOGISTIA est une infrastructure de supervision et de réponse à incident conçue pour
une PME de transport / logistique fictive. Elle démontre une chaîne SOC complète :
détection d'un événement de sécurité, création automatique d'une alerte, enrichissement
par renseignement sur les menaces (CTI), et investigation.

Objectifs pédagogiques :

- Architecture réseau segmentée (VLAN)
- Provisionnement automatisé (Terraform sur Proxmox)
- Configuration idempotente (Ansible)
- Intégration continue et déploiement (GitHub Actions)
- Supervision (Prometheus / Grafana)
- SIEM et réponse à incident (Wazuh, TheHive, Cortex, MISP)

---

## Architecture

### Plan réseau

```
Internet
   |
[Box FAI] 192.168.1.0/24
   |
[pfSense]  WAN em0 (bridge) -- LAN2 em2 : 192.168.10.254
   |
[router-logistia] 192.168.10.151  (NAT + forwarding nftables)
   |
   +-- VLAN APP     10.10.10.0/24   app-logistia
   +-- VLAN DB      10.20.20.0/24   db-logistia
   +-- VLAN DEVOPS  10.30.30.0/24   devops-logistia
   +-- VLAN SOC     10.40.40.0/24   soc / misp / cortex / thehive
   +-- VLAN IA      10.50.50.0/24   ia-logistia
   +-- VLAN BACKUP  10.60.60.0/24   backup-logistia
```

### Machines virtuelles

| VM  | VMID | IP            | Rôle                                   | vCPU | RAM   |
|-----|------|---------------|----------------------------------------|------|-------|
| router  | 101 | 192.168.10.151 | Routeur / pare-feu nftables          | 2 | 2 Go  |
| app     | 102 | 10.10.10.10   | Application (Dolibarr / nginx)         | 2 | 4 Go  |
| db      | 103 | 10.20.20.10   | Base de données MariaDB                | 2 | 4 Go  |
| devops  | 104 | 10.30.30.10   | Runner CI/CD, Terraform, Ansible       | 2 | 4 Go  |
| soc     | 105 | 10.40.40.10   | Wazuh, Prometheus, Grafana             | 2 | 12 Go |
| ia      | 106 | 10.50.50.10   | Modèle IA (Ollama)                     | 2 | 12 Go |
| backup  | 107 | 10.60.60.10   | Sauvegardes                            | 2 | 2 Go  |
| misp    | 108 | 10.40.40.20   | Threat Intelligence (MISP)             | 3 | 8 Go  |
| cortex  | 109 | 10.40.40.30   | Moteur d'analyse (Cortex)              | 4 | 8 Go  |
| thehive | 110 | 10.40.40.40   | Gestion d'incidents (TheHive)          | 4 | 12 Go |

> Les VM 108/109/110 utilisent `cpu_type = host` (requis pour NumPy, Java/Lucene et Cassandra).

---

## Stack technique

| Domaine            | Outils                                            |
|--------------------|---------------------------------------------------|
| Hyperviseur        | Proxmox VE                                        |
| IaC                | Terraform (provider Proxmox)                       |
| Configuration      | Ansible (rôles idempotents)                        |
| CI/CD              | GitHub Actions (self-hosted runner)               |
| SIEM               | Wazuh 4.14 (manager + indexer OpenSearch + dashboard) |
| CTI                | MISP                                              |
| Analyse            | Cortex + Elasticsearch                            |
| SOAR               | TheHive 5 (Cassandra + Elasticsearch + MinIO)     |
| Supervision        | Prometheus + Grafana                              |
| Conteneurisation   | Docker / Docker Compose (MISP, Cortex, TheHive)   |

---

## Chaîne de détection et réponse

```
   ┌─────────┐   alerte    ┌──────────┐   enrichit   ┌────────┐  confirme  ┌──────┐
   │  Wazuh  │ ──────────► │ TheHive  │ ───────────► │ Cortex │ ─────────► │ MISP │
   │  SIEM   │             │  SOAR    │              │ analyse│            │ CTI  │
   └─────────┘             └──────────┘              └────────┘            └──────┘
   détection                création                 analyzers            renseignement
   d'événement              d'alerte/case            (IP, hash...)        sur menaces
```

1. **Wazuh** détecte un événement (règle de niveau ≥ 7) sur un agent.
2. Un script d'intégration (`custom-w2thive`) crée automatiquement une **alerte TheHive**.
3. Depuis TheHive, un analyste lance les **analyzers Cortex** sur les observables.
4. **Cortex** interroge **MISP** pour confirmer si un indicateur est une menace connue.

---

## Déploiement

Le déploiement complet est piloté par le pipeline CI/CD (from scratch) :

```bash
# 1. Provisionnement des VM (Terraform)
cd infra/terraform
terraform init
terraform apply

# 2. Configuration (Ansible)
cd ../../ansible
ansible-playbook -i logistia-inventory.ini playbooks/logistia-site.yml \
  --private-key ~/.ssh/logistia_ed25519
```

Déploiement ciblé d'un seul composant :

```bash
ansible-playbook -i logistia-inventory.ini playbooks/logistia-site.yml \
  --limit logistia-soc --private-key ~/.ssh/logistia_ed25519
```

Voir [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) pour la procédure détaillée.

---

## Structure du dépôt

```
logistia/
├── infra/
│   └── terraform/
│       ├── main.tf                 # déclaration des 10 VM
│       ├── variables.tf
│       ├── modules/logistia-vm/    # module VM réutilisable (cpu_type paramétrable)
│       └── cloudinit/              # cloud-init (DNS, user, paquets de base)
├── ansible/
│   ├── logistia-inventory.ini      # inventaire (10 hôtes)
│   ├── playbooks/
│   │   └── logistia-site.yml       # playbook principal
│   ├── group_vars/
│   └── roles/
│       ├── logistia-common         # config commune
│       ├── logistia-hardening      # durcissement CIS
│       ├── logistia-router         # NAT / forwarding / nftables
│       ├── logistia-app            # Dolibarr
│       ├── logistia-db             # MariaDB
│       ├── logistia-devops         # runner, Docker
│       ├── logistia-soc            # Wazuh (manager+indexer+dashboard), Prometheus, Grafana
│       ├── logistia-ia             # Ollama
│       ├── logistia-backup         # sauvegardes
│       ├── logistia-misp           # MISP (Docker)
│       ├── logistia-cortex         # Cortex + Elasticsearch (Docker)
│       └── logistia-thehive        # TheHive + Cassandra + ES + MinIO (Docker)
├── .github/workflows/              # pipelines CI/CD
└── docs/                           # documentation
```

---

## Sécurité

- Segmentation réseau en 6+ VLAN, base de données isolée du réseau exposé.
- Durcissement CIS niveau 1 (rôle `logistia-hardening`).
- Pare-feu nftables sur le routeur (politique `drop` par défaut, règles explicites).
- Secrets gérés hors du dépôt (`.gitignore` couvre vault, `.env`, clés, tfvars).
- Authentification par clé SSH (pas de mot de passe).

> ⚠️ Cet environnement est un **lab pédagogique**. Certains secrets de démonstration
> figurent dans les valeurs par défaut pour faciliter le déploiement ; en production,
> utiliser Ansible Vault et régénérer toutes les clés.

---

## Auteur

Projet réalisé dans le cadre du Mastère ISRC.
