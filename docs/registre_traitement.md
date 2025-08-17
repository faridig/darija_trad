# Registre des Traitements de Données Personnelles

Ce document constitue un registre des activités de traitement des données personnelles effectuées dans le cadre du projet Darija App, conformément au Règlement Général sur la Protection des Données (RGPD).

## 1. Identification du Responsable de Traitement

**Entité** : Projet Darija App
**Contact** : Farid IGOUTI faridigouti@gmail.com

---

## 2. Description du Traitement

### Finalités du Traitement
Les données personnelles des utilisateurs sont collectées et traitées pour les finalités suivantes :
1.  **Authentification et Gestion de Compte** : Permettre aux utilisateurs de créer un compte, de se connecter et d'accéder aux fonctionnalités de l'application.
2.  **Sécurité** : Protéger l'application contre les accès non autorisés et les abus.
3.  **Administration** : Permettre aux administrateurs de gérer l'application et les utilisateurs.

### Base Légale du Traitement
Le traitement est basé sur :
-   **L'exécution d'un contrat** (Article 6.1.b du RGPD) : La création d'un compte par l'utilisateur constitue un contrat de service.
-   **L'intérêt légitime** (Article 6.1.f du RGPD) : Pour assurer la sécurité du service.

---

## 3. Inventaire des Données Personnelles Traitées

Les données personnelles sont stockées dans la table `users` de la base de données.

| Table | Champ | Type de Donnée | Description et Utilisation |
|:--- |:--- |:---|:---|
| `users` | `id` | Identifiant Technique | Identifiant unique généré par la base de données. |
| `users` | `username` | Donnée d'Identification | Nom d'utilisateur choisi par l'utilisateur pour se connecter. |
| `users` | `hashed_password`| Donnée d'Authentification | Mot de passe de l'utilisateur, stocké sous forme de hachage irréversible (bcrypt). |
| `users` | `is_admin` | Donnée de Profil | Flag booléen indiquant si l'utilisateur a des droits d'administrateur. |
| `users` | `created_at` | Métadonnée | Date et heure de création du compte utilisateur. |
| `users` | `last_login` | Métadonnée | Date et heure de la dernière connexion réussie de l'utilisateur. |

---

## 4. Durée de Conservation

-   Les données des utilisateurs sont conservées tant que le compte de l'utilisateur est actif.
-   En cas de suppression du compte par l'utilisateur ou après une période d'inactivité prolongée (3 ans), les données personnelles seront anonymisées ou supprimées de nos bases de données actives.

---

## 5. Destinataires des Données

Les données personnelles ne sont pas partagées avec des tiers. L'accès est strictement limité au personnel autorisé (administrateurs) pour des raisons de maintenance et de sécurité.