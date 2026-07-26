# Documentation cybersécurité — LOGISTIA

Ce document décrit les mesures de sécurité de l'infrastructure : segmentation réseau, supervision, détection, réponse automatisée aux incidents et durcissement.

## 1. Segmentation réseau (défense en profondeur)

L'infrastructure est découpée en **VLAN** isolés. Le routeur applique une table **nftables** dont la chaîne `forward` a pour politique par défaut **`drop`** : aucun trafic inter-VLAN n'est autorisé sauf déclaration explicite.

Bénéfices :

- **limitation de la propagation latérale** : une VM compromise ne peut pas atteindre librement les autres segments ;
- **surface d'attaque réduite** : seuls les flux nécessaires au fonctionnement sont ouverts ;
- **traçabilité** : chaque flux autorisé est documenté.

Ce principe a été vérifié en pratique : une tentative de rebond SSH depuis la VM applicative vers la base de données est **bloquée par le pare-feu**, le port 22 inter-VLAN n'étant pas ouvert.

## 2. Supervision centralisée (SIEM)

Le SOC repose sur **Wazuh** :

- **manager** : corrélation des événements, application des règles ;
- **indexer** (OpenSearch) : stockage et indexation des alertes ;
- **dashboard** : visualisation (HTTPS) ;
- **agents** : déployés sur l'ensemble des VM (sauf le manager), ils remontent les journaux système et réseau.

La supervision d'infrastructure est complétée par **Prometheus** (métriques via Node Exporter) et **Grafana** (tableaux de bord).

## 3. Threat Intelligence (CTI)

Trois outils constituent la chaîne CTI / gestion d'incidents :

| Outil | Rôle |
|-------|------|
| **MISP** | Base d'indicateurs de compromission (IOC) |
| **Cortex** | Analyse automatisée d'observables |
| **TheHive** | Gestion et suivi des incidents |

Les alertes Wazuh de niveau élevé sont transmises à **TheHive** ; les observables peuvent être analysés par **Cortex**, lui-même relié à **MISP**.

## 4. Détection personnalisée

Des **règles Wazuh sur mesure** (plage d'ID 100000+) enrichissent la détection native. Chaque règle est associée à une technique **MITRE ATT&CK**.

| Règle | Niveau | Détection | MITRE |
|-------|--------|-----------|-------|
| 100101 | 10 | Force brute SSH (5 échecs / 120 s) | T1110 |
| 100102 | 12 | Authentification échouée depuis une IP référencée MISP | T1110, T1078 |
| 100111 | 13 | Connexion sortante vers une IP de C2 (MISP) | T1071, T1571 |
| 100112 | 14 | Balise C2 répétée (hôte probablement compromis) | T1071 |

### Corrélation avec la CTI

Une **liste CDB** (`logistia-malicious-ips`) contient les IOC. Elle est **alimentée automatiquement depuis MISP** par un script synchronisé toutes les heures (attributs `ip-dst` / `ip-src` marqués *to_ids*). Les règles de détection interrogent cette liste : toute connexion vers une IP qu'elle contient déclenche une alerte de niveau critique.

Ce mécanisme réalise le pont **Threat Intelligence → détection** : la connaissance des menaces (MISP) est directement opérationnalisée dans le moteur de détection (Wazuh).

## 5. Réponse automatisée (SOAR / Active Response)

Les règles du groupe `logistia_cti` déclenchent une **Active Response** Wazuh : la commande `firewall-drop` **bloque automatiquement** l'adresse IP concernée sur l'agent (via le pare-feu local), pour une durée de 600 secondes.

Chaîne complète validée lors d'un test de détection :

```
Force brute SSH détectée
   └─► règle 5710 (échec d'authentification, natif Wazuh)
        └─► règle 100101 (force brute détectée, niveau 10)
             └─► Active Response : firewall-drop
                  └─► blocage automatique de l'adresse de l'attaquant
```

C'est le **« R » (Response)** d'un SOAR : la remédiation est appliquée sans intervention humaine.

## 6. Gestion des secrets

Aucun secret n'est stocké en clair dans le dépôt :

- les valeurs sensibles (mots de passe, clés d'API) résident dans `ansible/group_vars/all.yml`, **exclu du versionnement** (`.gitignore`) ;
- seul un modèle `all.yml.example` (valeurs `CHANGE_ME`) est versionné ;
- en déploiement CI/CD, le fichier est **généré à la volée** depuis un **GitHub Secret**, puis supprimé en fin de traitement.

## 7. Durcissement

- rôle `logistia-hardening` appliqué à l'ensemble des machines ;
- clés SSH dédiées (authentification par clé) ;
- mises à jour système automatisées lors du provisioning ;
- services exposés réduits au strict nécessaire par la segmentation.
