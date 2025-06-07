import pytest
import sys
import time
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

from api.data_api.main import app, get_db
from api.data_api.models import User
from api.data_api.db import Base
from passlib.context import CryptContext

# Load environment variables
load_dotenv()

# Setup DB with Supabase
SQLALCHEMY_DATABASE_URL = os.getenv("SUPABASE_URL")
print(f"🔗 Database URL configured: {SQLALCHEMY_DATABASE_URL is not None}", flush=True)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Overriding DB BEFORE creating admin user
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
print("🔧 Database dependency overridden", flush=True)

# Create tables if they don't exist (using ORM)
Base.metadata.create_all(bind=engine)
print("🏗️ Tables created", flush=True)

# 🔐 Ajouter un utilisateur admin en utilisant l'ORM
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
test_password = os.getenv("ADMIN_PASSWORD", "password")  # Récupérer depuis .env avec fallback
hashed = pwd_context.hash(test_password)
print("🔐 Password context configured", flush=True)
print(f"🔐 Using admin password from environment: {'✅' if os.getenv('ADMIN_PASSWORD') else '⚠️ fallback'}", flush=True)

# Flag to track if admin user existed before tests
admin_existed_before = False

# Create admin user ONLY if it doesn't exist or password is wrong
try:
    with TestingSessionLocal() as db:
        existing_user = db.query(User).filter(User.username == "admin").first()
        
        if existing_user:
            admin_existed_before = True
            # Check if password is correct
            is_valid = pwd_context.verify(test_password, existing_user.hashed_password)
            if is_valid:
                print(f"✅ Utilisateur admin existe avec le bon mot de passe: {existing_user.username}", flush=True)
            else:
                print(f"🔧 Mise à jour du mot de passe de l'utilisateur admin existant", flush=True)
                existing_user.hashed_password = hashed
                db.commit()
                print(f"✅ Mot de passe de l'utilisateur admin mis à jour", flush=True)
        else:
            admin_existed_before = False
            # Create new admin user
            print("🔧 Création de l'utilisateur admin...", flush=True)
            admin_user = User(
                username="admin",
                hashed_password=hashed,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print(f"✅ Utilisateur admin créé: {admin_user.username}", flush=True)
        
except Exception as e:
    print(f"❌ ERREUR lors de la gestion de l'utilisateur admin: {e}", flush=True)

# Final verification
try:
    with TestingSessionLocal() as db:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print(f"✅ Vérification finale: utilisateur admin trouvé - username: {admin_user.username}, is_admin: {admin_user.is_admin}", flush=True)
            # Test password verification
            is_valid = pwd_context.verify(test_password, admin_user.hashed_password)
            print(f"✅ Vérification finale du mot de passe: {is_valid}", flush=True)
        else:
            print("❌ ERREUR: utilisateur admin non trouvé après création!", flush=True)
except Exception as e:
    print(f"❌ ERREUR lors de la vérification finale de l'utilisateur admin: {e}", flush=True)

client = TestClient(app)

# Function to clean ONLY test data (more targeted)
def cleanup_test_translations():
    """Nettoie UNIQUEMENT les traductions de test créées pendant les tests"""
    try:
        with TestingSessionLocal() as db:
            # Delete only test translations with specific prefixes
            result = db.execute(text("""
                DELETE FROM translations 
                WHERE source_text LIKE 'Test %' 
                   OR target_text LIKE 'Test %'
            """))
            db.commit()
            deleted_count = result.rowcount
            if deleted_count > 0:
                print(f"🧹 Nettoyage: {deleted_count} traductions de test supprimées", flush=True)
            return deleted_count
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}", flush=True)
        return 0

def cleanup_test_admin_if_created():
    """Supprime l'utilisateur admin SEULEMENT s'il a été créé par les tests"""
    global admin_existed_before
    if not admin_existed_before:
        try:
            with TestingSessionLocal() as db:
                admin_user = db.query(User).filter(User.username == "admin").first()
                if admin_user:
                    db.delete(admin_user)
                    db.commit()
                    print("🗑️ Utilisateur admin créé par les tests supprimé", flush=True)
        except Exception as e:
            print(f"⚠️ Erreur lors de la suppression de l'admin de test: {e}", flush=True)
    else:
        print("✅ Utilisateur admin préexistant conservé", flush=True)

# Pytest hooks for session-level cleanup
def pytest_sessionfinish(session, exitstatus):
    """Nettoie la base de données après tous les tests"""
    print("\n" + "="*50, flush=True)
    print("🧹 NETTOYAGE FINAL DE LA BASE DE DONNÉES", flush=True)
    print("="*50, flush=True)
    
    # Clean test translations
    deleted_count = cleanup_test_translations()
    
    # Clean admin user if created by tests
    cleanup_test_admin_if_created()
    
    print(f"✅ Nettoyage terminé - {deleted_count} traductions de test supprimées", flush=True)
    print("✅ Base de données restaurée à son état initial", flush=True)
    print("="*50 + "\n", flush=True)

@pytest.fixture(scope="function")
def auth_headers():
    """Effectue un login et retourne les headers avec JWT"""
    print("🔐 Tentative de connexion...", flush=True)
    
    # Clean only test data before each test
    cleanup_test_translations()
    
    # NO need to recreate admin user - just verify it exists
    try:
        with TestingSessionLocal() as db:
            admin_user = db.query(User).filter(User.username == "admin").first()
            if not admin_user:
                print("🔧 Création d'urgence de l'utilisateur admin...", flush=True)
                admin_user = User(
                    username="admin",
                    hashed_password=pwd_context.hash(test_password),
                    is_admin=True
                )
                db.add(admin_user)
                db.commit()
                print("✅ Utilisateur admin créé en urgence", flush=True)
    except Exception as e:
        print(f"❌ ERREUR dans fixture lors de la vérification: {e}", flush=True)
    
    # Simple login format (works best)
    login_data = {
        "username": "admin",
        "password": test_password
    }
    
    response = client.post("/login", data=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        print(f"❌ Échec de l'authentification: {response.status_code} - {response.text}", flush=True)
        raise Exception(f"Authentication failed: {response.status_code}")

@pytest.fixture(scope="function")
def payload():
    # Use unique data for each test run to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    timestamp = str(int(time.time()))
    return {
        "source_lang": "fr",
        "source_text": f"Test Bonjour {unique_id}_{timestamp}",
        "target_lang": "dr",
        "target_text": f"Test السلام عليكم {unique_id}_{timestamp}"
    }

def test_create_translation(auth_headers, payload):
    res = client.post("/translations", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["source_text"] == payload["source_text"]
    assert "id" in data
    assert data["id"] > 0

def test_get_translation_by_id(auth_headers, payload):
    # Create a translation first
    create_res = client.post("/translations", json=payload, headers=auth_headers)
    assert create_res.status_code == 200
    created_id = create_res.json()["id"]
    
    # Then get it by ID
    res = client.get(f"/translations/{created_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == created_id

def test_get_all_translations(auth_headers, payload):
    # Create a translation first
    create_res = client.post("/translations", json=payload, headers=auth_headers)
    assert create_res.status_code == 200
    
    # Then get all translations
    res = client.get("/translations", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_update_translation(auth_headers, payload):
    # Create a translation first
    create_res = client.post("/translations", json=payload, headers=auth_headers)
    assert create_res.status_code == 200
    created_id = create_res.json()["id"]
    
    unique_id = str(uuid.uuid4())[:8]
    update_data = {
        "source_lang": "fr",
        "source_text": f"Test Merci {unique_id}",
        "target_lang": "dr",
        "target_text": f"Test شكرا {unique_id}"
    }
    res = client.put(f"/translations/{created_id}", json=update_data, headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["source_text"] == update_data["source_text"]

def test_delete_translation(auth_headers, payload):
    # Create a translation first
    create_res = client.post("/translations", json=payload, headers=auth_headers)
    assert create_res.status_code == 200
    created_id = create_res.json()["id"]
    
    # Then delete it
    res = client.delete(f"/translations/{created_id}", headers=auth_headers)
    assert res.status_code == 200
    
    # Verify it's deleted
    get_res = client.get(f"/translations/{created_id}", headers=auth_headers)
    assert get_res.status_code == 404
