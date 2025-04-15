# Enhanced Admin Panel

Panel de administración mejorado para gestión de VPS y conexiones múltiples.

## Características

- Gestión de conexiones VPN/SSH
- Soporte para múltiples protocolos
- Monitor de recursos del sistema
- Instalación de BadVPN-UDPGW
- Herramientas de administración VPS

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/enhanced-admin-panel.git
cd enhanced-admin-panel

# Instalar dependencias
chmod +x install_deps.sh
sudo ./install_deps.sh

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
pip install -r requirements.txt
```

## Uso

```bash
sudo python3 enhanced-admin-panel-final.py
```

## Requisitos

- Python 3.8+
- Sistema operativo: Ubuntu/Debian
- Permisos de root/administrador

## Licencia

Copyright (c) 2025 Corp Kad. Todos los derechos reservados.

Este software es propietario y confidencial.
Está prohibida la copia, modificación o distribución sin autorización expresa del autor.