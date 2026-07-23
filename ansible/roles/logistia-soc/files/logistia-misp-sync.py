#!/usr/bin/env python3
# ============================================================================
# LOGISTIA - Synchronisation MISP -> liste CDB Wazuh
#
# Recupere les attributs de type ip-dst / ip-src marques "to_ids" dans MISP
# et alimente la liste CDB utilisee par les regles de detection Wazuh.
# Execute sur soc-logistia (le manager Wazuh).
# ============================================================================
import json
import os
import subprocess
import sys
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MISP_URL  = os.environ.get("LOGISTIA_MISP_URL", "https://10.40.40.20")
MISP_KEY  = os.environ.get("LOGISTIA_MISP_KEY", "")
CDB_LIST  = "/var/ossec/etc/lists/logistia-malicious-ips"
LOG_FILE  = "/var/log/logistia-ia/misp-sync.log"


def log(msg):
    from datetime import datetime
    line = "[%s] %s" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def recuperer_iocs():
    """Interroge l'API MISP et renvoie un dict {ip: commentaire}."""
    if not MISP_KEY:
        log("Cle API MISP absente (LOGISTIA_MISP_KEY) - liste inchangee")
        return {}
    headers = {
        "Authorization": MISP_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {"returnFormat": "json", "type": ["ip-dst", "ip-src"], "to_ids": 1}
    try:
        r = requests.post(MISP_URL + "/attributes/restSearch",
                          headers=headers, json=payload,
                          verify=False, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log("Erreur interrogation MISP: %s" % e)
        return {}

    iocs = {}
    for attr in data.get("response", {}).get("Attribute", []):
        ip = attr.get("value", "").strip()
        if ip:
            iocs[ip] = "misp-event-%s" % attr.get("event_id", "0")
    return iocs


def ecrire_liste(iocs):
    """Fusionne les IOC MISP avec les entrees existantes et compile la liste."""
    existantes = {}
    if os.path.exists(CDB_LIST):
        with open(CDB_LIST) as f:
            for ligne in f:
                if ":" in ligne:
                    k, v = ligne.strip().split(":", 1)
                    existantes[k] = v

    avant = len(existantes)
    existantes.update(iocs)

    with open(CDB_LIST, "w") as f:
        for ip in sorted(existantes):
            f.write("%s:%s\n" % (ip, existantes[ip]))

    log("Liste CDB : %d entrees (%d ajoutees depuis MISP)" %
        (len(existantes), len(existantes) - avant))

    # Compilation de la liste CDB (binaire .cdb lu par analysisd)
    for binaire in ("/var/ossec/bin/wazuh-makelists",
                    "/var/ossec/bin/ossec-makelists"):
        if os.path.exists(binaire):
            subprocess.run([binaire], capture_output=True)
            log("Liste compilee via %s" % os.path.basename(binaire))
            break
    else:
        log("ATTENTION: binaire makelists introuvable")


def main():
    log("=== Synchronisation MISP -> Wazuh CDB ===")
    iocs = recuperer_iocs()
    log("IOC recuperes depuis MISP : %d" % len(iocs))
    ecrire_liste(iocs)
    log("=== Termine ===")


if __name__ == "__main__":
    main()
