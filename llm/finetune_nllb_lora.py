# llm/finetune_nllb_lora.py

"""
Script de fine-tuning pour spécialiser le modèle NLLB-600M sur la traduction
impliquant le Darija Marocain.

Ce script orchestre le cycle de vie complet de l'entraînement :
1.  Configuration et connexion à un serveur de suivi d'expériences MLflow.
2.  Chargement du modèle de base pré-entraîné de Hugging Face.
3.  Application de la technique d'adaptation efficace LoRA (Low-Rank Adaptation).
4.  Chargement et prétraitement des jeux de données d'entraînement et de validation.
5.  Configuration et exécution de l'entraînement avec le `Seq2SeqTrainer` de Transformers.
6.  Suivi des métriques (score BLEU) et des hyperparamètres sur MLflow.
7.  Sauvegarde de l'adaptateur LoRA entraîné et envoi comme artefact sur MLflow.

Ce script est une pièce centrale du pipeline MLOps, assurant un entraînement
structuré, monitoré et reproductible.
"""

import os
import glob
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
    DataCollatorForSeq2Seq,
)
from llm.utils import preprocess_dynamic

# Désactive le parallélisme des tokenizers de Hugging Face pour éviter des problèmes
# de blocage (deadlocks) avec les dataloaders multi-processus de PyTorch.
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def main():
    """
    Orchestre le pipeline complet de fine-tuning du modèle NLLB-Darija.

    Cette fonction principale exécute séquentiellement toutes les étapes nécessaires
    pour l'entraînement : configuration, chargement des données, prétraitement,
    configuration de l'entraînement, exécution et logging des résultats.
    """
    # ==============================================================================
    # 1. CONFIGURATION DU SUIVI D'EXPÉRIENCES AVEC MLFLOW
    # ==============================================================================
    # Récupère l'URI du serveur MLflow depuis les variables d'environnement,
    # avec une valeur par défaut pour le développement local.
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Définit le nom de l'expérience sous laquelle tous les entraînements seront regroupés.
    EXPERIMENT_NAME = "nllb_darija_finetuning"
    mlflow.set_experiment(EXPERIMENT_NAME)

    # ==============================================================================
    # 2. CHARGEMENT DU MODÈLE DE BASE ET DES DONNÉES
    # ==============================================================================
    print("🚀 Chargement du modèle de base et du tokenizer...")
    model_name = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    print("✅ Modèle et tokenizer chargés.")

    # Application de la configuration LoRA pour un fine-tuning efficace.
    print("🔧 Application de LoRA...")
    peft_config = LoraConfig(
        r=8,  # Rang de la décomposition, une petite valeur pour l'efficacité.
        lora_alpha=32,  # Facteur d'échelle pour les poids LoRA.
        lora_dropout=0.1,  # Taux de dropout pour la régularisation.
        bias="none",  # On n'entraîne pas les biais.
        # On cible spécifiquement les matrices de projection de l'attention (query/value).
        target_modules=["q_proj", "v_proj"],
        task_type=TaskType.SEQ_2_SEQ_LM,  # Spécifie le type de modèle pour PEFT.
    )
    # Enveloppe le modèle de base avec l'adaptateur LoRA.
    model = get_peft_model(model, peft_config)
    # Affiche le nombre de paramètres entraînables pour vérifier l'efficacité de LoRA.
    model.print_trainable_parameters()
    print("✅ LoRA appliqué avec succès.")

    # Chargement des jeux de données pré-divisés par le script `prepare_datasets.py`.
    print("📂 Chargement des datasets pré-divisés...")
    train_dataset = load_dataset("json", data_files="llm/train_dataset.jsonl", split="train")
    eval_dataset = load_dataset("json", data_files="llm/validation_dataset.jsonl", split="train")
    print(f"✅ Jeu de données chargé : {len(train_dataset)} pour l'entraînement, {len(eval_dataset)} pour la validation.")

    # ==============================================================================
    # 3. PRÉTRAITEMENT DES DONNÉES
    # ==============================================================================
    print("🧹 Prétraitement dynamique des datasets...")
    
    # Étape de nettoyage pour s'assurer que chaque exemple a bien une paire de traductions.
    cleaned_train_dataset = train_dataset.filter(lambda x: len([text for text in x['translation'].values() if text]) == 2)
    cleaned_eval_dataset = eval_dataset.filter(lambda x: len([text for text in x['translation'].values() if text]) == 2)
    print(f"Taille du jeu d'entraînement après nettoyage : {len(cleaned_train_dataset)}")

    # Application de la fonction de tokenisation sur les datasets.
    tokenized_train_dataset = cleaned_train_dataset.map(
        lambda examples: preprocess_dynamic(examples, tokenizer=tokenizer),
        batched=True,  # Traitement par lots pour une performance accrue.
        remove_columns=cleaned_train_dataset.column_names  # Supprime les colonnes de texte brut inutiles.
    )
    tokenized_eval_dataset = cleaned_eval_dataset.map(
        lambda examples: preprocess_dynamic(examples, tokenizer=tokenizer),
        batched=True,
        remove_columns=cleaned_eval_dataset.column_names
    )
    
    print(f"✅ Prétraitement terminé. Taille du jeu d'entraînement tokenisé : {len(tokenized_train_dataset)}")
    # Sanity check pour s'arrêter tôt si le dataset est vide après traitement.
    if len(tokenized_train_dataset) == 0:
        raise ValueError("Le jeu de données d'entraînement est vide après le prétraitement.")

    # ==============================================================================
    # 4. DÉFINITION DES MÉTRIQUES ET CONFIGURATION DE L'ENTRAÎNEMENT
    # ==============================================================================
    # Chargement de la métrique SacreBLEU, standard pour l'évaluation de la traduction.
    bleu_metric = load("sacrebleu")

    def compute_metrics(eval_preds):
        """
        Fonction appelée par le Trainer pour calculer les métriques d'évaluation.
        
        Args:
            eval_preds (tuple): Tuple contenant les prédictions du modèle et les vraies étiquettes.

        Returns:
            dict: Dictionnaire contenant le score BLEU calculé.
        """
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        
        # Remplace les tokens -100 (ignorés dans la loss) par le pad_token_id pour le décodage.
        preds = np.where(preds != -100, preds, tokenizer.pad_token_id)
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        
        # Décode les prédictions et les étiquettes en texte.
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        
        # Formate les étiquettes pour la métrique SacreBLEU (liste de listes).
        decoded_labels = [[label] for label in decoded_labels]
        
        result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
        
        print(f"[📊 Évaluation] Score BLEU : {result['score']:.2f}")
        return {"bleu": result["score"]}

    print("⚙️ Configuration des arguments d'entraînement...")
    training_args = Seq2SeqTrainingArguments(
        output_dir="./nllb-darija-finetuned-lora-checkpoints", # Dossier pour les sauvegardes.

        # === Paramètres d'Apprentissage ===
        learning_rate=1e-4,
        num_train_epochs=5,
        per_device_train_batch_size=4,  # Taille de batch par GPU.
        gradient_accumulation_steps=8,  # Simule une plus grande taille de batch effective.
        
        # === Planificateur de Taux d'Apprentissage ===
        warmup_ratio=0.1,  # Augmentation progressive du learning rate.
        lr_scheduler_type="cosine",  # Diminution cosinusoïdale du learning rate.
        
        # === Évaluation & Sauvegarde ===
        eval_strategy="steps",  # Évaluer à intervalles réguliers.
        save_strategy="steps",  # Sauvegarder à intervalles réguliers.
        eval_steps=300,  # Évaluer tous les 300 pas.
        save_steps=300,  # Sauvegarder tous les 300 pas.
        logging_steps=100, # Afficher les logs tous les 100 pas.
        
        load_best_model_at_end=True,  # Recharge le meilleur checkpoint à la fin.
        metric_for_best_model="bleu", # La métrique pour déterminer le "meilleur" modèle.
        greater_is_better=True, # Un score BLEU plus élevé est meilleur.
        save_total_limit=2, # Garde seulement les 2 meilleurs checkpoints.
        
        # === Optimisations Techniques ===
        bf16=True,  # Utilise le format bfloat16 sur les GPU compatibles pour la vitesse.
        predict_with_generate=True, # Nécessaire pour le calcul du score BLEU.
        dataloader_num_workers=4, # Utilise plusieurs processus pour charger les données.
        
        # === Logging ===
        logging_dir="./logs",
        report_to=["mlflow"], # CRUCIAL: Indique au Trainer d'envoyer les logs à MLflow.
    )
    print("✅ Arguments d'entraînement configurés.")

    # ==============================================================================
    # 5. EXÉCUTION DE L'ENTRAÎNEMENT
    # ==============================================================================
    print("🚀 Démarrage de la session MLflow...")
    # Le contexte `with` garantit que la session MLflow est correctement fermée.
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        print(f"✅ Session MLflow démarrée. Run ID: {run_id}")
        
        # Log des hyperparamètres importants pour une comparaison facile dans l'UI MLflow.
        mlflow.log_params({
            "model_name": model_name,
            "lora_r": peft_config.r,
            "lora_alpha": peft_config.lora_alpha,
            "learning_rate": training_args.learning_rate,
            "num_train_epochs": training_args.num_train_epochs,
            "train_batch_size": training_args.per_device_train_batch_size,
            "gradient_accumulation_steps": training_args.gradient_accumulation_steps,
        })
        
        # Collator pour gérer le padding dynamique des lots.
        data_collator = DataCollatorForSeq2Seq(
            tokenizer=tokenizer,
            model=model,
            padding=True,
            label_pad_token_id=-100  # Ignore les tokens de padding dans le calcul de la loss.
        )

        # Initialisation du Trainer avec tous les composants.
        trainer = Seq2SeqTrainer(
            model=model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=tokenized_train_dataset,
            eval_dataset=tokenized_eval_dataset,
            tokenizer=tokenizer,
            compute_metrics=compute_metrics,
            # Arrête l'entraînement si le score de validation ne s'améliore pas
            # pendant 3 évaluations consécutives, pour éviter le sur-apprentissage.
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        )

        print(f"🧠 Lancement de l'entraînement pour le Run ID: {run_id}...")
        
        # Logique robuste pour reprendre un entraînement interrompu.
        checkpoint_dir = training_args.output_dir
        latest_checkpoint = None
        if os.path.isdir(checkpoint_dir):
            checkpoints = glob.glob(os.path.join(checkpoint_dir, "checkpoint-*"))
            if checkpoints:
                # Trouve le checkpoint le plus récent en se basant sur le numéro de pas.
                latest_checkpoint = max(checkpoints, key=lambda x: int(x.split('-')[-1]))
                print(f"✅ Checkpoint trouvé : {latest_checkpoint}. Tentative de reprise...")

        try:
            # Tente de reprendre l'entraînement depuis le dernier checkpoint.
            trainer.train(resume_from_checkpoint=latest_checkpoint)
        except Exception as e:
            # Si la reprise échoue, démarre un nouvel entraînement depuis le début.
            print(f"‼️ AVERTISSEMENT : La reprise depuis '{latest_checkpoint}' a échoué ({e}).")
            print("ℹ️ Démarrage d'un nouvel entraînement.")
            trainer.train()
        
        print("🏁 Entraînement terminé.")

        # Sauvegarde de l'adaptateur LoRA final (les poids entraînés).
        final_model_dir = "nllb-darija-lora-model"
        trainer.save_model(final_model_dir)
        tokenizer.save_pretrained(final_model_dir) # Sauvegarde aussi le tokenizer avec le modèle.
        print(f"💾 Modèle et tokenizer sauvegardés dans '{final_model_dir}'.")

        # Envoie le dossier du modèle comme un artefact sur MLflow.
        print("📦 Envoi de l'artefact du modèle vers MLflow...")
        mlflow.log_artifacts(final_model_dir, artifact_path="model")
        
        # Log du meilleur score BLEU obtenu pendant l'entraînement.
        best_metrics = trainer.state.best_metric
        if best_metrics:
            mlflow.log_metric("best_bleu_score", best_metrics)
            print(f"🏆 Meilleur score BLEU obtenu : {best_metrics:.2f}")

# Point d'entrée pour l'exécution directe du script.
if __name__ == "__main__":
    main()
    print("✅ Processus de fine-tuning et de logging terminé.")