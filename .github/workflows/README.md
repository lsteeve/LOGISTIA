# Workflows GitHub Actions — LOGISTIA

## `logistia-ci.yml`

S'exécute sur `push` et `pull_request` vers `main` sur un runner GitHub public.

### Étapes

**Terraform fmt**
Vérifie que tous les fichiers respectent le format Terraform officiel. Le workflow échoue si le code n'est pas formaté.

**Terraform validate**
Vérifie la cohérence syntaxique des fichiers `.tf` et des modules sans contacter Proxmox.

**Ansible syntax check**
Valide la structure du playbook `logistia-site.yml` sans se connecter aux machines LOGISTIA.

**Trivy scan**
Scanne le dépôt pour détecter des vulnérabilités connues dans les dépendances et la configuration. Seules les vulnérabilités `CRITICAL` et `HIGH` avec correctif disponible font échouer le workflow.

## `logistia-deploy.yml`

Déclenché manuellement avec `workflow_dispatch` sur le runner self-hosted `devops-logistia`.

### Options

| Option | Valeurs | Effet |
|--------|---------|-------|
| `terraform_action` | `plan` / `apply` | Planifier ou appliquer l'infrastructure |
| `run_ansible` | `true` / `false` | Configurer les machines après Terraform |

### State Terraform

Le state est conservé sur `devops-logistia` dans `/srv/logistia/terraform/logistia.tfstate`. Il n'est jamais versionné dans le dépôt.

### Nettoyage

La clé SSH et le mot de passe Vault écrits temporairement sont supprimés à la fin du workflow avec `if: always()`, même en cas d'erreur.
