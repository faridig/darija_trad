# Version validée comme étant la plus cohérente avec l'architecture existante
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
from llm.utils import preprocess_dynamic

BASE_MODEL_NAME = "facebook/nllb-200-distilled-600M"

def evaluate_base_model():
    print(f"Évaluation du modèle de BASE depuis le Hub : {BASE_MODEL_NAME}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Utilisation du périphérique : {device.upper()}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL_NAME)

    print("📂 Chargement du jeu de test sanctuarisé...")
    eval_dataset = load_dataset("json", data_files="llm/test_dataset.json", split="train")

    cleaned_eval_dataset = eval_dataset.filter(
        lambda x: len([text for text in x.get('translation', {}).values() if text]) == 2
    )
    
    tokenized_eval_dataset = cleaned_eval_dataset.map(
        lambda example: preprocess_dynamic(example, tokenizer=tokenizer, model=model),
        remove_columns=cleaned_eval_dataset.column_names
    )

    bleu_metric = load("sacrebleu")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        
        # <<< CORRECTION APPLIQUÉE ICI >>>
        # Remplacer les valeurs de padding (-100) dans les prédictions et les labels
        preds = np.where(preds != -100, preds, tokenizer.pad_token_id)
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        decoded_labels = [[label] for label in decoded_labels]
        
        result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
        return {"bleu": result["score"]}

    trainer = Seq2SeqTrainer(
        model=model,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        args=Seq2SeqTrainingArguments(
            output_dir="./temp_base_eval",
            predict_with_generate=True,
            per_device_eval_batch_size=16,
            fp16=torch.cuda.is_available(),
        )
    )
    
    print("🚀 Démarrage de l'évaluation avec le Trainer...")
    metrics = trainer.evaluate(tokenized_eval_dataset)
    bleu_score = metrics.get("eval_bleu")
    
    print("\n=======================================================")
    print(f"SCORE BLEU DU MODÈLE DE BASE ({BASE_MODEL_NAME})")
    print(f"SCORE_BLEU={bleu_score:.4f}")
    print("=======================================================")
    
    return bleu_score

if __name__ == "__main__":
    evaluate_base_model()