import sys
import numpy as np
import torch
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

def evaluate(model_path):
    """
    Évalue un modèle de traduction sur le jeu de test avec des optimisations de vitesse.
    """
    print(f"Évaluation du modèle depuis : {model_path}")
    
    # Détection du GPU et de la compatibilité bf16
    use_cuda = torch.cuda.is_available()
    use_bf16 = use_cuda and torch.cuda.is_bf16_supported()
    device = "cuda" if use_cuda else "cpu"
    print(f"Utilisation du périphérique : {device.upper()} | Support BF16 : {use_bf16}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    # On charge le modèle directement sur le GPU pour éviter des transferts de données
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(device)

    print("📂 Chargement du jeu de test...")
    eval_dataset = load_dataset("json", data_files="test_dataset.jsonl", split="train")

    # Nettoyage pour garder uniquement les paires valides
    cleaned_eval_dataset = eval_dataset.filter(
        lambda x: len([text for text in x.get('translation', {}).values() if text]) == 2
    )
    
    # Pré-traitement en mode BATCHED pour une vitesse maximale
    print("🧹 Prétraitement des données en mode batch...")
    tokenized_eval_dataset = cleaned_eval_dataset.map(
        lambda examples: preprocess_dynamic(examples, tokenizer=tokenizer),
        batched=True,
        remove_columns=cleaned_eval_dataset.column_names
    )

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
            output_dir="./temp_eval",           # Répertoire temporaire
            predict_with_generate=True,         # Essentiel pour la métrique BLEU
            per_device_eval_batch_size=32,      # AUGMENTÉ : Taille de batch plus grande
            bf16=use_bf16,                      # AMÉLIORÉ : Utilise bf16 si disponible
            fp16=False if use_bf16 else use_cuda, # N'utilise fp16 que si bf16 n'est pas dispo
            dataloader_num_workers=4,           # Utilise plusieurs coeurs pour charger les données
        )
    )
    
    print("🚀 Lancement de l'évaluation...")
    metrics = trainer.evaluate(tokenized_eval_dataset)
    bleu_score = metrics.get("eval_bleu")
    
    print("\n" + "="*50)
    print(f"✅ Évaluation terminée. SCORE BLEU FINAL : {bleu_score:.4f}")
    print("="*50)
    
    return bleu_score

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_directory = sys.argv[1]
        evaluate(model_directory)
    else:
        print("Erreur : Veuillez fournir le chemin du modèle à évaluer en argument.")
        print("Usage: python evaluate_script.py chemin/vers/mon/modele")
        sys.exit(1)