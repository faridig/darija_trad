# api/ia_api/limiter.py
"""
Ce module centralise l'instance du rate limiter (SlowAPI) pour
assurer qu'une seule et même instance est utilisée à travers toute l'application.

Cela permet de la configurer en un seul endroit et de la désactiver
facilement pendant les tests.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Création de l'instance unique et partagée du limiter.
limiter = Limiter(key_func=get_remote_address)