# Automatisation GitHub Actions — LOGISTIA

Ce dossier contient les workflows d'automatisation du projet LOGISTIA.

## Pourquoi deux workflows

Le projet sépare la validation du déploiement.

`logistia-ci.yml` s'exécute à chaque push ou pull request sur `main`. Il vérifie la qualité du code Terraform et Ansible sans modifier l'infrastructure. Un développeur peut pousser du code en toute confiance — ce workflow détecte les erreurs de syntaxe et les vulnérabilités avant qu'elles atteignent Proxmox.

`logistia-deploy.yml` se déclenche manuellement depuis l'interface GitHub Actions. Il déploie réellement les machines et configure les services. Cette séparation est intentionnelle : un push sur `main` ne doit jamais modifier l'infrastructure LOGISTIA sans validation humaine.

## Pourquoi un runner self-hosted

Proxmox et les machines LOGISTIA sont dans un réseau privé, inaccessible depuis Internet. Un runner hébergé par GitHub ne peut pas joindre l'API Proxmox ni les VLANs LOGISTIA.

Le runner self-hosted est installé sur `devops-logistia` (10.30.30.10), dans le VLAN30. De là, il peut contacter l'API Proxmox pour Terraform et joindre toutes les machines LOGISTIA en SSH pour Ansible.

## Secrets GitHub

Les secrets GitHub remplacent les fichiers sensibles locaux pendant l'exécution du workflow. Aucun mot de passe, token ou clé privée n'est versionné dans le dépôt.

| Secret | Usage |
|--------|-------|
| `PROXMOX_PASSWORD` | Token API Terraform pour Proxmox |
| `PROXMOX_SSH_PASSWORD` | Upload du fichier cloud-init sur Proxmox |
| `SSH_PUBLIC_KEY` | Clé publique injectée dans les machines par cloud-init |
| `ANSIBLE_PRIVATE_KEY` | Clé privée pour les connexions SSH Ansible |
| `ANSIBLE_VAULT_PASSWORD` | Déchiffrement des secrets Ansible Vault |
