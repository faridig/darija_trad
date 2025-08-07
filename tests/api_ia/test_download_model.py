import pytest
from unittest.mock import patch, call
import sys

# On importe le script que l'on veut tester
from api.ia_api import download_model

# On récupère l'ID du modèle défini dans le script pour nos vérifications
MODEL_ID = download_model.MERGED_MODEL_ID

# ==============================================================================
# === Test 1 : Le cas où tout se passe bien (cas nominal)
# ==============================================================================
@patch('api.ia_api.download_model.AutoModelForSeq2SeqLM.from_pretrained')
@patch('api.ia_api.download_model.AutoTokenizer.from_pretrained')
def test_main_success(mock_tokenizer_from_pretrained, mock_model_from_pretrained, capsys):
    """
    Vérifie que le script appelle les fonctions de téléchargement avec le bon ID de modèle
    et affiche les messages de succès.
    """
    # Exécution de la fonction main() du script
    download_model.main()

    # Vérification que la fonction pour télécharger le tokenizer a été appelée une fois
    # avec le bon argument (l'ID de notre modèle).
    mock_tokenizer_from_pretrained.assert_called_once_with(MODEL_ID)
    
    # Vérification que la fonction pour télécharger le modèle a été appelée une fois
    # avec le bon argument.
    mock_model_from_pretrained.assert_called_once_with(MODEL_ID)

    # `capsys` est un outil de pytest qui capture ce qui est affiché dans la console.
    # On vérifie que les messages de succès ont bien été affichés.
    captured = capsys.readouterr()
    assert "Démarrage de la mise en cache" in captured.out
    assert f"Modèle à télécharger : {MODEL_ID}" in captured.out
    assert "Modèle et tokenizer mis en cache avec succès" in captured.out
    assert "Une erreur est survenue" not in captured.out

# ==============================================================================
# === Test 2 : Le cas où le téléchargement du modèle échoue
# ==============================================================================
@patch('api.ia_api.download_model.AutoModelForSeq2SeqLM.from_pretrained')
@patch('api.ia_api.download_model.AutoTokenizer.from_pretrained')
def test_main_failure_on_model_download(mock_tokenizer_from_pretrained, mock_model_from_pretrained, capsys):
    """
    Vérifie que le script gère correctement une erreur lors du téléchargement du modèle,
    affiche un message d'erreur et quitte avec un code d'erreur.
    """
    # Configuration du mock : on simule une erreur lors de l'appel à .from_pretrained
    # `side_effect` permet de déclencher une exception quand la fonction est appelée.
    mock_model_from_pretrained.side_effect = ConnectionError("Le modèle n'a pas pu être trouvé")

    # On utilise `pytest.raises` pour s'attendre à ce que `sys.exit(1)` soit appelé.
    # C'est la manière propre de tester un code qui doit quitter le programme.
    with pytest.raises(SystemExit) as e:
        download_model.main()
    
    # On vérifie que le code de sortie est bien 1, comme prévu dans le script.
    assert e.type == SystemExit
    assert e.value.code == 1

    # Vérification des appels : le tokenizer a été appelé, mais le modèle a échoué.
    mock_tokenizer_from_pretrained.assert_called_once_with(MODEL_ID)
    mock_model_from_pretrained.assert_called_once_with(MODEL_ID)
    
    # Vérification des messages affichés dans la console.
    captured = capsys.readouterr()
    assert "Une erreur est survenue" in captured.out
    assert "Le modèle n'a pas pu être trouvé" in captured.out # Le message de l'exception est bien affiché
    assert "mis en cache avec succès" not in captured.out