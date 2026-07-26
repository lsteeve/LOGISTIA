# Variables et gestion des secrets

Le dossier `group_vars/` contient les **variables** utilisées par Ansible, notamment les informations sensibles (mots de passe, clés d'API). LOGISTIA applique une règle stricte : **aucun secret n'est stocké en clair dans le dépôt Git**.

## Les deux fichiers

| Fichier | Rôle | Versionné dans Git ? |
|---------|------|----------------------|
| `all.yml.example` | **Modèle** : liste toutes les variables attendues, avec des valeurs fictives (`CHANGE_ME`) | ✅ Oui |
| `all.yml` | **Valeurs réelles** : les vrais secrets utilisés au déploiement | ❌ Non (exclu par `.gitignore`) |

Le fichier `all.yml.example` sert de documentation : il montre quelles variables doivent être renseignées, sans jamais exposer de vraie valeur.

## Comment renseigner les secrets

### En déploiement manuel

On copie le modèle et on renseigne les vraies valeurs, en local :

```bash
cp group_vars/all.yml.example group_vars/all.yml
# puis on édite all.yml avec les vraies valeurs
```

Ce fichier `all.yml` reste sur le poste d'administration et n'est jamais envoyé sur Git.

### En déploiement automatisé (GitHub Actions)

Le fichier `all.yml` est **généré automatiquement** au moment du déploiement, à partir d'un **secret GitHub** (`ANSIBLE_VAULT_VARS`). Il est créé le temps du déploiement, puis supprimé à la fin. Les secrets ne transitent donc jamais par le dépôt.

## Les variables gérées

Le fichier regroupe notamment :

- les mots de passe d'administration des services (MISP, Cortex, TheHive) ;
- les clés d'API permettant aux outils de communiquer entre eux ;
- le mot de passe du stockage interne.

Chaque rôle qui a besoin d'un secret le lit depuis ces variables, plutôt que de le contenir en dur. Ainsi, changer un mot de passe se fait à un seul endroit.

## Principe de sécurité

Cette organisation garantit que :

- le dépôt Git peut être partagé (avec le jury, par exemple) sans exposer aucun secret ;
- les vraies valeurs restent maîtrisées (fichier local ou secret GitHub) ;
- la configuration reste entièrement automatisée dans les deux modes de déploiement.
