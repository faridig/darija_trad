# Fichier: database/queries.py
# Rôle: Couche d'Accès aux Données (Data Access Layer) pour l'entité 'Translation'.
# Ce module isole toute la logique SQL de la couche API (FastAPI).
# Il respecte le principe de séparation des préoccupations.

import time
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import text, Index
from sqlalchemy.exc import SQLAlchemyError

# Configuration d'un logger spécifique à ce module pour un suivi clair.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranslationQueries:
    """
    Classe regroupant des méthodes statiques pour toutes les opérations CRUD
    sur la table 'translations'. Chaque méthode gère sa propre transaction
    et son logging.
    
    📌 Table `translations` :
        - id : INTEGER PRIMARY KEY
        - source_lang : VARCHAR(10)
        - source_text : TEXT
        - target_lang : VARCHAR(10)
        - target_text : TEXT
    """

    # Définition des index pour optimiser les requêtes, une bonne pratique de performance.
    INDEXES = [
        Index('idx_translations_id', 'id'),
        Index('idx_translations_langs', 'source_lang', 'target_lang')
    ]

    @staticmethod
    def _log_metrics(func_name: str, start_time: float, success: bool = True, 
                     error: Optional[Exception] = None) -> Dict[str, Any]:
        """
        Méthode utilitaire interne pour centraliser le logging de performance
        et le statut de chaque requête à la base de données.
        
        Args:
            func_name (str): Le nom de la méthode exécutée (ex: "get_all").
            start_time (float): Le timestamp de début de l'opération.
            success (bool): Indique si l'opération a réussi.
            error (Optional[Exception]): L'exception capturée en cas d'échec.
            
        Returns:
            Dict[str, Any]: Un dictionnaire de métriques pour un usage futur éventuel.
        """
        # Calcule la durée en millisecondes pour une meilleure lisibilité.
        duration = (time.perf_counter() - start_time) * 1000
        metrics = {
            "query_name": func_name,
            "execution_time_ms": duration,
            "timestamp": time.time(),
            "success": success,
            "error": str(error) if error else None
        }

        if success:
            logger.info(f"⏱️ {func_name} exécutée en {duration:.2f} ms")
        else:
            logger.error(f"❌ {func_name} échouée en {duration:.2f} ms: {error}")

        return metrics

    @staticmethod
    def get_all(db, source_lang: Optional[str] = None, target_lang: Optional[str] = None) -> List[Dict]:
        """
        Récupère toutes les traductions. Peut être filtrée par langue source et/ou cible.
        
        Args:
            db: La session de base de données SQLAlchemy.
            source_lang (Optional[str]): Le code de la langue source à filtrer.
            target_lang (Optional[str]): Le code de la langue cible à filtrer.
            
        Returns:
            List[Dict]: Une liste de dictionnaires, chaque dictionnaire représentant une traduction.
        """
        start = time.perf_counter()
        try:
            # La requête utilise des paramètres nommés (:source_lang) pour prévenir les injections SQL.
            # La clause WHERE est conçue pour ignorer les filtres s'ils ne sont pas fournis (valeur NULL).
            query = text("""
                SELECT * FROM translations
                WHERE (:source_lang IS NULL OR source_lang = :source_lang)
                AND (:target_lang IS NULL OR target_lang = :target_lang)
                ORDER BY id DESC
            """)
            result = db.execute(query, {
                "source_lang": source_lang,
                "target_lang": target_lang
            }).mappings().fetchall() # .mappings() transforme les résultats en objets de type dictionnaire.
            
            TranslationQueries._log_metrics("get_all", start)
            return [dict(row) for row in result]
        except SQLAlchemyError as e:
            TranslationQueries._log_metrics("get_all", start, False, e)
            raise # Propage l'exception pour que la couche supérieure (API) puisse la gérer.

    @staticmethod
    def get_by_id(db, id: int) -> Optional[Dict]:
        """
        Récupère une seule traduction par son identifiant unique.
        
        Returns:
            Optional[Dict]: Le dictionnaire de la traduction si trouvée, sinon None.
        """
        start = time.perf_counter()
        try:
            query = text("SELECT * FROM translations WHERE id = :id")
            result = db.execute(query, {"id": id}).mappings().fetchone()
            TranslationQueries._log_metrics("get_by_id", start)
            return dict(result) if result else None
        except SQLAlchemyError as e:
            TranslationQueries._log_metrics("get_by_id", start, False, e)
            raise

    @staticmethod
    def create(db, data: Dict) -> Dict:
        """
        Crée une nouvelle traduction dans la base de données.
        
        Returns:
            Dict: Le dictionnaire de la traduction nouvellement créée, incluant son ID.
        """
        start = time.perf_counter()
        try:
            # Validation simple pour s'assurer que les champs obligatoires sont présents.
            required_fields = ['source_lang', 'source_text', 'target_lang', 'target_text']
            if not all(field in data for field in required_fields):
                raise ValueError("Données manquantes pour la création.")

            # La clause RETURNING * est une optimisation de PostgreSQL qui renvoie la ligne insérée
            # sans avoir besoin de faire une deuxième requête SELECT.
            query = text("""
                INSERT INTO translations (
                    source_lang, source_text, 
                    target_lang, target_text
                ) VALUES (
                    :source_lang, :source_text,
                    :target_lang, :target_text
                )
                RETURNING *
            """)
            result = db.execute(query, data).mappings().fetchone()
            db.commit() # Valide la transaction, rendant l'insertion permanente.
            TranslationQueries._log_metrics("create", start)
            return dict(result)
        except SQLAlchemyError as e:
            db.rollback() # En cas d'erreur, annule la transaction pour garantir l'intégrité des données.
            TranslationQueries._log_metrics("create", start, False, e)
            raise

    @staticmethod
    def update(db, id: int, data: Dict) -> Optional[Dict]:
        """
        Met à jour une traduction existante.
        
        Returns:
            Optional[Dict]: Le dictionnaire de la traduction mise à jour, ou None si l'ID n'existe pas.
        """
        start = time.perf_counter()
        try:
            query = text("""
                UPDATE translations
                SET source_lang = :source_lang,
                    source_text = :source_text,
                    target_lang = :target_lang,
                    target_text = :target_text
                WHERE id = :id
                RETURNING *
            """)
            result = db.execute(query, {**data, "id": id}).mappings().fetchone()
            db.commit()
            TranslationQueries._log_metrics("update", start)
            return dict(result) if result else None
        except SQLAlchemyError as e:
            db.rollback()
            TranslationQueries._log_metrics("update", start, False, e)
            raise

    @staticmethod
    def delete(db, id: int) -> Optional[Dict]:
        """
        Supprime une traduction par son identifiant.
        
        Returns:
            Optional[Dict]: Le dictionnaire de la traduction qui vient d'être supprimée, ou None si l'ID n'existait pas.
        """
        start = time.perf_counter()
        try:
            query = text("DELETE FROM translations WHERE id = :id RETURNING *")
            result = db.execute(query, {"id": id}).mappings().fetchone()
            db.commit()
            TranslationQueries._log_metrics("delete", start)
            return dict(result) if result else None
        except SQLAlchemyError as e:
            db.rollback()
            TranslationQueries._log_metrics("delete", start, False, e)
            raise