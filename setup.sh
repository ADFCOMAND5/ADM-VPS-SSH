#!/bin/bash

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Instalador de Enhanced Admin Panel ===${NC}"

# Verificar si es root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Este script debe ejecutarse como root${NC}"
    echo "Ejecuta: sudo bash setup.sh"
    exit 1
fi

# Función para instalar paquetes
install_package() {
    if ! dpkg -l | grep -q "^ii  $1"; then
        echo -e "${YELLOW}Instalando $1...${NC}"
        apt-get install -y "$1" > /dev/null 2>&1
    fi
}

# Actualizar sistema
echo -e "\n${YELLOW}Actualizando sistema...${NC}"
apt-get update
apt-get upgrade -y

# Instalar Python y pip
echo -e "\n${YELLOW}Instalando Python y pip...${NC}"
install_package python3
install_package python3-pip
install_package python3-venv

# Crear entorno virtual
echo -e "\n${YELLOW}Creando entorno virtual...${NC}"
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
echo -e "\n${YELLOW}Instalando dependencias de Python...${NC}"
pip install paramiko
pip install cryptography
pip install requests

# Instalar herramientas del sistema
echo -e "\n${YELLOW}Instalando herramientas del sistema...${NC}"
install_package openssh-client
install_package openssh-server
install_package openvpn
install_package wireguard
install_package shadowsocks-libev
install_package screen
install_package cmake
install_package make
install_package gcc
install_package build-essential

# Instalar V2Ray
echo -e "\n${YELLOW}Instalando V2Ray...${NC}"
curl -O https://raw.githubusercontent.com/v2fly/fhs-install-v2ray/master/install-release.sh
chmod +x install-release.sh
./install-release.sh

# Instalar Trojan
echo -e "\n${YELLOW}Instalando Trojan...${NC}"
add-apt-repository ppa:greaterfire/trojan -y
apt-get update
install_package trojan

# Instalar BadVPN
echo -e "\n${YELLOW}Instalando BadVPN...${NC}"
cd /usr/local/src
wget https://github.com/ambrop72/badvpn/archive/refs/heads/master.zip
unzip master.zip
cd badvpn-master
cmake -DBUILD_NOTHING_BY_DEFAULT=1 -DBUILD_UDPGW=1
make install

# Crear script de inicio para BadVPN
echo -e "\n${YELLOW}Configurando BadVPN...${NC}"
cat > /usr/bin/badvpn-udpgw-start << 'EOF'
#!/bin/bash
screen -dmS badvpn badvpn-udpgw --listen-addr 127.0.0.1:7300 --max-clients 1000 --max-connections-for-client 10
EOF
chmod +x /usr/bin/badvpn-udpgw-start

# Crear servicio systemd para BadVPN
cat > /etc/systemd/system/badvpn.service << 'EOF'
[Unit]
Description=BadVPN UDPGW Service
After=network.target

[Service]
ExecStart=/usr/bin/badvpn-udpgw-start
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

# Iniciar servicios
echo -e "\n${YELLOW}Iniciando servicios...${NC}"
systemctl daemon-reload
systemctl enable badvpn
systemctl start badvpn

# Limpiar archivos temporales
echo -e "\n${YELLOW}Limpiando archivos temporales...${NC}"
rm -f install-release.sh
cd /usr/local/src
rm -rf badvpn-master master.zip

echo -e "\n${GREEN}¡Instalación completada!${NC}"
echo -e "\nPara ejecutar el panel:"
echo -e "${YELLOW}1. source venv/bin/activate${NC}"
echo -e "${YELLOW}2. python3 enhanced-admin-panel-final.py${NC}"