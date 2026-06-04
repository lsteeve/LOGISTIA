#!/usr/bin/env python3
# LOGISTIA — Scanner IA de securite
# Isolation Forest pour la detection d anomalies dans les logs
# Ollama phi3:mini pour l explication en langage naturel

import re
import requests
from datetime import datetime
from pathlib import Path
from collections import Counter, deque
from sklearn.ensemble import IsolationForest
import numpy as np

LOGISTIA_LOG_FILES  = ["/var/log/auth.log", "/var/log/syslog"]
LOGISTIA_ALERT_FILE = Path("/var/log/logistia-ia/logistia-alerts.log")
LOGISTIA_OLLAMA_URL = "http://10.50.50.10:11434/api/generate"
LOGISTIA_MODEL      = "phi3:mini"
LOGISTIA_THRESHOLD  = 5

LOGISTIA_PATTERNS = [
    {
        "name": "ssh-failure",
        "regex": re.compile(r"Failed password for (\S+) from (\S+)", re.I)
    },
    {
        "name": "invalid-user",
        "regex": re.compile(r"Invalid user (\S+) from (\S+)", re.I)
    },
    {
        "name": "auth-failure",
        "regex": re.compile(r"authentication failure.*rhost=(\S+)", re.I)
    },
]


def logistia_tail(path, n=1000):
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r", errors="ignore") as f:
        return list(deque(f, maxlen=n))


def logistia_parse_logs():
    counts = Counter()
    for log_path in LOGISTIA_LOG_FILES:
        for line in logistia_tail(log_path):
            for pattern in LOGISTIA_PATTERNS:
                match = pattern["regex"].search(line)
                if match:
                    ip = match.group(2) if match.lastindex >= 2 else match.group(1)
                    counts[(pattern["name"], ip)] += 1
    return counts


def logistia_build_features(counts):
    import random
    rows, labels = [], []
    hour = datetime.now().hour
    for (reason, ip), count in counts.items():
        rows.append([count, hour, 1])
        labels.append({"reason": reason, "ip": ip, "count": count, "hour": hour})
    for _ in range(max(30, len(rows) * 5)):
        rows.append([random.randint(0, 2), random.randint(8, 18), 0])
        labels.append(None)
    return rows, labels


def logistia_detect(rows, labels):
    if len(rows) < 5:
        return []
    X = np.array(rows)
    model = IsolationForest(contamination=0.1, random_state=42)
    predictions = model.fit_predict(X)
    return [labels[i] for i, p in enumerate(predictions) if p == -1 and labels[i] is not None]


def logistia_explain(anomaly):
    try:
        prompt = (
            f"Analyse securite LOGISTIA en 2 phrases : "
            f"{anomaly['count']} echecs {anomaly['reason']} depuis {anomaly['ip']} "
            f"a {anomaly['hour']}h. Suspect ? Recommandation ?"
        )
        response = requests.post(
            LOGISTIA_OLLAMA_URL,
            json={"model": LOGISTIA_MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        return response.json().get("response", "N/A")
    except Exception:
        return "Anomalie detectee par Isolation Forest (Ollama indisponible)"


def main():
    print("=== LOGISTIA Scanner — Analyse securite ===")
    print(f"Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    counts = logistia_parse_logs()
    rows, labels = logistia_build_features(counts)
    anomalies = logistia_detect(rows, labels)

    threshold_alerts = [
        {"reason": r, "ip": ip, "count": c, "hour": datetime.now().hour}
        for (r, ip), c in counts.items() if c >= LOGISTIA_THRESHOLD
    ]

    all_alerts = anomalies + [a for a in threshold_alerts if a not in anomalies]

    print(f"Logs analyses   : {sum(counts.values())}")
    print(f"Anomalies IA    : {len(anomalies)}")
    print(f"Alertes seuil   : {len(threshold_alerts)}")
    print()

    LOGISTIA_ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not all_alerts:
        print("Aucune anomalie detectee.")
        with LOGISTIA_ALERT_FILE.open("a") as f:
            f.write(f"{datetime.now()} — OK — Aucune anomalie\n")
        return

    for i, alert in enumerate(all_alerts):
        print(f"--- ALERTE LOGISTIA {i + 1} ---")
        print(f"  Type        : {alert['reason']}")
        print(f"  IP source   : {alert['ip']}")
        print(f"  Occurrences : {alert['count']}")
        print(f"  Heure       : {alert['hour']}h")
        explanation = logistia_explain(alert)
        print(f"  Analyse IA  : {explanation}")
        print()
        with LOGISTIA_ALERT_FILE.open("a") as f:
            f.write(
                f"{datetime.now()} — {alert['reason']} — "
                f"IP={alert['ip']} — {alert['count']} fois\n"
            )

    print("=== Scan termine ===")


if __name__ == "__main__":
    main()
