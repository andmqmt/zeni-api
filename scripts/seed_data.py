from app.config import SessionLocal
from app.infrastructure.database import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def seed_founder_user():
    db = SessionLocal()
    
    try:
        existing_user = db.query(User).filter(User.email == "admin@zeni.app").first()
        
        if existing_user:
            print(f"✓ Usuário já existe: {existing_user.first_name} {existing_user.last_name}")
            return
        
        founder_user = User(
            first_name="Admin",
            last_name="Zeni",
            email="admin@zeni.app",
            phone="+5511999999999",
            hashed_password=pwd_context.hash("Zeni@2025"),
            is_active=True
        )
        
        db.add(founder_user)
        db.commit()
        db.refresh(founder_user)
        
        print("✓ Usuário fundador criado com sucesso!")
        print(f"  Nome: {founder_user.first_name} {founder_user.last_name}")
        print(f"  Email: {founder_user.email}")
        print(f"  Telefone: {founder_user.phone}")
        print(f"\n📱 Login com Email: {founder_user.email}")
        print(f"📱 Login com Telefone: {founder_user.phone}")
        print(f"🔑 Senha: Zeni@2025")
        print(f"\n🔐 Código de Acesso para Registro: z3n1#2025")
        
    finally:
        db.close()


if __name__ == "__main__":
    seed_founder_user()
