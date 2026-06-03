# Variables Ansible LOGISTIA

Ce dossier contient les variables partagées entre les rôles.

Les fichiers `.example` sont versionnés. Les vrais fichiers contenant les secrets ne le sont pas.

## Fichiers

| Fichier | Rôle |
|---------|------|
| `logistia-all.yml.example` | Modèle pour les variables communes |
| `logistia-vault.yml.example` | Modèle pour les secrets chiffrés |

## Initialisation

```bash
cp group_vars/logistia-all.yml.example group_vars/logistia-all.yml
cp group_vars/logistia-vault.yml.example group_vars/logistia-vault.yml
# Renseigner logistia-vault.yml avec les mots de passe réels
ansible-vault encrypt group_vars/logistia-vault.yml
```

## Pourquoi chiffrer logistia-vault.yml

`logistia-vault.yml` contient les mots de passe de la base de données, les credentials Wazuh et Grafana. Ansible Vault chiffre ce fichier avec AES-256. Il peut être versionné dans Git sans exposer les secrets.

## Dans le pipeline GitHub Actions

Les fichiers `logistia-all.yml` et `logistia-vault.yml` ne viennent pas du dépôt. Le workflow les génère temporairement à partir des secrets GitHub, lance le playbook, puis les supprime.
