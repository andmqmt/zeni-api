"""
Script de teste para validar o comportamento do endpoint /preferences/init
Testa a validação de valores null e ordem dos thresholds
"""
from app.schemas.user import UserPreferencesInit
from pydantic import ValidationError
import json


def test_null_values():
    """Testa rejeição de valores null"""
    print("\n=== Teste 1: Enviando valores null ===")
    
    test_data = {
        "bad_threshold": None,
        "ok_threshold": None,
        "good_threshold": None
    }
    
    try:
        preferences = UserPreferencesInit(**test_data)
        print("❌ FALHOU: Deveria ter rejeitado valores null")
    except ValidationError as e:
        print("✅ PASSOU: Validação rejeitou valores null corretamente")
        print(f"\nErros retornados:")
        for error in e.errors():
            print(f"  - Campo: {error['loc'][0]}")
            print(f"    Mensagem: {error['msg']}\n")


def test_valid_values():
    """Testa valores válidos"""
    print("\n=== Teste 2: Enviando valores válidos ===")
    
    test_data = {
        "bad_threshold": 0,
        "ok_threshold": 500,
        "good_threshold": 1000
    }
    
    try:
        preferences = UserPreferencesInit(**test_data)
        print("✅ PASSOU: Valores válidos aceitos")
        print(f"  - bad_threshold: {preferences.bad_threshold}")
        print(f"  - ok_threshold: {preferences.ok_threshold}")
        print(f"  - good_threshold: {preferences.good_threshold}")
    except ValidationError as e:
        print("❌ FALHOU: Deveria ter aceito valores válidos")
        print(json.dumps(e.errors(), indent=2))


def test_invalid_order():
    """Testa ordem inválida"""
    print("\n=== Teste 3: Enviando valores fora de ordem ===")
    
    test_data = {
        "bad_threshold": 1000,
        "ok_threshold": 500,
        "good_threshold": 0
    }
    
    try:
        preferences = UserPreferencesInit(**test_data)
        print("❌ FALHOU: Deveria ter rejeitado valores fora de ordem")
    except ValidationError as e:
        print("✅ PASSOU: Validação rejeitou ordem inválida corretamente")
        print(f"\nErro retornado: {e.errors()[0]['msg']}")


def test_partial_null():
    """Testa quando apenas um campo é null"""
    print("\n=== Teste 4: Enviando apenas um campo null ===")
    
    test_data = {
        "bad_threshold": 0,
        "ok_threshold": None,
        "good_threshold": 1000
    }
    
    try:
        preferences = UserPreferencesInit(**test_data)
        print("❌ FALHOU: Deveria ter rejeitado valor null")
    except ValidationError as e:
        print("✅ PASSOU: Validação rejeitou valor null corretamente")
        print(f"\nErro: {e.errors()[0]['msg']}")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTES DE VALIDAÇÃO - UserPreferencesInit")
    print("=" * 60)
    
    test_null_values()
    test_valid_values()
    test_invalid_order()
    test_partial_null()
    
    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)
