
from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app.roles.routes import router as roles_router
from app.users.routes import router as users_router
from app.auth.routes import router as auth_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers
from app.users.models import ensure_default_genders

# **Configurar FastAPI**
app = FastAPI( 
    root_path="/disriego/base",
    title="Distrito de Riego API Gateway - Gestion de usuario",
    description="API Gateway para gestión de usuarios, roles y permisos en el sistema de riego",
    version="1.0.0"
)

# **Configurar Middlewares**
setup_middlewares(app)

# **Configurar Manejadores de Excepciones**
setup_exception_handlers(app)

# **Registrar Rutas**
app.include_router(roles_router)
app.include_router(users_router)
app.include_router(auth_router)



Base.metadata.create_all(bind=engine)

# **Endpoint de Salud**
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}
