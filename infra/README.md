# Infrastructure LOGISTIA

Ce dossier contient la partie Infrastructure as Code du projet.

## Organisation

`terraform/` crée les sept machines virtuelles LOGISTIA sur Proxmox et configure le réseau initial via cloud-init.

Ansible, dans le dossier `ansible/` à la racine, prend le relais une fois les machines démarrées pour installer et configurer les services applicatifs.

## Pourquoi séparer Terraform et Ansible

Terraform parle à l'API Proxmox. Il crée, modifie ou supprime des machines virtuelles. Il ne configure pas ce qui tourne à l'intérieur.

Ansible parle en SSH aux machines. Il installe des paquets, écrit des fichiers de configuration et démarre des services. Il ne crée pas de machines.

Cette séparation des responsabilités rend chaque outil plus simple à comprendre et à maintenir.

## Enchaînement du déploiement LOGISTIA

1. Terraform contacte l'API Proxmox avec le token `logistia-token`
2. Terraform clone le template Debian 13 pour chacune des sept machines
3. `logistia-cloudinit.yaml` installe les paquets de base et crée l'utilisateur `logistia`
4. Les machines démarrent et répondent en SSH
5. Ansible se connecte avec la clé `logistia_ed25519`
6. Ansible applique les rôles dans l'ordre du playbook `logistia-site.yml`
