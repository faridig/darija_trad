# llm/finetune_nllb_lora.py

# ==============================================================================
# 1. IMPORTS ET CONFIGURATION MLFLOW (inchangé)
# ==============================================================================
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
)

# Configuration de la connexion au serveur MLflow
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5001")
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Nom de l'expérience qui regroupera les entraînements dans l'UI de MLflow
EXPERIMENT_NAME = "nllb_darija_finetuning"
mlflow.set_experiment(EXPERIMENT_NAME)

# ==============================================================================
# 2. CHARGEMENT DU MODÈLE ET DES DONNÉES (inchangé)
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

# Chargement et division du dataset
print("📂 Chargement du dataset JSON...")
dataset = load_dataset("json", data_files="all_translations_dataset.json", split="train")
dataset = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = dataset["train"]
eval_dataset = dataset["test"].select(range(min(1000, len(dataset["test"]))))
print(f"✅ Jeu de données chargé : {len(train_dataset)} pour l'entraînement, {len(eval_dataset)} pour l'évaluation.")

# ==============================================================================
# 3. PRÉTRAITEMENT DYNAMIQUE (sans augmentation)
# ==============================================================================
def preprocess_dynamic(example):
    translation_dict = example.get("translation", {})

    # 1. Filtrer les clés dont la valeur est None ou une chaîne vide
    valid_pairs = {lang: text for lang, text in translation_dict.items() if text}

    # 2. On doit avoir exactement une paire de langues valides
    if len(valid_pairs) != 2:
        return None # On ne retourne rien pour que .filter() supprime la ligne

    # 3. Extraire la paire source/cible
    langs = list(valid_pairs.keys())
    src_lang, tgt_lang = langs[0], langs[1]
    src_text = valid_pairs[src_lang]
    tgt_text = valid_pairs[tgt_lang]

    # Définit les langues pour le tokenizer pour cet exemple spécifique
    tokenizer.src_lang = src_lang
    model_inputs = tokenizer(src_text, max_length=128, padding="max_length", truncation=True)
    
    tokenizer.tgt_lang = tgt_lang
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(tgt_text, max_length=128, padding="max_length", truncation=True)
    
    model_inputs["labels"] = labels["input_ids"]
    # Ligne corrigée
    model.config.forced_bos_token_id = model.config.lang_to_id[tgt_lang]    
    return model_inputs

print("🧹 Prétraitement dynamique des datasets...")

# --- MODIFICATION DE LA LOGIQUE DE NETTOYAGE ---
# Étape 1 : Filtrer les lignes qui n'ont pas exactement 2 traductions valides
cleaned_train_dataset = train_dataset.filter(lambda x: len([text for text in x['translation'].values() if text]) == 2)
cleaned_eval_dataset = eval_dataset.filter(lambda x: len([text for text in x['translation'].values() if text]) == 2)

print(f"Taille du jeu d'entraînement après nettoyage : {len(cleaned_train_dataset)}")

# Étape 2 : Appliquer la tokenisation sur le jeu de données nettoyé
tokenized_train_dataset = cleaned_train_dataset.map(preprocess_dynamic, remove_columns=cleaned_train_dataset.column_names)
tokenized_eval_dataset = cleaned_eval_dataset.map(preprocess_dynamic, remove_columns=cleaned_eval_dataset.column_names)


# --- VÉRIFICATION FINALE ---
print(f"✅ Prétraitement terminé. Taille du jeu d'entraînement tokenisé : {len(tokenized_train_dataset)}")
if len(tokenized_train_dataset) == 0:
    raise ValueError("Le jeu de données d'entraînement est vide après le prétraitement. Problème persistant.")

print("📏 Chargement de la métrique BLEU (sacrebleu)...")
bleu_metric = load("sacrebleu")
print("✅ Métrique BLEU chargée.")

def compute_metrics(eval_preds):
    preds, labels = eval_preds
    if isinstance(preds, tuple):
        preds = preds[0]
    
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    decoded_labels = [[label] for label in decoded_labels]
    result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
    
    print(f"[📊 Évaluation] Score BLEU : {result['score']:.2f}")
    return {"bleu": result["score"]}

# ==============================================================================
# 4. CONFIGURATION DE L'ENTRAÎNEMENT (inchangé)
# ==============================================================================
print("⚙️ Configuration des arguments d'entraînement...")
training_args = Seq2SeqTrainingArguments(
    output_dir="./nllb-darija-finetuned-lora-checkpoints",
    per_device_train_batch_size=8,
    learning_rate=5e-4,
    num_train_epochs=3,
    fp16=True,
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
# 5. EXÉCUTION DE L'ENTRAÎNEMENT (inchangé)
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
    )

    print(f"🧠 Lancement de l'entraînement pour le Run ID: {run_id}...")
    try:
        trainer.train(resume_from_checkpoint=True)
    except (ValueError, FileNotFoundError):
        print("Aucun checkpoint trouvé, démarrage d'un nouvel entraînement.")
        trainer.train()
    
    print("🏁 Entraînement terminé.")

    final_model_dir = "nllb-darija-lora-model"
    trainer.save_model(final_model_dir)
    tokenizer.save_pretrained(final_model_dir)
    print(f"💾 Modèle et tokenizer sauvegardés localement dans '{final_model_dir}'.")

    print(f"📦 Envoi de l'artefact du modèle vers le serveur MLflow...")
    mlflow.log_artifacts(final_model_dir, artifact_path="model")
    
    best_metrics = trainer.state.best_metric
    if best_metrics:
        mlflow.log_metric("best_bleu_score", best_metrics)
        print(f"🏆 Meilleur score BLEU obtenu : {best_metrics:.2f}")

print("✅ Processus de fine-tuning et de logging terminé.")