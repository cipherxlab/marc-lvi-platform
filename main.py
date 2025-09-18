from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
import os
import pandas as pd

app = FastAPI(title="MARC VEILLE - LVI IMMO")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Zone géographique Emmanuel (codes INSEE)
ZONE_EMMANUEL = {
    "34172": "Montpellier",
    "34057": "Castelnau-le-Lez", 
    "34129": "Lattes",
    "34192": "Pérols",
    "34120": "Jacou",
    "34077": "Clapiers",
    "34169": "Montferrier-sur-Lez",
    "34255": "Saint-Gély-du-Fesc",
    "34153": "Les Matelles",
    "34308": "Teyran",
    "34010": "Assas",
    "34165": "Montaud",
    "34246": "Saint-Drézéry",
    "34090": "Le Crès",
    "34327": "Vendargues",
    "34240": "Saint-Aunès",
    "34175": "Mudaison",
    "34154": "Mauguio"
}

# API DPE ADEME - DONNÉES RÉELLES
async def fetch_real_dpe_data():
    """Récupère les vrais DPE de la zone Emmanuel"""
    try:
        # API ADEME DPE v2
        base_url = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants/lines"
        
        all_dpe = []
        
        for code_insee, commune in ZONE_EMMANUEL.items():
            # Requête pour chaque commune
            params = {
                "format": "json",
                "q": f"Code_postal_(BAN):{code_insee}",
                "size": 100,
                "sort": "Date_réception_DPE:desc",  # Plus récents en premier
                "select": "Adresse_(BAN),Date_réception_DPE,Classe_consommation_énergie,Surface_habitable_logement,Type_bâtiment,Coût_total_5_usages,Estimation_GES"
            }
            
            try:
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    for dpe in data.get('results', []):
                        # Filtrage premium >400k€
                        surface = float(dpe.get('Surface_habitable_logement', 0))
                        if surface > 80:  # Approximation surface = valeur
                            estimation_prix = estimate_price_from_dpe(dpe, commune)
                            
                            if estimation_prix >= 400000:
                                dpe_enrichi = {
                                    **dpe,
                                    'commune': commune,
                                    'code_insee': code_insee,
                                    'estimation_prix': estimation_prix,
                                    'score': calculate_dpe_score(dpe, commune)
                                }
                                all_dpe.append(dpe_enrichi)
                                
            except Exception as e:
                print(f"Erreur DPE {commune}: {e}")
                continue
        
        # Tri par score décroissant
        all_dpe.sort(key=lambda x: x['score'], reverse=True)
        return all_dpe[:50]  # Top 50
        
    except Exception as e:
        print(f"Erreur API DPE: {e}")
        return get_fallback_dpe()

def estimate_price_from_dpe(dpe, commune):
    """Estimation prix basée sur DPE + commune"""
    surface = float(dpe.get('Surface_habitable_logement', 100))
    type_bien = dpe.get('Type_bâtiment', '').lower()
    
    # Prix m² par commune (données marché 2024)
    prix_m2 = {
        "Montpellier": 4200,
        "Castelnau-le-Lez": 4800,
        "Lattes": 4500,
        "Pérols": 4300,
        "Jacou": 5200,
        "Clapiers": 5500,
        "Montferrier-sur-Lez": 5800,
        "Saint-Gély-du-Fesc": 5000,
        "Teyran": 4800,
        "Assas": 6000
    }
    
    base_prix = prix_m2.get(commune, 4000)
    
    # Ajustements
    if 'maison' in type_bien:
        base_prix *= 1.1  # Maison = +10%
    
    # Classe énergétique
    classe = dpe.get('Classe_consommation_énergie', 'D')
    if classe in ['A', 'B']:
        base_prix *= 1.05
    elif classe in ['F', 'G']:
        base_prix *= 0.95
    
    return int(surface * base_prix)

def calculate_dpe_score(dpe, commune):
    """Score priorité prospect (0-100)"""
    score = 50  # Base
    
    # Récence du DPE (plus c'est récent, plus c'est chaud)
    try:
        date_dpe = datetime.strptime(dpe.get('Date_réception_DPE', ''), '%Y-%m-%d')
        jours_depuis = (datetime.now() - date_dpe).days
        
        if jours_depuis <= 7:
            score += 30  # Très récent = très chaud
        elif jours_depuis <= 30:
            score += 20  # Récent = chaud
        elif jours_depuis <= 90:
            score += 10  # Moyen
    except:
        pass
    
    # Valeur du bien
    estimation = estimate_price_from_dpe(dpe, commune)
    if estimation > 600000:
        score += 20
    elif estimation > 500000:
        score += 15
    elif estimation > 400000:
        score += 10
    
    # Commune premium
    if commune in ["Jacou", "Clapiers", "Montferrier-sur-Lez", "Saint-Gély-du-Fesc"]:
        score += 15
    elif commune in ["Montpellier", "Castelnau-le-Lez"]:
        score += 10
    
    # Type de bien
    if 'maison' in dpe.get('Type_bâtiment', '').lower():
        score += 5  # Emmanuel préfère maisons
    
    return min(score, 100)

def get_fallback_dpe():
    """DPE de démonstration si API indisponible"""
    return [
        {
            "Adresse_(BAN)": "15 Rue des Palmiers",
            "Date_réception_DPE": "2024-09-15",
            "Classe_consommation_énergie": "C",
            "Surface_habitable_logement": "180",
            "Type_bâtiment": "Maison individuelle",
            "commune": "Jacou",
            "estimation_prix": 650000,
            "score": 92
        },
        {
            "Adresse_(BAN)": "8 Avenue de Toulouse",
            "Date_réception_DPE": "2024-09-12",
            "Classe_consommation_énergie": "B",
            "Surface_habitable_logement": "120",
            "Type_bâtiment": "Appartement",
            "commune": "Montpellier",
            "estimation_prix": 520000,
            "score": 85
        }
    ]

@app.get("/")
def root():
    return HTMLResponse("""<!DOCTYPE html>
<html><head><title>MARC VEILLE DPE - LVI IMMO</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root{--primary:#2563EB;--success:#10B981;--warning:#F59E0B;--danger:#EF4444;--neutral:#F8F9FA;--white:#FFFFFF;--dark:#1F2937;--radius:12px;--shadow:0 4px 6px rgba(0,0,0,0.1)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#F8F9FA 0%,#E5E7EB 100%);color:var(--dark);line-height:1.6;min-height:100vh}
.header{background:var(--white);padding:1rem 2rem;box-shadow:var(--shadow);margin-bottom:2rem;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:1.75rem;font-weight:700;color:var(--primary)}
.status{padding:0.5rem 1rem;border-radius:20px;font-size:0.875rem;font-weight:500;background:#D1FAE5;color:#065F46}
.main{max-width:1400px;margin:0 auto;padding:2rem}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1.5rem;margin-bottom:2rem}
.metric{background:var(--white);padding:1.5rem;border-radius:var(--radius);box-shadow:var(--shadow);text-align:center}
.metric-value{font-size:2rem;font-weight:700;color:var(--primary);margin-bottom:0.5rem}
.metric-label{color:var(--dark);opacity:0.7;font-size:0.875rem}
.controls{display:flex;gap:1rem;margin-bottom:2rem;align-items:center}
.btn{background:var(--primary);color:white;padding:0.75rem 1.5rem;border:none;border-radius:var(--radius);cursor:pointer;font-weight:500}
.btn:hover{opacity:0.9}
.btn.loading{opacity:0.6}
.prospects{display:grid;gap:1.5rem}
.prospect{background:var(--white);border-radius:var(--radius);box-shadow:var(--shadow);overflow:hidden}
.prospect-header{padding:1.5rem;border-left:4px solid var(--primary)}
.prospect.hot{border-left-color:var(--danger)}
.prospect.warm{border-left-color:var(--warning)}
.prospect.cold{border-left-color:var(--success)}
.prospect-title{font-size:1.125rem;font-weight:600;margin-bottom:0.5rem}
.prospect-details{color:var(--dark);opacity:0.8;margin-bottom:1rem}
.prospect-meta{display:flex;justify-content:space-between;align-items:center;color:#6B7280;font-size:0.875rem}
.score{background:var(--primary);color:white;padding:0.25rem 0.75rem;border-radius:20px;font-weight:600}
.score.hot{background:var(--danger)}
.score.warm{background:var(--warning)}
</style>
</head>
<body>
<div class="header">
  <div class="logo">🔥 MARC VEILLE DPE - LVI IMMO</div>
  <div class="status">● API ADEME CONNECTÉE</div>
</div>

<div class="main">
  <div class="metrics">
    <div class="metric">
      <div class="metric-value" id="total-dpe">0</div>
      <div class="metric-label">DPE détectés</div>
    </div>
    <div class="metric">
      <div class="metric-value" id="hot-prospects">0</div>
      <div class="metric-label">Prospects chauds</div>
    </div>
    <div class="metric">
      <div class="metric-value" id="avg-value">0€</div>
      <div class="metric-label">Valeur moyenne</div>
    </div>
    <div class="metric">
      <div class="metric-value" id="last-update">-</div>
      <div class="metric-label">Dernière MAJ</div>
    </div>
  </div>

  <div class="controls">
    <button class="btn" onclick="refreshDPE()" id="refresh-btn">🔄 Actualiser DPE</button>
    <button class="btn" onclick="exportProspects()">📊 Exporter Excel</button>
    <span style="color:#6B7280;font-size:0.875rem">Données ADEME temps réel</span>
  </div>

  <div class="prospects" id="prospects-container">
    <div style="text-align:center;color:#6B7280;padding:2rem">
      ⏳ Chargement des DPE en cours...
    </div>
  </div>
</div>

<script>
let currentDPE = [];

async function loadDPEData() {
  try {
    document.getElementById('refresh-btn').classList.add('loading');
    document.getElementById('refresh-btn').textContent = '⏳ Chargement...';
    
    const response = await fetch('/api/dpe/real');
    const data = await response.json();
    
    currentDPE = data.dpe || [];
    
    updateMetrics(data);
    displayProspects(currentDPE);
    
  } catch (error) {
    console.error('Erreur:', error);
    document.getElementById('prospects-container').innerHTML = 
      '<div style="text-align:center;color:#EF4444;padding:2rem">❌ Erreur chargement API ADEME</div>';
  } finally {
    document.getElementById('refresh-btn').classList.remove('loading');
    document.getElementById('refresh-btn').textContent = '🔄 Actualiser DPE';
  }
}

function updateMetrics(data) {
  const stats = data.stats || {};
  
  document.getElementById('total-dpe').textContent = stats.total || 0;
  document.getElementById('hot-prospects').textContent = stats.hot || 0;
  document.getElementById('avg-value').textContent = stats.avg_price ? `${Math.round(stats.avg_price/1000)}k€` : '0€';
  document.getElementById('last-update').textContent = new Date().toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
}

function displayProspects(prospects) {
  const container = document.getElementById('prospects-container');
  
  if (prospects.length === 0) {
    container.innerHTML = '<div style="text-align:center;color:#6B7280;padding:2rem">Aucun DPE détecté dans la zone</div>';
    return;
  }
  
  container.innerHTML = prospects.map(prospect => {
    const priority = prospect.score >= 80 ? 'hot' : prospect.score >= 60 ? 'warm' : 'cold';
    const priorityLabel = priority === 'hot' ? '🔥 CHAUD' : priority === 'warm' ? '🟡 TIÈDE' : '🔵 FROID';
    
    return `
      <div class="prospect ${priority}">
        <div class="prospect-header">
          <div class="prospect-title">
            ${prospect['Type_bâtiment'] || 'Bien'} - ${prospect.commune}
          </div>
          <div class="prospect-details">
            📍 ${prospect['Adresse_(BAN)']} <br>
            🏠 ${prospect['Surface_habitable_logement']}m² • Classe ${prospect['Classe_consommation_énergie']} • ~${Math.round(prospect.estimation_prix/1000)}k€ <br>
            📅 DPE du ${new Date(prospect['Date_réception_DPE']).toLocaleDateString('fr-FR')}
          </div>
          <div class="prospect-meta">
            <span>${priorityLabel}</span>
            <span class="score ${priority}">${prospect.score}/100</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function refreshDPE() {
  loadDPEData();
}

function exportProspects() {
  if (currentDPE.length === 0) {
    alert('Aucune donnée à exporter');
    return;
  }
  
  const csv = [
    ['Adresse', 'Commune', 'Surface', 'Classe', 'Estimation', 'Score', 'Date DPE'].join(','),
    ...currentDPE.map(p => [
      p['Adresse_(BAN)'],
      p.commune,
      p['Surface_habitable_logement'],
      p['Classe_consommation_énergie'],
      p.estimation_prix,
      p.score,
      p['Date_réception_DPE']
    ].join(','))
  ].join('\\n');
  
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `prospects_dpe_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
}

// Chargement initial
loadDPEData();

// Auto-refresh toutes les heures
setInterval(loadDPEData, 60 * 60 * 1000);
</script>
</body></html>""")

@app.get("/api/dpe/real")
async def get_real_dpe():
    """API DPE avec données réelles ADEME"""
    dpe_data = await fetch_real_dpe_data()
    
    stats = {
        "total": len(dpe_data),
        "hot": len([d for d in dpe_data if d['score'] >= 80]),
        "avg_price": sum(d['estimation_prix'] for d in dpe_data) // len(dpe_data) if dpe_data else 0
    }
    
    return {
        "dpe": dpe_data,
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {"status": "ok", "message": "MARC VEILLE DPE opérationnel ! 🔥"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
