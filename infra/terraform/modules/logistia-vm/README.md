# Module logistia-vm

Ce module crée une machine virtuelle Debian 13 sur Proxmox en clonant le template ID 9000.

Il est utilisé pour toutes les machines du projet LOGISTIA.

## Variables

| Variable | Description |
|----------|-------------|
| `name` | Nom de la machine — convention `fonction-logistia` |
| `vmid` | Identifiant Proxmox unique |
| `cores` | Nombre de vCPU |
| `memory` | RAM en Mo |
| `disk_size` | Taille disque en Go |
| `bridge` | Bridge réseau principal |
| `ip` | Adresse IP statique avec masque CIDR |
| `gateway` | Passerelle par défaut |
| `ssh_key` | Clé publique logistia_ed25519 injectée par cloud-init |
| `extra_nets` | Bridges supplémentaires pour router-logistia |

## Pourquoi des machines virtuelles

Les machines virtuelles offrent un meilleur isolement de sécurité que les conteneurs LXC. Chaque machine dispose de son propre noyau. Pour un projet centré sur la cybersécurité avec un SOC et de l'analyse de logs, cet isolement est justifié.

## Clé SSH

La clé publique `logistia_ed25519` est injectée via `initialization.user_account.keys`. Aucun mot de passe root n'est créé. Ansible se connecte avec la clé privée correspondante après le démarrage.
