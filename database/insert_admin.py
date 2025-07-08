# database/insert_admin.py

import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Assure qu'on charge les variables
load_dotenv()

# Import du contexte et de la base
from database.core.db import SessionLocal, engine
from database.core.models import Base, User



# Contexte de hachage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def initialize_db():
    """
    Crée les tables si elles n'existent pas encore.
    On ne lève pas d'exception ici, c'est safe.
    """
    Base.metadata.create_all(bind=engine)

def insert_admin():
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "password")
    hashed = pwd_context.hash(password)

    db: Session = SessionLocal()

    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"ℹ️ L'utilisateur '{username}' existe déjà. Aucune action nécessaire.")
            return

        admin = User(username=username, hashed_password=hashed, is_admin=True)
        db.add(admin)
        db.commit()
        print("✅ Utilisateur admin inséré dans la base.")
    except IntegrityError as e:
        db.rollback()
        print("⚠️ Utilisateur déjà existant ou erreur d'intégrité :", e)
    except Exception as e:
        db.rollback()
        print("❌ Erreur lors de l'insertion de l'admin :", e)
    finally:
        db.close()

if __name__ == "__main__":
    insert_admin()
