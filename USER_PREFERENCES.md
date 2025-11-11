# Área do Usuário - Preferências de Faixa de Valores

## Visão Geral

A área do usuário permite configurar preferências personalizadas de faixa de valores para colorização visual no front-end. Cada usuário pode definir seus próprios limites para classificar seus saldos diários.

## Modelo de Colorização

O sistema usa três faixas de valores configuráveis:

- **🔴 Vermelho (Ruim)**: Saldo ≤ `bad_threshold`
- **🟡 Amarelo (OK)**: `bad_threshold` < Saldo ≤ `good_threshold`
- **🟢 Verde (Bom)**: Saldo > `good_threshold`

## Estado Inicial

Não existem valores padrão globais. As preferências são definidas pelo próprio usuário.
Enquanto não forem configuradas, os valores podem vir como `null` na API e o front-end deve orientar o usuário a configurá-los.

Além disso, o perfil do usuário expõe o campo booleano `preferences_configured` indicando se os três valores já foram definidos.

## Endpoints da API

### 1. Obter Perfil Completo

```http
GET /user/profile
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "id": 1,
  "first_name": "Admin",
  "last_name": "Zeni",
  "email": "admin@zeni.app",
  "phone": "+5511999999999",
  "is_active": true,
  "preferences_configured": false,
  "preferences": {
    "bad_threshold": 4000,
    "ok_threshold": 6000,
    "good_threshold": 8000
  },
  "created_at": "2025-11-06T10:00:00Z",
  "updated_at": null
}
```

### 2. Atualizar Perfil

```http
PUT /user/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "first_name": "Novo Nome",
  "last_name": "Novo Sobrenome",
  "phone": "+5511988888888"
}
```

**Resposta:** Perfil atualizado completo (mesmo formato do GET /user/profile)

### 3. Obter Preferências

```http
GET /user/preferences
Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "bad_threshold": 4000,
  "ok_threshold": 6000,
  "good_threshold": 8000
}
```

### 4. Atualizar Preferências

```http
PUT /user/preferences
Authorization: Bearer {token}
Content-Type: application/json

{
  "bad_threshold": 5000,
  "ok_threshold": 7000,
  "good_threshold": 10000
}
```

**Resposta:**
```json
{
  "bad_threshold": 5000,
  "ok_threshold": 7000,
  "good_threshold": 10000
}
```

Observação: Se as preferências ainda não tiverem sido configuradas, este endpoint retornará **400 Bad Request**.
Use `POST /user/preferences/init` para a primeira configuração.

### 5. Primeira Configuração (todos obrigatórios)

```http
POST /user/preferences/init
Authorization: Bearer {token}
Content-Type: application/json

{
  "bad_threshold": 4000,
  "ok_threshold": 6000,
  "good_threshold": 8000
}
```

Define todos os três valores de uma vez e valida a ordem crescente. Resposta segue o mesmo formato de `GET /user/preferences`.

## Validações

### Ordem Crescente

Os valores devem sempre estar em ordem crescente:

```
bad_threshold ≤ ok_threshold ≤ good_threshold
```

❌ **Inválido:**
```json
{
  "bad_threshold": 8000,
  "ok_threshold": 6000,
  "good_threshold": 4000
}
```

✅ **Válido:**
```json
{
  "bad_threshold": 4000,
  "ok_threshold": 6000,
  "good_threshold": 8000
}
```

### Valores Não Negativos

Todos os valores devem ser maiores ou iguais a zero (≥ 0).

### Atualização Parcial

É possível atualizar apenas um ou alguns campos:

```json
{
  "good_threshold": 12000
}
```

O sistema validará a ordem considerando os valores atuais dos outros campos.

## Lógica de Colorização no Front-end

```javascript
function getBalanceColor(balance, preferences) {
  if (preferences.bad_threshold != null && balance <= preferences.bad_threshold) {
    return 'red';      // Cenário ruim
  } else if (preferences.good_threshold != null && balance <= preferences.good_threshold) {
    return 'yellow';   // Cenário ok
  } else {
    return 'green';    // Cenário bom
  }
}

// Exemplo de uso
const preferences = {
  bad_threshold: null,
  ok_threshold: null,
  good_threshold: null
};

console.log(getBalanceColor(3500, preferences));  // 'red'
console.log(getBalanceColor(5000, preferences));  // 'yellow'
console.log(getBalanceColor(7000, preferences));  // 'yellow'
console.log(getBalanceColor(9000, preferences));  // 'green'
```

## Exemplos de Casos de Uso

### Usuário Conservador

```json
{
  "bad_threshold": 10000,
  "ok_threshold": 15000,
  "good_threshold": 20000
}
```

Este usuário precisa de saldos mais altos para se sentir confortável.

### Usuário Moderado (Padrão)

```json
{
  "bad_threshold": 4000,
  "ok_threshold": 6000,
  "good_threshold": 8000
}
```

### Usuário Arrojado

```json
{
  "bad_threshold": 1000,
  "ok_threshold": 3000,
  "good_threshold": 5000
}
```

Este usuário se sente confortável com saldos menores.

## Integração com Saldo Diário

Ao buscar o saldo diário via `GET /transactions/balance/daily`, o front-end deve:

1. Obter as preferências do usuário: `GET /user/preferences`
2. Para cada dia retornado, aplicar a lógica de colorização
3. Renderizar com as cores apropriadas

**Exemplo:**

```javascript
// 1. Buscar preferências
const preferences = await fetch('/user/preferences').then(r => r.json());

// 2. Buscar saldos diários
const dailyBalances = await fetch('/transactions/balance/daily?year=2025&month=11')
  .then(r => r.json());

// 3. Aplicar colorização
const coloredBalances = dailyBalances.map(day => ({
  ...day,
  color: getBalanceColor(day.balance, preferences)
}));

// 4. Renderizar
coloredBalances.forEach(day => {
  console.log(`Dia ${day.day}: R$ ${day.balance} - ${day.color}`);
});
```

## Migrações Aplicadas

**Arquivo:** `alembic/versions/68ee136086e9_add_user_preferences_fields.py`

Campos adicionados à tabela `users` (sem valores padrão):
- `bad_threshold` (INTEGER, nullable)
- `ok_threshold` (INTEGER, nullable)
- `good_threshold` (INTEGER, nullable)

## Testando via Swagger UI

1. Acesse: http://127.0.0.1:8000/docs
2. Faça login para obter o token
3. Clique em "Authorize" e insira o token
4. Teste os novos endpoints em **user**:
   - GET /user/profile
   - PUT /user/profile
   - GET /user/preferences
   - PUT /user/preferences
