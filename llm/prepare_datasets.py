import json
from datasets import load_dataset
import os

def prepare_and_save_datasets():
    """
    Charge le dataset complet, le divise en trois ensembles (train, validation, test)
    et sauvegarde chaque ensemble dans un fichier JSONL distinct.
    """
    print("Préparation et division des datasets...")

    # Assurer que les anciens fichiers sont supprimés pour éviter les confusions
    for f in ["train_dataset.json", "validation_dataset.json", "test_dataset.json"]:
        if os.path.exists(f):
            os.remove(f)

    # Charger le dataset complet
    full_dataset = load_dataset("json", data_files="all_translations_dataset.json", split="train")

    # Première division : 90% pour train+validation, 10% pour le test final
    train_val_dataset = full_dataset.train_test_split(test_size=0.1, seed=42)
    
    # Seconde division : Le train_val_dataset est divisé en train et validation
    # test_size=0.111 équivaut à prendre 10% du dataset original (10/90)
    train_test_dataset = train_val_dataset['train'].train_test_split(test_size=0.111, seed=42)

    # Assigner les ensembles finaux
    train_set = train_test_dataset['train']
    validation_set = train_test_dataset['test']
    test_set = train_val_dataset['test']

    print(f"Taille du jeu d'entraînement : {len(train_set)}")
    print(f"Taille du jeu de validation : {len(validation_set)}")
    print(f"Taille du jeu de test : {len(test_set)}")

    # Sauvegarder chaque ensemble dans un fichier JSONL (json lines)
    train_set.to_json("train_dataset.json", orient="records", lines=True)
    validation_set.to_json("validation_dataset.json", orient="records", lines=True)
    test_set.to_json("test_dataset.json", orient="records", lines=True)
    
    print("✅ Datasets sauvegardés avec succès.")

if __name__ == "__main__":
    prepare_and_save_datasets()