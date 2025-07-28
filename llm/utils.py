# llm/utils.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def preprocess_dynamic(examples, tokenizer):
    """
    Prétraite un BATCH d'exemples pour l'entraînement BIDIRECTIONNEL.

    Pour chaque paire (langue1, langue2) dans un exemple, cette fonction
    génère deux tâches d'entraînement :
    1. langue1 -> langue2
    2. langue2 -> langue1

    Args:
        examples (dict): Un batch d'exemples de la bibliothèque `datasets`.
                         Contient une clé 'translation'.
        tokenizer: L'instance du tokenizer NLLB.

    Returns:
        dict: Un dictionnaire tokenisé contenant les 'input_ids', 'attention_mask'
              et 'labels' pour toutes les paires générées.
    """
    inputs = []
    targets = []
    
    # On parcourt chaque exemple du batch
    for translation_dict in examples["translation"]:
        # 1. Filtrer les paires valides (texte non-nul et non-vide)
        valid_pairs = {lang: text for lang, text in translation_dict.items() if text}

        # 2. On s'assure qu'on a exactement une paire
        if len(valid_pairs) == 2:
            langs = list(valid_pairs.keys())
            
            # On extrait les deux langues et textes
            lang1_code, lang2_code = langs[0], langs[1]
            text1, text2 = valid_pairs[lang1_code], valid_pairs[lang2_code]

            # 3. CRÉATION DES DEUX TÂCHES D'ENTRAÎNEMENT
            
            # Tâche 1: langue1 -> langue2
            tokenizer.src_lang = lang1_code
            tokenizer.tgt_lang = lang2_code
            # On préfixe avec le code langue pour aider le modèle
            inputs.append(text1) 
            targets.append(text2)

            # Tâche 2: langue2 -> langue1
            tokenizer.src_lang = lang2_code
            tokenizer.tgt_lang = lang1_code
            inputs.append(text2)
            targets.append(text1)

    # 4. Tokenisation en batch de toutes les paires générées
    model_inputs = tokenizer(
        inputs, 
        text_target=targets, 
        max_length=128, 
        truncation=True
    )
    
    return model_inputs