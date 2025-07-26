# llm/finetune_nllb_lora.py

import os
import mlflow
import numpy as np
from datasets import load_dataset
from evaluate import load
from peft import get_peft_model, LoraConfig, TaskType
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    # MODIFICATION : Importation du callback pour l'arrêt précoce
    EarlyStoppingCallback,
)
# MODIFICATION : Importer la fonction de prétraitement depuis le fichier partagé
from llm.utils import preprocess_dynamic

def main():
    """
    Fonction principale encapsulant la logique d'entraînement.
    """
    # ==============================================================================
    # 1. CONFIGURATION MLFLOW
    # ==============================================================================
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    EXPERIMENT_NAME = "nllb_darija_finetuning"
    mlflow.set_experiment(EXPERIMENT_NAME)

    # ==============================================================================
    # 2. CHARGEMENT DU MODÈLE ET DES DONNÉES
    # ==============================================================================
    print("🚀 Chargement du modèle et du tokenizer...")
    model_name = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    print("✅ Modèle et tokenizer chargés.")

    # Appliquer LoRA
    print("🔧 Application de LoRA...")
    peft_config = LoraConfig(
        r=8,
        lora_alpha=32,
        lora_dropout=0.1,
        bias="none",
        target_modules=["q_proj", "v_proj"],
        task_type=TaskType.SEQ_2_SEQ_LM,
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()
    print("✅ LoRA appliqué avec succès.")

    # Chargement du dataset
    print("📂 Chargement des datasets pré-divisés...")
    train_dataset = load_dataset("json", data_files="train_dataset.json", split="train")
    eval_dataset = load_dataset("json", data_files="validation_dataset.json", split="train")
    print(f"✅ Jeu de données chargé : {len(train_dataset)} pour l'entraînement, {len(eval_dataset)} pour la validation.")

    # ==============================================================================
    # 3. PRÉTRAITEMENT
    # ==============================================================================
    print("🧹 Prétraitement dynamique des datasets...")
    
    cleaned_train_dataset = train_dataset.filter(lambda x: len([text for text in x['translation'].values() if text]) == 2)
    cleaned_eval_dataset = eval_dataset.filter(lambda x: len([text for text in x['translation'].values() if text]) == 2)
    print(f"Taille du jeu d'entraînement après nettoyage : {len(cleaned_train_dataset)}")

    # MODIFICATION : Utilisation de lambda pour passer tokenizer et model
    tokenized_train_dataset = cleaned_train_dataset.map(
        lambda example: preprocess_dynamic(example, tokenizer=tokenizer, model=model),
        remove_columns=cleaned_train_dataset.column_names
    )
    tokenized_eval_dataset = cleaned_eval_dataset.map(
        lambda example: preprocess_dynamic(example, tokenizer=tokenizer, model=model),
        remove_columns=cleaned_eval_dataset.column_names
    )
    
    print(f"✅ Prétraitement terminé. Taille du jeu d'entraînement tokenisé : {len(tokenized_train_dataset)}")
    if len(tokenized_train_dataset) == 0:
        raise ValueError("Le jeu de données d'entraînement est vide après le prétraitement.")

# ==============================================================================
    # 4. MÉTRIQUES ET CONFIGURATION DE L'ENTRAÎNEMENT
    # ==============================================================================
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
        
        print(f"[📊 Évaluation] Score BLEU : {result['score']:.2f}")
        return {"bleu": result["score"]}

    print("⚙️ Configuration des arguments d'entraînement...")
    training_args = Seq2SeqTrainingArguments(
        output_dir="./nllb-darija-finetuned-lora-checkpoints",
        per_device_train_batch_size=8,
        learning_rate=5e-4,
        # MODIFICATION : Augmentation du nombre d'époques à 5
        num_train_epochs=0.2,
        bf16=True,
        logging_dir="./logs",
        save_strategy="steps",
        save_steps=1000,
        save_total_limit=3,
        eval_strategy="steps",
        logging_strategy="steps",
        logging_steps=100,
        eval_steps=1000,
        predict_with_generate=True,
        load_best_model_at_end=True,
        metric_for_best_model="bleu",
        greater_is_better=True,
        report_to=["mlflow"],
        remove_unused_columns=False,
    )
    print("✅ Arguments d'entraînement configurés.")

    # ==============================================================================
    # 5. EXÉCUTION DE L'ENTRAÎNEMENT
    # ==============================================================================
    print("🚀 Démarrage de la session MLflow...")
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"✅ Session MLflow démarrée. Run ID: {run_id}")
        
        mlflow.log_params({
            "model_name": model_name,
            "lora_r": peft_config.r,
            "lora_alpha": peft_config.lora_alpha,
            "learning_rate": training_args.learning_rate,
            "num_train_epochs": training_args.num_train_epochs,
            "train_batch_size": training_args.per_device_train_batch_size,
        })

        trainer = Seq2SeqTrainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_train_dataset,
            eval_dataset=tokenized_eval_dataset,
            tokenizer=tokenizer,
            compute_metrics=compute_metrics,
            # MODIFICATION : Ajout du callback pour l'arrêt précoce.
            # L'entraînement s'arrêtera si le score BLEU ne s'améliore pas
            # pendant 3 évaluations consécutives.
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        )

        print(f"🧠 Lancement de l'entraînement pour le Run ID: {run_id}...")
        try:
            checkpoint_dir = training_args.output_dir
            if os.path.isdir(checkpoint_dir) and any(d.startswith("checkpoint-") for d in os.listdir(checkpoint_dir)):
                print(f"✅ Checkpoints trouvés dans '{checkpoint_dir}'. Tentative de reprise...")
                trainer.train(resume_from_checkpoint=True)
            else:
                print("ℹ️ Aucun checkpoint trouvé, démarrage d'un nouvel entraînement.")
                trainer.train()
        except Exception as e:
            print(f"‼️ AVERTISSEMENT : La reprise a échoué ({e}). Démarrage d'un nouvel entraînement.")
            trainer.train()
        
        print("🏁 Entraînement terminé.")

        final_model_dir = "nllb-darija-lora-model"
        trainer.save_model(final_model_dir)
        tokenizer.save_pretrained(final_model_dir)
        print(f"💾 Modèle et tokenizer sauvegardés dans '{final_model_dir}'.")

        print("📦 Envoi de l'artefact du modèle vers MLflow...")
        mlflow.log_artifacts(final_model_dir, artifact_path="model")
        
        best_metrics = trainer.state.best_metric
        if best_metrics:
            mlflow.log_metric("best_bleu_score", best_metrics)
            print(f"🏆 Meilleur score BLEU obtenu : {best_metrics:.2f}")

# Point d'entrée pour l'exécution directe du script
if __name__ == "__main__":
    main()
    print("✅ Processus de fine-tuning et de logging terminé.")