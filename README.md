# LOGISTIA — Infrastructure sécurisée et supervisée sur Proxmox

[![LOGISTIA CI](https://github.com/lsteeve/LOGISTIA/actions/workflows/logistia-ci.yml/badge.svg)](https://github.com/lsteeve/LOGISTIA/actions/workflows/logistia-ci.yml)
[![LOGISTIA Deploy](https://github.com/lsteeve/LOGISTIA/actions/workflows/logistia-deploy.yml/badge.svg)](https://github.com/lsteeve/LOGISTIA/actions/workflows/logistia-deploy.yml)


LOGISTIA est l'infrastructure informatique centrale d'une PME de **transport et logistique**. Elle héberge les applications métier (ERP de gestion, suivi GPS des véhicules) auxquelles se connectent les entrepôts et sites distants de l'entreprise, et intègre une chaîne complète de cybersécurité : supervision, détection des menaces, analyse par intelligence artificielle et réponse automatisée aux incidents.

L'ensemble est **déployé automatiquement** grâce à l'Infrastructure as Code (Terraform + Ansible) et à un pipeline CI/CD (GitHub Actions), sur un hyperviseur **Proxmox VE 9**.

## Équipe projet

| Membre | Rôle | Responsabilité principale |
|--------|------|---------------------------|
| **Steeve Larive** | Chef de projet · Analyste cybersécurité | SOC, détection, SOAR, durcissement |
| **Gabriel Malka** | Chef de projet · Ingénieur DevOps / IaC | Terraform, Ansible, pipeline CI/CD |
| **Silamakan Traore** | Chef de projet · Ingénieur IA / Data | Brique d'intelligence artificielle |

## Objectifs du projet

- Concevoir une **architecture virtualisée segmentée** (VLAN) sur Proxmox.
- **Automatiser** entièrement le déploiement (Terraform pour les VM, Ansible pour la configuration).
- Mettre en place un **pipeline GitHub Actions** (tests, sécurité, déploiement).
- Déployer un **SOC** complet : centralisation des logs, supervision, détection.
- Intégrer un **modèle d'IA open source local** analysant les logs et détectant les comportements suspects.
- Automatiser la **réponse aux incidents** (blocage des menaces).

## Architecture

L'infrastructure est hébergée sur un serveur **Proxmox VE 9** et découpée en **VLAN** isolés. Un routeur interne applique un filtrage strict entre les segments (politique « tout est bloqué sauf autorisation explicite »).

### Plan réseau

```text
                    Proxmox VE 9 — 192.168.10.150
                              │
                    ┌─────────────────────┐
                    │   router-logistia    │  routeur interne
                    │   192.168.10.151     │  (nftables : NAT + filtrage inter-VLAN)
                    └──────────┬──────────┘
                               │
   ┌──────────────┬───────────┼───────────┬──────────────┬─────────────┐
   ▼              ▼           ▼           ▼              ▼             ▼
 VLAN10 DMZ   VLAN20 Data  VLAN30      VLAN40 SOC     VLAN50 IA     VLAN60 Backup
 app-logistia db-logistia  DevOps    ┌ soc-logistia  ia-logistia   backup-logistia
 10.10.10.10  10.20.20.10  devops    ├ misp-logistia 10.50.50.10   10.60.60.10
                           10.30.30.10├ cortex-logistia
                                      └ thehive-logistia
                                                        VLAN70 Admin — 10.70.70.0/24
```

### VLAN

| VLAN | Sous-réseau | Zone | Contenu |
|------|-------------|------|---------|
| VLAN10 | 10.10.10.0/24 | DMZ | Serveur web applicatif (exposé) |
| VLAN20 | 10.20.20.0/24 | Data | Base de données (isolée) |
| VLAN30 | 10.30.30.0/24 | DevOps | Runner CI/CD, outils d'automatisation |
| VLAN40 | 10.40.40.0/24 | SOC | SIEM, supervision, Threat Intelligence |
| VLAN50 | 10.50.50.0/24 | IA | Moteur d'analyse par intelligence artificielle |
| VLAN60 | 10.60.60.0/24 | Backup | Sauvegardes |
| VLAN70 | 10.70.70.0/24 | Admin | Poste d'administration (SSH, accès Proxmox) |

### Machines virtuelles

| VMID | Nom | IP | VLAN | vCPU | RAM | Services |
|------|-----|----|------|------|-----|---------|
| 101 | router-logistia | 192.168.10.151 | — | 2 | 2 Go | Routeur nftables (NAT, filtrage) |
| 102 | app-logistia | 10.10.10.10 | DMZ | 2 | 4 Go | Nginx, Dolibarr (ERP), Traccar (suivi GPS) |
| 103 | db-logistia | 10.20.20.10 | Data | 2 | 4 Go | MariaDB |
| 104 | devops-logistia | 10.30.30.10 | DevOps | 2 | 4 Go | Runner GitHub Actions, Terraform, Ansible |
| 105 | soc-logistia | 10.40.40.10 | SOC | 4 | 12 Go | Wazuh, Prometheus, Grafana, scanner IA |
| 108 | misp-logistia | 10.40.40.20 | SOC | 3 | 8 Go | MISP (Threat Intelligence) |
| 109 | cortex-logistia | 10.40.40.30 | SOC | 4 | 8 Go | Cortex (analyse d'observables) |
| 110 | thehive-logistia | 10.40.40.40 | SOC | 4 | 12 Go | TheHive (gestion d'incidents) |
| 106 | ia-logistia | 10.50.50.10 | IA | 4 | 12 Go | Ollama (modèle phi3), détection d'anomalies |
| 107 | backup-logistia | 10.60.60.10 | Backup | 1 | 2 Go | Proxmox Backup Server, sauvegardes 3-2-1 |

Un schéma illustré est disponible : [docs/architecture-schema.html](docs/architecture-schema.html).
Détails complets : [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Déploiement

L'infrastructure se déploie de **deux façons**, décrites en détail dans [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) :

1. **Manuellement** — Terraform crée les VM, puis Ansible les configure.
2. **Automatiquement** — le workflow GitHub Actions `LOGISTIA Deploy` exécute Terraform et Ansible via un runner interne.

## Documentation

| Document | Contenu |
|----------|---------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture détaillée : VLAN, VM, flux réseau |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Déploiement manuel et automatisé (pas à pas) |
| [docs/IA.md](docs/IA.md) | Brique d'intelligence artificielle |
| [docs/SOC-SOAR.md](docs/SOC-SOAR.md) | Fonctionnement du SOC, du SOAR et de leur lien avec l'IA |
| [docs/CYBERSECURITE.md](docs/CYBERSECURITE.md) | Segmentation, détection, durcissement |
| [ansible/README.md](ansible/README.md) | Organisation et fonctionnement d'Ansible |
| [ansible/roles/README.md](ansible/roles/README.md) | Description de chaque rôle |
| [ansible/playbooks/README.md](ansible/playbooks/README.md) | Ordre d'exécution du playbook |
| [ansible/group_vars/README.md](ansible/group_vars/README.md) | Variables et gestion des secrets |
| [infra/README.md](infra/README.md) | Infrastructure Terraform |

## Structure du dépôt

```text
LOGISTIA/
├── .github/workflows/       # Pipelines CI/CD (intégration + déploiement)
│   ├── logistia-ci.yml
│   └── logistia-deploy.yml
├── ansible/                 # Configuration des serveurs
│   ├── logistia-inventory.ini
│   ├── playbooks/
│   ├── group_vars/
│   └── roles/               # 13 rôles (voir ansible/roles/README.md)
├── infra/terraform/         # Création des VM sur Proxmox
│   ├── main.tf
│   ├── variables.tf
│   └── modules/logistia-vm/
└── docs/                    # Documentation détaillée
```

## Accès au dépôt

- **Dépôt** : `https://github.com/lsteeve/LOGISTIA`
- **Branche principale** : `main`
- **CI/CD** : onglet *Actions* du dépôt

---

*Mastère ISRC (Ingénieur Systèmes Réseaux et Cybersécurité) — Année 2 — 2026*
