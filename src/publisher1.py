import paho.mqtt.client as mqtt
import json
import random
import time

BROKER = "broker.hivemq.com"
PORT = 1883
BASE_TOPIC = "/sae203/itaida/weather"

def generate_payload(city_name, base_temp):
    """Génère le payload JSON conforme au cahier des charges de la SAE."""
    timestamp = int(time.time())
    temp = round(base_temp + random.uniform(-1.2, 1.2), 2)
    humidity = random.randint(55, 75)
    
    return {
        "name": f"itaida.sensor.{city_name}.{timestamp}",
        "results": [
            {"label": "temp", "value": temp, "unit": "Celsius"},
            {"label": "humidity", "value": humidity, "unit": "%"}
        ],
        "collections": ["IUT_MdM_weather"],
        "featureOfInterest": f"IUT_MdM_{city_name}"
    }

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    
    try:
        client.connect(BROKER, PORT, 60)
        print("[+] Publisher Synchrone Démarré.")
        print("[-] Envoi des paquets (MDM & DAX) toutes les 10 secondes...\n")
        
        while True:
            # Envoi Mont-de-Marsan
            payload_mdm = generate_payload("mdm", 20.2)
            client.publish(f"{BASE_TOPIC}/mdm/all", json.dumps(payload_mdm))
            print(f"[PUBLISH] -> Données de Mont-de-Marsan envoyées.")
            
            # Envoi Dax
            payload_dax = generate_payload("dax", 17.8)
            client.publish(f"{BASE_TOPIC}/dax/all", json.dumps(payload_dax))
            print(f"[PUBLISH] -> Données de Dax envoyées.")
            print("--------------------------------------------------")
            
            time.sleep(10) # Cadence fixe et propre de 10 secondes
            
    except KeyboardInterrupt:
        print("\n[-] Arrêt du émetteur.")
