import time
import re
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from geopy.geocoders import Nominatim
import urllib.parse 

# --- CONFIGURACIÓN AUTOMATIZADA ---
PAGES_TO_SCAN = 10  # Escaneamos más páginas ya que es una vez a la semana
OUTPUT_FILE = "data.csv"
TARGET_CITY = "Mérida, Yucatán" # Búsqueda general

# Cache de coordenadas (Igual que antes para velocidad)
COORD_CACHE = {
    "Temozón Norte": [21.0655, -89.6338],
    "Cholul": [21.0456, -89.5516],
    "Mérida Centro": [20.9676, -89.6237],
    "Centro": [20.9676, -89.6237],
    "Altabrisa": [21.0182, -89.5855],
    "Montes de Amé": [21.0205, -89.6102],
    "Cabo Norte": [21.0378, -89.5935],
    "Dzityá": [21.0505, -89.6805],
    "Country Club": [21.0805, -89.6005],
    "Santa Gertrudis Copó": [21.0255, -89.5955],
    "Caucel": [20.9905, -89.7005],
    "Las Américas": [21.0555, -89.6555],
    "Conkal": [21.0735, -89.5205],
    "Campestre": [21.0005, -89.6155],
    "Montebello": [21.0285, -89.5905],
    "Benito Juárez Norte": [21.0105, -89.6055],
    "Itzimná": [20.9925, -89.6125],
    "Pensiones": [20.9855, -89.6605],
    "Los Héroes": [20.9805, -89.5405]
}

def get_clean_title(raw_text):
    lines = raw_text.split('\n')
    blacklist = ["DESTACADO", "RECIÉN", "PRECIO", "NUEVO", "OFERTA", "REMATE", 
                 "OPORTUNIDAD", "MIEMBRO", "VER TELÉFONO", "CONTACTAR", "WHATSAPP"]
    for line in lines:
        clean = line.strip()
        if not clean or "$" in clean or clean.isdigit() or len(clean) < 5: continue
        if any(b in clean.upper() for b in blacklist): continue
        return re.sub(r'^\d+\s*', '', clean)
    return "Propiedad"

def get_real_coords(zone_name):
    for key, val in COORD_CACHE.items():
        if key.lower() in zone_name.lower():
            return val[0] + (random.uniform(-0.0005, 0.0005)), val[1] + (random.uniform(-0.0005, 0.0005))
    try:
        geolocator = Nominatim(user_agent="gh_action_inmobot")
        loc = geolocator.geocode(f"{zone_name}, Mérida, Yucatán", timeout=3)
        if loc:
            COORD_CACHE[zone_name] = [loc.latitude, loc.longitude]
            return loc.latitude, loc.longitude
    except: pass
    return 20.9676 + random.uniform(-0.02, 0.02), -89.6237 + random.uniform(-0.02, 0.02)

def run_scraper():
    print("--- 🤖 INICIANDO EJECUCIÓN AUTOMATIZADA (GITHUB ACTIONS) ---")
    
    options = Options()
    options.add_argument("--headless") # OBLIGATORIO PARA LA NUBE (Sin pantalla)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    data = []
    processed_ids = set()
    
    # URL General para Mérida
    base_url = "https://www.lamudi.com.mx/yucatan/merida/for-sale/"

    try:
        for page in range(1, PAGES_TO_SCAN + 1):
            url = f"{base_url}?page={page}"
            print(f"Scanning: {url}")
            driver.get(url)
            time.sleep(5 + random.random()) 
            
            prices = driver.find_elements(By.XPATH, "//*[contains(text(), '$')]")
            
            for elem in prices:
                try:
                    p_txt = elem.text.strip()
                    if "$" not in p_txt or len(p_txt) > 25 or not any(c.isdigit() for c in p_txt): continue

                    try: card = elem.find_element(By.XPATH, "./../../..")
                    except: continue
                    
                    full_txt = card.text
                    if full_txt in processed_ids: continue
                    processed_ids.add(full_txt)

                    title = get_clean_title(full_txt)
                    meters = 0
                    m_match = re.search(r'(\d[\d,.]*)\s*(m²|m2)', full_txt, re.IGNORECASE)
                    if m_match: meters = float(m_match.group(1).replace(",", ""))

                    loc = "Mérida"
                    for z in COORD_CACHE.keys():
                        if z.lower() in full_txt.lower():
                            loc = z
                            break
                    
                    lat, lon = get_real_coords(loc)
                    price = float(re.sub(r'[^\d.]', '', p_txt))
                    try: link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except: link = "#"

                    if price > 100000:
                        data.append({
                            "Titulo": title, "Precio": price, "Metros": meters,
                            "Precio_m2": round(price/meters, 2) if meters > 0 else 0,
                            "Ubicacion": loc, "Link": link, "lat": lat, "lon": lon
                        })
                except: continue
    except Exception as e: print(e)
    finally: driver.quit()

    if data:
        df = pd.DataFrame(data)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"✅ EXITO: {len(df)} propiedades guardadas en {OUTPUT_FILE}")
    else:
        print("⚠️ No se encontraron datos.")

if __name__ == "__main__":
    run_scraper()