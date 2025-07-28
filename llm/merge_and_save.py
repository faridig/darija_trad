# llm/merge_and_save.py
import sys
import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel

def main():
    """
    Script pour charger un modèle de base, appliquer un adaptateur LoRA,
    fusionner les poids, et sauvegarder le modèle complet et autonome avec
    son tokenizer propre.
    """
    if len(sys.argv) != 4:
        print("\n❌ Erreur : Nombre d'arguments incorrect.")
        print("   Usage: python llm/merge_and_save.py <base_model_id> <adapter_path> <output_path>")
        print("   Exemple:")
        print("   python llm/merge_and_save.py facebook/nllb-200-distilled-600M ./nllb-darija-lora-model ./merged_model_final\n")
        sys.exit(1)

    base_model_id, adapter_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    print("=" * 60)
    print("🚀 DÉBUT DU PROCESSUS DE FUSION DU MODÈLE LORA")
    print("=" * 60)
    print(f"  - Modèle de base : {base_model_id}")
    print(f"  - Adaptateur LoRA : {adapter_path}")
    print(f"  - Dossier de sortie : {output_path}")
    print("-" * 60)

    # Déterminer le type de calcul (torch_dtype) pour optimiser le chargement
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

    # Étape 1 : Charger le modèle de base ET le tokenizer fiable EN PREMIER.
    print(f"1. Chargement du modèle de base et du tokenizer depuis '{base_model_id}'...")
    try:
        base_model = AutoModelForSeq2SeqLM.from_pretrained(
            base_model_id,
            torch_dtype=dtype,
            low_cpu_mem_usage=True # Optimisation pour ne pas saturer la RAM
        )
        tokenizer = AutoTokenizer.from_pretrained(base_model_id)
        print("   ✅ Modèle et tokenizer chargés.")
    except Exception as e:
        print(f"   ❌ Erreur lors du chargement : {e}")
        sys.exit(1)

    # Étape 2 : Appliquer l'adaptateur LoRA.
    print(f"\n2. Application de l'adaptateur depuis '{adapter_path}'...")
    try:
        model = PeftModel.from_pretrained(base_model, adapter_path)
        print("   ✅ Adaptateur appliqué.")
    except Exception as e:
        print(f"   ❌ Erreur lors de l'application de l'adaptateur : {e}")
        print("      Vérifiez que le chemin de l'adaptateur est correct.")
        sys.exit(1)

    # Étape 3 : Fusionner les poids.
    print("\n3. Fusion des poids de l'adaptateur dans le modèle de base...")
    merged_model = model.merge_and_unload()
    print("   ✅ Fusion terminée.")

    # Étape 4 : Sauvegarder le modèle ET le tokenizer ENSEMBLE.
    # C'est la méthode la plus sûre pour éviter les conflits de configuration.
    print(f"\n4. Sauvegarde du modèle fusionné et du tokenizer dans '{output_path}'...")
    try:
        os.makedirs(output_path, exist_ok=True)
        merged_model.save_pretrained(output_path)
        tokenizer.save_pretrained(output_path)
        print("   ✅ Sauvegarde locale terminée.")
    except Exception as e:
        print(f"   ❌ Erreur lors de la sauvegarde : {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🎉 PROCESSUS TERMINÉ AVEC SUCCÈS")
    print("=" * 60)
    print(f"   Le dossier '{output_path}' contient maintenant un modèle autonome.")
    print("   Vous pouvez le téléverser sur le Hub Hugging Face.\n")

if __name__ == "__main__":
    main()