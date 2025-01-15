# Usa una imagen base de Python
FROM python:3.12-slim

# Instala las dependencias del sistema necesarias para OpenCV
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requisitos y el código
COPY requirements.txt requirements.txt
COPY . .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto 5000
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["python", "app.py"]

