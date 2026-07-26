# Dossier `infra/` — création des machines avec Terraform

Ce dossier contient la description de l'infrastructure au format **Terraform**. Terraform est l'outil qui **crée les machines virtuelles** sur Proxmox, à partir d'une description écrite. C'est la première étape du déploiement, avant la configuration par Ansible.

## Rôle de Terraform vs Ansible

Les deux outils sont complémentaires et interviennent l'un après l'autre :

| Outil | Rôle | Ce qu'il fait |
|-------|------|---------------|
| **Terraform** | Crée l'infrastructure | Clone le template, crée les 10 machines, configure leur réseau (VLAN), leur mémoire, leurs disques, et injecte la clé SSH |
| **Ansible** | Configure l'infrastructure | Installe et configure les logiciels sur les machines une fois créées |

En résumé : **Terraform fabrique les machines, Ansible les habille.**

## Organisation

```text
infra/terraform/
├── main.tf                    # Description des 10 machines
├── variables.tf               # Variables (adresse Proxmox, identifiants…)
├── terraform.tfvars.example   # Modèle de configuration (à copier)
└── modules/
    └── logistia-vm/           # Module réutilisable de création d'une VM
```

## Le module de création de VM

Plutôt que de décrire dix fois une machine, LOGISTIA utilise un **module** : un modèle paramétrable de machine virtuelle. Le fichier `main.tf` appelle ce module dix fois, une par machine, en changeant seulement les paramètres (nom, IP, VLAN, mémoire, disque).

Cela rend la description **courte, cohérente et facile à faire évoluer** : pour ajouter une machine, il suffit d'un nouvel appel au module.

## Utilisation

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# renseigner : adresse Proxmox, identifiant et jeton d'API, clé SSH publique

terraform init      # télécharge le nécessaire
terraform plan      # montre ce qui va être créé (sans rien créer)
terraform apply     # crée réellement les machines
```

Pour supprimer toute l'infrastructure : `terraform destroy`.

## Lien avec le déploiement

Terraform est la première étape des deux méthodes de déploiement décrites dans [../docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md). En déploiement automatisé, c'est le pipeline GitHub Actions qui exécute ces commandes à la place de l'utilisateur.
