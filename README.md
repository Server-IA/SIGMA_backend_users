# DisRiego_Backend

Este repositorio contiene el backend de **DisRiego**. La arquitectura está basada en **Python** y se estructura en microservicios. Este documento guía al equipo desde la instalación del entorno de desarrollo, la ejecución de tests y el despliegue, hasta la integración con Docker y CI/CD.

---

## 1. Organización del Repositorio y Ramas

- **Ramas Principales:**
  - **develop:** Rama de desarrollo activa.
  - **test:** Rama para integración y pruebas.
  - **main:** Rama de producción.

- **Flujo de Trabajo:**
  1. Desarrollo en `develop`.
  2. Una vez estabilizado, se realiza merge a `test` para ejecutar pruebas exhaustivas.
  3. Finalmente, se fusiona `test` en `main` para el despliegue en producción.

---

## 2. Configuración del Entorno Local

### Requisitos
- [Visual Studio Code](https://code.visualstudio.com/) u otro IDE de preferencia.
- Python 3 (recomendado virtualenv o pipenv para gestión de entornos).
- Docker y Docker Compose instalados.

### Pasos

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/DisRiego_Backend.git
   cd DisRiego_Backend
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python3 -m venv env
   source env/bin/activate  # En Windows: env\Scripts\activate
   ```

3. **Instalar Dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Variables de Entorno:**
   - Copia el archivo `.env.example` a `.env` y ajusta los valores.
   - Ejemplo:
     ```dotenv
     DATABASE_URL=postgres://youruser:yourpassword@db:5432/yourdb
     FIREBASE_CREDENTIALS='{}'
     FIREBASE_STORAGE_BUCKET=
     
     API_KEY=tu_api_key
     SECRET_KEY=super_secret_key
     DB_NAME=db_name
     DB_USER=db_username
     DB_PASSWORD=db_password
     ```

5. **Levantamiento del Entorno con Docker Compose:**
   - Ejecuta:
     ```bash
     docker-compose up
     ```
   - Esto levantará el contenedor del backend (microservicios en Python) y un contenedor de PostgreSQL para el desarrollo local.

6. **Ejecución de Tests:**
   - Ejecuta los tests locales (por ejemplo, usando pytest):
     ```bash
     pytest
     ```

---

## 3. Contenerización con Docker

### Dockerfile

Ejemplo de Dockerfile para un microservicio en Python:
```dockerfile
# Usa Python 3.11 como imagen base
FROM python:3.11

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos del backend al contenedor
COPY . /app/

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto 8000 para FastAPI
EXPOSE 8001

# Comando de inicio del backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose

Archivo `docker-compose.yml` para levantar el backend y PostgreSQL:
```yaml
version: "3.8"

services:
  backend:
    build: .
    container_name: users_backend
    command: >
      sh -c "sleep 10 && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
    ports:
      - "8001:8001"
    depends_on:
      - db
    env_file:
      - .env

  db:
    image: postgres:15
    container_name: users_db
    restart: always
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    ports:
      - "5433:5432"
    volumes:
      - users_postgres_data:/var/lib/postgresql/data

volumes:
  users_postgres_data:
```

---

## 4. Integración de CI/CD con GitHub Actions

### Flujo de CI/CD

- **CI:**  
  - Se ejecutan tests (por ejemplo, con pytest) en cada push o Pull Request en `develop` y `test`.
- **CD:**  
  - Al fusionar en `main`, se despliega automáticamente en Render u otro servicio de hosting para backend.

### Ejemplo de Workflow (archivo `.github/workflows/ci-cd.yml`):
```yaml
name: CI/CD Backend

on:
  push:
    branches: [develop, test, main]
  pull_request:
    branches: [develop, test, main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker Image
        run: docker build -t disriego-backend .
      - name: Run Tests
        run: docker run --env-file .env disriego-backend pytest

  deploy:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to Render
        run: echo "Desplegando a Render..."
```

---

## 5. Consideraciones Finales

- **Variables Sensibles:**  
  - Utiliza GitHub Secrets y configura las variables en el panel de Render.
- **Actualización:**  
  - Este README se actualizará conforme se presenten cambios o imprevistos.
- **Soporte:**  
  - Para dudas, abre un issue en el repositorio o contacta al líder del equipo.

¡Manos a la obra con el backend de DisRiego!
