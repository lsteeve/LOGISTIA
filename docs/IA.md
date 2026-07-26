# Brique d'intelligence artificielle — LOGISTIA

## 1. Objectif

L'infrastructure intègre un **modèle d'intelligence artificielle open source, exécuté localement**, chargé d'**analyser les journaux (logs) système et réseau** et de **détecter les comportements anormaux ou suspects**. Il produit des **rapports d'analyse d'incident** en français, directement exploitables par un analyste.

## 2. Une architecture répartie sur deux machines

La brique est distribuée sur deux VM, ce qui respecte la segmentation réseau :

| Composant | Machine | Rôle |
|-----------|---------|------|
| **Scanner d'analyse** | soc-logistia (VLAN SOC) | Lit les alertes, sélectionne les incidents, génère les rapports |
| **Moteur d'inférence** | ia-logistia (VLAN IA) | Héberge Ollama et le modèle phi3 qui rédige l'analyse |

Le scanner tourne **au plus près des données** (sur le SOC, où arrivent les logs) et ne communique avec le moteur d'IA que par **un seul flux réseau autorisé**. Tout le reste du trafic entre ces deux zones reste bloqué.

```
   soc-logistia                              ia-logistia
 ┌────────────────────────────┐          ┌────────────────────┐
 │ Alertes Wazuh              │          │  Ollama            │
 │        │                   │          │    └─ modèle phi3  │
 │        ▼                   │  flux    │                    │
 │ Sélection des incidents    │ ───────► │  (analyse IA)      │
 │ (gravité + anomalies ML)   │ ◄─────── │                    │
 │        │                   │          └────────────────────┘
 │        ▼                   │
 │ Rapport d'incident         │
 └────────────────────────────┘
```

## 3. Technologies

- **Modèle de langage** : **phi3** (modèle open source léger), exécuté via **Ollama**, entièrement **en local**. Aucune donnée n'est envoyée à un service externe.
- **Détection d'anomalies** : **Isolation Forest** (bibliothèque scikit-learn), un algorithme non supervisé qui repère les événements sortant de l'ordinaire.
- **Langage** : Python 3.

## 4. Fonctionnement du scanner

Le scanner s'exécute automatiquement à intervalle régulier (toutes les 10 minutes) grâce à une tâche planifiée. À chaque exécution :

1. **Lecture** — il lit les dernières alertes générées par Wazuh.
2. **Sélection des incidents** — il combine deux approches :
   - **priorité à la gravité** : toutes les alertes de niveau élevé sont retenues, car une attaque avérée ne doit jamais être ignorée ;
   - **détection d'anomalies** : sur les alertes restantes, l'*Isolation Forest* repère celles qui sortent statistiquement de l'ordinaire.
3. **Analyse** — chaque incident retenu est transmis au modèle phi3, qui **explique** en français pourquoi l'alerte est suspecte et **recommande une action**.
4. **Rapport** — un rapport d'incident horodaté est généré.

### Pourquoi combiner deux méthodes ?

Un algorithme d'anomalies seul pourrait laisser passer une attaque fréquente (qui finit par « paraître normale ») ; la priorité donnée à la gravité garantit que ces attaques sont toujours analysées. Inversement, l'Isolation Forest permet de repérer des signaux faibles qu'une simple règle ne détecterait pas. Les deux approches sont complémentaires.

## 5. Exemple de rapport

Extrait d'un rapport généré lors d'un test de détection :

> **Incident** — Machine : app-logistia · Règle : connexion sortante vers une IP malveillante connue · Gravité : 13/15
>
> *Analyse IA :* « L'alerte est suspecte car elle indique un accès à une adresse IP connue pour le trafic malveillant. Je recommande de bloquer l'adresse concernée et d'enquêter sur cette connexion sortante. »

L'IA a correctement qualifié la menace **et** recommandé l'action appropriée — action ensuite appliquée automatiquement par la réponse automatique (voir [SOC-SOAR.md](SOC-SOAR.md)).

## 6. Déploiement (Infrastructure as Code)

La brique est entièrement décrite dans le code, donc reproductible à l'identique :

- le rôle Ansible **logistia-ia** installe Ollama et télécharge le modèle sur ia-logistia ;
- le rôle **logistia-soc** installe le scanner, ses dépendances et sa tâche planifiée sur soc-logistia.

Elle fonctionne donc de la même façon quel que soit le mode de déploiement (manuel ou automatisé).
