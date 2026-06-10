#!/bin/bash
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

DB_FILE="db/iot_data.db"

echo -e "${RED}[-] Suppression de l'ancienne base de données...${NC}"
rm -f $DB_FILE

echo -e "${GREEN}[+] Recréation d'une base de données SQLite vierge...${NC}"
# On utilise le script python d'initialisation pour recréer la structure
python3 src/subscriber1.py --init-only 2>/dev/null || python3 -c "
import sqlite3, os
os.makedirs('db', exist_ok=True)
conn = sqlite3.connect('$DB_FILE')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS measurements (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, value REAL, unit TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
c.execute('CREATE TABLE IF NOT EXISTS derived_data (id INTEGER PRIMARY KEY AUTOINCREMENT, metric_name TEXT, calculated_value REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
conn.commit()
conn.close()
"

echo -e "${GREEN}[V] Base de données réinitialisée avec succès !${NC}"


