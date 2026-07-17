# Intégrations SOC — LOGISTIA

Détail des trois intégrations qui forment la chaîne de détection et de réponse.

---

## 1. Wazuh → TheHive

Chaque alerte Wazuh de niveau suffisant crée automatiquement une **alerte** dans
TheHive, dans l'organisation LOGISTIA.

**Mécanisme** : le manager Wazuh exécute un script d'intégration à chaque alerte.

```
Alerte Wazuh (niveau ≥ 7)
   → /var/ossec/integrations/custom-w2thive   (wrapper shell)
   → custom-w2thive.py                         (thehive4py)
   → API TheHive (10.40.40.40:9000)
   → Alerte créée dans l'org LOGISTIA
```

**Configuration** (`/var/ossec/etc/ossec.conf`) :

```xml
<integration>
  <name>custom-w2thive</name>
  <hook_url>http://10.40.40.40:9000</hook_url>
  <api_key>__CLE_API_ANALYSTE_THEHIVE__</api_key>
  <alert_format>json</alert_format>
</integration>
```

Le seuil `lvl_threshold` (défaut 7) filtre le bruit : seules les alertes
significatives remontent. La clé API est celle d'un utilisateur **membre de
l'organisation LOGISTIA** (les alertes appartiennent à une organisation).

---

## 2. TheHive → Cortex

TheHive délègue l'analyse des observables à Cortex. Le connecteur est déclaré
dans la configuration TheHive.

**Configuration** (`application.conf`) :

```
cortex {
  servers = [
    {
      name = "cortex-logistia"
      url  = "http://10.40.40.30:9001"
      auth { type = "bearer", key = "__CLE_API_ANALYSTE_CORTEX__" }
    }
  ]
}
```

Vérification : dans TheHive → *Gestion de la plateforme → Connecteurs → Cortex*,
le serveur `cortex-logistia` doit apparaître connecté (« configuration testée avec
succès »).

---

## 3. Cortex → MISP

L'analyzer `MISP_2_1` de Cortex interroge le serveur MISP pour déterminer si un
observable (IP, domaine, hash…) figure dans les événements de renseignement.

**Configuration de l'analyzer** (via l'interface Cortex, compte analyste) :

| Paramètre    | Valeur                       |
|--------------|------------------------------|
| `url`        | `https://10.40.40.20`        |
| `key`        | clé API MISP                 |
| `cert_check` | désactivé (certificat auto-signé) |
| Max TLP/PAP  | RED (lab)                    |

Test : lancer une analyse sur une IP (ex. `8.8.8.8`) avec `MISP_2_1`. Un statut
**Success** confirme la connexion, même sans correspondance (« 0 hit ») si la base
MISP est vide.

---

## Workflow analyste complet

1. Wazuh détecte → alerte créée dans TheHive.
2. L'analyste ouvre l'alerte, la promeut en **Case**.
3. Sur les observables du case, il lance les **analyzers Cortex**.
4. Cortex enrichit via MISP (et autres sources) → verdict.
5. Le case est documenté, classé, et clôturé.
