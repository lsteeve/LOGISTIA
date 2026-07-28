# Sauvegarde et reprise d'activité — LOGISTIA

LOGISTIA applique une stratégie de sauvegarde à **deux niveaux complémentaires**, conforme à la règle **3-2-1** (trois copies, deux supports, une hors site).

## 1. Vue d'ensemble

| Niveau | Outil | Portée | Emplacement |
|--------|-------|--------|-------------|
| **Machines complètes** | Proxmox Backup Server (PBS) | Les 10 VM entières (snapshots) | Hôte Proxmox |
| **Données applicatives** | rsync + mysqldump | Fichiers applicatifs et base de données | VM backup-logistia |

Le premier niveau permet de **restaurer une machine entière** en cas de perte ; le second offre une **granularité fine** sur les données métier (fichiers de l'application, dump de la base).

## 2. Sauvegarde des machines (Proxmox Backup Server)

### Principe

Proxmox Backup Server réalise des **snapshots incrémentaux** de chaque machine virtuelle. Seules les données modifiées depuis la dernière sauvegarde sont transférées, ce qui rend les sauvegardes rapides et peu volumineuses.

### Configuration du job

Le job de sauvegarde est configuré **sur l'hôte Proxmox** (et non dans une VM), car il relève de l'hyperviseur. Il n'est donc pas géré par Ansible mais configuré directement dans Proxmox.

Paramètres du job :

- **Stockage** : `pbs-logistia`
- **Machines** : les 10 VM (VMID 101 à 110)
- **Planification** : tous les jours à 22h30
- **Mode** : snapshot (sans interruption des VM)
- **Rétention** : 3 dernières, 7 quotidiennes, 4 hebdomadaires, 3 mensuelles

> **Important** — lors de l'ajout d'une nouvelle VM à l'infrastructure, il faut l'**ajouter au job de sauvegarde PBS**. La liste des VMID est explicite. Vérifier avec :
>
> ```bash
> grep vmid /etc/pve/jobs.cfg
> ```
>
> et l'étendre si nécessaire :
>
> ```bash
> JOB=$(grep -oE 'backup-[a-f0-9-]+' /etc/pve/jobs.cfg | head -1)
> pvesh set /cluster/backup/$JOB --vmid "101,102,103,104,105,106,107,108,109,110"
> ```

### Restauration d'une VM

Depuis l'interface Proxmox : sélectionner le stockage `pbs-logistia` → onglet **Sauvegardes** → choisir la sauvegarde → **Restaurer**.

### Sauvegarde manuelle immédiate

```bash
vzdump 108 109 110 --storage pbs-logistia --mode snapshot --notes-template '{{guestname}}'
```

## 3. Sauvegarde applicative (rsync + mysqldump)

La VM **backup-logistia** exécute un script (`/opt/logistia-backup/logistia-backup.sh`) qui, via une tâche planifiée :

- **synchronise** les fichiers de l'application (app-logistia) par rsync ;
- **exporte** la base de données (db-logistia) par mysqldump ;
- **journalise** chaque exécution.

Ce niveau est **géré par Ansible** (rôle `logistia-backup`) et donc reproductible automatiquement.

### Restauration applicative

Les fichiers et le dump SQL sont disponibles dans `/opt/logistia-backup/` sur backup-logistia. La restauration se fait en recopiant les fichiers vers la VM cible et en réimportant le dump SQL.

## 4. Conformité 3-2-1

- **3 copies** : la donnée en production + la sauvegarde PBS + la sauvegarde applicative rsync.
- **2 supports** : le stockage PBS et le stockage de la VM backup.
- **1 hors ligne / isolée** : la VM backup est dans un VLAN dédié (VLAN60), isolée du reste.

## 5. Points de vigilance

- **Nouvelle VM** : penser à l'ajouter au job PBS (voir §2).
- **Espace disque** : surveiller le remplissage du stockage `pbs-logistia` (la rétention limite l'accumulation).
- **Test de restauration** : vérifier périodiquement qu'une sauvegarde est restaurable (une sauvegarde jamais testée n'est pas une sauvegarde fiable).
