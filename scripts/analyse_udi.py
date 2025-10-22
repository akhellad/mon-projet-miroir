import requests
from collections import defaultdict

BASE_URL = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/communes_udi"
DEPT_CODE = "07"

def get_ardeche_communes():
    """Récupère tous les codes INSEE des communes d'Ardèche."""
    url = "https://geo.api.gouv.fr/departements/07/communes"
    r = requests.get(url)
    r.raise_for_status()
    return [c["code"] for c in r.json()]

def fetch_ardeche_data(communes):
    """Télécharge les données UDI pour toutes les communes d'Ardèche."""
    all_data = []
    batch_size = 20
    
    for i in range(0, len(communes), batch_size):
        batch = communes[i:i+batch_size]
        codes = ",".join(batch)
        
        page = 1
        while True:
            url = f"{BASE_URL}?code_commune={codes}&page={page}&size=5000"
            print(f"Batch {i//batch_size + 1}/{(len(communes)-1)//batch_size + 1}, page {page}...")
            
            r = requests.get(url)
            r.raise_for_status()
            json_data = r.json()
            
            data = json_data.get("data", [])
            if not data:
                break
                
            all_data.extend(data)
            
            if not json_data.get("next"):
                break
            page += 1
    
    print(f"✅ {len(all_data)} enregistrements récupérés")
    return all_data

def analyze_data(data):
    """Analyse la relation commune ↔ UDI pour l'Ardèche."""
    commune_to_udis = defaultdict(lambda: {"udis": set(), "nom": None})
    udi_to_communes = defaultdict(lambda: {"communes": set(), "nom": None})
    
    for record in data:
        code_commune = record.get("code_commune")
        code_reseau = record.get("code_reseau")
        nom_commune = record.get("nom_commune")
        nom_reseau = record.get("nom_reseau")
        
        if not code_commune or not code_reseau:
            continue
        
        commune_to_udis[code_commune]["udis"].add(code_reseau)
        commune_to_udis[code_commune]["nom"] = nom_commune
        udi_to_communes[code_reseau]["communes"].add(code_commune)
        udi_to_communes[code_reseau]["nom"] = nom_reseau
    
    communes_multi_udi = {c: v for c, v in commune_to_udis.items() if len(v["udis"]) > 1}
    udis_multi_communes = {u: v for u, v in udi_to_communes.items() if len(v["communes"]) > 1}
    
    print(f"\n=== Résumé ===")
    print(f"Communes : {len(commune_to_udis)}")
    print(f"UDI : {len(udi_to_communes)}")
    print(f"Communes avec plusieurs UDI : {len(communes_multi_udi)}")
    print(f"UDI multi-communes : {len(udis_multi_communes)}")
    
    if communes_multi_udi:
        print(f"\n--- Exemples communes multi-UDI ---")
        for c, v in list(communes_multi_udi.items())[:5]:
            print(f"  {v['nom']} ({c}) → {len(v['udis'])} UDI")
    
    if udis_multi_communes:
        print(f"\n--- Exemples UDI multi-communes ---")
        for u, v in list(udis_multi_communes.items())[:5]:
            print(f"  {v['nom']} ({u}) → {len(v['communes'])} communes")
    
    return commune_to_udis, udi_to_communes

if __name__ == "__main__":
    communes = get_ardeche_communes()
    print(f"🎯 {len(communes)} communes en Ardèche")
    
    data = fetch_ardeche_data(communes)
    commune_to_udis, udi_to_communes = analyze_data(data)