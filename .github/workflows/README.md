# Workflows GitHub Actions — LOGISTIA

## `logistia-ci.yml`

Ce workflow s'exécute sur `push` et `pull_request` vers `main`.

### Terraform fmt

```bash
terraform fmt -check -recursive
```

Vérifie que tous les fichiers Terraform respectent le format officiel. `-check` fait échouer le workflow sans modifier le dépôt.

### Terraform init sans backend

```bash
terraform init -backend=false -input=false
```

`-backend=false` évite d'utiliser le vrai state pendant la validation. Le but est uniquement de télécharger les providers et vérifier la cohérence du code.

### Terraform validate

```bash
terraform validate
```

Valide que les fichiers `.tf` sont syntaxiquement corrects et que les modules sont cohérents.

### Ansible syntax check

```bash
ANSIBLE_ROLES_PATH=roles ansible-playbook -i logistia-inventory.ini --syntax-check playbooks/logistia-site.yml
```

Vérifie la structure du playbook sans se connecter aux machines LOGISTIA. `ANSIBLE_ROLES_PATH=roles` garantit que les rôles sont trouvés quel que soit l'environnement.

### Trivy scan

```bash
trivy fs --format table --exit-code 1 --severity CRITICAL,HIGH --ignore-unfixed .
```

Scanne les fichiers du dépôt pour détecter des vulnérabilités connues. `--ignore-unfixed` évite d'échouer sur des vulnérabilités sans correctif disponible.

## `logistia-deploy.yml`

Ce workflow est déclenché manuellement avec `workflow_dispatch`.

Il tourne sur `self-hosted`, c'est-à-dire sur `devops-logistia` dans le réseau interne.

### Options disponibles

| Option | Valeurs | Effet |
|--------|---------|-------|
| `terraform_action` | `plan` / `apply` | Planifier ou appliquer |
| `run_ansible` | `true` / `false` | Configurer les machines après Terraform |

### Vérification des secrets

Le workflow vérifie que les secrets essentiels sont présents avant de démarrer. Cela fait échouer rapidement si une variable manque plutôt que d'attendre une erreur plus loin.

### State Terraform persistant

Le state est conservé sur `devops-logistia` dans `/srv/logistia/terraform/logistia.tfstate`. Il survit aux redémarrages du runner et n'est jamais versionné dans le dépôt.

### Nettoyage des fichiers temporaires

La clé SSH et le mot de passe Vault écrits temporairement sur le disque sont supprimés à la fin du workflow, même en cas d'erreur (`if: always()`).
