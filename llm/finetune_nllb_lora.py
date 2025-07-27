# llm/finetune_nllb_lora.py

import os
import glob # Assurez-vous que glob est importé pour la reprise robuste
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
    EarlyStoppingCallback,
)
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
        
        preds = np.where(preds != -100, preds, tokenizer.pad_token_id)
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        decoded_labels = [[label] for label in decoded_labels]
        result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
        
        print(f"[📊 Évaluation] Score BLEU : {result['score']:.2f}")
        return {"bleu": result["score"]}

    # --- DEBUT DU BLOC CORRIGÉ ---
    print("⚙️ Configuration des arguments d'entraînement...")
    training_args = Seq2SeqTrainingArguments(
        output_dir="./nllb-darija-finetuned-lora-checkpoints",

        # === SECTION APPRENTISSAGE : Stabilité et Performance ===
        learning_rate=1e-4,              # Plus sûr pour éviter de "casser" le modèle.
        num_train_epochs=5,              # 5 époques est un excellent point de départ.
        per_device_train_batch_size=16,  # Doublé pour mieux utiliser le GPU (si votre VRAM le permet).
        gradient_accumulation_steps=2,   # Résultat : batch size effectif de 32, favorise la stabilité.
        
        # === SECTION PLANIFICATION : Éviter l'instabilité ===
        warmup_ratio=0.1,                # 10% des pas pour "chauffer" le learning rate. C'est excellent.
        lr_scheduler_type="cosine",      # Décroissance douce du LR, souvent mieux que "linear".
        
        # === SECTION ÉVALUATION & SAUVEGARDE : Efficacité et Robustesse ===
        eval_strategy="steps",
        save_strategy="steps",
        # À ajuster selon la taille du dataset. Viser 2-4 évaluations par époque.
        # Si une époque = 2000 pas, alors 500 est bien. Si une époque = 500 pas, alors 200 est mieux.
        eval_steps=500,
        save_steps=500,                  # Doit être identique à eval_steps pour load_best_model_at_end
        logging_steps=50,                # Logs fréquents pour bien suivre.
        
        load_best_model_at_end=True,     # Indispensable pour ne garder que le meilleur modèle.
        metric_for_best_model="bleu",
        greater_is_better=True,
        save_total_limit=2,              # 2 suffisent : le meilleur, le dernier, et le précédent.
        
        # === SECTION TECHNIQUE : Vitesse et Compatibilité ===
        bf16=True,                       # Crucial pour la vitesse sur votre RTX 4060.
        predict_with_generate=True,      # Nécessaire pour le score BLEU.
        remove_unused_columns=False,     # Correct, car vous gérez les colonnes vous-même.
        
        # === SECTION LOGGING ===
        logging_dir="./logs",
        report_to=["mlflow"],            # Parfait pour le suivi d'expériences.
    )
    print("✅ Arguments d'entraînement configurés.")
    # --- FIN DU BLOC CORRIGÉ ---

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
            "gradient_accumulation_steps": training_args.gradient_accumulation_steps,
        })

        trainer = Seq2SeqTrainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_train_dataset,
            eval_dataset=tokenized_eval_dataset,
            tokenizer=tokenizer,
            compute_metrics=compute_metrics,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        )

        print(f"🧠 Lancement de l'entraînement pour le Run ID: {run_id}...")
        
        # Logique de reprise robuste
        checkpoint_dir = training_args.output_dir
        latest_checkpoint = None
        if os.path.isdir(checkpoint_dir):
            checkpoints = glob.glob(os.path.join(checkpoint_dir, "checkpoint-*"))
            if checkpoints:
                latest_checkpoint = max(checkpoints, key=lambda x: int(x.split('-')[-1]))
                print(f"✅ Checkpoint trouvé : {latest_checkpoint}. Tentative de reprise...")

        try:
            trainer.train(resume_from_checkpoint=latest_checkpoint)
        except Exception as e:
            print(f"‼️ AVERTISSEMENT : La reprise depuis '{latest_checkpoint}' a échoué ({e}).")
            print("ℹ️ Démarrage d'un nouvel entraînement.")
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