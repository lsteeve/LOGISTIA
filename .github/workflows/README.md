# Workflows GitHub Actions — LOGISTIA

## `logistia-ci.yml`

S'exécute sur `push` et `pull_request` vers `main` sur un runner GitHub public.

### Étapes

**Terraform fmt**
Vérifie que tous les fichiers respectent le format Terraform officiel.

**Terraform validate**
Vérifie la cohérence syntaxique des fichiers `.tf` et des modules sans contacter Proxmox.

**Ansible syntax check**
Valide la structure du playbook `logistia-site.yml` sans se connecter aux machines LOGISTIA.

**Trivy scan**
Scanne le dépôt pour détecter des vulnérabilités connues dans les dépendances et la
configuration (`CRITICAL` et `HIGH`).

> La CI est **informative** : chaque étape est en `continue-on-error` et Trivy en
> `exit-code: 0`. Un push sur `main` n'est jamais bloqué par un avertissement de lint
> ou de scan — cohérent avec le fait qu'il s'agit d'un lab pédagogique dont certains
> secrets de démonstration figurent volontairement dans le code.

## `logistia-deploy.yml`

Déclenché manuellement avec `workflow_dispatch` sur le runner self-hosted `devops-logistia`.

### Options

Un seul paramètre `action` (menu déroulant) :

| Valeur | Effet |
|-----------------|--------------------------------------------------------------|
| `full` | Terraform (crée/maj les VM) **puis** Ansible (configure tout) |
| `terraform_only`| Provisionne uniquement les VM (Terraform) |
| `ansible_only` | Reconfigure uniquement les services (Ansible), sans toucher aux VM |

Valeur par défaut : `ansible_only` (l'action la plus fréquente et la moins risquée).

### Garde-fou sauvegarde

Avant toute action Terraform (`full` / `terraform_only`), le pipeline vérifie qu'une
sauvegarde de moins de 3 h existe sur `backup-logistia` (10.60.60.10). Sans sauvegarde
récente, le déploiement est **refusé** — protection anti-écrasement.

### State Terraform

Le state est conservé sur `devops-logistia` (workspace du runner). Il n'est jamais
versionné dans le dépôt.

### Nettoyage

`terraform.tfvars`, le plan Terraform, la clé SSH et le mot de passe Vault écrits
temporairement sont supprimés à la fin du workflow avec `if: always()`, même en cas d'erreur.
