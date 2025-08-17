# 🤖 Module `llm` - Fine-Tuning, Évaluation et Gestion de Modèles

Ce module contient l'ensemble du pipeline MLOps pour le fine-tuning, l'évaluation et la mise en production d'un modèle de traduction basé sur **NLLB**. Il utilise **LoRA** pour un entraînement efficace et **MLflow** pour le suivi des expérimentations.

## 🛠️ Workflow MLOps

1. **Export des Données** (`export_dataset.py`)
   - Connexion à la **Data API**, récupération du corpus et conversion en `JSONL`.

2. **Préparation des Données** (`prepare_datasets.py`)
   - Division : 80% train, 10% val, 10% test.
   - Sur-échantillonnage pour équilibre linguistique.
   - Sauvegarde : `train_dataset.jsonl`, `validation_dataset.jsonl`, `test_dataset.jsonl`.

3. **Fine-Tuning avec LoRA** (`finetune_nllb_lora.py`)
   - Modèle : `facebook/nllb-200-distilled-600M`.
   - Adaptation **LoRA** via `transformers.Seq2SeqTrainer`.
   - Callbacks : `EarlyStopping`.
   - Logs : hyperparamètres + métriques dans **MLflow**.
   - Sauvegarde des poids LoRA.

4. **Évaluation** (`evaluate_model.py`, `evaluate_base_model.py`)
   - Score BLEU sur le jeu de test.
   - Comparaison modèle fine-tuné vs modèle de base.

5. **Fusion et Production** (`merge_and_save.py`)
   - Fusion modèle de base + poids LoRA.
   - Sauvegarde du modèle final prêt au déploiement.

## ✨ Choix Techniques et Fonctionnalités

- **Modèle de base** : `facebook/nllb-200-distilled-600M`.
- **LoRA** : Fine-tuning rapide et économe en VRAM.
- **MLflow** : Suivi complet des expériences.
- **Prétraitement bidirectionnel** (`preprocess_dynamic`) pour augmenter la robustesse.
- **Score BLEU** comme métrique clé.

## 🚀 Utilisation du Pipeline

### 1. Préparation des Données
```bash
python -m llm.export_dataset
python -m llm.prepare_datasets
```

### 2. Entraînement
```bash
python -m llm.finetune_nllb_lora
```
- Les poids LoRA sont dans `nllb-darija-lora-model/`.

### 3. Fusion
```bash
python -m llm.merge_and_save   facebook/nllb-200-distilled-600M   ./nllb-darija-lora-model   ./merged_model_final
```

### 4. Évaluation
```bash
python -m llm.evaluate_model ./merged_model_final
python -m llm.evaluate_base_model  # optionnel
```

## ⚙️ Dépendances

- `transformers`
- `datasets`
- `evaluate`
- `peft`
- `sacrebleu`
- `mlflow`
- `torch` (CUDA si possible)
