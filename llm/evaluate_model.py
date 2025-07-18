import sys
import json
import numpy as np
from datasets import load_dataset
from evaluate import load
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Seq2SeqTrainer, Seq2SeqTrainingArguments
from finetune_nllb_lora import preprocess_dynamic # On réutilise votre fonction

def evaluate(model_path):
    print(f"Évaluation du modèle depuis : {model_path}")

    # Charger le tokenizer et le modèle
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    # Charger le jeu de données d'évaluation (TOUJOURS LE MÊME !)
    print("📂 Chargement du jeu de test sanctuarisé...")
    # MODIFICATION : Utiliser uniquement le test_dataset.json
    eval_dataset = load_dataset("json", data_files="test_dataset.json", split="train")

    # Prétraitement
    cleaned_eval_dataset = eval_dataset.filter(lambda x: len([text for text in x['translation'].values() if text]) == 2)
    tokenized_eval_dataset = cleaned_eval_dataset.map(preprocess_dynamic, remove_columns=cleaned_eval_dataset.column_names)

    bleu_metric = load("sacrebleu")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        decoded_labels = [[label] for label in decoded_labels]
        result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
        return {"bleu": result["score"]}

    # Utiliser un Seq2SeqTrainer juste pour la prédiction/évaluation
    trainer = Seq2SeqTrainer(
        model=model,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        args=Seq2SeqTrainingArguments(output_dir="./temp_eval", predict_with_generate=True)
    )
    
    metrics = trainer.evaluate(tokenized_eval_dataset)
    bleu_score = metrics.get("eval_bleu")
    
    print(f"SCORE_BLEU={bleu_score}") # Sortie facile à parser
    return bleu_score

if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_directory = sys.argv[1]
        evaluate(model_directory)
    else:
        print("Erreur : Veuillez fournir le chemin du modèle à évaluer.")