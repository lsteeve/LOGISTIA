# Infrastructure LOGISTIA

Ce dossier contient la partie Infrastructure as Code du projet.

## Organisation

`terraform/` crée les sept machines virtuelles LOGISTIA sur Proxmox et configure le réseau initial via cloud-init.

Ansible, dans le dossier `ansible/` à la racine, prend le relais une fois les machines démarrées pour installer et configurer les services applicatifs.

## Pourquoi séparer Terraform et Ansible

Terraform parle à l'API Proxmox. Il sait créer, modifier ou supprimer des machines virtuelles. Il ne sait pas configurer ce qui tourne à l'intérieur.

Ansible parle en SSH aux machines. Il sait installer des paquets, écrire des fichiers de configuration et démarrer des services. Il ne sait pas créer des machines.

Cette séparation des responsabilités rend chaque outil plus simple à comprendre et à maintenir. Une erreur Terraform touche l'infrastructure. Une erreur Ansible touche la configuration d'un service. Les deux ne se mélangent pas.

## Enchaînement du déploiement LOGISTIA

1. Terraform contacte l'API Proxmox avec le token `logistia-token`
2. Terraform clone le template Debian 13 pour chacune des sept machines
3. cloud-init installe les paquets de base et crée l'utilisateur `logistia`
4. Les machines démarrent et répondent en SSH
5. Ansible se connecte avec la clé `logistia_ed25519`
6. Ansible applique les rôles dans l'ordre du playbook `logistia-site.yml`
