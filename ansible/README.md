# Ansible LOGISTIA

Ce dossier configure les machines créées par Terraform.

Terraform prépare les machines avec les ressources et le réseau. Ansible se connecte ensuite en SSH et installe les services applicatifs, le SOC, l'IA et les outils de supervision.

## Structure

| Élément | Rôle |
|---------|------|
| `ansible.cfg` | Configuration Ansible LOGISTIA |
| `logistia-inventory.ini` | Machines par groupe fonctionnel |
| `group_vars/` | Variables et secrets chiffrés |
| `playbooks/logistia-site.yml` | Ordre d'application des rôles |
| `roles/` | Rôles applicatifs LOGISTIA |

## Exécution manuelle

```bash
ansible-playbook playbooks/logistia-site.yml --ask-vault-pass
```

## Syntax check

```bash
ANSIBLE_ROLES_PATH=roles ansible-playbook \
  -i logistia-inventory.ini \
  --syntax-check \
  playbooks/logistia-site.yml
```
