# llm/merge_and_save.py
import sys
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

if len(sys.argv) != 4:
    print("Usage: python merge_and_save.py <base_model_id> <adapter_path> <output_path>")
    sys.exit(1)

base_model_id, adapter_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

print(f"Chargement du modèle de base '{base_model_id}'...")
base_model = AutoModelForSeq2SeqLM.from_pretrained(base_model_id)

print(f"Application de l'adaptateur depuis '{adapter_path}'...")
model = PeftModel.from_pretrained(base_model, adapter_path)

print("Fusion des poids de l'adaptateur dans le modèle de base...")
merged_model = model.merge_and_unload()
print("Fusion terminée.")

print(f"Sauvegarde du modèle FUSIONNÉ COMPLET dans '{output_path}'...")
merged_model.save_pretrained(output_path)

print(f"Sauvegarde du tokenizer dans '{output_path}'...")
tokenizer = AutoTokenizer.from_pretrained(base_model_id)
tokenizer.save_pretrained(output_path)

print("Sauvegarde terminée.")