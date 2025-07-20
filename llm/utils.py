# llm/utils.py

# Imports nécessaires pour la fonction
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def preprocess_dynamic(example, tokenizer, model):
    """
    Prétraite un exemple de traduction pour le fine-tuning.

    Cette fonction prend un dictionnaire `example` contenant des paires de traduction,
    ainsi que le tokenizer et le modèle, puis retourne les entrées formatées pour
    l'entraînement.

    Args:
        example (dict): Un dictionnaire contenant une clé 'translation' avec les paires de langues.
                        Ex: {'translation': {'fra_Latn': 'Bonjour', 'ary_Arab': 'سلام'}}
        tokenizer: L'instance du tokenizer de Hugging Face.
        model: L'instance du modèle Seq2Seq de Hugging Face.

    Returns:
        dict or None: Un dictionnaire avec 'input_ids', 'attention_mask' et 'labels',
                      ou None si l'exemple est invalide.
    """
    translation_dict = example.get("translation", {})

    # 1. Filtrer les clés dont la valeur est None ou une chaîne vide
    valid_pairs = {lang: text for lang, text in translation_dict.items() if text}

    # 2. On doit avoir exactement une paire de langues valides
    if len(valid_pairs) != 2:
        return None  # On ne retourne rien pour que .filter() supprime la ligne

    # 3. Extraire la paire source/cible
    langs = list(valid_pairs.keys())
    # On s'assure que l'ordre est toujours le même pour la reproductibilité
    langs.sort() 
    src_lang, tgt_lang = langs[0], langs[1]
    src_text = valid_pairs[src_lang]
    tgt_text = valid_pairs[tgt_lang]

    # Définit les langues pour le tokenizer pour cet exemple spécifique
    tokenizer.src_lang = src_lang
    model_inputs = tokenizer(src_text, max_length=128, padding="max_length", truncation=True)
    
    # Prépare les labels (texte cible)
    tokenizer.tgt_lang = tgt_lang
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(tgt_text, max_length=128, padding="max_length", truncation=True)
    
    model_inputs["labels"] = labels["input_ids"]
    
    # Configure le modèle pour forcer le token de début de la langue cible
    model.config.forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang)
    
    return model_inputs