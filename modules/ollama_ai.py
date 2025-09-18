import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

class OllamaAILVI:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama3.1:8b"
        
    def is_available(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def generate_prospect_score(self, prospect_data: Dict) -> int:
        """Score intelligent prospect avec IA"""
        if not self.is_available():
            return self.fallback_scoring(prospect_data)
            
        prompt = f"""
        Analyse ce prospect immobilier pour LVI IMMO (vente interactive Montpellier).
        
        Données prospect:
        - Nom: {prospect_data.get('name', 'N/A')}
        - Localisation: {prospect_data.get('location', 'N/A')}
        - Prix estimé: {prospect_data.get('price', 'N/A')}€
        - Source: {prospect_data.get('source', 'N/A')}
        - Signaux: {prospect_data.get('signals', [])}
        
        Critères LVI IMMO:
        - Vente interactive = biens >400k€ 
        - Zone Montpellier EST premium
        - CSP+ qui comprennent innovation
        - Signaux urgence/frustration = opportunité
        
        Réponds UNIQUEMENT par un score 0-100.
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                score_text = result.get("response", "50")
                # Extraction du score
                import re
                numbers = re.findall(r'\d+', score_text)
                if numbers:
                    return min(100, max(0, int(numbers[0])))
                    
        except Exception as e:
            print(f"Erreur Ollama scoring: {e}")
            
        return self.fallback_scoring(prospect_data)
    
    def generate_personalized_message(self, prospect: Dict) -> str:
        """Génère message personnalisé avec IA"""
        if not self.is_available():
            return self.fallback_message(prospect)
            
        prompt = f"""
        Rédige un message de contact pour ce prospect immobilier.
        
        Prospect:
        - Nom: {prospect.get('name', 'Prospect')}
        - Profil: {prospect.get('title', 'Propriétaire')}
        - Entreprise: {prospect.get('company', 'N/A')}
        - Situation: {prospect.get('signals', [])}
        
        Contexte LVI IMMO:
        - Emmanuel Clément, co-fondateur
        - Méthode vente interactive révolutionnaire
        - +15-25% vs estimations traditionnelles
        - Transparence totale, vente sous 4 semaines
        - Basé Montpellier, expertise locale
        
        Style:
        - Professionnel mais chaleureux
        - Personnalisé selon son profil
        - Intriguant sur la méthode
        - Call-to-action café informel
        - Maximum 100 mots
        
        Message:
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", self.fallback_message(prospect))
                
        except Exception as e:
            print(f"Erreur Ollama message: {e}")
            
        return self.fallback_message(prospect)
    
    def predict_selling_probability(self, prospect: Dict) -> Dict:
        """Prédiction IA probabilité de vente"""
        if not self.is_available():
            return {"probability": 65, "timeline": "6-12 mois", "confidence": "medium"}
            
        prompt = f"""
        Analyse prédictive: probabilité que ce prospect vende dans les 12 prochains mois.
        
        Données:
        - Localisation: {prospect.get('location', '')}
        - Type bien: {prospect.get('property_type', '')}
        - Signaux détectés: {prospect.get('signals', [])}
        - Source découverte: {prospect.get('source', '')}
        - Score actuel: {prospect.get('score', 0)}
        
        Facteurs prédictifs:
        - DPE récent = 80% vente sous 6 mois
        - Mandat expiré = 70% nouvelle tentative sous 3 mois  
        - Déménagement professionnel = 90% vente urgente
        - Signaux réseaux sociaux = 60% réflexion active
        - CSP+ frustré = 85% changement d'agent
        
        Réponds en JSON:
        {{"probability": 0-100, "timeline": "X mois", "confidence": "low/medium/high"}}
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=12
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Parse JSON response
                try:
                    import json
                    prediction = json.loads(response_text)
                    return prediction
                except:
                    # Fallback parsing
                    prob = 65
                    if "80" in response_text or "90" in response_text:
                        prob = 85
                    elif "70" in response_text:
                        prob = 70
                    return {"probability": prob, "timeline": "6-9 mois", "confidence": "medium"}
                    
        except Exception as e:
            print(f"Erreur prédiction: {e}")
            
        return {"probability": 65, "timeline": "6-12 mois", "confidence": "medium"}
    
    def fallback_scoring(self, prospect: Dict) -> int:
        """Scoring de secours sans IA"""
        score = 50
        
        # Prix
        try:
            price = int(str(prospect.get('price', '0')).replace('€', '').replace(' ', ''))
            if price > 600000: score += 25
            elif price > 500000: score += 20  
            elif price > 400000: score += 15
        except: pass
        
        # Localisation
        location = str(prospect.get('location', '')).lower()
        if any(zone in location for zone in ['jacou', 'castelnau', 'antigone']):
            score += 15
            
        # Signaux
        signals = str(prospect.get('signals', [])).lower()
        if 'urgent' in signals: score += 20
        if 'expiré' in signals: score += 25
        if 'déménagement' in signals: score += 15
        
        return min(100, score)
    
    def fallback_message(self, prospect: Dict) -> str:
        """Message de secours sans IA"""
        name = prospect.get('name', 'Monsieur/Madame').split()[0]
        
        return f"""Bonjour {name},

Emmanuel Clément, co-fondateur LVI IMMO à Montpellier.

Notre méthode de vente interactive obtient 15-25% de plus que les estimations traditionnelles grâce à une transparence totale.

Seriez-vous intéressé(e) par un échange autour d'un café ?

Cordialement,
Emmanuel - 04 67 XX XX XX"""

# Instance globale
ollama_ai = OllamaAILVI()
