#!/usr/bin/env python3
"""LOGISTIA Scanner IA — Lit alerts.json Wazuh via SSH + Isolation Forest + Ollama"""

import json, os, subprocess, requests, numpy as np
from datetime import datetime
from sklearn.ensemble import IsolationForest
from collections import Counter

SOC_IP       = "10.40.40.10"
SOC_USER     = "logistia"
SSH_KEY      = "/home/logistia/.ssh/logistia_ed25519"
ALERTS_FILE  = "/var/ossec/logs/alerts/alerts.json"
OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3:mini"
LOG_FILE     = "/var/log/logistia-scanner/logistia-scanner.log"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    open(LOG_FILE, "a").write(line + "\n")

def lire_alertes():
    alertes = []
    try:
        result = subprocess.run([
            "ssh", "-i", SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            f"{SOC_USER}@{SOC_IP}",
            f"sudo tail -500 {ALERTS_FILE}"
        ], capture_output=True, text=True, timeout=15)
        for line in result.stdout.splitlines():
            try:
                a = json.loads(line.strip())
                alertes.append({
                    "agent":   a.get("agent", {}).get("name", "unknown"),
                    "level":   int(a.get("rule", {}).get("level", 0)),
                    "rule_id": int(a.get("rule", {}).get("id", 0)),
                    "desc":    a.get("rule", {}).get("description", ""),
                    "src_ip":  a.get("data", {}).get("srcip", ""),
                })
            except:
                continue
    except Exception as e:
        log(f"Erreur lecture alertes SSH: {e}")
    return alertes

def detecter(alertes):
    if len(alertes) < 3:
        return []
    ips = Counter(a["src_ip"] for a in alertes)
    X = np.array([[a["level"], ips[a["src_ip"]], a["rule_id"]] for a in alertes])
    preds = IsolationForest(contamination=0.1, random_state=42).fit_predict(X)
    return [alertes[i] for i, p in enumerate(preds) if p == -1]

def expliquer(a):
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": f"2 phrases en francais: pourquoi suspect? agent={a['agent']}, regle={a['desc']}, niveau={a['level']}, ip={a['src_ip']}",
            "stream": False}, timeout=120)
        return r.json().get("response", "N/A")
    except Exception as e:
        return f"Ollama indisponible: {e}"

log("=== LOGISTIA Scanner IA — Demarrage ===")
alertes = lire_alertes()
log(f"Alertes Wazuh lues: {len(alertes)}")
anomalies = detecter(alertes)
log(f"Anomalies detectees: {len(anomalies)}")
for i, a in enumerate(anomalies[:3]):
    log(f"--- ANOMALIE {i+1} ---")
    log(f"  Agent : {a['agent']}")
    log(f"  Regle : {a['desc']} (level {a['level']})")
    log(f"  IP    : {a['src_ip']}")
    log(f"  IA    : {expliquer(a)}")
log("=== Analyse terminee ===")
