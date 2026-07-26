# Déploiement — manuel et automatisé

L'infrastructure LOGISTIA se déploie de **deux façons**, qui aboutissent au même résultat. Ce document explique les deux, pas à pas.

- **Méthode 1 — manuelle** : on lance Terraform puis Ansible à la main, depuis un poste d'administration.
- **Méthode 2 — automatisée** : GitHub Actions exécute Terraform et Ansible via un runner interne.

Dans les deux cas, le principe est le même :

```
Terraform  ──►  crée les machines virtuelles sur Proxmox
     puis
Ansible    ──►  configure chaque machine (applications, sécurité, SOC, IA)
```

## Prérequis

- Un serveur **Proxmox VE 9** accessible.
- Un **template de machine** (Debian 13) préparé sur Proxmox, que Terraform clonera.
- Un **jeton d'API Proxmox** autorisant la création de machines.
- Une **paire de clés SSH** dédiée au projet.
- **Terraform** et **Ansible** installés (pour la méthode manuelle).

---

## Méthode 1 — Déploiement manuel

### Étape 1 : créer les machines avec Terraform

Terraform lit une description de l'infrastructure et crée les machines correspondantes sur Proxmox.

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# renseigner : adresse Proxmox, identifiant et jeton d'API, clé SSH publique
terraform init      # initialise Terraform
terraform plan      # affiche ce qui va être créé
terraform apply     # crée réellement les machines
```

À l'issue de cette étape, les dix machines existent sur Proxmox, avec leur réseau configuré et la clé SSH installée.

### Étape 2 : configurer les machines avec Ansible

```bash
cd ../../ansible
cp group_vars/all.yml.example group_vars/all.yml
# renseigner les secrets dans all.yml
ansible-playbook -i logistia-inventory.ini playbooks/logistia-site.yml \
  --private-key ~/.ssh/logistia_ed25519
```

Ansible se connecte à chaque machine et installe tout : applications, durcissement, SOC, IA. L'ordre d'exécution est décrit dans [../ansible/playbooks/README.md](../ansible/playbooks/README.md).

---

## Méthode 2 — Déploiement automatisé (GitHub Actions)

Ici, c'est GitHub qui exécute Terraform et Ansible, à la demande, sans intervention manuelle.

### Le runner self-hosted

Le pipeline s'exécute sur un **runner** (agent d'exécution) installé sur la machine `devops-logistia`, à l'intérieur de l'infrastructure. Ce choix est nécessaire car le déploiement doit pouvoir joindre les machines sur leurs réseaux internes, ce qu'un runner externe (chez GitHub) ne pourrait pas faire.

### Les secrets

Les informations sensibles sont stockées dans les **secrets GitHub** du dépôt (jamais dans le code) :

| Secret | Contenu |
|--------|---------|
| `PROXMOX_URL` | Adresse de l'API Proxmox |
| `PROXMOX_USER` | Identifiant du jeton d'API |
| `PROXMOX_PASSWORD` | Valeur du jeton d'API |
| `SSH_PUBLIC_KEY` | Clé publique installée dans les machines |
| `ANSIBLE_PRIVATE_KEY` | Clé privée utilisée par Ansible pour se connecter |
| `ANSIBLE_VAULT_VARS` | Les secrets applicatifs (génèrent le fichier `all.yml`) |

### Les deux workflows

**1. Workflow d'intégration (`logistia-ci.yml`)** — se déclenche automatiquement à chaque modification du code. Il vérifie la qualité et la sécurité :

- vérification de la syntaxe Terraform ;
- vérification de la syntaxe Ansible ;
- analyse de sécurité du code (outil Trivy).

C'est la partie **tests et vérifications** : elle garantit qu'on ne déploie pas du code cassé ou vulnérable.

**2. Workflow de déploiement (`logistia-deploy.yml`)** — se déclenche manuellement, avec un choix :

| Choix | Effet |
|-------|-------|
| `terraform_only` | Crée ou met à jour les machines |
| `ansible_only` | Configure les machines existantes |
| `full` | Fait les deux, dans l'ordre |

Le workflow, étape par étape :

1. récupère le code du dépôt ;
2. génère la configuration Terraform à partir des secrets ;
3. exécute Terraform (création des machines) ;
4. prépare la clé SSH et génère le fichier de secrets Ansible ;
5. exécute Ansible (configuration) — **en excluant le routeur et la machine devops**, qui constituent le socle et ne doivent pas être reconfigurés pendant que le pipeline tourne sur eux ;
6. **efface** les fichiers sensibles créés temporairement.

### Lancer le déploiement

Dans l'onglet **Actions** du dépôt GitHub → workflow **LOGISTIA Deploy** → bouton **Run workflow** → choisir l'action → **Run**.

---

## Vérifications après déploiement

```bash
# Les services du SOC sont-ils actifs ?
ssh logistia@10.40.40.10 "sudo systemctl is-active wazuh-manager wazuh-indexer wazuh-dashboard"

# Le modèle d'IA est-il disponible ?
ssh logistia@10.50.50.10 "curl -s localhost:11434/api/tags"

# Les agents Wazuh sont-ils enregistrés ?
ssh logistia@10.40.40.10 "sudo /var/ossec/bin/agent_control -l"
```

## Fiabilité du déploiement

Les rôles sont **idempotents** : on peut relancer le déploiement sans risque, il n'applique que les changements nécessaires. Plusieurs sécurités sont intégrées pour que le déploiement aboutisse même après un redémarrage ou une coupure (réparation automatique du gestionnaire de paquets, forwarding réseau rendu persistant, délai de démarrage augmenté pour les services lents).
