# Variables de Entorno para DisRiego Backend

## Configuración de Base de Datos
```
DATABASE_URL=postgres://youruser:yourpassword@db:5432/yourdb
```

## Configuración de Firebase
```
FIREBASE_CREDENTIALS='{}'
FIREBASE_STORAGE_BUCKET=
```

## Configuración de API
```
API_KEY=tu_api_key
SECRET_KEY=super_secret_key
DB_NAME=db_name
DB_USER=db_username
DB_PASSWORD=db_password
```

## Configuración de Email (Gmail SMTP)
```
EMAIL_SENDER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
```

## Configuración del Frontend (para enlaces en correos)
```
FRONTEND_URL=http://localhost:3000
```

## Notas Importantes

### Configuración de Gmail
Para usar Gmail como servidor SMTP, necesitas:

1. **Habilitar la verificación en dos pasos** en tu cuenta de Google
2. **Generar una contraseña de aplicación**:
   - Ve a la configuración de tu cuenta de Google
   - Seguridad > Verificación en dos pasos
   - Contraseñas de aplicación
   - Genera una nueva contraseña para "Correo"

3. **Usar la contraseña de aplicación** en `EMAIL_PASSWORD`

### Variables Requeridas para Email
- `EMAIL_SENDER`: Tu dirección de Gmail
- `EMAIL_PASSWORD`: Contraseña de aplicación de Gmail
- `FRONTEND_URL`: URL base del frontend (para enlaces en correos)

### Ejemplo de Configuración
```bash
EMAIL_SENDER=sigma.inmero@gmail.com
EMAIL_PASSWORD=iqfq tppk ptyw luxu
FRONTEND_URL=http://localhost:3000
```
