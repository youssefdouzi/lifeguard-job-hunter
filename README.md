# QLD Lifeguard Job Hunter

Chasse automatique 2x/jour des offres lifeguard/pool lifeguard/ocean lifeguard sur Gold Coast
et Brisbane (extensible à toute la côte QLD si rien ne sort), avec analyse IA poussée de
chaque offre par rapport à ton profil, notification Telegram, et dashboard consultable.

## Ce que ça fait concrètement

1. Toutes les 12h (5h et 21h heure Queensland), un scraper va chercher des offres sur
   Seek, Indeed, les sites carrières officiels (SLSQ, RLSSA, councils de Gold Coast et
   Brisbane), des chaînes hôtelières/resorts/parcs aquatiques, et une recherche web
   best-effort (Facebook, Gumtree).
2. Chaque offre trouvée est analysée par un **moteur 100% déterministe** (aucune IA,
   aucune API, 0€) : détection du type de poste, de la zone, du niveau d'expérience,
   extraction du salaire et des prérequis par règles explicites et expressions
   régulières. Le détail des règles est dans `scraper/analyzer_rules.py`, entièrement
   lisible et modifiable.
3. Les nouvelles offres avec un score suffisant te sont envoyées sur Telegram.
4. Un dashboard (page web statique gratuite via GitHub Pages) garde l'historique complet
   et se met à jour à chaque run.

**Limite honnête** : un moteur à règles fait du pattern-matching, pas de la compréhension.
Sur une annonce bien structurée (la norme sur Seek/Indeed/sites officiels), le résultat est
très correct. Sur une annonce mal rédigée ou très atypique, il sera plus rigide qu'une
vraie lecture humaine. Le fichier `analyzer_rules.py` est fait pour être ajusté au fil du
temps si tu remarques un cas mal géré (nouveau mot-clé à ajouter, nouvelle certification,
etc).

Facebook reste le maillon faible de toute façon (voir plus bas), indépendamment du moteur
d'analyse choisi.

**Limite honnête** : Facebook bloque agressivement le scraping automatisé. La couverture
Facebook est best-effort (recherche web indirecte), moins fiable que Seek/Indeed/sites
officiels. Si tu vois trop peu de résultats Facebook, le plus fiable reste de checker
manuellement les groupes Facebook "Gold Coast jobs" / "Brisbane jobs" de temps en temps.

## Setup (environ 15 minutes, une seule fois)

### 1. Créer le repo GitHub
- Crée un nouveau repo **privé** sur GitHub (privé car il contiendra ton historique
  de candidatures potentiel).
- Pousse tout le contenu de ce dossier dedans :
  ```
  git remote add origin https://github.com/TON-USER/qld-lifeguard-hunter.git
  git add .
  git commit -m "Initial commit"
  git branch -M main
  git push -u origin main
  ```

### 2. (Optionnel) Créer une clé API Anthropic
Uniquement si tu veux plus tard passer sur le moteur IA au lieu du moteur à règles
(voir section "Basculer sur l'analyse IA" plus bas). **Ignore cette étape pour rester
à 0€.**
- Va sur https://console.anthropic.com/settings/keys
- Crée une clé API (nécessite un petit budget prépayé).

### 3. Créer un bot Telegram (2 minutes, gratuit)
- Ouvre Telegram, cherche **@BotFather**, envoie `/newbot`, suis les instructions.
- BotFather te donne un **token** (ex: `123456:ABC-DEF...`) → c'est `TELEGRAM_BOT_TOKEN`.
- Envoie un message quelconque à ton nouveau bot pour l'activer.
- Va sur `https://api.telegram.org/bot<TON_TOKEN>/getUpdates` dans ton navigateur,
  tu y trouveras ton `chat.id` → c'est `TELEGRAM_CHAT_ID`.

### 4. Ajouter les secrets dans GitHub
Dans ton repo GitHub : **Settings → Secrets and variables → Actions → New repository secret**.
Ajoute ces 2 secrets (les seuls obligatoires) :
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

(N'ajoute `ANTHROPIC_API_KEY` et `ANALYSIS_ENGINE` que si tu bascules sur le moteur IA,
voir plus bas.)

### 5. Activer GitHub Pages pour le dashboard
- **Settings → Pages → Source** → choisis la branche `main`, dossier `/docs`.
- Ton dashboard sera visible à `https://TON-USER.github.io/qld-lifeguard-hunter/`.

### 6. Premier lancement manuel (pour tester avant d'attendre le cron)
- Onglet **Actions** de ton repo → sélectionne "QLD Lifeguard Job Hunt" → **Run workflow**.
- Vérifie que tu reçois bien un message Telegram (ou le message "rien de nouveau" dans les
  logs si aucune offre ne dépasse le seuil).

## Ajuster les critères

Deux fichiers à connaître :
- `scraper/profile.py` : le texte de référence sur ton profil (certifs, expérience,
  dispo). Sert de documentation interne, à tenir à jour.
- `scraper/analyzer_rules.py` : **le vrai moteur de décision**. C'est ici que tout se
  joue : mots-clés de type de poste, zones géographiques et leurs points, certifications
  reconnues, expressions régulières de salaire, mots-clés de rôle senior, etc. Si tu vois
  une offre mal classée, c'est le fichier à ouvrir - chaque liste est commentée et facile
  à étendre.
- `NOTIFY_SCORE_THRESHOLD` dans `profile.py` : score minimum (0-100) pour déclencher une
  notif Telegram.

## Basculer sur l'analyse IA (optionnel, payant)

Si un jour tu veux un raisonnement plus fin qu'un moteur à règles (nuances qu'un simple
pattern-matching ne capte pas), tu peux repasser sur l'analyse via l'API Anthropic sans
toucher au reste du projet :
1. Crée une clé API sur https://console.anthropic.com/settings/keys
2. Ajoute les secrets GitHub `ANTHROPIC_API_KEY` (ta clé) et `ANALYSIS_ENGINE` = `llm`
3. C'est tout, `main.py` bascule automatiquement sur `scraper/analyzer.py`

Coût si tu actives ce mode : variable selon le modèle et si la recherche web est activée
dans `analyzer.py` (compter large, la recherche web coûte 10€/1000 recherches en plus des
tokens). Le mode par défaut (règles) reste à 0€ dans tous les cas.

## Coûts

- GitHub Actions, GitHub Pages, Telegram : gratuits.
- Moteur d'analyse par défaut (règles) : **0€, aucune clé API nécessaire**.
- Mode IA optionnel : voir section ci-dessus.
