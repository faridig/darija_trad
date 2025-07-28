# Fichier: evaluate_base_model.py

import sys
import torch
import numpy as np
from datasets import load_dataset
from evaluate import load
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)
# Assurez-vous que cette version de preprocess_dynamic est celle qui gère les batches
from llm.utils import preprocess_dynamic

BASE_MODEL_NAME = "facebook/nllb-200-distilled-600M"

def evaluate_base_model():
    """
    Évalue le modèle de base NLLB sur le jeu de test avec des optimisations de vitesse.
    """
    print(f"Évaluation du modèle de BASE depuis le Hub : {BASE_MODEL_NAME}")
    
    # --- 1. CONFIGURATION DU MATÉRIEL (OPTIMISÉ) ---
    use_cuda = torch.cuda.is_available()
    # Détecte si le GPU supporte bf16 pour une meilleure performance sur les RTX 30xx/40xx
    use_bf16 = use_cuda and torch.cuda.is_bf16_supported()
    device = "cuda" if use_cuda else "cpu"
    print(f"Utilisation du périphérique : {device.upper()} | Support BF16 : {use_bf16}")

    # --- 2. CHARGEMENT DU MODÈLE ET DES DONNÉES (OPTIMISÉ) ---
    print("🚀 Chargement du modèle et du tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    # On charge le modèle directement sur le GPU et en précision mixte si possible
    model = AutoModelForSeq2SeqLM.from_pretrained(
        BASE_MODEL_NAME,
        torch_dtype=torch.bfloat16 if use_bf16 else torch.float16 if use_cuda else torch.float32
    ).to(device)
    print("✅ Modèle et tokenizer chargés.")

    print("📂 Chargement du jeu de test...")
    # Chemin mis à jour pour être plus cohérent
    test_file_path = "test_dataset.jsonl"
    if not os.path.exists(test_file_path):
        print(f"❌ ERREUR: Fichier de test '{test_file_path}' introuvable.")
        sys.exit(1)
        
    eval_dataset = load_dataset("json", data_files=test_file_path, split="train")

    # --- 3. PRÉ-TRAITEMENT (OPTIMISÉ) ---
    # Nettoyage pour garder uniquement les paires valides
    cleaned_eval_dataset = eval_dataset.filter(
        lambda x: len([text for text in x.get('translation', {}).values() if text]) == 2,
        num_proc=os.cpu_count() # Utilise plusieurs cœurs pour accélérer le filtrage
    )
    
    # Pré-traitement en mode BATCHED pour une vitesse maximale
    print("🧹 Prétraitement des données en mode batch...")
    tokenized_eval_dataset = cleaned_eval_dataset.map(
        lambda examples: preprocess_dynamic(examples, tokenizer=tokenizer),
        batched=True,
        remove_columns=cleaned_eval_dataset.column_names,
        num_proc=os.cpu_count() # Utilise plusieurs cœurs pour accélérer la tokenisation
    )

    # --- 4. CONFIGURATION DE L'ÉVALUATION (OPTIMISÉ) ---
    bleu_metric = load("sacrebleu")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        
        preds = np.where(preds != -100, preds, tokenizer.pad_token_id)
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        decoded_labels = [[label] for label in decoded_labels]
        
        result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
        return {"bleu": result["score"]}

    print("⚙️ Configuration du Seq2SeqTrainer pour l'évaluation...")
    trainer = Seq2SeqTrainer(
        model=model,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        args=Seq2SeqTrainingArguments(
            output_dir="./temp_base_eval",         # Répertoire temporaire
            predict_with_generate=True,           # Essentiel pour la métrique BLEU
            per_device_eval_batch_size=32,        # AUGMENTÉ : Taille de batch plus grande
            bf16=use_bf16,                        # AMÉLIORÉ : Utilise bf16 si disponible
            fp16=False if use_bf16 else use_cuda, # N'utilise fp16 que si bf16 n'est pas dispo
            dataloader_num_workers=os.cpu_count() // 2, # Utilise plusieurs cœurs pour charger les données
            remove_unused_columns=False,          # Correct, car on le gère manuellement
        )
    )
    
    # --- 5. EXÉCUTION DE L'ÉVALUATION ---
    print("🚀 Lancement de l'évaluation du modèle de base...")
    metrics = trainer.evaluate(tokenized_eval_dataset)
    bleu_score = metrics.get("eval_bleu")
    
    print("\n" + "="*50)
    print(f"✅ Évaluation terminée.")
    print(f"📊 SCORE BLEU DU MODÈLE DE BASE ({BASE_MODEL_NAME})")
    print(f"   SCORE_BLEU={bleu_score:.4f}")
    print("="*50 + "\n")
    
    return bleu_score

if __name__ == "__main__":
    evaluate_base_model()