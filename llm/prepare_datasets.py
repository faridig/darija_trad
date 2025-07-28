import json
from datasets import load_dataset, concatenate_datasets
import os

def prepare_and_save_datasets():
    """
    Charge le dataset complet, l'équilibre, le divise en trois ensembles (train, validation, test)
    et sauvegarde chaque ensemble dans un fichier JSONL distinct.
    """
    print("Préparation et division des datasets...")
    
    source_file = "all_translations_dataset.jsonl"
    if not os.path.exists(source_file):
        print(f"❌ ERREUR: Le fichier source '{source_file}' est introuvable. Veuillez vous assurer qu'il est dans le bon répertoire.")
        return

    # Assurer que les anciens fichiers sont supprimés pour éviter les confusions
    output_files = ["train_dataset.jsonl", "validation_dataset.jsonl", "test_dataset.jsonl"]
    for f in output_files:
        if os.path.exists(f):
            print(f"Suppression de l'ancien fichier : {f}")
            os.remove(f)

    # Charger le dataset complet.
    # La bibliothèque 'datasets' peut unifier le schéma en ajoutant des clés manquantes avec des valeurs null.
    print(f"Chargement du dataset depuis '{source_file}'...")
    full_dataset = load_dataset("json", data_files=source_file, split="train")
    print(f"Chargement terminé. {len(full_dataset)} exemples trouvés.")

    # Première division : 90% pour train+validation, 10% pour le test final
    train_val_dataset = full_dataset.train_test_split(test_size=0.1, seed=42)
    
    # Seconde division : Le train_val_dataset est divisé en train et validation (80/10 du total)
    # test_size=0.111 équivaut à prendre 10% du dataset original (10/90)
    train_test_dataset = train_val_dataset['train'].train_test_split(test_size=0.111, seed=42)

    # Assigner les ensembles finaux
    train_set = train_test_dataset['train']
    validation_set = train_test_dataset['test']
    test_set = train_val_dataset['test']

    print("\n--- Tailles des ensembles de données après division ---")
    print(f"Jeu d'entraînement (avant équilibrage) : {len(train_set)} exemples")
    print(f"Jeu de validation : {len(validation_set)} exemples")
    print(f"Jeu de test : {len(test_set)} exemples")
    print("-" * 55)

    # ======================================================================
    #                 ÉQUILIBRAGE DU JEU D'ENTRAÎNEMENT
    # ======================================================================

    print("\nÉquilibrage du jeu d'entraînement par sur-échantillonnage...")

    # 1. Séparer le JEU D'ENTRAÎNEMENT en deux groupes
    #    CORRECTION : On vérifie la présence d'une valeur non-nulle/non-vide,
    #    pas seulement l'existence de la clé.
    print("Filtrage des paires de langues dans le jeu d'entraînement...")
    fr_ary_train = train_set.filter(
        lambda x: x['translation']['fra_Latn']
    )
    en_ary_train = train_set.filter(
        lambda x: x['translation']['eng_Latn']
    )

    print(f"Analyse du jeu d'entraînement : {len(fr_ary_train)} paires fr<=>ary, {len(en_ary_train)} paires en<=>ary.")

    # 2. Vérifier si le groupe Français-Darija est minoritaire et doit être sur-échantillonné
    if len(fr_ary_train) > 0 and len(en_ary_train) > len(fr_ary_train):
        
        # Calculer combien de fois dupliquer les exemples minoritaires
        # On utilise // pour une division entière, et on ajoute 1 pour s'assurer qu'on dépasse légèrement
        # la classe majoritaire plutôt que de rester juste en dessous.
        oversample_factor = len(en_ary_train) // len(fr_ary_train) + 1
        
        print(f"Le groupe fr<=>ary est minoritaire. Facteur de sur-échantillonnage : {oversample_factor}")
        
        # Créer une liste de datasets à concaténer (le groupe original + ses copies)
        oversampled_fr_datasets = [fr_ary_train] * oversample_factor
        balanced_fr_train = concatenate_datasets(oversampled_fr_datasets)
        
        # Le jeu d'entraînement final est la combinaison des deux groupes, bien mélangés
        final_train_set = concatenate_datasets([en_ary_train, balanced_fr_train]).shuffle(seed=42)
        
        print(f"Taille finale du jeu d'entraînement après équilibrage : {len(final_train_set)}")
    else:
        # Si pas de déséquilibre significatif, on se contente de mélanger le jeu d'entraînement existant
        print("Le jeu d'entraînement est déjà équilibré ou le groupe fr<=>ary n'est pas minoritaire.")
        final_train_set = train_set.shuffle(seed=42)

    # ======================================================================
    #                          FIN DE L'ÉQUILIBRAGE
    # ======================================================================

    # Sauvegarder chaque ensemble dans un fichier JSONL (json lines)
    print("\nSauvegarde des datasets finaux au format JSONL...")
    final_train_set.to_json("train_dataset.jsonl", orient="records", lines=True)
    validation_set.to_json("validation_dataset.jsonl", orient="records", lines=True)
    test_set.to_json("test_dataset.jsonl", orient="records", lines=True)
    
    print("\n✅ Préparation et sauvegarde des datasets terminées avec succès.")
    print("   - train_dataset.jsonl (équilibré)")
    print("   - validation_dataset.jsonl (original)")
    print("   - test_dataset.jsonl (original)")


if __name__ == "__main__":
    prepare_and_save_datasets()