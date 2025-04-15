#!/bin/bash
# filepath: c:\Users\CORP CKD\Documents\ADM SSH\install_deps.sh

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Instalando dependencias ===${NC}"

# Verificar root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Este script requiere privilegios root${NC}"
    echo "Ejecute: sudo bash install_deps.sh"
    exit 1
fi

# Actualizar sistema
echo -e "\n${YELLOW}Actualizando sistema...${NC}"
apt update
apt upgrade -y

# Instalar dependencias Python
echo -e "\n${YELLOW}Instalando dependencias Python...${NC}"
apt install -y python3-pip python3-dev

# Instalar paquetes requeridos
echo -e "\n${YELLOW}Instalando herramientas necesarias...${NC}"
apt install -y \
    openvpn \
    wireguard \
    shadowsocks-libev \
    screen \
    cmake \
    make \
    gcc \
    build-essential \
    curl \
    wget

# Instalar V2Ray
echo -e "\n${YELLOW}Instalando V2Ray...${NC}"
bash <(curl -L https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh)

# Instalar dependencias Python
echo -e "\n${YELLOW}Instalando dependencias Python...${NC}"
pip3 install paramiko cryptography requests

echo -e "\n${GREEN}Instalación completada!${NC}"