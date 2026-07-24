#!/usr/bin/env bash
# ============================================================================
# LOGISTIA - Scenario d'attaque simulee (v2)
# A lancer depuis app-logistia. Simule un attaquant sur le serveur web :
#   1. Canal C2 vers une IP malveillante MISP (ecrit dans /var/log/logistia-net.log)
#   2. Rebond force brute SSH vers une VM interne
# USAGE : ./logistia-attack-sim.sh [c2|bruteforce|full]
# ============================================================================
set -u
C2_IP="185.220.101.5"
C2_PORT="443"
SSH_TARGET="10.20.20.10"
NETLOG="/var/log/logistia-net.log"
SRC_HOST="app-logistia"
SCENARIO="${1:-full}"

ecrire_netlog() {
  echo "$*" | sudo tee -a "${NETLOG}" >/dev/null 2>&1 || echo "$*" >> "${NETLOG}" 2>/dev/null
}

log_c2() {
  echo ">>> [Phase C2] Canal Command & Control vers ${C2_IP}"
  for i in 1 2 3 4; do
    ecrire_netlog "logistia-net: outbound connection to ${C2_IP} port ${C2_PORT} from ${SRC_HOST}"
    echo "    balise C2 #${i} envoyee (${C2_IP}:${C2_PORT})"
    sleep 3
  done
  echo "    -> regles attendues : 100111 (niveau 13) puis 100112 (niveau 14)"
}

brute_force() {
  echo ">>> [Phase Brute-force] Tentatives SSH repetees vers ${SSH_TARGET}"
  for i in 1 2 3 4 5 6; do
    ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
        -o PreferredAuthentications=password -o PubkeyAuthentication=no \
        "attacker${i}@${SSH_TARGET}" "exit" 2>/dev/null
    echo "    tentative SSH #${i} (attacker${i}@${SSH_TARGET})"
    sleep 2
  done
  echo "    -> regle attendue : 100101 (niveau 10) cote db-logistia"
}

echo "=================================================="
echo " LOGISTIA - Scenario d'attaque simulee : ${SCENARIO}"
echo " Source : ${SRC_HOST} ($(hostname -I | awk '{print $1}'))"
echo " Horodatage : $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

case "${SCENARIO}" in
  c2)          log_c2 ;;
  bruteforce)  brute_force ;;
  full)        log_c2; echo; brute_force ;;
  *)           echo "Usage: $0 [c2|bruteforce|full]"; exit 1 ;;
esac
echo
echo "Scenario termine. Verifiez le dashboard Wazuh et le prochain rapport IA."
