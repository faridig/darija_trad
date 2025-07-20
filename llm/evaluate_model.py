import sys
import numpy as np
from datasets import load_dataset
from evaluate import load
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)
# MODIFICATION : Importer depuis le nouveau fichier partagé
from llm.utils import preprocess_dynamic

def evaluate(model_path):
    """
    Évalue un modèle de traduction sur le jeu de test et retourne le score BLEU.
    """
    print(f"Évaluation du modèle depuis : {model_path}")

    # Charger le tokenizer et le modèle depuis le chemin spécifié
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    # Charger le jeu de données de test standardisé
    print("📂 Chargement du jeu de test sanctuarisé...")
    eval_dataset = load_dataset("json", data_files="test_dataset.json", split="train")

    # Prétraitement des données
    cleaned_eval_dataset = eval_dataset.filter(
        lambda x: len([text for text in x.get('translation', {}).values() if text]) == 2
    )
    
    # MODIFICATION : Utilisation de lambda pour passer les arguments nécessaires
    tokenized_eval_dataset = cleaned_eval_dataset.map(
        lambda example: preprocess_dynamic(example, tokenizer=tokenizer, model=model),
        remove_columns=cleaned_eval_dataset.column_names
    )

    # Charger la métrique
    bleu_metric = load("sacrebleu")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        
        # Remplacer -100 (token d'ignorance) par le pad_token_id pour le décodage
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        # Mettre les labels au format attendu par sacrebleu ([['ref1'], ['ref2'], ...])
        decoded_labels = [[label] for label in decoded_labels]
        
        result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
        return {"bleu": result["score"]}

    # Créer un Trainer uniquement pour l'évaluation
    trainer = Seq2SeqTrainer(
        model=model,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
        args=Seq2SeqTrainingArguments(
            output_dir="./temp_eval", # Répertoire temporaire, non utilisé pour la sauvegarde
            predict_with_generate=True,
        )
    )
    
    # Lancer l'évaluation
    metrics = trainer.evaluate(tokenized_eval_dataset)
    bleu_score = metrics.get("eval_bleu")
    
    # Sortie standardisée pour être parsée par le workflow CI/CD
    print(f"SCORE_BLEU={bleu_score}")
    
    return bleu_score

# Point d'entrée pour l'exécution directe du script
if __name__ == "__main__":
    if len(sys.argv) > 1:
        model_directory = sys.argv[1]
        evaluate(model_directory)
    else:
        print("Erreur : Veuillez fournir le chemin du modèle à évaluer en argument.")
        sys.exit(1)