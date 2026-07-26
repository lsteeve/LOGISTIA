# Dossier `ansible/` — configuration des serveurs

Une fois les machines virtuelles créées par Terraform, **Ansible** se charge de les configurer : installation des paquets, déploiement des applications, durcissement de sécurité, mise en place du SOC et de la brique IA. Ansible applique une configuration **idempotente** : on peut relancer le playbook autant de fois que nécessaire, il n'applique que ce qui doit l'être.

## Organisation du dossier

```text
ansible/
├── logistia-inventory.ini     # Liste des machines, classées par groupe
├── playbooks/
│   └── logistia-site.yml       # Playbook principal (orchestre tous les rôles)
├── group_vars/
│   ├── all.yml.example         # Modèle de variables et secrets (versionné)
│   └── all.yml                 # Valeurs réelles (NON versionné, voir group_vars/README.md)
└── roles/                      # 13 rôles, un par fonction (voir roles/README.md)
```

## L'inventaire

Le fichier `logistia-inventory.ini` recense toutes les machines, regroupées par fonction :

```ini
[logistia-routers]
router-logistia ansible_host=192.168.10.151

[logistia-apps]
app-logistia ansible_host=10.10.10.10

[logistia-databases]
db-logistia ansible_host=10.20.20.10

[logistia-soc]
soc-logistia ansible_host=10.40.40.10
... (etc.)
```

Chaque groupe reçoit les rôles qui le concernent. Par exemple, le groupe `logistia-soc` reçoit le rôle qui installe Wazuh, Prometheus, Grafana et la brique IA.

## Comment fonctionne un déploiement Ansible

1. Ansible lit l'**inventaire** pour savoir sur quelles machines agir.
2. Il lit le **playbook** `logistia-site.yml` qui associe chaque groupe de machines à ses rôles.
3. Il lit les **variables** (`group_vars/all.yml`), notamment les secrets.
4. Il se connecte en SSH à chaque machine et **applique les rôles** dans l'ordre défini.

## Détails

- Ordre d'exécution du playbook : [playbooks/README.md](playbooks/README.md)
- Description de chaque rôle : [roles/README.md](roles/README.md)
- Variables et gestion des secrets : [group_vars/README.md](group_vars/README.md)

## Lancer Ansible manuellement

```bash
cd ansible
ansible-playbook -i logistia-inventory.ini playbooks/logistia-site.yml \
  --private-key ~/.ssh/logistia_ed25519
```

On peut cibler un seul groupe de machines avec l'option `--limit` :

```bash
ansible-playbook -i logistia-inventory.ini playbooks/logistia-site.yml \
  --limit logistia-soc --private-key ~/.ssh/logistia_ed25519
```
