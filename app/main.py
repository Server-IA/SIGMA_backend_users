
from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app.roles.routes import router as roles_router
from app.users.routes import router as users_router
from app.auth.routes import router as auth_router
from app.middlewares import setup_middlewares
from app.exceptions import setup_exception_handlers
from app.users.models import ensure_default_genders

# Auditoría
from audit_sdk.context_fastapi import AuditContextMiddleware

# **Configurar FastAPI**
app = FastAPI(
    root_path="/sigma",
    title="Inmero API - Gestión de Usuarios, Roles y Permisos",
    description="Microservicio de gestión de usuarios, roles y permisos dentro del sistema de gestión de maquinaria y nómina.",
    version="1.0.0"
)

# **Configurar Middlewares**
setup_middlewares(app)

# **Configurar Manejadores de Excepciones**
setup_exception_handlers(app)

# **Registrar Rutas**
app.include_router(roles_router, prefix="/users/roles")
app.include_router(users_router, prefix="/users/users")
app.include_router(auth_router, prefix="/users/auth")



Base.metadata.create_all(bind=engine)

# **Endpoint de Salud**
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "API funcionando correctamente"}
