# Zeni API

API para gerenciamento financeiro pessoal com controle de transações, visualização de saldo diário, preferências de thresholds e categorização automática de descrições.

## 🏗️ Arquitetura

Seguindo princípios de Clean Architecture / SOLID:

```
app/
  api/            # FastAPI routers (interfaces HTTP)
  schemas/        # DTOs Pydantic (v2)
  services/       # Casos de uso / regra de negócio
  repositories/   # Persistência (SQLAlchemy queries)
  infrastructure/ # Implementações (models, DB engine)
  config/         # Settings / env
scripts/          # Scripts utilitários (seed, etc.)
alembic/          # Migrations
docs/             # Documentação adicional
```

Camadas superiores não importam detalhes das inferiores (ex: `api` -> `services` -> `repositories`).

## 🚀 Setup (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copiar .env exemplo:
```powershell
Copy-Item .env.example .env
```

Editar `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/zeni_db
SECRET_KEY=troque-por-uma-chave-forte
ACCESS_CODE=m0n3if#2025
```

Criar banco (se ainda não existir):
```sql
CREATE DATABASE zeni_db;
```

Aplicar migrations:
```powershell
alembic upgrade head
# ou
python -m alembic upgrade head
```

Popular dados iniciais (seed):
```powershell
python -m scripts.seed_data
```

Iniciar servidor:
```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

URLs:
- API root: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Base v1: http://localhost:8000/api/v1

## 🔐 Autenticação & Sessão

Fluxo padrão JWT (Bearer). Rotas protegidas exigem:
```
Authorization: Bearer <token>
```

Login (form-encoded):
```http
POST /api/v1/auth/login
username=email@exemplo.com
password=senha123
```
Resposta 200:
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

Registro:
```http
POST /api/v1/auth/register
{
  "first_name": "Nome",
  "last_name": "Sobrenome",
  "email": "email@exemplo.com",
  "phone": "+5511999999999",
  "password": "Senha@Forte1",
  "access_code": "m0n3if#2025"
}
```

Erros padronizados:
```json
{ "detail": "Invalid credentials", "code": "INVALID_CREDENTIALS" }
{ "detail": "Not authenticated", "code": "NOT_AUTHENTICATED" }
```

## ❗️ Formato de Erro Global

Todos os erros seguem estrutura mínima:
```json
{ "detail": "Mensagem", "code": "CODIGO_OPCIONAL", "meta": { "campo": "info" } }
```
Validação (422):
```json
{ "detail": "Validation error", "code": "VALIDATION_ERROR", "meta": { "errors": [ {"loc": ["body","field"], "msg": "..."} ] } }
```

## 📊 Endpoints Principais

### Transações
- `POST /api/v1/transactions/` Criar
- `GET /api/v1/transactions/` Listar (paginação: `skip=0`, `limit=50` padrão, máximo `200`)
  - filtros opcionais: `on_date=YYYY-MM-DD`, `category_id=<id>`
- `GET /api/v1/transactions/{id}` Detalhar
- `PUT /api/v1/transactions/{id}` Atualizar
- `DELETE /api/v1/transactions/{id}` Remover

Ordenação: `transaction_date DESC, id DESC`.

Sugestão de categoria (stateless, não exige auth):
```http
POST /api/v1/transactions/suggest-category
{ "description": "Uber aeroporto" }
```
Resposta:
```json
{ "category": "Transporte", "matched_keyword": "uber" }
```
Pode retornar `{ "category": null }`.

### Saldo Diário
```http
GET /api/v1/transactions/balance/daily?year=2025&month=12
```
Alias: `/api/v1/transactions/daily-balance`.

Resposta (exemplo):
```json
[
  { "date": "2025-12-01", "balance": 1200.50, "status": "green" },
  { "date": "2025-12-02", "balance": 1180.50, "status": "yellow" }
]
```

Status (thresholds do usuário):
- `green` >= good_threshold
- `yellow` >= ok_threshold
- `red` >= bad_threshold (e abaixo de bad também `red`)
- `unconfigured` preferências ausentes ou inconsistentes

### Categorias
- `GET /api/v1/categories/` Lista (ordenadas por nome ASC) filtro opcional `origin=auto|manual`
- `POST /api/v1/categories/` Criar
- `PUT /api/v1/categories/{id}` Atualizar
- `DELETE /api/v1/categories/{id}` Remover

Campo adicional: `is_auto_generated` indica se criação foi automática.

### Usuário & Preferências
- `GET /api/v1/user/profile`
- `PUT /api/v1/user/profile` (inclui `auto_categorize_enabled`)
- `GET /api/v1/user/preferences`
- `POST /api/v1/user/preferences/init` (define bad < ok < good)
- `PUT /api/v1/user/preferences` (atualização parcial validando ordem)

## 🧠 Categorização Automática

Ativa apenas se `auto_categorize_enabled=true` para o usuário. Ao criar/atualizar transação sem `category_id`:
1. Heurística avalia descrição (normalização, tokens, pontuação por keyword).
2. Sugere categoria.
3. Se categoria não existir, cria com `is_auto_generated=true`.
4. Associa à transação.

Endpoint de sugestão separado não altera banco.

## 🛠️ Tecnologias
- FastAPI
- SQLAlchemy 2.x + Alembic
- PostgreSQL
- Pydantic v2
- python-jose (JWT)
- passlib[bcrypt]
- pytest / pytest-cov

## 📂 Estrutura de Dados (resumo)

### User
| Campo | Descrição |
|-------|-----------|
| first_name / last_name | Nome |
| email / phone | Únicos |
| password | Hash bcrypt |
| auto_categorize_enabled | Flag categorização automatizada |

### Preferences
| Campo | Descrição |
| bad_threshold | Limite mínimo (vermelho) |
| ok_threshold  | Limite intermediário (amarelo) |
| good_threshold| Limite desejado (verde) |

### Category
| Campo | Descrição |
| name | Nome único por usuário |
| is_auto_generated | Criada por heurística |

### Transaction
| Campo | Descrição |
| description | Texto livre |
| amount | Decimal (positivo) |
| type | income | expense |
| transaction_date | Data efetiva |
| category_id | FK opcional |
| user_id | Dono |

## 🔒 Segurança
- Hash de senhas com bcrypt
- JWT (expiração configurável) Bearer auth
- Código de acesso externo para impedir registros não autorizados
- Escopo de dados isolado por `user_id`

## 📋 Usuário Seed
Após `python -m scripts.seed_data`:
| Email | Telefone | Senha |
|-------|----------|-------|
| admin@zeni.app | +5511999999999 | Zeni@2025 |

## 🧪 Testes

Executar suite:
```powershell
pytest -q
```

Cobertura:
```powershell
pytest --cov=app --cov-report=term-missing
```

## 🧹 Remoções / Deprecações
- Funcionalidade de Budgets removida (modelo & tabela). Migrations limpam a tabela se existir.

## 📎 Próximos Passos Sugestões
- Testes adicionais para cálculo de saldo diário (edge cases mês sem transações).
- Cache leve para categorias auto-geradas mais frequentes.
- Rate limiting em endpoints públicos (suggest-category).

## 📜 Licença
Uso interno / privado.
# Zeni API

API para gerenciamento financeiro pessoal com controle de transações e visualização de saldo diário.

## 🏗️ Arquitetura

O projeto segue princípios de **Clean Architecture**:

```
app/
├── api/                    # Camada de apresentação (FastAPI routes)
├── schemas/                # DTOs e validação (Pydantic)
├── services/               # Casos de uso e lógica de negócio
├── repositories/           # Acesso a dados
├── infrastructure/         # Detalhes de implementação
│   └── database/          # Models SQLAlchemy
└── config/                 # Configurações da aplicação

scripts/                    # Scripts utilitários
alembic/                    # Migrations do banco de dados
```

## 🚀 Setup

### 1. Instalar Dependências

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e configure suas credenciais:

```bash
Copy-Item .env.example .env
```

Edite o `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/zeni_db
SECRET_KEY=your-secret-key-here
ACCESS_CODE=z3n1#2025
```

### 3. Criar o Banco de Dados

```sql
CREATE DATABASE zeni_db;
```

### 4. Executar Migrations

```bash
alembic upgrade head
```

### 5. Popular Dados Iniciais

```bash
python -m scripts.seed_data
```

### 6. Iniciar o Servidor

```bash
uvicorn app.main:app --reload
```

Acesse:
- API: http://localhost:8000
- Documentação: http://localhost:8000/docs

## 📝 Migrations

### Criar Nova Migration

```bash
alembic revision --autogenerate -m "descrição da mudança"
```

### Aplicar Migrations

```bash
alembic upgrade head
```

### Reverter Última Migration

```bash
alembic downgrade -1
```

### Ver Histórico

```bash
alembic history
```

## 🔐 Autenticação

### Registro

```http
POST /api/v1/auth/register
{
  "first_name": "Nome",
  "last_name": "Sobrenome",
  "email": "email@exemplo.com",
  "phone": "+5511999999999",
  "password": "senha123",
  "access_code": "m0n3if#2025"
}
```

### Login

```http
POST /api/v1/auth/login
username=email@exemplo.com  (ou telefone)
password=senha123
```

Retorna um `access_token` que deve ser usado no header:
```
Authorization: Bearer {token}
```

## 📊 Endpoints Principais

### Transações

- `POST /api/v1/transactions/` - Criar transação
- `GET /api/v1/transactions/` - Listar transações
- `GET /api/v1/transactions/{id}` - Ver transação específica
- `PUT /api/v1/transactions/{id}` - Atualizar transação
- `DELETE /api/v1/transactions/{id}` - Deletar transação

### Saldo Diário

```http
GET /api/v1/transactions/balance/daily?year=2025&month=12
```

Retorna o saldo acumulado dia a dia do mês.

## 🛠️ Tecnologias

- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Alembic** - Migrations
- **PostgreSQL** - Banco de dados
- **Pydantic** - Validação de dados
- **JWT** - Autenticação
- **Bcrypt** - Hash de senhas

## 📂 Estrutura de Dados

### User
- first_name, last_name
- email (único)
- phone (único)
- password (hash)

### Transaction
- description
- amount
- type (income/expense)
- transaction_date
- user_id (FK)

## 🔒 Segurança

- Senhas hasheadas com bcrypt
- JWT tokens com expiração de 30 dias
- Código de acesso para registro (configurável via .env)
- Isolamento de dados por usuário

## 📋 Usuário Inicial

Após executar `python -m scripts.seed_data`:

- **Email**: admin@zeni.app
- **Telefone**: +5511999999999
- **Senha**: Zeni@2025

## 🧪 Desenvolvimento

O projeto está configurado com:
- ✅ Clean Architecture
- ✅ SOLID Principles
- ✅ Type Hints
- ✅ Migrations automáticas
- ✅ API Documentation (Swagger)
