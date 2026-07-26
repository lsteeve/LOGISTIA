#!/usr/bin/env python3
# ============================================================================
# LOGISTIA - Dashboard IA
#
# Genere une page HTML a partir des rapports d'incident produits par le
# scanner IA, et la sert sur http://10.40.40.10:8080
#
# Usage :
#   python3 logistia-ia-dashboard.py           # genere + sert (port 8080)
#   python3 logistia-ia-dashboard.py --once     # genere seulement le HTML
# ============================================================================
import os
import re
import sys
import glob
import html
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler

RAPPORTS_DIR = "/var/log/logistia-ia/rapports"
OUTPUT_HTML  = "/var/log/logistia-ia/dashboard.html"
PORT         = 8080


def lire_rapport(chemin):
    """Extrait les infos d'un rapport Markdown."""
    with open(chemin, encoding="utf-8", errors="replace") as f:
        contenu = f.read()

    data = {"fichier": os.path.basename(chemin), "incidents": []}

    # Date d'analyse
    m = re.search(r"\*\*Date d'analyse\*\*\s*:\s*(.+)", contenu)
    data["date"] = m.group(1).strip() if m else "?"

    # Synthese
    m = re.search(r"niveau >= 5\)\s*:\s*\*\*(\d+)\*\*", contenu)
    data["nb_alertes"] = m.group(1) if m else "?"
    m = re.search(r"analyses en detail\s*:\s*\*\*(\d+)\*\*", contenu)
    data["nb_incidents"] = m.group(1) if m else "?"

    # Incidents : on decoupe par "### Incident"
    blocs = re.split(r"### Incident \d+", contenu)[1:]
    for bloc in blocs:
        inc = {}
        for champ, cle in (("Agent", "agent"), ("Regle", "regle"),
                           ("Severite", "severite"), ("IP source", "ip")):
            m = re.search(r"\|\s*" + champ + r"\s*\|\s*(.+?)\s*\|", bloc)
            inc[cle] = m.group(1).strip() if m else "-"
        # Analyse IA (apres "**Analyse IA :**")
        m = re.search(r"\*\*Analyse IA\s*:\*\*\s*(.+?)(?:###|$)", bloc, re.DOTALL)
        analyse = m.group(1).strip() if m else ""
        # Nettoyer les "> " de citation
        analyse = re.sub(r"^\s*>\s?", "", analyse, flags=re.MULTILINE).strip()
        inc["analyse"] = analyse
        data["incidents"].append(inc)

    return data


def severite_classe(sev):
    """Retourne une classe CSS selon la severite."""
    m = re.match(r"(\d+)", sev)
    if not m:
        return "sev-low"
    n = int(m.group(1))
    if n >= 13:
        return "sev-critique"
    if n >= 10:
        return "sev-haute"
    if n >= 7:
        return "sev-moyenne"
    return "sev-low"


def generer_html():
    fichiers = sorted(glob.glob(os.path.join(RAPPORTS_DIR, "incident_*.md")),
                      reverse=True)
    rapports = [lire_rapport(f) for f in fichiers]

    # Statistiques globales
    total_incidents = sum(len(r["incidents"]) for r in rapports)
    total_critiques = sum(
        1 for r in rapports for i in r["incidents"]
        if severite_classe(i["severite"]) == "sev-critique"
    )

    cartes = []
    for r in rapports:
        incidents_html = []
        for inc in r["incidents"]:
            cls = severite_classe(inc["severite"])
            incidents_html.append(f"""
              <div class="incident {cls}">
                <div class="inc-head">
                  <span class="badge {cls}">{html.escape(inc['severite'])}</span>
                  <span class="agent">{html.escape(inc['agent'])}</span>
                </div>
                <div class="regle">{html.escape(inc['regle'])}</div>
                <div class="meta">IP source : {html.escape(inc['ip'])}</div>
                <div class="analyse">
                  <div class="analyse-label">Analyse IA</div>
                  <p>{html.escape(inc['analyse'])}</p>
                </div>
              </div>""")
        cartes.append(f"""
          <div class="rapport">
            <div class="rapport-head">
              <h2>Rapport du {html.escape(r['date'])}</h2>
              <div class="synthese">
                <span>{r['nb_alertes']} alertes analysees</span>
                <span>{r['nb_incidents']} incidents examines</span>
              </div>
            </div>
            {''.join(incidents_html)}
          </div>""")

    page = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="60">
<title>LOGISTIA - Dashboard IA</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
         background: #0f1419; color: #e6e6e6; padding: 24px; line-height: 1.5; }}
  header {{ text-align: center; margin-bottom: 28px; }}
  header h1 {{ font-size: 26px; color: #4fc3f7; font-weight: 600; }}
  header .sub {{ color: #7a8899; font-size: 13px; margin-top: 4px; }}
  .stats {{ display: flex; gap: 16px; justify-content: center; margin: 24px 0; flex-wrap: wrap; }}
  .stat {{ background: #1a2129; border: 1px solid #2a3441; border-radius: 10px;
          padding: 18px 28px; text-align: center; min-width: 150px; }}
  .stat .num {{ font-size: 32px; font-weight: 700; color: #4fc3f7; }}
  .stat.crit .num {{ color: #ff5252; }}
  .stat .lbl {{ font-size: 12px; color: #7a8899; margin-top: 4px; }}
  .container {{ max-width: 1000px; margin: 0 auto; }}
  .rapport {{ background: #1a2129; border: 1px solid #2a3441; border-radius: 12px;
             padding: 20px; margin-bottom: 20px; }}
  .rapport-head {{ display: flex; justify-content: space-between; align-items: center;
                  border-bottom: 1px solid #2a3441; padding-bottom: 12px; margin-bottom: 16px;
                  flex-wrap: wrap; gap: 8px; }}
  .rapport-head h2 {{ font-size: 16px; color: #cdd9e5; font-weight: 600; }}
  .synthese {{ display: flex; gap: 16px; font-size: 12px; color: #7a8899; }}
  .incident {{ background: #0f1419; border-radius: 8px; padding: 16px; margin-bottom: 12px;
              border-left: 4px solid #2a3441; }}
  .incident.sev-critique {{ border-left-color: #ff5252; }}
  .incident.sev-haute {{ border-left-color: #ff9800; }}
  .incident.sev-moyenne {{ border-left-color: #ffc107; }}
  .inc-head {{ display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }}
  .badge {{ font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 20px;
           background: #2a3441; color: #cdd9e5; }}
  .badge.sev-critique {{ background: #ff5252; color: #fff; }}
  .badge.sev-haute {{ background: #ff9800; color: #fff; }}
  .badge.sev-moyenne {{ background: #ffc107; color: #000; }}
  .agent {{ font-size: 13px; color: #4fc3f7; font-weight: 500; }}
  .regle {{ font-size: 14px; color: #e6e6e6; margin-bottom: 6px; font-weight: 500; }}
  .meta {{ font-size: 12px; color: #7a8899; margin-bottom: 12px; }}
  .analyse {{ background: #141b22; border-radius: 6px; padding: 12px; }}
  .analyse-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;
                   color: #4fc3f7; margin-bottom: 6px; font-weight: 600; }}
  .analyse p {{ font-size: 13px; color: #b8c4d0; white-space: pre-wrap; }}
  footer {{ text-align: center; margin-top: 30px; color: #4a5666; font-size: 12px; }}
  .empty {{ text-align: center; color: #7a8899; padding: 60px; }}
</style>
</head>
<body>
<header>
  <h1>LOGISTIA — Dashboard d'analyse IA</h1>
  <div class="sub">Analyse des incidents de securite par intelligence artificielle locale (phi3 + Isolation Forest)</div>
</header>

<div class="stats">
  <div class="stat"><div class="num">{len(rapports)}</div><div class="lbl">Rapports generes</div></div>
  <div class="stat"><div class="num">{total_incidents}</div><div class="lbl">Incidents analyses</div></div>
  <div class="stat crit"><div class="num">{total_critiques}</div><div class="lbl">Incidents critiques</div></div>
</div>

<div class="container">
  {''.join(cartes) if cartes else '<div class="empty">Aucun rapport pour le moment.</div>'}
</div>

<footer>
  Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M:%S')} — actualisation automatique toutes les 60s
</footer>
</body>
</html>"""

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(page)
    return OUTPUT_HTML


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Regenere la page a chaque visite (toujours a jour)
        generer_html()
        self.path = "/dashboard.html"
        return super().do_GET()

    def log_message(self, *args):
        pass  # silencieux


if __name__ == "__main__":
    chemin = generer_html()
    if "--once" in sys.argv:
        print(f"Dashboard genere : {chemin}")
        sys.exit(0)
    os.chdir(os.path.dirname(OUTPUT_HTML))
    print(f"Dashboard IA disponible sur http://0.0.0.0:{PORT}")
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
