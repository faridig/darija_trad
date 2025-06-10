from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, Seq2SeqTrainer, Seq2SeqTrainingArguments
from peft import get_peft_model, LoraConfig, TaskType
from datasets import load_dataset
from evaluate import load
import numpy as np

# Charger le modèle et tokenizer
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
    task_type=TaskType.SEQ_2_SEQ_LM
)
model = get_peft_model(model, peft_config)
print("✅ LoRA appliqué avec succès.")

# Définir les langues source et cible
SOURCE_LANG = "fra_Latn"  # français
TARGET_LANG = "ary_Arab"  # darija

# 📂 Chargement et division du dataset
print("📂 Chargement du dataset JSON...")
dataset = load_dataset("json", data_files="all_translations_dataset.json", split="train")
dataset = dataset.train_test_split(test_size=0.1, seed=42)
train_dataset = dataset["train"]
eval_dataset = dataset["test"]

# 🧪 Réduction du jeu d’évaluation pour accélérer les évaluations intermédiaires
eval_dataset = eval_dataset.select(range(1000))

print(f"✅ Jeu de données chargé : {len(train_dataset)} pour l'entraînement, {len(eval_dataset)} pour l'évaluation.")


# Fonction de prétraitement
def preprocess(example, idx):
    translation = example["translation"]
    langs = list(translation.keys())
    langs = [lang for lang in langs if translation[lang] is not None]

    if SOURCE_LANG in langs and TARGET_LANG in langs:
        src_lang = SOURCE_LANG
        tgt_lang = TARGET_LANG
    elif TARGET_LANG in langs and SOURCE_LANG not in langs:
        src_lang = [lang for lang in langs if lang != TARGET_LANG][0]
        tgt_lang = TARGET_LANG
    elif SOURCE_LANG in langs and TARGET_LANG not in langs:
        src_lang = SOURCE_LANG
        tgt_lang = [lang for lang in langs if lang != SOURCE_LANG][0]
    else:
        src_lang, tgt_lang = langs[:2]
    
    src_text = translation[src_lang]
    tgt_text = translation[tgt_lang]

    if idx < 5:
        print(f"[Prétraitement - Exemple {idx}] {src_lang} -> {tgt_lang}")
        print(f"  Source: {src_text}")
        print(f"  Cible: {tgt_text}")

    tokenizer.src_lang = src_lang
    model_inputs = tokenizer(src_text, max_length=128, padding="max_length", truncation=True)

    labels = tokenizer(tgt_text, max_length=128, padding="max_length", truncation=True)
    model_inputs["labels"] = labels["input_ids"]

    model.config.forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)

    return model_inputs

# Prétraitement
print("🧹 Début du prétraitement du jeu d'entraînement...")
tokenized_train_dataset = train_dataset.map(preprocess, with_indices=True)
print("✅ Prétraitement du jeu d'entraînement terminé.")

print("🧹 Début du prétraitement du jeu d'évaluation...")
tokenized_eval_dataset = eval_dataset.map(preprocess, with_indices=True)
print("✅ Prétraitement du jeu d'évaluation terminé.")

# Définir la métrique BLEU
print("📏 Chargement de la métrique BLEU (sacrebleu)...")
bleu_metric = load("sacrebleu")
print("✅ Métrique BLEU chargée.")

def compute_metrics(eval_preds):
    print("[🔍 Évaluation] Calcul des métriques BLEU...")
    preds, labels = eval_preds
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)

    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)

    decoded_labels = [[label] for label in decoded_labels]
    result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
    print(f"[📊 Évaluation] Score BLEU : {result['score']:.2f}")
    return {"bleu": result["score"]}

# Arguments d'entraînement
print("⚙️ Configuration des arguments d'entraînement...")
training_args = Seq2SeqTrainingArguments(
    output_dir="./nllb-darija-finetuned-lora",         # 📂 Où sauvegarder les checkpoints
    per_device_train_batch_size=8,
    learning_rate=5e-4,
    num_train_epochs=3,                                # Garde cette ligne, sera ignorée si max_steps > 0
    fp16=True,
    logging_dir="./logs",
    
    # ✅ Sauvegarde & évaluation tous les N steps
    save_strategy="steps",
    save_steps=1000,
    save_total_limit=3,
    eval_strategy="steps",
                               

    # ✅ Logging
    logging_strategy="steps",
    logging_steps=100,

    # ✅ Évaluation aussi tous les 100 steps
    
    eval_steps=1000,

    # ✅ Génération pour le calcul du BLEU
    predict_with_generate=True,

    # ✅ Reprise possible
    load_best_model_at_end=True,
    metric_for_best_model="bleu",
    greater_is_better=True
)
print("✅ Arguments d'entraînement configurés.")

# Trainer avec évaluation
print("🧠 Initialisation du Trainer...")
trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_train_dataset,
    eval_dataset=tokenized_eval_dataset,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)
print("✅ Trainer prêt.")

# Entraînement
print("🚀 Début de l'entraînement...")
# trainer.train()

# print("🚀 Reprise ou démarrage de l'entraînement...")
trainer.train(resume_from_checkpoint=True)


print("🏁 Entraînement terminé.")

# Sauvegarde
print("💾 Sauvegarde du modèle et du tokenizer...")
model.save_pretrained("nllb-darija-lora-model")
tokenizer.save_pretrained("nllb-darija-lora-model")
print("✅ Modèle et tokenizer sauvegardés avec succès.")
