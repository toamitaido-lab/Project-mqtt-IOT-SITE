# Analyse de Sécurité et Vulnérabilités (Plateforme IoT)

Ce document présente l'analyse des risques de cybersécurité liés à notre infrastructure IoT de remontée de capteurs météorologiques. Il identifie les failles présentes dans le code de démonstration actuel et propose des remédiations pour un passage en production.

---

## 1. Interception des Données (Man-in-the-Middle)
**Importance : Élevé**

* **Le Problème :** Le système actuel utilise le protocole MQTT standard sur le port `1883` avec le broker public HiveMQ (`broker.hivemq.com`). Sur ce port, les données circulent **en clair** sur le réseau. Un attaquant positionné sur le même réseau (ou n'importe où sur le trajet de la donnée) peut "sniffer" les paquets et lire le contenu des JSON.
* **La Remédiation :**
  1. Passer sur le port **8883** (MQTTS).
  2. Implémenter le chiffrement **TLS/SSL** dans les scripts Python lors de la connexion au broker (via `client.tls_set()`).

## 2. Injection de Fausses Données & Usurpation (Spoofing)
**Importance : Élevé**

* **Le Problème :** Le broker public HiveMQ ne requiert **aucune authentification**. N'importe qui connaissant notre topic (ex: `/sae203/itaida/weather/#`) peut publier de fausses températures ou envoyer des données corrompues. Le `subscriber.py` enregistrera ces fausses données dans la base de données SQLite en pensant qu'elles viennent de Mont-de-Marsan ou Dax.
* **La Remédiation :**
  1. Utiliser un **broker MQTT privé** (ex: Mosquitto auto-hébergé sur un serveur Linux).
  2. Activer l'authentification par identifiant et mot de passe (`username_pw_set` dans Paho-MQTT).
  3. Mettre en place des certificats clients (X.509) pour s'assurer que seuls nos capteurs (publishers) peuvent envoyer des données.

## 3. Déni de Service (DoS) et Saturation de la Base de Données
**Importance : Moyen / Élevé**

* **Le Problème :** Le `subscriber.py` écoute le topic et insère *chaque* message reçu dans la base SQLite. Un attaquant peut créer une boucle infinie et publier 10 000 messages par seconde sur notre topic. Le script Python va tenter de tout écrire, ce qui va saturer le CPU, remplir le disque dur avec une base de données gigantesque, et potentiellement faire planter le tableau de bord PHP.
* **La Remédiation :**
  1. **Filtrage applicatif :** Dans le `subscriber.py`, vérifier la taille du payload avant de le traiter (rejeter les paquets > 1 Ko).
  2. **Rate Limiting (Limitation de taux) :** Implémenter une logique en Python pour ignorer les messages si plus de 2 requêtes par seconde proviennent du même topic.
  3. **Durcissement du Broker :** Configurer le broker pour limiter la taille maximale des messages (`message_size_limit`).

## 4. Risques d'Injection (XSS & SQL)
**Importance : Faible (Actuellement mitigé, mais à surveiller)**

* **Le Problème :** Si un attaquant envoie un payload JSON contenant du code JavaScript malveillant dans le champ `"unit"` (ex: `<script>alert('hack')</script>`), ce code pourrait être exécuté par le navigateur de l'administrateur regardant le tableau de bord PHP (Faille XSS). De plus, l'injection de commandes SQL via ces mêmes champs est un risque classique.
* **État Actuel & Remédiation :**
  * **Côté SQL :** Le code actuel utilise partiellement des requêtes préparées (`$stmt->execute([$metric_name])`) ce qui est une excellente pratique. Il faut s'assurer que **toutes** les requêtes d'insertion (dans Python) et de sélection (dans PHP) utilisent l'échappement de paramètres.
  * **Côté XSS :** Le code PHP utilise déjà `htmlspecialchars($row['topic'])` lors de l'affichage dans le tableau. C'est la bonne méthode à conserver absolument.
  * **Amélioration :** Ajouter une **validation stricte du schéma JSON** côté `subscriber.py`. Si le champ `temp` n'est pas un nombre (float), le paquet doit être détruit avant même de toucher à la base de données.

---

## 🔒 Résumé des bonnes pratiques implémentées
Malgré ces vulnérabilités de conception (liées au périmètre de la maquette), certaines bonnes pratiques sont déjà en place :
- Isolation des identifiants : Aucun mot de passe n'est hardcodé en clair dans les scripts actuels.
- Assainissement des affichages Web (utilisation de `htmlspecialchars`).
- Utilisation de `PDO` pour les interactions complexes avec la base de données en PHP.
