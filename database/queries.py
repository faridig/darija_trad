import time
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import text, Index
from sqlalchemy.exc import SQLAlchemyError

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranslationQueries:
    """
    Classe de requêtes SQL pour la gestion des traductions.
    
    📌 Table `translations` :
        - id : INTEGER PRIMARY KEY
        - source_lang : VARCHAR(2)
        - source_text : TEXT
        - target_lang : VARCHAR(2)
        - target_text : TEXT
    """

    INDEXES = [
        Index('idx_translations_id', 'id'),
        Index('idx_translations_langs', 'source_lang', 'target_lang')
    ]

    @staticmethod
    def _log_metrics(func_name: str, start_time: float, success: bool = True, 
                     error: Optional[Exception] = None) -> Dict[str, Any]:
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
        Récupère toutes les traductions, éventuellement filtrées par langue source/cible.
        """
        start = time.perf_counter()
        try:
            query = text("""
                SELECT * FROM translations
                WHERE (:source_lang IS NULL OR source_lang = :source_lang)
                AND (:target_lang IS NULL OR target_lang = :target_lang)
                ORDER BY id DESC
            """)
            result = db.execute(query, {
                "source_lang": source_lang,
                "target_lang": target_lang
            }).mappings().fetchall()
            TranslationQueries._log_metrics("get_all", start)
            return [dict(row) for row in result]
        except SQLAlchemyError as e:
            TranslationQueries._log_metrics("get_all", start, False, e)
            raise

    @staticmethod
    def get_by_id(db, id: int) -> Optional[Dict]:
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
        start = time.perf_counter()
        try:
            required_fields = ['source_lang', 'source_text', 'target_lang', 'target_text']
            if not all(field in data for field in required_fields):
                raise ValueError("Données manquantes pour la création.")

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
            db.commit()
            TranslationQueries._log_metrics("create", start)
            return dict(result)
        except SQLAlchemyError as e:
            db.rollback()
            TranslationQueries._log_metrics("create", start, False, e)
            raise

    @staticmethod
    def update(db, id: int, data: Dict) -> Optional[Dict]:
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
