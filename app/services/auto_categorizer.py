import unicodedata
from typing import Optional, List, Tuple, Dict, Iterable


def _normalize(text: str) -> str:
    text = text or ""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)).lower()


# Default rules for Brazilian common transactions: (category_name, [keywords])
_RULES: List[Tuple[str, List[str]]] = [
    ("Transporte", ["uber", "99", "cabify", "estacionamento", "pedagio", "sem parar"]),
    ("Delivery", ["ifood", "rappi", "uber eats", "delivery"]),
    ("Supermercado", [
        "mercado livre", "carrefour", "extra", "paodeacucar", "pao de acucar", "assai", "atacadao", "dia ", "guanabara",
    ]),
    ("Compras", [
        "amazon", "magazine luiza", "magazineluiza", "americanas", "submarino", "casas bahia", "shopee", "shein", "aliexpress",
    ]),
    ("Assinaturas", [
        "netflix", "spotify", "prime video", "disney+", "hbo max", "youtube premium", "globoplay", "deezer",
        "icloud", "google drive", "office 365", "microsoft 365",
    ]),
    ("Telefone/Internet", ["vivo", "claro", "tim", "oi", "internet", "banda larga"]),
    ("Energia", ["enel", "light", "copel", "ceee", "cpfl", "energisa", "celesc"]),
    ("Agua", ["sabesp", "copasa", "sanepar", "caesb", "saae", "casan"]),
    ("Condominio", ["condominio"]),
    ("Aluguel", ["aluguel", "locacao"]),
    ("Impostos", ["iptu", "ipva", "irpf", "darf", "taxa" ]),
    ("Seguro", ["seguro", "porto seguro", "sulamerica", "bradesco seguros", "allianz"]),
    ("Saude", ["farmacia", "drogasil", "droga raia", "pague menos", "panvel", "ultrafarma", "laboratorio", "consulta", "hospital", "clinica"]),
    ("Combustivel", ["posto", "shell", "ipiranga", "br ", "petrobras", "gasolina", "etanol", "diesel"]),
    ("Academia", ["academia", "smart fit", "bodytech", "bluefit"]),
    ("Educacao", ["escola", "curso", "udemy", "alura", "coursera", "faculdade", "universidade"]),
    ("Alimentacao", ["restaurante", "lanchonete", "bar", "cafeteria", "padaria"]),
    ("Tarifas Bancarias", ["tarifa", "cesta", "manutencao de conta", "iof", "ted", "doc", "pix tarifa", "bancaria"]),
    ("Investimentos", ["investimento", "tesouro", "cdb", "lci", "lca", "acoes", "fundos", "renda fixa"]),
    ("Renda: Salario", ["salario", "pagamento", "provento", "holerite"]),
    ("Renda: Transferencias", ["pix recebido", "transferencia recebida", "deposito"]),
]

# Peso base por categoria (pode ser ajustado futuramente se quisermos favorecer algumas categorias)
_CATEGORY_BASE_WEIGHT: Dict[str, float] = {c: 1.0 for c, _ in _RULES}

def _tokenize(desc: str) -> List[str]:
    return [t for t in desc.replace('/', ' ').replace('-', ' ').split() if t]


def suggest_category(description: str) -> Optional[str]:
    """Return the best matching category using a simple scoring heuristic.

    Scoring:
      - Each keyword match contributes (len(keyword) / total_len) * 10
      - Exact token match adds +2
      - Category base weight added at the end
    The highest score above a minimal threshold wins; otherwise returns None.
    """
    desc = _normalize(description)
    if not desc:
        return None
    tokens = set(_tokenize(desc))
    best_category = None
    best_score = 0.0
    total_len = len(desc) or 1
    for category, keywords in _RULES:
        score = 0.0
        for kw in keywords:
            if kw in desc:
                # Longer keywords weigh more
                score += (len(kw) / total_len) * 10
                # Exact token match bonus
                if kw in tokens:
                    score += 2
        if score > 0:
            score += _CATEGORY_BASE_WEIGHT.get(category, 1.0)
        if score > best_score:
            best_score = score
            best_category = category
    # Threshold: require at least modest evidence
    if best_score < 1.5:
        return None
    return best_category


def suggest_category_explain(description: str) -> Optional[Dict[str, str]]:
    """Return suggested category, top keyword and internal score for explainability."""
    desc = _normalize(description)
    if not desc:
        return None
    tokens = set(_tokenize(desc))
    best = None
    for category, keywords in _RULES:
        for kw in keywords:
            if kw in desc:
                # Use length and token exactness as a proxy score
                base = len(kw)
                if kw in tokens:
                    base += 5
                if (not best) or base > best[2]:
                    best = (category, kw, base)
    if not best:
        return None
    return {"category": best[0], "matched_keyword": best[1]}
