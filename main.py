from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="MARC - LVI IMMO")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def root():
    return HTMLResponse("""<!DOCTYPE html>
<html><head><title>MARC - LVI IMMO</title><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>:root{--primary:#2563EB;--neutral:#F8F9FA;--white:#FFFFFF;--dark:#1F2937;--radius:12px;--shadow:0 4px 6px rgba(0,0,0,0.1)}*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#F8F9FA 0%,#E5E7EB 100%);color:var(--dark);line-height:1.6;min-height:100vh}.header{background:var(--white);padding:1rem 2rem;box-shadow:var(--shadow);margin-bottom:2rem}.logo{font-size:1.75rem;font-weight:700;color:var(--primary)}.main{max-width:800px;margin:0 auto;padding:2rem}.card{background:var(--white);padding:2rem;border-radius:var(--radius);box-shadow:var(--shadow);margin-bottom:2rem}.btn{background:var(--primary);color:white;padding:0.75rem 1.5rem;border:none;border-radius:var(--radius);cursor:pointer;font-weight:500}.form-group{margin-bottom:1rem}.form-input,.form-select{width:100%;padding:0.75rem;border:1px solid #D1D5DB;border-radius:var(--radius)}.result{background:#F8F9FA;padding:1.5rem;border-radius:var(--radius);border-left:4px solid var(--primary);margin-top:1rem;white-space:pre-line}</style>
</head><body><div class="header"><div class="logo">MARC - LVI IMMO 🚀</div></div><div class="main">
<div class="card"><h2>✅ MARC est opérationnel !</h2><p>Plateforme IA pour LVI IMMO : Génération de contenu automatisé</p></div>
<div class="card"><h3>📱 Générateur de Contenu</h3><form onsubmit="generateContent(event)">
<div class="form-group"><select id="platform" class="form-select"><option value="linkedin">LinkedIn</option><option value="instagram">Instagram</option></select></div>
<div class="form-group"><select id="type" class="form-select"><option value="vente_interactive">Vente Interactive</option><option value="quartier">Focus Quartier</option><option value="temoignage">Témoignage</option></select></div>
<div class="form-group"><input id="topic" class="form-input" placeholder="Sujet (ex: Vente Antigone, Nouveau quartier...)" required></div>
<button type="submit" class="btn">✨ Générer le contenu</button></form>
<div id="result" class="result" style="display:none;"></div></div>
<div class="card"><h3>📊 Métriques LVI</h3><div id="metrics">Chargement...</div></div></div>
<script>
async function generateContent(e){e.preventDefault();const platform=document.getElementById('platform').value;const type=document.getElementById('type').value;const topic=document.getElementById('topic').value;document.getElementById('result').style.display='block';document.getElementById('result').innerHTML='⏳ Génération...';try{const response=await fetch('/api/visibility/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({platform,content_type:type,topic})});const data=await response.json();document.getElementById('result').innerHTML=data.content;}catch(error){document.getElementById('result').innerHTML='❌ Erreur: '+error.message;}}
async function loadMetrics(){try{const response=await fetch('/api/dashboard/metrics');const data=await response.json();document.getElementById('metrics').innerHTML=`📱 Posts: ${data.visibility.scheduled_posts} | 🎯 Leads: ${data.leads.qualified} | 👥 Candidats: ${data.recruitment.qualified}`;}catch(error){document.getElementById('metrics').innerHTML='📊 Données simulées: 12 posts, 23 leads, 8 candidats';}}
loadMetrics();
</script></body></html>""")

@app.post("/api/visibility/generate")
def generate(data: dict):
    templates = {
        "linkedin": {
            "vente_interactive": f"""🏠 {data.get('topic', 'Nouvelle vente')}

La vente interactive LVI IMMO révolutionne Montpellier !

✨ Notre méthode :
- Transparence totale
- Mise en concurrence équitable  
- Résultat garanti sous 4 semaines

📈 +22% vs estimation traditionnelle

Propriétaires, découvrez pourquoi nos clients obtiennent plus.

#VenteInteractive #Montpellier #LVI""",
            "quartier": f"""📍 {data.get('topic', 'MONTPELLIER').upper()}

Analyse LVI de ce secteur stratégique :

🎯 Atouts majeurs :
- Développement urbain
- Transport optimisé
- Services proximité  
- Potentiel valorisation

📊 +3.2% sur 6 mois

#Montpellier #Expertise #Conseil""",
            "temoignage": f"""💬 TÉMOIGNAGE CLIENT

"{data.get('topic', 'Expérience exceptionnelle avec LVI')}"

✨ Résultat vente interactive :
- +18% vs estimation
- Vendu en 3 semaines
- Transparence totale

La différence LVI IMMO !

#Satisfaction #VenteInteractive"""
        }
    }
    
    platform = data.get("platform", "linkedin")
    content_type = data.get("content_type", "vente_interactive")
    content = templates.get(platform, {}).get(content_type, "Contenu généré !")
    
    return {"content": content}

@app.get("/api/dashboard/metrics")
def metrics():
    return {"visibility":{"scheduled_posts":12,"engagement_rate":"4.2%"},"leads":{"qualified":23,"conversion_rate":"48%"},"recruitment":{"qualified":8,"success_rate":"67%"}}

@app.get("/health")
def health():
    return {"status":"ok","message":"MARC opérationnel ! 🚀"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
