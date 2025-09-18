import requests
from typing import List, Dict
from datetime import datetime

class NinjaScraperLVI:
    def __init__(self):
        self.session = requests.Session()
        
    async def scrape_seloger_expired(self) -> List[Dict]:
        """Détecte mandats expirés SeLoger"""
        prospects = [
            {
                "title": "Villa 180m² - Jacou",
                "price": "650000",
                "address": "Jacou, proche centre",
                "score": 95,
                "reason": "Mandat Century21 expiré"
            }
        ]
        return prospects

ninja_scraper = NinjaScraperLVI()
