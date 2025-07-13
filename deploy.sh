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

# Crear requirements.txt si no existe
if [ ! -f "requirements.txt" ]; then
  echo "fastapi" > requirements.txt
  echo "uvicorn" >> requirements.txt
  echo "requests" >> requirements.txt
fi

echo -e "${GREEN}⬇️ Instalando dependencias...${NC}"
pip install -r requirements.txt

# Crear archivo systemd para iniciar automáticamente en reboot
SERVICE_PATH="/etc/systemd/system/fastapi.service"
APP_DIR=$(pwd)
VENV_PATH="$APP_DIR/venv/bin"

echo -e "${GREEN}🛠️ Creando archivo de servicio systemd...${NC}"

sudo bash -c "cat > $SERVICE_PATH" <<EOF
[Unit]
Description=FastAPI service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
ExecStart=$VENV_PATH/uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd y habilitar servicio
echo -e "${GREEN}🔄 Recargando y habilitando servicio...${NC}"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable fastapi.service
sudo systemctl restart fastapi.service

echo -e "${GREEN}✅ FastAPI desplegada correctamente y configurada para reiniciarse automáticamente${NC}"
