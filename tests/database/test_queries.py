import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database.queries import TranslationQueries

@pytest.fixture
def sqlite_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_lang TEXT,
                source_text TEXT,
                target_lang TEXT,
                target_text TEXT
            )
        """))
    return engine

@pytest.fixture
def db_session(sqlite_engine):
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sqlite_engine
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_create_and_get_by_id(db_session):
    data = {
        "source_lang": "fr",
        "source_text": "Bonjour",
        "target_lang": "dr",
        "target_text": "سلام"
    }
    created = TranslationQueries.create(db_session, data)
    assert created["id"] > 0

    fetched = TranslationQueries.get_by_id(db_session, created["id"])
    assert fetched["source_text"] == "Bonjour"

def test_get_all_and_filter(db_session):
    TranslationQueries.create(db_session, {
        "source_lang": "fr", "source_text": "A",
        "target_lang": "dr", "target_text": "a"
    })
    TranslationQueries.create(db_session, {
        "source_lang": "en", "source_text": "B",
        "target_lang": "dr", "target_text": "b"
    })
    all_no_filter = TranslationQueries.get_all(db_session)
    assert isinstance(all_no_filter, list)
    assert len(all_no_filter) >= 2

    filtered = TranslationQueries.get_all(db_session, source_lang="fr")
    assert all(item["source_lang"] == "fr" for item in filtered)

def test_update(db_session):
    created = TranslationQueries.create(db_session, {
        "source_lang": "fr", "source_text": "Old",
        "target_lang": "dr", "target_text": "old"
    })
    updated = TranslationQueries.update(db_session, created["id"], {
        "source_lang": "fr", "source_text": "New",
        "target_lang": "dr", "target_text": "new"
    })
    assert updated["source_text"] == "New"
    fetched = TranslationQueries.get_by_id(db_session, created["id"])
    assert fetched["target_text"] == "new"

def test_delete(db_session):
    created = TranslationQueries.create(db_session, {
        "source_lang": "fr", "source_text": "X",
        "target_lang": "dr", "target_text": "x"
    })
    deleted = TranslationQueries.delete(db_session, created["id"])
    assert deleted["id"] == created["id"]
    assert TranslationQueries.get_by_id(db_session, created["id"]) is None

def test_nonexistent_returns_none(db_session):
    assert TranslationQueries.get_by_id(db_session, 9999) is None
    assert TranslationQueries.update(db_session, 9999, {
        "source_lang": "fr", "source_text": "a",
        "target_lang": "dr", "target_text": "a"
    }) is None
    assert TranslationQueries.delete(db_session, 9999) is None
