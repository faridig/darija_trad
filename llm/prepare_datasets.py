import json
from datasets import load_dataset, concatenate_datasets
import os

def prepare_and_save_datasets():
    """
    Charge le dataset complet, l'équilibre, le divise en trois ensembles (train, validation, test)
    et sauvegarde chaque ensemble dans un fichier JSONL distinct.
    """
    print("Préparation et division des datasets...")

    # Assurer que les anciens fichiers sont supprimés pour éviter les confusions
    for f in ["train_dataset.json", "validation_dataset.json", "test_dataset.json"]:
        if os.path.exists(f):
            os.remove(f)

    # Charger le dataset complet
    full_dataset = load_dataset("json", data_files="all_translations_dataset.jsonl", split="train")

    # Première division : 90% pour train+validation, 10% pour le test final
    train_val_dataset = full_dataset.train_test_split(test_size=0.1, seed=42)
    
    # Seconde division : Le train_val_dataset est divisé en train et validation
    # test_size=0.111 équivaut à prendre 10% du dataset original (10/90)
    train_test_dataset = train_val_dataset['train'].train_test_split(test_size=0.111, seed=42)

    # Assigner les ensembles finaux
    train_set = train_test_dataset['train']
    validation_set = train_test_dataset['test']
    test_set = train_val_dataset['test']

    print(f"Taille initiale du jeu d'entraînement : {len(train_set)}")
    print(f"Taille du jeu de validation : {len(validation_set)}")
    print(f"Taille du jeu de test : {len(test_set)}")


    # ======================================================================
    # <-- DÉBUT DE LA MODIFICATION : ÉQUILIBRAGE DU JEU D'ENTRAÎNEMENT -->
    # ======================================================================

    print("\nÉquilibrage du jeu d'entraînement par sur-échantillonnage...")

    # 1. Séparer le JEU D'ENTRAÎNEMENT en deux groupes
    fr_ary_train = train_set.filter(lambda x: 'fra_Latn' in x['translation'])
    en_ary_train = train_set.filter(lambda x: 'eng_Latn' in x['translation'])

    print(f"Dans le jeu d'entraînement : {len(fr_ary_train)} paires fr<=>ary, {len(en_ary_train)} paires en<=>ary.")

    # 2. Vérifier s'il faut dupliquer le groupe Français-Darija
    if len(fr_ary_train) > 0 and len(en_ary_train) > len(fr_ary_train):
        # Calculer combien de fois dupliquer les exemples minoritaires
        oversample_factor = round(len(en_ary_train) / len(fr_ary_train))
        print(f"Le groupe fr<=>ary est minoritaire. Facteur de duplication : {oversample_factor}")
        
        # Créer une liste de datasets à concaténer (le groupe original + ses copies)
        oversampled_fr_datasets = [fr_ary_train] * oversample_factor
        balanced_fr_train = concatenate_datasets(oversampled_fr_datasets)
        
        # Le jeu d'entraînement final est la combinaison des deux groupes
        final_train_set = concatenate_datasets([en_ary_train, balanced_fr_train]).shuffle(seed=42)
        
        print(f"Taille finale du jeu d'entraînement après équilibrage : {len(final_train_set)}")
    else:
        # Si pas de déséquilibre, on se contente de mélanger le jeu d'entraînement existant
        print("Le jeu d'entraînement est déjà équilibré ou ne nécessite pas de changement.")
        final_train_set = train_set.shuffle(seed=42)

    # ======================================================================
    # <-- FIN DE LA MODIFICATION -->
    # ======================================================================


    # Sauvegarder chaque ensemble dans un fichier JSONL (json lines)
    # On sauvegarde le jeu d'entraînement équilibré, et les autres jeux "purs"
    final_train_set.to_json("train_dataset.json", orient="records", lines=True)
    validation_set.to_json("validation_dataset.json", orient="records", lines=True)
    test_set.to_json("test_dataset.json", orient="records", lines=True)
    
    print("\n✅ Datasets sauvegardés avec succès (entraînement équilibré).")

if __name__ == "__main__":
    prepare_and_save_datasets()