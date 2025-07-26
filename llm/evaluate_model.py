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
from llm.utils import preprocess_dynamic

def evaluate(model_path):
    """
    Évalue un modèle de traduction sur le jeu de test et retourne le score BLEU.
    """
    print(f"Évaluation du modèle depuis : {model_path}")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Utilisation du périphérique : {device.upper()}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    print("📂 Chargement du jeu de test sanctuarisé...")
    eval_dataset = load_dataset("json", data_files="test_dataset.json", split="train")

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
            output_dir="./temp_eval",
            predict_with_generate=True,
            per_device_eval_batch_size=16,
            fp16=torch.cuda.is_available(),
        )
    )
    
    metrics = trainer.evaluate(tokenized_eval_dataset)
    bleu_score = metrics.get("eval_bleu")
    
    print(f"SCORE_BLEU={bleu_score:.4f}")
    
    return bleu_score

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_directory = sys.argv[1]
        evaluate(model_directory)
    else:
        print("Erreur : Veuillez fournir le chemin du modèle à évaluer en argument.")
        sys.exit(1)