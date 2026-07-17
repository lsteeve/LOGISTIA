# Guide de déploiement — LOGISTIA

Procédure de déploiement complet de l'infrastructure, du provisionnement des
machines virtuelles jusqu'à la configuration des services SOC.

---

## Prérequis

- Un hôte **Proxmox VE** accessible (API activée).
- Un **template cloud-init** Debian 13 (VMID 9000 dans ce projet).
- Une paire de **clés SSH** dédiée (`logistia_ed25519`).
- Les **secrets** renseignés (voir `group_vars/logistia-vault.yml.example`).

---

## 1. Provisionnement (Terraform)

Le module `logistia-vm` factorise la création de chaque VM. Les trois VM du stack
SOAR (MISP, Cortex, TheHive) surchargent `cpu_type = "host"`.

```bash
cd infra/terraform
terraform init
terraform plan     # vérifier le plan (10 VM à créer)
terraform apply
```

Variables principales (voir `variables.tf`) :

| Variable          | Description                          |
|-------------------|--------------------------------------|
| `proxmox_node`    | Nom du nœud Proxmox                  |
| `proxmox_storage` | Datastore de destination            |
| `vmid_start`      | VMID de base (les VM = start + N)    |
| `ssh_public_key`  | Clé publique injectée par cloud-init |

---

## 2. Configuration (Ansible)

Le playbook `logistia-site.yml` applique les rôles dans l'ordre des dépendances :
commun → durcissement → routeur → services.

```bash
cd ../../ansible

# Déploiement complet
ansible-playbook -i logistia-inventory.ini playbooks/logistia-site.yml \
  --private-key ~/.ssh/logistia_ed25519

# Déploiement ciblé (exemple : uniquement le SOC)
ansible-playbook -i logistia-inventory.ini playbooks/logistia-site.yml \
  --limit logistia-soc --private-key ~/.ssh/logistia_ed25519
```

---

## 3. Ordre de démarrage des services SOC

Certains services ont un premier démarrage long (initialisation de base de données) :

| Service              | Délai de première initialisation                  |
|----------------------|---------------------------------------------------|
| Wazuh indexer        | ~1-2 min (OpenSearch)                             |
| TheHive (Cassandra)  | ~3-10 min (création du keyspace + migration)      |
| Cortex (Elasticsearch)| ~1-2 min                                         |

Les rôles Ansible intègrent des `wait_for` / `until` pour patienter automatiquement.

---

## 4. Vérifications post-déploiement

```bash
# SIEM Wazuh (dashboard)
curl -sk -o /dev/null -w "%{http_code}\n" https://10.40.40.10        # 302

# MISP
curl -sk -o /dev/null -w "%{http_code}\n" https://10.40.40.20        # 200

# Cortex
curl -s  -o /dev/null -w "%{http_code}\n" http://10.40.40.30:9001/api/status  # 200

# TheHive
curl -s  -o /dev/null -w "%{http_code}\n" http://10.40.40.40:9000/api/status  # 200
```

---

## 5. Points de vigilance connus

- **CPU host** obligatoire pour MISP/Cortex/TheHive (instructions vectorielles
  NumPy et JVM/Cassandra). Sans cela, certains conteneurs plantent au démarrage.
- **DNS** : le cloud-init force `8.8.8.8 / 1.1.1.1` (resolv_conf + systemd-resolved)
  pour éviter l'héritage d'un résolveur défaillant.
- **soc-logistia est le manager Wazuh** : ne jamais y installer d'agent Wazuh
  (conflit de paquet qui désinstalle le manager).
- **Règles nftables du routeur** persistées dans `/etc/nftables.conf` (rôle
  `logistia-router`) pour survivre aux redémarrages.

---

## 6. Test de reconstruction complète

Le projet est conçu pour un cycle « détruire et redéployer » :

```bash
cd infra/terraform
terraform destroy      # supprime les 10 VM
terraform apply        # recrée tout depuis zéro
# puis relancer le playbook Ansible complet
```

Aucune intervention manuelle n'est requise : toute la configuration (y compris
l'installation complète de Wazuh indexer + dashboard + filebeat) est dans le code.
