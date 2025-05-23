# Documentation Technique - Ensemble E1
## Projet de Traduction Darija

### 1. Présentation du Projet

#### 1.1 Contexte
Le projet vise à développer un service de traduction automatique entre le Darija (dialecte arabe marocain) et le Français/Anglais, en utilisant le dataset MBZUAI-Paris/Darija-SFT-Mixture comme source principale de données.

#### 1.2 Objectifs
- Fonctionnels :
  - Extraction et préparation des données de traduction
  - Stockage structuré des données nettoyées
  - Mise à disposition des données via une API REST
- Techniques :
  - Automatisation du processus d'extraction et de nettoyage
  - Optimisation des performances de traitement
  - Sécurisation des accès aux données

#### 1.3 Acteurs
- Équipe de développement
- Data Scientists
- Utilisateurs finaux (via l'API)

### 2. Architecture Technique

#### 2.1 Structure des Données
```
data/darija_sft_mixture/
├── nettoyage/
├── parquet_download/
└── statistics/
```

#### 2.2 Technologies Utilisées
- Python 3.8+
- Apache Hadoop
- PostgreSQL
- FastAPI

#### 2.3 Dépendances
```
pandas>=1.4.0
numpy>=1.21.0
fastapi>=0.68.0
pyspark>=3.2.0
psycopg2-binary>=2.9.3
python-dotenv>=0.19.0
```

### 3. Configuration de l'Environnement

#### 3.1 Variables d'Environnement
```env
HUGGINGFACE_TOKEN=votre_token
AZURE_CONNECTION_STRING=votre_connection_string
```

#### 3.2 Installation
1. Cloner le repository
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer les variables d'environnement
4. Installer Hadoop JAR dans le répertoire spécifié

### 4. Processus d'Extraction des Données

#### 4.1 Sources de Données
- Dataset MBZUAI-Paris/Darija-SFT-Mixture
- Format : Parquet
- Localisation : `data/darija_sft_mixture/parquet_download/`

#### 4.2 Processus de Nettoyage
1. Validation des données d'entrée
2. Suppression des doublons
3. Normalisation des caractères
4. Filtrage des traductions invalides

#### 4.3 Stockage
- Base de données PostgreSQL
- Structure normalisée selon Merise
- Sauvegarde régulière des données

### 5. API REST

#### 5.1 Points de Terminaison
- GET /api/v1/translations
- POST /api/v1/translations
- GET /api/v1/statistics

#### 5.2 Authentification
- JWT Token
- Gestion des rôles utilisateurs
- Rate limiting

#### 5.3 Documentation API
- Format OpenAPI
- Accessible via /docs
- Exemples d'utilisation inclus

### 6. Sécurité et RGPD

#### 6.1 Mesures de Sécurité
- Chiffrement des données sensibles
- Validation des entrées
- Journalisation des accès

#### 6.2 Conformité RGPD
- Registre des traitements
- Procédures de suppression des données
- Durée de conservation définie

### 7. Maintenance

#### 7.1 Journalisation
- Logs applicatifs
- Logs d'accès
- Logs d'erreurs

#### 7.2 Sauvegarde
- Sauvegarde quotidienne
- Rétention de 30 jours
- Procédure de restauration documentée

### 8. Tests

#### 8.1 Tests Unitaires
- Coverage > 80%
- Tests automatisés
- Validation des données

#### 8.2 Tests d'Intégration
- Validation des flux
- Tests de charge
- Tests de sécurité 