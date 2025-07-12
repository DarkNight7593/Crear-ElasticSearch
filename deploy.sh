#!/bin/bash

set -e  # Terminar si ocurre algún error

GREEN='\033[0;32m'
NC='\033[0m' # Sin color

echo -e "${GREEN}🚀 Iniciando despliegue de la API FastAPI...${NC}"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
  echo -e "${GREEN}📦 Creando entorno virtual...${NC}"
  python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias si falta alguna
if [ ! -f "requirements.txt" ]; then
  echo "fastapi" > requirements.txt
  echo "uvicorn" >> requirements.txt
fi

echo -e "${GREEN}⬇️ Instalando dependencias...${NC}"
pip install -r requirements.txt

# Ejecutar Uvicorn
echo -e "${GREEN}▶️ Ejecutando servidor Uvicorn en 0.0.0.0:8080...${NC}"
uvicorn main:app --host 0.0.0.0 --port 8080
