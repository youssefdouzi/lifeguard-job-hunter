"""
Profil du candidat et critères de matching.
Modifie ce fichier librement, aucun autre fichier n'a besoin de changer.
"""

CANDIDATE_PROFILE = """
Nom: Youssef Douzi
Situation: Relocalisation en Australie sur Working Holiday Visa (subclass 417), arrivée prévue
début novembre 2026, plein droit de travailler. Ouvert aux placements saisonniers et régionaux
partout dans le Queensland, dispo week-ends, jours fériés, débuts tôt et shifts coupés.
Zone cible prioritaire: Queensland, Gold Coast et Brisbane. Sunshine Coast et reste du QLD
acceptables si rien ne sort dans les deux premières zones.

Niveau réel: PAS un profil débutant. Superviseur/chef de poste avec responsabilité d'équipe
et gestion d'incidents, à valoriser sur des offres senior/lead si elles existent, en plus
des offres lifeguard standard.

Certifications françaises/UK et équivalences visées:
- BNSSA (-> Bronze Medallion / Certificate II in Public Safety - Aquatic Rescue)
- SLSGB Surf Lifeguard Award, passé en Bretagne fin septembre 2026 (-> pathway direct Bronze Medallion)
- PSE1 (-> HLTAID011 Provide First Aid)
- PSE2 (-> soins pré-hospitaliers avancés: immobilisation spinale, oxygénothérapie, gestion
  traumatologie/noyade, leadership d'équipe)
- PAE FPSE: formateur premiers secours accrédité (conception et évaluation de formations)
- Permis B, Permis côtier (-> Queensland Recreational Marine Driver Licence), Permis A2 en cours

Démarches déjà en cours en Australie:
- Cours de mise à niveau RLSSA Queensland (~250 AUD) devisé et prévu à l'arrivée
- Blue Card et USI à déposer à l'arrivée
- Correspondance et candidature envoyées à Surf Life Saving Queensland (zone SEQ / Gold Coast)
- Candidature envoyée à l'Australian Lifeguard Service Queensland
- Prépare les tests physiques: 800m piscine sous 14 minutes + circuit run-swim-run océan

Expérience terrain (résumé, à considérer comme un vrai atout de séniorité):
- Chef de poste / superviseur, Lac de Peyrolles (France), saisons 2024-2026: supervise une
  équipe d'environ 10 sauveteurs sur plage surveillée + aquapark gonflable, gère plannings,
  briefings, commandement d'incident, statut des drapeaux, stock matériel, formation des
  nouveaux sauveteurs
- Chef d'équipe secours (jusqu'à 30 secouristes), AMS Croix Blanche, depuis février 2024:
  couverture médicale d'événements de plus de 50 000 personnes (Stade Vélodrome, Dôme de
  Marseille, 14 juillet, réveillon), Ironman, marathons, soins PSE2, liaison SAMU/pompiers/police
- Sauveteur eau libre (saisonnier 2024-2026): Défi Monte-Cristo, La Ciotat, Embrunman,
  extraction de nageurs, hypothermie, gestion houle/courant/visibilité, coordination avec
  officiels de course
- Jeux Olympiques Paris 2024: sécurité aquatique sur les épreuves de voile, marina olympique
- Disneyland Paris (Davy Crockett Ranch), saisons hiver 2024-2025: surveillance piscine resort
  familial international, service en anglais et français
- Formateur premiers secours accrédité (Service Civique, AMS Croix Blanche, oct 2025-mai 2026):
  dispense de formations PSE/PSC1, tenue de postes de secours événementiels

Langues: français natif, anglais C1 (fluent professionnel), arabe B2, espagnol A2 -
argument fort pour des postes orientés clientèle internationale (resorts, parcs aquatiques).

Fitness: entretenue à l'année (natation, callisthénie, taekwondo, randonnée/montagne),
standards Surf Life Saving Australia visés (800m/14min, run-swim-run).

Ce qu'il n'est PAS: pas moniteur de natation (swim instructor) sauf si l'offre n'exige aucune
expérience préalable ou accepte un profil sauveteur en reconversion.

Types de postes recherchés (large, pas de filtre mot-clé strict):
- Lifeguard / Ocean Lifeguard / Beach Lifeguard, y compris rôles senior/lead/supervisor
- Pool Lifeguard / Aquatic Lifeguard
- Postes privés: hôtels, resorts, parcs aquatiques, piscines de complexes résidentiels,
  camps, écoles avec piscine - un profil multilingue et orienté clientèle internationale
  est un vrai plus ici
- Tout poste de sécurité aquatique/premiers secours/formation premiers secours où ce profil
  serait pertinent, même si l'intitulé exact diffère

Contrat: peu importe (casual, saisonnier, permanent, temps partiel) - tout est à montrer.
"""

# Zones à couvrir, dans cet ordre de priorité (utilisé pour les requêtes de recherche)
LOCATIONS_PRIORITY = [
    "Gold Coast QLD",
    "Brisbane QLD",
    "Sunshine Coast QLD",
    "Queensland",
]

# Score minimum (0-100, donné par l'analyse IA) pour qu'une offre soit remontée en notification
NOTIFY_SCORE_THRESHOLD = 55
