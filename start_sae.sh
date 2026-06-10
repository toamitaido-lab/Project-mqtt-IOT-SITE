#!/bin/bash

# Couleurs pour rendre le terminal propre (Style R&T)
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # Pas de couleur

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   DÉMARRAGE DE LA PLATEFORME IOT - SAÉ 203 (UBUNTU)  ${NC}"
echo -e "${CYAN}======================================================${NC}"

# 1. Vérification et installation des dépendances Python si nécessaires
#if ! python3 -c "import paho.mqtt" &> /dev/null; then
 #   echo -e "${RED}[!] Paho-MQTT non trouvé. Installation...${NC}"
  #  pip3 install paho-mqtt
#fi

# 2. Lancement du Subscriber MQTT (Arrière-plan)
echo -e "${GREEN}[+] Lancement du Subscriber MQTT...${NC}"
python3 src/subscriber1.py &
SUB_PID=$! # On garde le PID pour pouvoir le tuer à la fin

# Attente de 2 secondes pour laisser le temps au subscriber d'initialiser la DB
sleep 2

# 3. Lancement du Publisher OpenWeatherMap (Arrière-plan)
echo -e "${GREEN}[+] Lancement du Publisher (API OpenWeather)...${NC}"
python3 src/publisher1.py &
PUB_PID=$!

sleep 1

# 4. Lancement du serveur Web PHP intégré (Premier plan)
echo -e "${GREEN}[+] Démarrage du serveur Web PHP sur http://localhost:8080${NC}"
echo -e "${CYAN}--> Pour couper tout le système, fais : Ctrl+C${NC}"
echo -e "${CYAN}------------------------------------------------------${NC}"

# On se place dans le dossier contenant index.php pour lancer le serveur
cd src/
php -S localhost:8080 index.php

# --- SECTION ARRÊT (Déclenchée lors du Ctrl+C) ---
echo -e "\n${RED}[-] Arrêt des processus IoT en arrière-plan...${NC}"
kill $SUB_PID 2>/dev/null
kill $PUB_PID 2>/dev/null
echo -e "${GREEN}[V] Tout est arrêté proprement. À plus !${NC}"
