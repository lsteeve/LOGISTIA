# Architecture technique — LOGISTIA

## 1. Contexte

LOGISTIA héberge, sur un hyperviseur **Proxmox VE 9**, l'infrastructure centrale d'une chaîne logistique connectée. Les entrepôts et sites distants se connectent aux applications hébergées (ERP Dolibarr, suivi IoT Traccar) ; la plateforme assure leur sécurité, leur supervision et leur déploiement automatisé.

L'infrastructure est **segmentée par VLAN** : chaque fonction réside dans son propre sous-réseau, et un routeur logiciel applique un filtrage strict entre les segments.

## 2. Segmentation en VLAN

| VLAN | Sous-réseau | Zone | Contenu |
|------|-------------|------|---------|
| WAN | 192.168.10.0/24 | Périmètre | Routeur, hyperviseur Proxmox |
| VLAN10 | 10.10.10.0/24 | DMZ | Serveur web applicatif (exposé) |
| VLAN20 | 10.20.20.0/24 | Data | Base de données (isolée) |
| VLAN30 | 10.30.30.0/24 | DevOps | Runner CI/CD, outils IaC |
| VLAN40 | 10.40.40.0/24 | SOC | SIEM, supervision, Threat Intelligence |
| VLAN50 | 10.50.50.0/24 | IA | Moteur d'inférence |
| VLAN60 | 10.60.60.0/24 | Backup | Sauvegardes |
| VLAN70 | 10.70.70.0/24 | Admin | Poste d'administration (SSH, accès Proxmox) |

La chaîne de **Threat Intelligence** (MISP, Cortex, TheHive) est regroupée dans le **VLAN40 SOC**, aux côtés du SIEM et de la supervision.

## 3. Mise en œuvre réseau (bridges Proxmox)

La segmentation décrite ci-dessus est réalisée concrètement au moyen de **bridges Proxmox**. Un bridge est un **commutateur (switch) virtuel** interne à l'hyperviseur : chaque zone correspond à un bridge dédié, ce qui garantit une isolation au niveau de la topologie du réseau.

### Un bridge par zone

L'hôte Proxmox définit huit bridges. Seul le premier, `vmbr0`, est relié à la carte réseau physique du serveur (`nic0`) : c'est l'unique point de contact avec l'extérieur. Les sept autres bridges sont **purement internes** (`bridge-ports none`), sans aucune connexion physique vers le monde extérieur.

| Bridge | Réseau | Passerelle | Zone |
|--------|--------|-----------|------|
| `vmbr0` | 192.168.10.0/24 | 192.168.10.254 | Périmètre (accès extérieur, carte physique) |
| `vmbr1` | 10.10.10.0/24 | 10.10.10.254 | DMZ |
| `vmbr2` | 10.20.20.0/24 | 10.20.20.254 | Data |
| `vmbr3` | 10.30.30.0/24 | 10.30.30.254 | DevOps |
| `vmbr4` | 10.40.40.0/24 | 10.40.40.254 | SOC |
| `vmbr5` | 10.50.50.0/24 | 10.50.50.254 | IA |
| `vmbr6` | 10.60.60.0/24 | 10.60.60.254 | Backup |
| `vmbr7` | 10.70.70.0/24 | 10.70.70.254 | Admin |

### Le routeur, présent dans toutes les zones

Le **routeur** (VM 101) est la pièce maîtresse du dispositif : il possède **huit interfaces réseau**, une connectée à chacun des huit bridges. Il est donc présent dans toutes les zones à la fois, ce qui lui permet de router et de filtrer le trafic entre elles.

```text
Routeur (VM 101)
 |- net0 -> vmbr0   (acces exterieur)
 |- net1 -> vmbr1   (DMZ)
 |- net2 -> vmbr2   (Data)
 |- net3 -> vmbr3   (DevOps)
 |- net4 -> vmbr4   (SOC)
 |- net5 -> vmbr5   (IA)
 |- net6 -> vmbr6   (Backup)
 \- net7 -> vmbr7   (Admin)
```

À l'inverse, **chaque autre machine ne possède qu'une seule interface**, rattachée uniquement au bridge de sa zone. Par exemple, le serveur applicatif est connecté à `vmbr1` (DMZ), et le SOC à `vmbr4`.

### Isolation par la topologie

Cette conception a une conséquence forte : deux machines de zones différentes **ne peuvent pas communiquer directement**, car leurs bridges ne sont reliés que par le routeur. Tout échange entre zones traverse obligatoirement le routeur, où **nftables** applique la politique de filtrage (voir la section « Flux réseau autorisés »).

L'isolation ne repose donc pas seulement sur des règles logiques : elle est **inscrite dans la structure même du réseau**. Même en cas de mauvaise configuration d'une règle, une zone reste physiquement séparée des autres tant que le routeur ne relaie pas le trafic.

### Ce qui est automatisé, ce qui est un prérequis

La mise en place du réseau se répartit en trois niveaux :

- **Prérequis (hyperviseur)** — les huit bridges `vmbr0` à `vmbr7` doivent exister sur l'hôte Proxmox avant tout déploiement. Ils constituent le socle physique du réseau.
- **Automatisé (Terraform)** — la création des machines et leur rattachement au bon bridge selon leur zone. Le routeur reçoit une interface dans chacun des huit bridges.
- **Automatisé (Ansible)** — la configuration du routage et du filtrage nftables à l'intérieur du routeur.

Autrement dit, les switchs virtuels sont un prérequis de l'hôte, mais l'ensemble du câblage des machines et de la configuration réseau est reproductible automatiquement.

## 4. Machines virtuelles

| VMID | Nom | IP | VLAN | vCPU | RAM | Disque | Services |
|------|-----|----|------|------|-----|--------|---------|
| 101 | router-logistia | 192.168.10.151 | WAN | 2 | 2 Go | 20 Go | nftables (NAT, filtrage inter-VLAN) |
| 102 | app-logistia | 10.10.10.10 | VLAN10 DMZ | 2 | 4 Go | 30 Go | Nginx HTTPS, Dolibarr ERP, Traccar IoT |
| 103 | db-logistia | 10.20.20.10 | VLAN20 Data | 2 | 4 Go | 40 Go | MariaDB |
| 104 | devops-logistia | 10.30.30.10 | VLAN30 DevOps | 2 | 4 Go | 30 Go | GitHub Runner, Terraform, Ansible |
| 105 | soc-logistia | 10.40.40.10 | VLAN40 SOC | 4 | 12 Go | 60 Go | Wazuh Manager/Indexer/Dashboard, Prometheus, Grafana, scanner IA |
| 108 | misp-logistia | 10.40.40.20 | VLAN40 SOC | 3 | 8 Go | — | MISP (Threat Intelligence) |
| 109 | cortex-logistia | 10.40.40.30 | VLAN40 SOC | 4 | 8 Go | — | Cortex (analyse d'observables) |
| 110 | thehive-logistia | 10.40.40.40 | VLAN40 SOC | 4 | 12 Go | — | TheHive (gestion d'incidents) |
| 106 | ia-logistia | 10.50.50.10 | VLAN50 IA | 4 | 12 Go | 40 Go | Ollama phi3:mini, Isolation Forest |
| 107 | backup-logistia | 10.60.60.10 | VLAN60 Backup | 1 | 2 Go | 100 Go | Sauvegardes |

Les VM sont clonées depuis un **template Debian 13 cloud-init** (VMID 9000) et démarrent automatiquement au boot de l'hyperviseur.

## 5. Schéma logique

Un schéma complet et illustré est fourni dans [architecture-schema.html](architecture-schema.html). Version simplifiée ci-dessous :

```
                     Internet
                        │
                        ▼
              ┌──────────────────┐
              │  router-logistia  │  nftables : NAT + filtrage inter-VLAN
              │  192.168.10.151   │  (politique forward = drop)
              └─┬──┬──┬──┬──┬──┬──┘
     ┌──────────┘  │  │  │  │  └──────────────┐
     ▼             ▼  │  │  ▼                 ▼
 VLAN10 DMZ  VLAN20   │  │  VLAN40 SOC     VLAN50 IA
 app-logistia db-log. │  │ ┌ soc-logistia  ia-logistia
                      │  │ ├ misp-logistia
              VLAN30 ─┘  │ ├ cortex-logistia
              devops     │ └ thehive-logistia
                         │
              VLAN60 Backup ── backup-logistia
              VLAN70 Admin  ── poste d'administration
```

## 6. Flux réseau autorisés

Le routeur applique une politique **`drop`** par défaut sur la chaîne `forward`. Seuls les flux nécessaires sont ouverts :

| Source | Destination | Port | Usage |
|--------|-------------|------|-------|
| Internet | app-logistia | 443 | Accès HTTPS aux applications |
| app-logistia | db-logistia | 3306 | Requêtes MariaDB |
| Toutes les VM | soc-logistia | 1514 / 1515 | Remontée des logs Wazuh |
| soc-logistia | ia-logistia | 11434 | Appel du moteur IA (Ollama) |
| soc-logistia | misp-logistia | 443 | Synchronisation des IOC |
| thehive-logistia | cortex-logistia | 9001 | Analyse d'observables |
| cortex-logistia | misp-logistia | 443 | Enrichissement CTI |
| devops-logistia | Toutes les VM | 22 | Configuration Ansible |
| VLAN70 Admin | Toutes les VM | 22 | Administration SSH |
| VLAN70 Admin | Proxmox | 8006 | Interface d'administration |
| Toutes les VM | Internet | — | NAT (mises à jour) |

Le forwarding IPv4 est rendu **persistant** (fichier `sysctl.d` prioritaire + directive `ExecStartPost` sur le service nftables) afin de résister aux redémarrages.

## 7. Choix d'architecture

- **Moindre privilège** : aucun flux inter-VLAN n'est ouvert sans justification ; la propagation latérale est limitée.
- **SIEM au cœur du SOC** : Wazuh, la supervision et la CTI partagent le VLAN40, ce qui facilite la corrélation tout en isolant l'ensemble.
- **IA séparée** : le scanner d'analyse tourne sur le SOC (au plus près des logs), le modèle lourd sur une VM IA dédiée ; un unique flux les relie.
- **Administration cloisonnée** : l'accès SSH et Proxmox est réservé au VLAN70 Admin.
- **Sauvegarde isolée** : le VLAN backup est séparé du reste.
