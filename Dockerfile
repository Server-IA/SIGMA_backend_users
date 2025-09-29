# Usa Python 3.11 como imagen base
FROM python:3.11

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Reqs y vendor
COPY requirements.txt /app/
COPY vendor/ /app/vendor/

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt
# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Ahora copia el resto del código
COPY . /app/

# Expone el puerto
EXPOSE 8001

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]