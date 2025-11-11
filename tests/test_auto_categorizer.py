import pytest
from app.services.auto_categorizer import suggest_category, suggest_category_explain

@pytest.mark.parametrize("text, expected", [
    ("Uber corrida aeroporto", "Transporte"),
    ("Pagamento salario empresa", "Renda: Salario"),
    ("Compra supermercado carrefour", "Supermercado"),
    ("Assinatura netflix premium", "Assinaturas"),
    ("Posto shell gasolina", "Combustivel"),
])
def test_suggest_category_basic(text, expected):
    assert suggest_category(text) == expected

@pytest.mark.parametrize("text", [
    "Descricao aleatoria sem palavra chave",
    "XYZ abc 123",
])
def test_suggest_category_none(text):
    assert suggest_category(text) is None


def test_suggest_category_explain_contains_keyword():
    result = suggest_category_explain("Uber corrida")
    assert result is not None
    assert result["category"] == "Transporte"
    assert result["matched_keyword"] in ["uber"]
