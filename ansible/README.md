# Ansible LOGISTIA

Ce dossier configure les machines créées par Terraform.

Terraform prépare les machines avec les ressources et le réseau. Ansible se connecte ensuite en SSH et installe les services applicatifs, le SOC, l'IA et les outils de supervision.

## Structure

| Élément | Rôle |
|---------|------|
| `ansible.cfg` | Configuration Ansible LOGISTIA |
| `logistia-inventory.ini` | Liste des machines par groupe fonctionnel |
| `group_vars/` | Variables et secrets par groupe |
| `playbooks/logistia-site.yml` | Ordre d'application des rôles |
| `roles/` | Rôles applicatifs LOGISTIA |

## Configuration Ansible

`ansible.cfg` contient :

```ini
[defaults]
inventory           = logistia-inventory.ini
roles_path          = roles
host_key_checking   = False
retry_files_enabled = False
```

`inventory = logistia-inventory.ini` évite de fournir `-i` à chaque commande.

`roles_path = roles` indique que les rôles LOGISTIA sont dans `ansible/roles`.

`host_key_checking = False` évite un blocage au premier contact SSH avec des machines recréées par Terraform. En environnement de production, les empreintes SSH seraient gérées plus strictement.

## Inventaire LOGISTIA

`logistia-inventory.ini` regroupe les machines par fonction :

- `routers` — router-logistia, routeur NAT et pare-feu
- `apps` — app-logistia, application web DMZ
- `databases` — db-logistia, base de données isolée
- `devops` — devops-logistia, CI/CD et déploiement
- `soc` — soc-logistia, supervision et SOC
- `ia` — ia-logistia, analyse IA des logs
- `backup` — backup-logistia, sauvegardes

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

Cette commande ne se connecte pas aux machines. Elle vérifie uniquement la structure du playbook.
