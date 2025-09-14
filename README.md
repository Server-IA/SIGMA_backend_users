# Users Sigma Backend

Este repositorio contiene el backend de **Users Sigma**. La arquitectura está basada en **Python** y se estructura en microservicios. Este documento guía al equipo desde la organización de ramas hasta el levantamiento del contenedor con Docker.

---

## 1. Organización del Repositorio y Ramas

- **Ramas principales:**
  - **develop:** Desarrollo y Pull Requests.
  - **main:** Recibe los cambios aprobados desde `develop`.
  - **test:** El equipo de QA trae cambios desde `main` para ejecutar pruebas.
  - **dokploy:** Se actualiza tras aprobar pruebas para despliegue/producción.

- **Flujo de trabajo:**
  1. Desarrollo en **develop** (PRs).
  2. Aprobación por el líder → merge a **main**.
  3. QA trae cambios de **main** a **test** y realiza pruebas.
  4. Si todo OK, se actualiza **dokploy** para despliegue.

---

## 2. Configurar Variables de Entorno

Copia el archivo `.env.example` a `.env` y ajusta los valores:

```dotenv
DATABASE_URL=postgresql://youruser:yourpassword.@machpay_db:5432/usersdb
FIREBASE_CREDENTIALS='{}'
FIREBASE_STORAGE_BUCKET=

DB_NAME=youruser
DB_USER=youruser
DB_PASSWORD=yourpassword
DB_HOST=machpay_db
DB_PORT=5432

EMAIL_SENDER=email_envio_correo
EMAIL_PASSWORD=password_generada

FRONTEND_URL=http://localhost:3000
EXTERNAL_USERS_API_URL=http://web:8000/main/

SERVICE_NAME=users
AUDIT_URL=http://audit-service:8002/audit-events
AUDIT_TOKEN=devtoken
AUDIT_HTTP_TIMEOUT=1.5
```

## 3. Crear la Red de Docker

Antes de levantar el contenedor de este proyecto, es necesario crear una red compartida en Docker para permitir la comunicación entre los distintos servicios.  

Este paso solo debe ejecutarse una vez en la máquina local:  

```bash
docker network create shared_net
```

## 4. Levantar el Contenedor

El backend de **Users Sigma** depende de los servicios definidos en el proyecto **main** en el repositorio https://github.com/Usuario/AppMachineryPayrollBackend.git, especialmente la base de datos.  
Por esta razón, **antes de iniciar este contenedor debes asegurarte de que el proyecto `main` ya esté levantado** con su `docker-compose`.

Una vez verificado lo anterior, puedes construir e iniciar el servicio de este proyecto con:

```bash
docker-compose up --build
```

## 5. Consideraciones Finales

- Todo el desarrollo y ejecución de este backend se realiza dentro de **Docker**, por lo que **no es necesario configurar entornos virtuales locales**.  
- Antes de levantar este contenedor, valida siempre que:
  - La red **shared_net** esté creada.
  - El proyecto **main** se encuentre corriendo, ya que provee los servicios base (como la base de datos).  
- Si realizas cambios frecuentes en el código, es recomendable usar:
  ```bash
  docker-compose up --build
