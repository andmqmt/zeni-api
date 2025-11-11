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
