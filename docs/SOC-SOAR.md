# SOC, SOAR et intelligence artificielle — fonctionnement

Ce document explique **comment fonctionne la chaîne de sécurité** de LOGISTIA : quels sont les composants, qui fait quoi, et dans quel ordre les événements sont traités, de la détection d'une menace jusqu'à sa neutralisation.

## 1. Les composants et leur rôle

| Composant | Machine | Rôle dans la chaîne |
|-----------|---------|---------------------|
| **Wazuh** (SIEM) | soc-logistia | Collecte les journaux de toutes les machines, applique les règles de détection, génère les alertes |
| **MISP** | misp-logistia | Base de renseignement sur les menaces (adresses IP et indicateurs malveillants connus) |
| **Cortex** | cortex-logistia | Analyse automatiquement un élément suspect (une IP, un fichier) |
| **TheHive** | thehive-logistia | Centralise les incidents pour l'investigation par l'analyste |
| **Scanner IA** | soc-logistia | Lit les alertes, sélectionne les plus importantes, les fait analyser |
| **Ollama + phi3** | ia-logistia | Modèle d'IA local qui explique l'incident et recommande une action |
| **Active Response** | Wazuh (agents) | Applique automatiquement la réponse (blocage de l'attaquant) |

## 2. La chaîne de traitement, étape par étape

```
   ┌─────────────────────────────────────────────────────────────┐
   │  1. COLLECTE                                                  │
   │  Chaque machine (agent Wazuh) envoie ses journaux au SIEM.   │
   └────────────────────────────┬────────────────────────────────┘
                                 ▼
   ┌─────────────────────────────────────────────────────────────┐
   │  2. DÉTECTION                                                 │
   │  Wazuh applique ses règles. Une règle peut consulter la      │
   │  liste des IP malveillantes synchronisée depuis MISP.        │
   │  → génération d'une alerte (niveau de gravité 1 à 15).       │
   └────────────────────────────┬────────────────────────────────┘
                                 ▼
   ┌─────────────────────────────────────────────────────────────┐
   │  3. ANALYSE PAR L'IA                                          │
   │  Le scanner IA lit les alertes, retient en priorité les plus │
   │  graves, puis demande au modèle phi3 d'expliquer l'incident  │
   │  et de recommander une action. Un rapport est produit.       │
   └────────────────────────────┬────────────────────────────────┘
                                 ▼
   ┌─────────────────────────────────────────────────────────────┐
   │  4. RÉPONSE AUTOMATIQUE (SOAR)                                │
   │  Pour les menaces avérées, Wazuh déclenche l'Active Response │
   │  qui bloque automatiquement l'adresse de l'attaquant.        │
   └────────────────────────────┬────────────────────────────────┘
                                 ▼
   ┌─────────────────────────────────────────────────────────────┐
   │  5. INVESTIGATION                                            │
   │  Les alertes importantes remontent dans TheHive, où          │
   │  l'analyste peut enquêter et solliciter Cortex / MISP.       │
   └─────────────────────────────────────────────────────────────┘
```

## 3. Le SOC — la détection

Le SOC (*Security Operations Center*) est le centre de surveillance. Il repose sur **Wazuh**, qui reçoit les journaux de toutes les machines via des agents installés sur chacune d'elles.

Wazuh applique des **règles de détection**. LOGISTIA ajoute ses propres règles adaptées au contexte, en plus des règles standard :

- détection d'une **attaque en force brute** (nombreuses tentatives de connexion échouées) ;
- détection d'une **connexion vers une adresse malveillante** connue ;
- chaque règle est reliée à une technique référencée dans le cadre **MITRE ATT&CK**.

### Le lien avec la Threat Intelligence (MISP)

Une **liste d'adresses IP malveillantes** est maintenue à jour automatiquement à partir de **MISP** (base de renseignement sur les menaces). Les règles de détection consultent cette liste : si une machine communique avec une adresse qu'elle contient, une alerte de gravité élevée est immédiatement générée.

C'est le pont entre la **connaissance des menaces** (MISP) et la **détection** (Wazuh) : le renseignement est directement mis en pratique.

## 4. L'IA — l'analyse intelligente

Un SIEM produit beaucoup d'alertes, dont la plupart sont mineures. L'analyste ne peut pas toutes les traiter. La brique IA répond à ce problème.

Le **scanner IA** (sur soc-logistia) fonctionne en continu :

1. il **lit** les alertes générées par Wazuh ;
2. il **sélectionne** les incidents à analyser : toutes les alertes graves sont retenues en priorité, complétées par les anomalies statistiques repérées par un algorithme de détection d'anomalies (*Isolation Forest*) ;
3. pour chaque incident, il interroge le **modèle d'IA local** (phi3, via Ollama sur ia-logistia) qui **explique en français** pourquoi l'alerte est suspecte et **recommande une action** ;
4. il produit un **rapport d'incident** lisible.

Le modèle est **open source et exécuté localement** : aucune donnée ne sort de l'infrastructure.

Détails : [IA.md](IA.md).

## 5. Le SOAR — la réponse automatique

SOAR signifie *Security Orchestration, Automation and Response* : l'automatisation de la réponse aux incidents.

Lorsqu'une menace avérée est détectée (par exemple une attaque en force brute), Wazuh déclenche une **Active Response** : la commande de blocage s'exécute automatiquement sur la machine concernée et **bloque l'adresse de l'attaquant** au niveau du pare-feu, pour une durée déterminée.

L'intervention humaine n'est pas nécessaire : la menace est neutralisée en quelques secondes. C'est la traduction concrète de la recommandation faite par l'IA à l'étape précédente.

## 6. L'investigation — MISP, Cortex, TheHive

Pour les incidents nécessitant une analyse approfondie, la chaîne de Threat Intelligence prend le relais :

- **TheHive** centralise les incidents et permet à l'analyste de suivre l'enquête ;
- **Cortex** analyse automatiquement les éléments suspects (une adresse IP, un fichier…) ;
- **MISP** fournit et enrichit le renseignement sur les menaces.

Les alertes Wazuh de gravité élevée sont automatiquement transmises à TheHive, où elles deviennent des cas d'investigation.

## 7. En résumé

LOGISTIA met en œuvre une chaîne de sécurité complète et cohérente :

**détecter** (Wazuh + MISP) → **comprendre** (IA locale) → **répondre** (Active Response) → **enquêter** (TheHive + Cortex).

Chaque maillon a un rôle précis, et l'ensemble fonctionne de façon largement automatisée, ce qui correspond aux pratiques d'un centre de sécurité moderne.
