# Usa una imagen oficial de Python
FROM python:3.8-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos necesarios
COPY . /app

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar tu bot
CMD ["python", "gork_fuente.py"]
