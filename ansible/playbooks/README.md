# Le playbook principal — ordre d'exécution

Le fichier `logistia-site.yml` est le **playbook principal**. Il orchestre la configuration de toute l'infrastructure en associant chaque groupe de machines aux rôles qui le concernent, dans un ordre précis.

## Ordre d'exécution

Le playbook applique les rôles groupe par groupe. L'ordre est important : les fondations réseau et système sont posées avant les applications et la sécurité.

1. **router-logistia** — le routeur est configuré en premier : sans lui, les autres machines n'ont pas de connectivité inter-VLAN ni d'accès à Internet.
2. **Machines applicatives** (app, db) — configuration système commune, durcissement, puis installation des applications (Nginx/Dolibarr/Traccar, MariaDB).
3. **devops-logistia** — le runner CI/CD et les outils d'automatisation.
4. **soc-logistia** — le cœur du SOC : SIEM Wazuh, supervision, règles de détection, réponse automatique, scanner IA.
5. **ia-logistia** — le moteur d'IA (Ollama + modèle phi3).
6. **backup-logistia** — les sauvegardes.
7. **misp / cortex / thehive** — la chaîne de Threat Intelligence.
8. **Agents Wazuh** — enregistrement des agents sur toutes les machines pour qu'elles remontent leurs journaux au SOC.
9. **Vérification finale** — contrôle que les machines répondent correctement.

## Pourquoi cet ordre

- Le **routeur d'abord**, car toute la connectivité en dépend.
- Les **rôles transverses** (système commun, durcissement) avant les rôles applicatifs, pour partir d'une base saine et sécurisée.
- Le **SOC et l'IA** ensemble, car le scanner du SOC a besoin du moteur d'IA.
- Les **agents Wazuh en fin de parcours**, une fois que le manager Wazuh (sur le SOC) est prêt à les accueillir.

## Particularité du déploiement automatisé

Lors du déploiement par GitHub Actions, deux machines sont **volontairement exclues** du playbook : le **routeur** et la machine **devops** (qui héberge le runner). En effet, reconfigurer le routeur couperait le réseau en plein déploiement, et reconfigurer la machine devops interromprait le runner qui exécute le pipeline. Ces deux machines constituent le socle et sont déployées séparément.

Voir [docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md) pour le détail.
