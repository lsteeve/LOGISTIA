#!/usr/bin/env bash
# ============================================================================
# LOGISTIA v2 — Pose du role logistia-misp dans le depot + patch inventaire/site
# A executer sur PVE, dans /root/logistia
# ============================================================================
set -e
cd /root/logistia

echo "==> 1. Creation de l'arborescence du role logistia-misp"
mkdir -p ansible/roles/logistia-misp/{tasks,handlers,templates,defaults}

echo "==> 2. tasks/main.yml"
cat > ansible/roles/logistia-misp/tasks/main.yml <<'EOF'
---
- name: Installer dependances misp-logistia
  apt:
    name:
      - docker.io
      - docker-compose-v2
      - git
      - curl
      - jq
    state: present
    update_cache: true

- name: Activer Docker
  systemd:
    name: docker
    enabled: true
    state: started

- name: Ajouter logistia au groupe docker
  user:
    name: logistia
    groups: docker
    append: true

- name: Cloner le depot officiel misp-docker
  git:
    repo: https://github.com/MISP/misp-docker.git
    dest: /opt/logistia-misp
    version: master
    force: false
  become_user: logistia

- name: Generer le fichier .env MISP
  template:
    src: env.j2
    dest: /opt/logistia-misp/.env
    owner: logistia
    mode: '0640'
  notify: Redemarrer MISP

- name: Recuperer les images MISP (pull)
  command: docker compose pull
  args:
    chdir: /opt/logistia-misp
  register: misp_pull
  changed_when: "'Pulled' in misp_pull.stdout or 'Downloaded' in misp_pull.stdout"

- name: Demarrer la stack MISP
  command: docker compose up -d
  args:
    chdir: /opt/logistia-misp
  register: misp_up
  changed_when: "'Started' in misp_up.stderr or 'Created' in misp_up.stderr"

- name: Node Exporter metriques misp-logistia
  apt:
    name: prometheus-node-exporter
    state: present

- name: Activer Node Exporter
  systemd:
    name: prometheus-node-exporter
    enabled: true
    state: started

- name: Attendre que MISP reponde en HTTPS
  uri:
    url: "https://{{ misp_ip }}/users/login"
    validate_certs: false
    status_code: [200, 302]
  register: misp_health
  until: misp_health.status in [200, 302]
  retries: 30
  delay: 20
  ignore_errors: true

- name: Etat du deploiement MISP
  debug:
    msg: >
      MISP deploye sur https://{{ misp_ip }} —
      compte admin initial : {{ misp_admin_email }} /
      (voir ADMIN_PASSWORD dans /opt/logistia-misp/.env).
      Health check HTTPS : {{ 'OK' if misp_health.status is defined and misp_health.status in [200,302] else 'en cours de demarrage' }}
EOF

echo "==> 3. handlers/main.yml"
cat > ansible/roles/logistia-misp/handlers/main.yml <<'EOF'
---
- name: Redemarrer MISP
  command: docker compose up -d --force-recreate
  args:
    chdir: /opt/logistia-misp
EOF

echo "==> 4. defaults/main.yml (secrets references vers le vault)"
cat > ansible/roles/logistia-misp/defaults/main.yml <<'EOF'
---
# Variables du role logistia-misp
# Les secrets viennent de group_vars/logistia-vault.yml (ansible-vault),
# avec un default() de secours comme les autres roles du projet.
misp_ip: "10.40.40.20"
misp_admin_email: "admin@logistia.net"
misp_admin_org: "LOGISTIA"
misp_admin_password:   "{{ logistia_misp_admin_password | default('logistia_misp') }}"
misp_db_password:      "{{ logistia_misp_db_password | default('logistia_misp') }}"
misp_db_root_password: "{{ logistia_misp_db_root_password | default('logistia_misp_root') }}"
EOF

echo "==> 5. templates/env.j2"
cat > ansible/roles/logistia-misp/templates/env.j2 <<'EOF'
# MISP misp-docker — configuration LOGISTIA (genere par Ansible)
BASE_URL=https://{{ misp_ip }}
MISP_BASEURL=https://{{ misp_ip }}
ADMIN_EMAIL={{ misp_admin_email }}
ADMIN_PASSWORD={{ misp_admin_password }}
ADMIN_ORG={{ misp_admin_org }}
MYSQL_HOST=db
MYSQL_DATABASE=misp
MYSQL_USER=misp
MYSQL_PASSWORD={{ misp_db_password }}
MYSQL_ROOT_PASSWORD={{ misp_db_root_password }}
REDIS_FQDN=redis
DISABLE_IPV6=true
MISP_MODULES_FQDN=http://misp-modules
NUMBER_OF_MISP_WORKERS=3
TIMEZONE=Europe/Paris
EOF

echo "==> 6. Patch inventaire (idempotent)"
if ! grep -q "logistia-misp" ansible/logistia-inventory.ini; then
  # insere le bloc misp juste apres la ligne soc-logistia
  awk '
    /^soc-logistia ansible_host=/ {
      print
      print ""
      print "[logistia-misp]"
      print "misp-logistia ansible_host=10.40.40.20"
      next
    }
    { print }
  ' ansible/logistia-inventory.ini > /tmp/inv.new && mv /tmp/inv.new ansible/logistia-inventory.ini
  echo "    -> bloc [logistia-misp] ajoute"
else
  echo "    -> deja present, rien a faire"
fi

echo "==> 7. Patch playbook site.yml (idempotent)"
if ! grep -q "logistia-misp" ansible/playbooks/logistia-site.yml; then
  python3 - <<'PY'
import io
p = "ansible/playbooks/logistia-site.yml"
s = open(p).read()
anchor = "- name: ia-logistia"
play = ("- name: misp-logistia — CTI MISP via Docker\n"
        "  hosts: logistia-misp\n"
        "  become: true\n"
        "  roles:\n"
        "    - logistia-misp\n")
s = s.replace(anchor, play + anchor, 1)
open(p, "w").write(s)
print("    -> play misp-logistia insere avant ia-logistia")
PY
else
  echo "    -> deja present, rien a faire"
fi

echo "==> 8. Patch vault .example (idempotent)"
VEX="ansible/group_vars/logistia-vault.yml.example"
if [ -f "$VEX" ] && ! grep -q "logistia_misp_admin_password" "$VEX"; then
  cat >> "$VEX" <<'EOF'
logistia_misp_admin_password:     "CHANGE_ME"
logistia_misp_db_password:        "CHANGE_ME"
logistia_misp_db_root_password:   "CHANGE_ME"
EOF
  echo "    -> 3 secrets MISP ajoutes au .example"
else
  echo "    -> deja present ou fichier absent"
fi
echo ""
echo "    RAPPEL: ajouter les VRAIES valeurs dans le vault chiffre :"
echo "      cd ansible && ansible-vault edit group_vars/logistia-vault.yml"

echo ""
echo "======================================================================"
echo " Role logistia-misp pose + inventaire + site.yml + vault.example patches."
echo " Verifs :"
echo "   grep -A1 logistia-misp ansible/logistia-inventory.ini"
echo "   grep -A4 'misp-logistia' ansible/playbooks/logistia-site.yml"
echo ""
echo " Deploiement MISP :"
echo "   cd ansible"
echo "   ansible-playbook -i logistia-inventory.ini playbooks/logistia-site.yml --limit logistia-misp"
echo "======================================================================"
