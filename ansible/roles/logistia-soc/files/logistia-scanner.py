#!/usr/bin/env python3
# ============================================================================
# LOGISTIA Scanner IA v2
# Analyse les logs Wazuh (systeme + reseau) et detecte les comportements
# suspects via Isolation Forest (ML) + explication par LLM local (Ollama/phi3).
# Genere des rapports d'analyse d'incident horodates.
#
# Architecture : tourne SUR soc-logistia (acces local aux logs Wazuh),
# appelle le moteur IA Ollama sur ia-logistia (10.50.50.10:11434).
# ============================================================================

import json
import os
import requests
import numpy as np
from datetime import datetime
from sklearn.ensemble import IsolationForest
from collections import Counter

# ---------- Configuration ----------
ALERTS_FILE   = "/var/ossec/logs/alerts/alerts.json"   # logs Wazuh en local
OLLAMA_URL    = "http://10.50.50.10:11434/api/generate" # moteur IA sur ia-logistia
OLLAMA_MODEL  = "phi3:mini"
OLLAMA_TIMEOUT = 300                                    # phi3 en CPU est lent
LOG_DIR       = "/var/log/logistia-ia"
LOG_FILE      = f"{LOG_DIR}/logistia-scanner.log"
REPORT_DIR    = "/var/log/logistia-ia/rapports"
N_TAIL        = 500      # nombre de lignes d'alertes analysees
MAX_ANALYSES  = 2        # nb max d'anomalies expliquees par l'IA (phi3 est lent)
MIN_LEVEL     = 5        # ne considerer que les alertes de niveau >= 5

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def lire_alertes():
    """Lit les dernieres alertes Wazuh depuis le fichier local."""
    alertes = []
    if not os.path.exists(ALERTS_FILE):
        log(f"ERREUR: {ALERTS_FILE} introuvable")
        return alertes
    try:
        # Lire les N dernieres lignes efficacement
        with open(ALERTS_FILE, "r", errors="ignore") as f:
            lines = f.readlines()[-N_TAIL:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
                level = int(a.get("rule", {}).get("level", 0))
                if level < MIN_LEVEL:
                    continue
                alertes.append({
                    "agent":   a.get("agent", {}).get("name", "unknown"),
                    "level":   level,
                    "rule_id": int(a.get("rule", {}).get("id", 0)),
                    "desc":    a.get("rule", {}).get("description", ""),
                    "src_ip":  a.get("data", {}).get("srcip", ""),
                    "ts":      a.get("timestamp", ""),
                })
            except (json.JSONDecodeError, ValueError):
                continue
    except Exception as e:
        log(f"Erreur lecture alertes: {e}")
    return alertes


SEUIL_CRITIQUE = 10   # au-dela, une alerte est toujours analysee (attaque averee)


def detecter_anomalies(alertes):
    """Selection hybride des incidents a analyser :
    1) toutes les alertes CRITIQUES (niveau >= SEUIL_CRITIQUE) - securite d'abord ;
    2) complete par les anomalies statistiques (Isolation Forest) sur le reste.
    Les doublons exacts d'une meme regle sont dedupliques pour eviter le bruit.
    """
    def dedup(liste):
        vus, uniques = set(), []
        for a in liste:
            cle = (a["rule_id"], a["src_ip"])
            if cle not in vus:
                vus.add(cle)
                uniques.append(a)
        return uniques

    # 1) Alertes critiques : priorite absolue
    critiques = [a for a in alertes if a["level"] >= SEUIL_CRITIQUE]

    # 2) Anomalies statistiques sur les alertes non critiques
    non_critiques = [a for a in alertes if a["level"] < SEUIL_CRITIQUE]
    anomalies_ml = []
    if len(non_critiques) >= 5:
        ips = Counter(a["src_ip"] for a in non_critiques if a["src_ip"])
        X = np.array([
            [a["level"], ips.get(a["src_ip"], 0), a["rule_id"]]
            for a in non_critiques
        ])
        model = IsolationForest(contamination=0.15, random_state=42)
        preds = model.fit_predict(X)
        anomalies_ml = [non_critiques[i] for i, p in enumerate(preds) if p == -1]

    # Fusion : critiques d'abord (tries par niveau), puis anomalies ML
    resultat = dedup(critiques) + dedup(anomalies_ml)
    return sorted(resultat, key=lambda x: x["level"], reverse=True)


def expliquer_ia(a):
    """Demande a phi3 (via Ollama) une analyse en francais de l'anomalie."""
    prompt = (
        "Analyste SOC. En 2 phrases courtes en francais: pourquoi cette "
        "alerte est-elle suspecte et quelle action recommandes-tu ?\n"
        f"Agent: {a['agent']} | Regle: {a['desc']} | "
        f"Niveau: {a['level']}/15 | IP: {a['src_ip'] or 'N/A'}"
    )
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 120,   # limite la sortie -> reponse plus rapide
                "temperature": 0.3,   # reponse factuelle
            },
        }, timeout=OLLAMA_TIMEOUT)
        return r.json().get("response", "N/A").strip()
    except Exception as e:
        return f"[Analyse IA indisponible: {e}]"


def generer_rapport(alertes, anomalies, analyses):
    """Ecrit un rapport d'analyse d'incident horodate (Markdown)."""
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = f"{REPORT_DIR}/incident_{ts}.md"
    with open(path, "w") as f:
        f.write(f"# Rapport d'analyse d'incident LOGISTIA\n\n")
        f.write(f"**Date d'analyse** : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
        f.write(f"**Moteur** : Wazuh (SIEM) + Isolation Forest (ML) + phi3:mini (LLM local)\n\n")
        f.write("---\n\n")
        f.write(f"## Synthese\n\n")
        f.write(f"- Alertes analysees (niveau >= {MIN_LEVEL}) : **{len(alertes)}**\n")
        f.write(f"- Comportements anormaux detectes par l'IA : **{len(anomalies)}**\n")
        f.write(f"- Incidents analyses en detail : **{len(analyses)}**\n\n")
        if not analyses:
            f.write("Aucun incident critique necessitant une analyse detaillee.\n")
        else:
            f.write("---\n\n## Incidents detailles\n\n")
            for i, (a, expl) in enumerate(analyses, 1):
                f.write(f"### Incident {i}\n\n")
                f.write(f"| Champ | Valeur |\n|---|---|\n")
                f.write(f"| Agent | {a['agent']} |\n")
                f.write(f"| Regle | {a['desc']} |\n")
                f.write(f"| Severite | {a['level']}/15 |\n")
                f.write(f"| IP source | {a['src_ip'] or 'N/A'} |\n\n")
                f.write(f"**Analyse IA :**\n\n> {expl}\n\n")
    return path


# ---------- Programme principal ----------
def main():
    log("=== LOGISTIA Scanner IA v2 — Demarrage ===")
    alertes = lire_alertes()
    log(f"Alertes Wazuh lues (niveau >= {MIN_LEVEL}): {len(alertes)}")

    anomalies = detecter_anomalies(alertes)
    log(f"Comportements anormaux detectes: {len(anomalies)}")

    analyses = []
    for a in anomalies[:MAX_ANALYSES]:
        log(f"Analyse IA de: {a['agent']} / {a['desc']} (niveau {a['level']})")
        expl = expliquer_ia(a)
        log(f"  -> {expl[:120]}")
        analyses.append((a, expl))

    rapport = generer_rapport(alertes, anomalies, analyses)
    log(f"Rapport genere: {rapport}")
    log("=== Analyse terminee ===")


if __name__ == "__main__":
    main()
