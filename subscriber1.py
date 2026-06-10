import paho.mqtt.client as mqtt
import sqlite3
import json
import os

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "/sae203/itaida/weather/#"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "iot_data.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            value REAL,
            unit TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS derived_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            calculated_value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("[+] Base de données prête et initialisée.")

def compute_derived_metrics(cursor):
    """Calcule et insère les moyennes par ville et la moyenne globale entre les deux."""
    # 1. Moyenne générale historique de Mont-de-Marsan
    cursor.execute("SELECT AVG(value) FROM measurements WHERE topic = '/weather/mdm/temp'")
    avg_mdm = cursor.fetchone()[0]
    if avg_mdm is not None:
        cursor.execute("INSERT INTO derived_data (metric_name, calculated_value) VALUES (?, ?)", ("avg_temp_mdm", round(avg_mdm, 2)))

    # 2. Moyenne générale historique de Dax
    cursor.execute("SELECT AVG(value) FROM measurements WHERE topic = '/weather/dax/temp'")
    avg_dax = cursor.fetchone()[0]
    if avg_dax is not None:
        cursor.execute("INSERT INTO derived_data (metric_name, calculated_value) VALUES (?, ?)", ("avg_temp_dax", round(avg_dax, 2)))

    # 3. Moyenne instantanée entre les deux villes (Moyenne entre les deux derniers points reçus)
    cursor.execute("SELECT value FROM measurements WHERE topic = '/weather/mdm/temp' ORDER BY timestamp DESC LIMIT 1")
    last_mdm = cursor.fetchone()
    cursor.execute("SELECT value FROM measurements WHERE topic = '/weather/dax/temp' ORDER BY timestamp DESC LIMIT 1")
    last_dax = cursor.fetchone()
    
    if last_mdm and last_dax:
        mean_between = (last_mdm[0] + last_dax[0]) / 2
        cursor.execute("INSERT INTO derived_data (metric_name, calculated_value) VALUES (?, ?)", ("mean_temp_mdm_dax", round(mean_between, 2)))
        print(f"[CALCUL] Moyennes recalculées (MDM: {avg_mdm:.1f}°C | DAX: {avg_dax:.1f}°C | Entre-deux: {mean_between:.1f}°C)")

def save_to_db(topic, payload):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if topic.endswith("/all"):
            city = "mdm" if "mdm" in topic else "dax"
            data = json.loads(payload)
            
            for res in data["results"]:
                label = res.get("label")
                value = res.get("value")
                unit = res.get("unit", "")
                
                virtual_topic = f"/weather/{city}/{label}"
                cursor.execute("INSERT INTO measurements (topic, value, unit) VALUES (?, ?, ?)", (virtual_topic, value, unit))
                
                # Dès qu'une nouvelle température arrive, on met à jour les calculs dérivés
                if label == "temp":
                    compute_derived_metrics(cursor)
                    
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERREUR BDD] : {e}")

def on_connect(client, userdata, flags, rc):
    print("[+] Subscriber connecté. Écoute du flux météo en cours...")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    save_to_db(msg.topic, msg.payload.decode())

if __name__ == "__main__":
    init_db()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
