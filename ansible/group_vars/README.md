# Variables Ansible LOGISTIA

Les fichiers `.example` sont versionnés. Les vrais fichiers contenant les secrets ne le sont pas.

## Initialisation

```bash
cp group_vars/logistia-all.yml.example group_vars/logistia-all.yml
cp group_vars/logistia-vault.yml.example group_vars/logistia-vault.yml
ansible-vault encrypt group_vars/logistia-vault.yml
```

## Pourquoi chiffrer logistia-vault.yml

`logistia-vault.yml` contient les mots de passe de la base de données, les credentials Wazuh et Grafana. Ansible Vault chiffre ce fichier avec AES-256. Il peut être versionné dans Git sans exposer les secrets.

## Dans le pipeline GitHub Actions

Les fichiers sont générés temporairement à partir des secrets GitHub, utilisés par Ansible, puis supprimés.
