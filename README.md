# LOGISTIA — Plateforme intelligente de cybersécurité

Projet Mastère ISRC — Déploiement automatisé d'une infrastructure de cybersécurité pour une chaîne logistique connectée.

## Contexte

L'entreprise LOGISTIA exploite plusieurs entrepôts connectés équipés de capteurs IoT (température, RFID) et d'applications web de suivi logistique. Face à l'augmentation des cyberattaques visant les chaînes logistiques, ce projet déploie une infrastructure sécurisée, supervisée et capable de détecter les anomalies grâce à l'intelligence artificielle.

## Architecture

```
Internet
    │
Freebox — IP fixe — redirection UDP 51820
    │
pfSense (routeur lab externe)
    │
Proxmox VE 9 — 192.168.10.150
    │
    ├── router-logistia    192.168.10.151   Routeur NAT nftables WireGuard
    ├── app-logistia       10.10.10.10      VLAN10 DMZ — Nginx Dolibarr Traccar
    ├── db-logistia        10.20.20.10      VLAN20 Data — MariaDB isolée
    ├── devops-logistia    10.30.30.10      VLAN30 DevOps — GitHub Runner
    ├── soc-logistia       10.40.40.10      VLAN40 SOC — Wazuh Prometheus Grafana
    ├── ia-logistia        10.50.50.10      VLAN50 IA — Ollama Mistral
    └── backup-logistia    10.60.60.10      VLAN60 Backup — rsync 3-2-1
```

## Segmentation réseau

| VLAN | Réseau | Machine | Rôle | Exposé Internet |
|------|--------|---------|------|----------------|
| VLAN10 | 10.10.10.0/24 | app-logistia | Application DMZ | Oui — :443 uniquement |
| VLAN20 | 10.20.20.0/24 | db-logistia | Base de données | Non |
| VLAN30 | 10.30.30.0/24 | devops-logistia | DevOps CI/CD | Non |
| VLAN40 | 10.40.40.0/24 | soc-logistia | SOC supervision | Non |
| VLAN50 | 10.50.50.0/24 | ia-logistia | IA détection | Non |
| VLAN60 | 10.60.60.0/24 | backup-logistia | Sauvegarde | Non |

## Flux réseau autorisés

- Internet → app-logistia : HTTPS port 443 uniquement
- app-logistia → db-logistia : MariaDB port 3306
- devops-logistia → toutes machines : SSH port 22
- Toutes machines → soc-logistia : Wazuh 1514, Syslog 514
- soc-logistia → toutes machines : Node Exporter 9100
- ia-logistia → soc-logistia : OpenSearch 9200
- backup-logistia → toutes machines : SSH port 22
- Toutes machines → Internet : NAT masquerade apt

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Hyperviseur | Proxmox VE 9.2 |
| IaC | Terraform bpg/proxmox ~> 0.46 |
| Configuration | Ansible rôles modulaires |
| CI/CD | GitHub Actions |
| OS | Debian 13 Trixie cloud-init |
| Routeur | nftables + WireGuard + dnsmasq |
| Application | Dolibarr ERP + Traccar IoT |
| Base de données | MariaDB VLAN isolé |
| SOC | Wazuh + Syslog-ng + Prometheus + Grafana |
| IA | Ollama + Mistral + Isolation Forest |
| Sauvegarde | rsync règle 3-2-1 |

## Méthode 1 — Déploiement manuel

### Prérequis Proxmox

Créer le template Debian 13 cloud-init avec l'ID 9000 et les bridges vmbr0 à vmbr6.

Voir `infra/terraform/README.md` pour les commandes détaillées.

### Terraform

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Renseigner terraform.tfvars avec les valeurs de l'environnement

terraform init
terraform plan -out=logistia-plan.tfplan
terraform apply logistia-plan.tfplan
```

### Ansible

```bash
# Attendre que cloud-init termine sur toutes les machines
sleep 90

cd ansible
cp group_vars/logistia-all.yml.example group_vars/logistia-all.yml
cp group_vars/logistia-vault.yml.example group_vars/logistia-vault.yml
# Renseigner logistia-vault.yml avec les mots de passe
ansible-vault encrypt group_vars/logistia-vault.yml

ansible-playbook playbooks/logistia-site.yml --ask-vault-pass
```

## Méthode 2 — Déploiement GitHub Actions

Le workflow `logistia-deploy.yml` se déclenche manuellement depuis GitHub Actions.

Il nécessite le runner self-hosted installé sur devops-logistia.

### Secrets GitHub requis

| Secret | Description |
|--------|-------------|
| `PROXMOX_PASSWORD` | Token API Proxmox |
| `PROXMOX_SSH_PASSWORD` | Mot de passe root SSH Proxmox |
| `SSH_PUBLIC_KEY` | Clé publique Ed25519 logistia |
| `ANSIBLE_PRIVATE_KEY` | Clé privée Ed25519 logistia |
| `ANSIBLE_VAULT_PASSWORD` | Mot de passe Ansible Vault |

### Options du workflow

```
terraform_action : plan | apply
run_ansible      : true | false
```

## Accès aux services via WireGuard

| Service | URL |
|---------|-----|
| Proxmox | https://192.168.10.150:8006 |
| Dolibarr ERP | https://10.10.10.10 |
| Traccar IoT | http://10.10.10.10:8082 |
| Wazuh Dashboard | https://10.40.40.10 |
| Grafana | http://10.40.40.10:3000 |
| Prometheus | http://10.40.40.10:9090 |
| Ollama API | http://10.50.50.10:11434 |

## Sécurité

- `terraform.tfvars` et `terraform.tfstate` ignorés par Git
- `logistia-vault.yml` chiffré avec Ansible Vault
- Clé SSH publique uniquement injectée par Terraform
- Secrets fournis par GitHub Actions dans le pipeline
- Flux inter-VLANs filtrés par nftables sur router-logistia

## Structure du dépôt

```
.
├── .github/
│   ├── ACTIONS.md
│   └── workflows/
│       ├── logistia-ci.yml
│       └── logistia-deploy.yml
├── infra/
│   ├── README.md
│   └── terraform/
│       ├── README.md
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tfvars.example
│       ├── cloudinit/logistia-cloudinit.yaml
│       └── modules/logistia-vm/
│           ├── README.md
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
└── ansible/
    ├── README.md
    ├── ansible.cfg
    ├── logistia-inventory.ini
    ├── group_vars/
    │   ├── logistia-all.yml.example
    │   └── logistia-vault.yml.example
    ├── playbooks/
    │   └── logistia-site.yml
    └── roles/
        ├── logistia-common/
        ├── logistia-hardening/
        ├── logistia-router/
        ├── logistia-app/
        ├── logistia-db/
        ├── logistia-devops/
        ├── logistia-soc/
        ├── logistia-ia/
        └── logistia-backup/
```

## Équipe

| Membre | Rôle |
|--------|------|
| Steeve Larive | Chef de projet — Analyste cybersécurité |
| Gabriel | Ingénieur DevOps / IaC |
| Silamakan | Ingénieur IA / Data |
