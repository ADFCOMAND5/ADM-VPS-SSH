#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import socket
import paramiko
import threading
import time
import getpass
import subprocess
import requests
from ftplib import FTP
import ssl
from datetime import datetime
from cryptography.fernet import Fernet
import shutil

class MultiProtocolAdminPanel:
    def __init__(self):
        self.connections = {}
        self.active_sessions = {}
        self.log_file = "admin_panel.log"
        self.config_file = "connections_config.txt"
        self.encryption_key_file = "encryption.key"
        self.running = True
        self.encryption_key = self.load_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Protocolos soportados
        self.supported_protocols = {
            "ssh": {"port": 22, "handler": self.handle_ssh},
            "dropbear": {"port": 443, "handler": self.handle_dropbear},
            "squid": {"port": 3128, "handler": self.handle_squid},
            "openvpn": {"port": 1194, "handler": self.handle_openvpn},
            "wireguard": {"port": 51820, "handler": self.handle_wireguard},
            "telnet": {"port": 23, "handler": self.handle_telnet},
            "ftp": {"port": 21, "handler": self.handle_ftp},
            "http": {"port": 80, "handler": self.handle_http},
            "https": {"port": 443, "handler": self.handle_https},
            "shadowsocks": {"port": 8388, "handler": self.handle_shadowsocks},
             "v2ray": {"port": 10086, "handler": self.handle_v2ray}
        }
        
    def log(self, message):
        """Registra mensajes en el archivo de registro"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[{timestamp}] {message}")

    def load_encryption_key(self):
        """Carga o genera una clave de cifrado"""
        if os.path.exists(self.encryption_key_file):
            with open(self.encryption_key_file, "rb") as f:
                return f.read()
        else:
            pass  # Placeholder for future implementation
            pass
            pass  # Placeholder for future implementation
            key = Fernet.generate_key()
            with open(self.encryption_key_file, "wb") as f:
                f.write(key)
            return key

    def encrypt_password(self, password):
        """Cifra una contraseña"""
        return self.cipher.encrypt(password.encode('utf-8'))

    def decrypt_password(self, encrypted_password):
        """Descifra una contraseña"""
        return self.cipher.decrypt(encrypted_password).decode('utf-8')
        
    def load_connections(self):
        """Carga las conexiones guardadas desde el archivo de configuración"""
        try:
            if not os.path.exists(self.config_file):
                self.log("No se encontró archivo de configuración. Creando uno nuevo.")
                return
                
            with open(self.config_file, "r") as f:
                lines = f.readlines()
                
            for line in lines:
                if line.strip() and not line.startswith("#"):
                    parts = line.strip().split(":")
                    if len(parts) >= 5:  # Ahora incluimos el protocolo
                        name = parts[0]
                        protocol = parts[1]
                        host = parts[2]
                        port = int(parts[3])
                        username = parts[4]
                        password = parts[5] if len(parts) > 5 else ""
                        extra_params = parts[6] if len(parts) > 6 else ""
                        
                        self.connections[name] = {
                            "protocol": protocol,
                            "host": host,
                            "port": port,
                            "username": username,
                            "password": password,
                            "extra_params": extra_params
                        }
            
            self.log(f"Se cargaron {len(self.connections)} conexiones")
        except Exception as e:
            self.log(f"Error al cargar conexiones: {str(e)}")
            
    def save_connections(self):
        """Guarda las conexiones en el archivo de configuración"""
        try:
            with open(self.config_file, "w") as f:
                f.write("# Formato: nombre:protocolo:host:puerto:usuario:contraseña:parametros_extra\n")
                for name, conn in self.connections.items():
                    f.write(f"{name}:{conn['protocol']}:{conn['host']}:{conn['port']}:{conn['username']}:{conn['password']}:{conn.get('extra_params', '')}\n")
                    
            self.log(f"Se guardaron {len(self.connections)} conexiones")
        except Exception as e:
            self.log(f"Error al guardar conexiones: {str(e)}")
            
    def add_connection(self):
        """Añade una nueva conexión"""
        print("\n=== Añadir nueva conexión ===")
        name = input("Nombre de la conexión: ")
        
        # Mostrar protocolos disponibles
        protocol = self.select_protocol()
                
        # Obtener información de conexión
        host = input("Host (dirección IP o nombre de dominio): ")
        
        default_port = self.supported_protocols[protocol]["port"]
        while True:
            try:
                port = int(input(f"Puerto ({default_port}): ") or str(default_port))
                break
            except ValueError:
                print("Por favor, introduce un número válido para el puerto.")
                
        username = input("Nombre de usuario: ")
        password = getpass.getpass("Contraseña (dejar en blanco para usar clave SSH o si no aplica): ")
        
        # Cifrar la contraseña
        encrypted_password = self.encrypt_password(password) if password else ""
        
        # Parámetros extra específicos del protocolo
        extra_params = ""
        if protocol == "ssh":
            use_key = input("¿Usar clave SSH? (s/n): ").lower() == 's'
            if use_key:
                key_path = input("Ruta de la clave privada SSH: ")
                extra_params = f"key:{key_path}"
        elif protocol == "squid":
            proxy_type = input("Tipo de proxy (http/socks): ") or "http"
            extra_params = f"type:{proxy_type}"
        elif protocol == "openvpn":
            config_path = input("Ruta del archivo de configuración (.ovpn): ")
            extra_params = config_path
        elif protocol == "wireguard":
            config_path = input("Ruta del archivo de configuración WireGuard: ")
            extra_params = config_path
        elif protocol in ["shadowsocks", "v2ray", "trojan"]:
            encryption = input("Método de encriptación: ")
            extra_params = encryption
        
        # Guardar la conexión
        self.connections[name] = {
            "protocol": protocol,
            "host": host,
            "port": port,
            "username": username,
            "password": encrypted_password,
            "extra_params": extra_params
        }
        
        self.log(f"Se añadió una nueva conexión {protocol}: {name}")
        self.save_connections()
        
    def remove_connection(self):
        """Elimina una conexión existente"""
        if not self.connections:
            print("No hay conexiones para eliminar.")
            return
            
        print("\n=== Eliminar una conexión ===")
        self.list_connections()
        
        name = input("\nNombre de la conexión a eliminar (o 'cancelar'): ")
        if name.lower() == 'cancelar':
            return
            
        if name in self.connections:
            del self.connections[name]
            self.log(f"Se eliminó la conexión: {name}")
            self.save_connections()
        else:
            print(f"No se encontró la conexión: {name}")
            
    def list_connections(self):
        """Muestra la lista de conexiones guardadas"""
        if not self.connections:
            print("No hay conexiones guardadas.")
            return
            
        print("\n=== Conexiones Guardadas ===")
        print(f"{'Nombre':<15} {'Protocolo':<12} {'Host':<25} {'Puerto':<8} {'Usuario':<15}")
        print("-" * 75)
        
        for name, conn in self.connections.items():
            protocol = conn['protocol'].upper()
            print(f"{name:<15} {protocol:<12} {conn['host']:<25} {conn['port']:<8} {conn['username']:<15}")
            
    def connect(self, connection_name):
        """Establece una conexión basada en el protocolo"""
        try:
            if connection_name not in self.connections:
                print(f"No se encontró la conexión: {connection_name}")
                return False
                
            conn = self.connections[connection_name]
            protocol = conn['protocol'].lower()
            
            if protocol not in self.supported_protocols:
                print(f"Protocolo no soportado: {protocol}")
                return False
                
            # Llamar al manejador específico del protocolo
            handler = self.supported_protocols[protocol]["handler"]
            return handler(connection_name, conn)
        except KeyError:
            print("Conexión no encontrada")
            return False
    
    # Manejadores de protocolo
    def handle_ssh(self, connection_name, conn_info):
        """Maneja conexiones SSH (incluye Dropbear)"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            self.log(f"Conectando a SSH {conn_info['host']}:{conn_info['port']} como {conn_info['username']}...")
            
            # Descifrar la contraseña
            decrypted_password = self.decrypt_password(conn_info['password'])
            
            # Manejo de autenticación
            if conn_info['extra_params'].startswith('key:'):
                key_path = conn_info['extra_params'].split(':', 1)[1]
                client.connect(
                    hostname=conn_info['host'],
                    port=conn_info['port'],
                    username=conn_info['username'],
                    key_filename=key_path,
                    timeout=10
                )
            elif decrypted_password:
                client.connect(
                    hostname=conn_info['host'],
                    port=conn_info['port'],
                    username=conn_info['username'],
                    password=decrypted_password,
                    timeout=10
                )
            else:
                # Intentar autenticación con clave SSH del sistema
                client.connect(
                    hostname=conn_info['host'],
                    port=conn_info['port'],
                    username=conn_info['username'],
                    timeout=10
                )
                
            self.log(f"Conexión SSH establecida con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "ssh",
                "client": client,
                "connected_at": datetime.now()
            }
            
            return client
        except Exception as e:
            self.log(f"Error al conectar a SSH {connection_name}: {str(e)}")
            return False
        finally:
            if client:
                client.close()
            if connection_name in self.active_sessions:
                del self.active_sessions[connection_name]
            print(f"Conexión con {connection_name} cerrada.")
            
    def handle_dropbear(self, connection_name, conn_info):
        """Maneja conexiones Dropbear (usa el cliente SSH estándar)"""
        return self.handle_ssh(connection_name, conn_info)
            
    def handle_squid(self, connection_name, conn_info):
        """Maneja conexiones Squid (proxy)"""
        try:
            self.log(f"Configurando proxy Squid {conn_info['host']}:{conn_info['port']}...")
            
            proxy_type = "http"
            if conn_info['extra_params'].startswith('type:'):
                proxy_type = conn_info['extra_params'].split(':', 1)[1]
                
            # Verificar la conexión al proxy
            proxies = {
                "http": f"{proxy_type}://{conn_info['username']}:{conn_info['password']}@{conn_info['host']}:{conn_info['port']}",
                "https": f"{proxy_type}://{conn_info['username']}:{conn_info['password']}@{conn_info['host']}:{conn_info['port']}"
            }
            
            # Hacer una solicitud de prueba
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=10)
            
            # Si llegamos aquí, el proxy funciona
            self.log(f"Conexión Squid establecida con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "squid",
                "proxies": proxies,
                "connected_at": datetime.now()
            }
            
            return proxies
        except Exception as e:
            self.log(f"Error al conectar a Squid {connection_name}: {str(e)}")
            return False
            
    def handle_openvpn(self, connection_name, conn_info):
        """Maneja conexiones OpenVPN"""
        try:
            self.log(f"Iniciando conexión OpenVPN a {conn_info['host']}...")
            config_path = conn_info['extra_params']
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
                
            # Verificar si el usuario tiene permisos para ejecutar OpenVPN
            if os.name == 'posix' and os.geteuid() != 0:
                self.log("Advertencia: Este comando requiere privilegios de administrador.")
                
            # Iniciar el proceso OpenVPN
            process = subprocess.Popen(
                ["openvpn", "--config", config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar un momento para verificar si se inicia correctamente
            time.sleep(2)
            if process.poll() is not None:
                stderr = process.stderr.read().decode('utf-8')
                raise Exception(f"Error al iniciar OpenVPN: {stderr}")
                
            self.log(f"Conexión OpenVPN iniciada con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "openvpn",
                "process": process,
                "connected_at": datetime.now()
            }
            
            return process
        except Exception as e:
            self.log(f"Error al conectar a OpenVPN {connection_name}: {str(e)}")
            return False
        finally:
            config_file = conn_info.get('extra_params', '')  # Ensure config_file is defined
            if os.path.exists(config_file):
                os.remove(config_file)
                self.log(f"Archivo de configuración temporal eliminado: {config_file}")
            
    def handle_wireguard(self, connection_name, conn_info):
        """Maneja conexiones WireGuard"""
        try:
            self.log(f"Iniciando conexión WireGuard a {conn_info['host']}...")
            config_path = conn_info['extra_params']
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
                
            # Verificar si el usuario tiene permisos para ejecutar WireGuard
            if os.name == 'posix' and os.geteuid() != 0:
                self.log("Advertencia: WireGuard requiere privilegios de administrador")
                
            # Extraer el nombre de la interfaz del archivo de configuración
            interface_name = "wg0"  # Valor predeterminado
            with open(config_path, 'r') as f:
                for line in f:
                    if line.strip().lower().startswith("interface"):
                        interface_name = line.strip().split("=")[1].strip()
                        break
                        
            # Iniciar la conexión WireGuard
            process = subprocess.Popen(
                ["wg-quick", "up", config_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar a que termine el proceso
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Error al iniciar WireGuard: {stderr.decode('utf-8')}")
                
            self.log(f"Conexión WireGuard {interface_name} iniciada con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "wireguard",
                "interface": interface_name,
                "config_path": config_path,
                "connected_at": datetime.now()
            }
            
            return True
        except Exception as e:
            self.log(f"Error al conectar a WireGuard {connection_name}: {str(e)}")
            return False
            
    def handle_telnet(self, connection_name, conn_info):
        """Maneja conexiones Telnet usando sockets"""
        try:
            self.log(f"Conectando a Telnet {conn_info['host']}:{conn_info['port']}...")
            
            # Crear socket TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            # Conectar al servidor
            sock.connect((conn_info['host'], conn_info['port']))
            
            # Manejar autenticación si es necesario
            if conn_info['username']:
                # Esperar prompt de login
                data = sock.recv(1024).decode('ascii')
                if 'login' in data.lower():
                    sock.send((conn_info['username'] + '\n').encode('ascii'))
                    
                    if conn_info['password']:
                        # Esperar prompt de password
                        data = sock.recv(1024).decode('ascii')
                        if 'password' in data.lower():
                            sock.send((conn_info['password'] + '\n').encode('ascii'))
            
            self.log(f"Conexión Telnet establecida con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "telnet",
                "socket": sock,
                "connected_at": datetime.now()
            }
            
            return sock
        except Exception as e:
            self.log(f"Error al conectar a Telnet {connection_name}: {str(e)}")
            return False
            
    def handle_ftp(self, connection_name, conn_info):
        """Maneja conexiones FTP"""
        try:
            self.log(f"Conectando a FTP {conn_info['host']}:{conn_info['port']}...")
            
            # Crear cliente FTP
            ftp = FTP()
            ftp.connect(conn_info['host'], conn_info['port'])
            
            # Iniciar sesión si se proporcionaron credenciales
            if conn_info['username']:
                ftp.login(conn_info['username'], conn_info['password'])
            else:
                ftp.login()  # Inicio de sesión anónimo
                
            self.log(f"Conexión FTP establecida con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "ftp",
                "client": ftp,
                "connected_at": datetime.now()
            }
            
            return ftp
        except Exception as e:
            self.log(f"Error al conectar a FTP {connection_name}: {str(e)}")
            return False
            
    def handle_http(self, connection_name, conn_info):
        """Maneja conexiones HTTP"""
        try:
            self.log(f"Conectando a HTTP {conn_info['host']}:{conn_info['port']}...")
            
            # Construir la URL base
            base_url = f"http://{conn_info['host']}:{conn_info['port']}"
            
            # Crear una sesión HTTP
            session = requests.Session()
            
            # Establecer autenticación básica si se proporcionaron credenciales
            if conn_info['username'] and conn_info['password']:
                session.auth = (conn_info['username'], conn_info['password'])
                
            # Comprobar la conexión
            response = session.get(base_url, timeout=10)
            response.raise_for_status()  # Lanzar excepción si hay error HTTP
            
            self.log(f"Conexión HTTP establecida con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "http",
                "session": session,
                "base_url": base_url,
                "connected_at": datetime.now()
            }
            
            return session
        except Exception as e:
            self.log(f"Error al conectar a HTTP {connection_name}: {str(e)}")
            return False
            
    def handle_https(self, connection_name, conn_info):
        """Maneja conexiones HTTPS"""
        try:
            self.log(f"Conectando a HTTPS {conn_info['host']}:{conn_info['port']}...")
            
            # Construir la URL base
            base_url = f"https://{conn_info['host']}:{conn_info['port']}"
            
            # Crear una sesión HTTPS
            session = requests.Session()
            
            # Configurar la verificación SSL
            session.verify = True  # Cambiar a False para omitir verificación
            
            # Establecer autenticación básica si se proporcionaron credenciales
            if conn_info['username'] and conn_info['password']:
                session.auth = (conn_info['username'], conn_info['password'])
                
            # Comprobar la conexión
            response = session.get(base_url, timeout=10)
            response.raise_for_status()  # Lanzar excepción si hay error HTTP
            
            self.log(f"Conexión HTTPS establecida con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "https",
                "session": session,
                "base_url": base_url,
                "connected_at": datetime.now()
            }
            
            return session
        except Exception as e:
            self.log(f"Error al conectar a HTTPS {connection_name}: {str(e)}")
            return False
            
    def handle_shadowsocks(self, connection_name, conn_info):
        """Maneja conexiones Shadowsocks"""
        try:
            self.log(f"Iniciando cliente Shadowsocks a {conn_info['host']}:{conn_info['port']}...")
            
            # Crear archivo de configuración temporal para shadowsocks
            config = {
                "server": conn_info['host'],
                "server_port": conn_info['port'],
                "password": conn_info['password'],
                "method": conn_info['extra_params'] or "aes-256-gcm",
                "local_address": "127.0.0.1",
                "local_port": 1080
            }
            
            config_file = f"ss_config_{connection_name}.json"
            with open(config_file, "w") as f:
                import json
                json.dump(config, f)
                
            # Iniciar el cliente shadowsocks
            process = subprocess.Popen(
                ["sslocal", "-c", config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar un momento para verificar si se inicia correctamente
            time.sleep(2)
            if process.poll() is not None:
                stderr = process.stderr.read().decode('utf-8')
                os.remove(config_file)
                raise Exception(f"Error al iniciar Shadowsocks: {stderr}")
                
            self.log(f"Cliente Shadowsocks iniciado con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "shadowsocks",
                "process": process,
                "config_file": config_file,
                "connected_at": datetime.now()
            }
            
            return process
        except Exception as e:
            self.log(f"Error al conectar a Shadowsocks {connection_name}: {str(e)}")
            return False
        finally:
            if os.path.exists(config_file):
                os.remove(config_file)
                self.log(f"Archivo de configuración temporal eliminado: {config_file}")
            
    def handle_v2ray(self, connection_name, conn_info):
        """Maneja conexiones V2Ray"""
        try:
            self.log(f"Iniciando cliente V2Ray a {conn_info['host']}:{conn_info['port']}...")
            
            # Crear archivo de configuración temporal para V2Ray
            config = {
                "inbounds": [{
                    "port": 1080,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "settings": {
                        "udp": True
                    }
                }],
                "outbounds": [{
                    "protocol": "vmess",
                    "settings": {
                        "vnext": [{
                            "address": conn_info['host'],
                            "port": conn_info['port'],
                            "users": [{
                                "id": conn_info['password'],
                                "alterId": 0,
                                "security": conn_info['extra_params'] or "auto"
                            }]
                        }]
                    },
                    "streamSettings": {
                        "network": "tcp"
                    }
                }]
            }
            
            config_file = f"v2ray_config_{connection_name}.json"
            with open(config_file, "w") as f:
                import json
                json.dump(config, f)
                
            # Iniciar el cliente V2Ray
            process = subprocess.Popen(
                ["v2ray", "-config", config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar un momento para verificar si se inicia correctamente
            time.sleep(2)
            if process.poll() is not None:
                stderr = process.stderr.read().decode('utf-8')
                os.remove(config_file)
                raise Exception(f"Error al iniciar V2Ray: {stderr}")
                
            self.log(f"Cliente V2Ray iniciado con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "v2ray",
                "process": process,
                "config_file": config_file,
                "connected_at": datetime.now()
            }
            
            return process
        except Exception as e:
            self.log(f"Error al conectar a V2Ray {connection_name}: {str(e)}")
            return False
        finally:
            if os.path.exists(config_file):
                os.remove(config_file)
                self.log(f"Archivo de configuración temporal eliminado: {config_file}")
            
    def handle_trojan(self, connection_name, conn_info):
        """Maneja conexiones Trojan"""
        try:
            self.log(f"Iniciando cliente Trojan a {conn_info['host']}:{conn_info['port']}...")
            
            # Crear archivo de configuración temporal para Trojan
            config = {
                "run_type": "client",
                "local_addr": "127.0.0.1",
                "local_port": 1080,
                "remote_addr": conn_info['host'],
                "remote_port": conn_info['port'],
                "password": [conn_info['password']],
                "ssl": {
                    "verify": True,
                    "verify_hostname": True,
                    "cert": "",
                    "cipher": conn_info['extra_params'] or "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
                }
            }
            
            config_file = f"trojan_config_{connection_name}.json"
            with open(config_file, "w") as f:
                import json
                json.dump(config, f)
                
            # Iniciar el cliente Trojan
            process = subprocess.Popen(
                ["trojan", "-c", config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar un momento para verificar si se inicia correctamente
            time.sleep(2)
            if process.poll() is not None:
                stderr = process.stderr.read().decode('utf-8')
                os.remove(config_file)
                raise Exception(f"Error al iniciar Trojan: {stderr}")
                
            self.log(f"Cliente Trojan iniciado con {connection_name}")
            
            # Guardar la sesión activa
            self.active_sessions[connection_name] = {
                "protocol": "trojan",
                "process": process,
                "config_file": config_file,
                "connected_at": datetime.now()
            }
            
            return process
        except Exception as e:
            self.log(f"Error al conectar a Trojan {connection_name}: {str(e)}")
            return False
        finally:
            if os.path.exists(config_file):
                os.remove(config_file)
                self.log(f"Archivo de configuración temporal eliminado: {config_file}")

    def execute_command(self):
        """Ejecuta un comando en una o todas las conexiones SSH activas"""
        if not self.active_sessions:
            print("No hay sesiones activas.")
            return
            
        # Filtrar sesiones SSH
        ssh_sessions = {name: info for name, info in self.active_sessions.items() 
                       if info.get("protocol") in ["ssh", "dropbear"]}
        
        if not ssh_sessions:
            print("No hay sesiones SSH activas para ejecutar comandos.")
            return
            
        print("\n=== Ejecutar Comando SSH ===")
        print("Sesiones SSH activas:")
        
        for idx, (name, info) in enumerate(ssh_sessions.items(), 1):
            conn_time = info["connected_at"].strftime("%H:%M:%S")
            host = self.connections[name]["host"]
            print(f"{idx}. {name} ({host}, conectado desde {conn_time})")
            
        choice = input("\nSelecciona el número de sesión, 'todas' para todas, o 'cancelar': ")
        
        if choice.lower() == 'cancelar':
            return
            
        command = input("Comando a ejecutar: ")
        if not command:
            print("Comando vacío, operación cancelada.")
            return
            
        targets = []
        if choice.lower() == 'todas':
            targets = list(ssh_sessions.keys())
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(ssh_sessions):
                    targets = [list(ssh_sessions.keys())[idx]]
                else:
                    print("Selección inválida.")
                    return
            except ValueError:
                print("Por favor, introduce un número válido o 'todas'.")
                return
                
        # Registrar resultados en el archivo de log
        for name in targets:
            try:
                client = self.active_sessions[name]["client"]
                host = self.connections[name]["host"]

                print(f"\n=== Ejecutando en {name} ({host}) ===")
                stdin, stdout, stderr = client.exec_command(command)
                
                output = stdout.read().decode('utf-8')
                errors = stderr.read().decode('utf-8')
                
                print("Salida:")
                print(output[:1000])  # Mostrar solo los primeros 1000 caracteres
                if len(output) > 1000:
                    print("... (salida truncada)")
                
                print("Errores:")
                print(errors)
                
                # Registrar en el log
                self.log(f"Comando ejecutado en {name} ({host}): {command}")
                self.log(f"Salida: {output}")
                self.log(f"Errores: {errors}")
            except Exception as e:
                error_message = f"Error al ejecutar el comando en {name}: {str(e)}"
                print(error_message)
                self.log(error_message)
            finally:
                client.close()
                del self.active_sessions[name]
                print(f"Conexión con {name} cerrada.")
                
    def check_dependencies(self):
        required_tools = ["openvpn", "wg-quick", "sslocal", "v2ray", "trojan"]
        for tool in required_tools:
            if not shutil.which(tool):
                self.log(f"Advertencia: {tool} no está instalado.")
                
    def select_protocol(self):
        print("\nProtocolos disponibles:")
        for idx, protocol in enumerate(sorted(self.supported_protocols.keys()), 1):
            default_port = self.supported_protocols[protocol]["port"]
            print(f"{idx}. {protocol.upper()} (puerto predeterminado: {default_port})")

        while True:
            try:
                protocol_idx = int(input("\nSelecciona el número del protocolo: "))
                if 1 <= protocol_idx <= len(self.supported_protocols):
                    return sorted(self.supported_protocols.keys())[protocol_idx - 1]
                else:
                    print("Selección inválida.")
            except ValueError:
                print("Por favor, introduce un número válido.")
                
    def setup_environment(self):
        """Configura el entorno instalando dependencias y verificando permisos"""
        print("\n=== Configuración del Entorno ===")
        
        try:
            # Remove problematic repository file if exists
            repo_file = '/etc/apt/sources.list.d/greaterfire-ubuntu-trojan-noble.list'
            if os.path.exists(repo_file):
                try:
                    os.remove(repo_file)
                    print("Repositorio problemático eliminado.")
                except:
                    print("No se pudo eliminar el repositorio problemático.")

            # Install Python packages first
            print("\nInstalando dependencias de Python...")
            python_packages = ["paramiko", "cryptography", "requests"]
            for package in python_packages:
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install", "--user", package], check=True)
                except:
                    print(f"Error al instalar {package}, continuando...")

            # System tools installation
            if os.name == 'posix':
                print("\nInstalando herramientas del sistema...")
                
                # Clean APT cache
                subprocess.run(["apt", "clean"], check=False)
                subprocess.run(["apt", "autoclean"], check=False)
                
                # Update package list without error stopping
                try:
                    subprocess.run(["apt", "update"], check=False)
                except:
                    pass

                # Install required tools
                tools = [
                    "openvpn",
                    "wireguard",
                    "shadowsocks-libev",
                    "v2ray"
                ]

                for tool in tools:
                    try:
                        subprocess.run(["apt", "install", "-y", tool], check=False)
                    except:
                        print(f"Error al instalar {tool}, continuando...")
                        continue

            print("\nConfiguración del entorno completada.")
            return True

        except Exception as e:
            print(f"Error durante la configuración: {str(e)}")
            print("Continuando con funcionalidad limitada...")
            return True  # Return True to allow program to continue
                
    def detect_package_manager(self):
        """Detecta el gestor de paquetes del sistema"""
        package_managers = {
            "apt-get": "apt-get install -y",
            "yum": "yum install -y",
            "dnf": "dnf install -y",
            "pacman": "pacman -S --noconfirm"
        }
        
        for pm in package_managers:
            if shutil.which(pm):
                return package_managers[pm]
        
        return None

    def install_linux_tools(self):
        """Instala las herramientas necesarias en Linux/Ubuntu"""
        if os.name != 'posix':
            print("Esta opción solo está disponible para sistemas Linux/Ubuntu")
            return

        try:
            print("\n=== Instalando herramientas en Ubuntu/Debian ===")

            # Script de instalación modificado
            bash_script = """#!/bin/bash
# Actualizar repositorios
echo "🔄 Actualizando repositorios..."
apt update -y

# Instalar dependencias básicas
echo "📦 Instalando dependencias básicas..."
apt install -y curl wget apt-transport-https ca-certificates software-properties-common

# Agregar repositorios
echo "➕ Agregando repositorios..."
# V2Ray
curl -fsSL https://raw.githubusercontent.com/v2fly/debian-install-release/main/install-release.sh | bash
# Shadowsocks
add-apt-repository universe -y

# Actualizar después de agregar repos
apt update -y

# Instalar herramientas
echo "🛠️ Instalando herramientas principales..."
tools=(
    "openvpn"
    "wireguard wireguard-tools"
    "shadowsocks-libev"
    "v2ray"
    "python3-pip python3-setuptools"
)

for tool in "${tools[@]}"; do
    echo "📥 Instalando $tool..."
    apt install -y $tool
done

# Verificar instalaciones
echo "✅ Verificando instalaciones..."
command -v openvpn >/dev/null && echo "OpenVPN ✓" || echo "OpenVPN ✗"
command -v wg >/dev/null && echo "WireGuard ✓" || echo "WireGuard ✗"
command -v ss-local >/dev/null && echo "Shadowsocks ✓" || echo "Shadowsocks ✗"
command -v v2ray >/dev/null && echo "V2Ray ✓" || echo "V2Ray ✗"
"""
        
            # Guardar el script
            script_path = "/tmp/install_tools.sh"
            with open(script_path, "w") as f:
                f.write(bash_script)
        
            # Dar permisos de ejecución
            os.chmod(script_path, 0o755)
        
            # Ejecutar el script
            subprocess.run(["bash", script_path], check=True)
        
            # Limpiar
            os.remove(script_path)
        
            print("\n✅ Instalación completada!")
            print("Todas las herramientas han sido instaladas y configuradas.")
        
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error durante la instalación: {str(e)}")
            print("Código de error:", e.returncode)
            if e.output:
                print("Salida:", e.output.decode())
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        finally:
            if os.path.exists("/tmp/install_tools.sh"):
                os.remove("/tmp/install_tools.sh")

    def vps_manager(self):
        """Administrador de VPS"""
        while True:
            print("\n=== Administrador de VPS ===")
            print("1. Monitorear recursos")
            print("2. Administrar servicios")
            print("3. Backup/Restauración")
            print("4. Firewall")
            print("5. Usuarios y permisos")
            print("6. Actualizar sistema")
            print("7. Instalar BadVPN-UDPGW")  # Nueva opción
            print("8. Volver al menú principal")

            choice = input("\nSeleccione una opción: ")

            try:
                if choice == "1":
                    self._monitor_vps_resources()
                elif choice == "2":
                    self._manage_vps_services()
                elif choice == "3":
                    self._manage_vps_backup()
                elif choice == "4":
                    self._manage_vps_firewall()
                elif choice == "5":
                    self._manage_vps_users()
                elif choice == "6":
                    self._update_vps_system()
                elif choice == "7":
                    self._install_badvpn_udpgw()  # Nueva función
                elif choice == "8":
                    break
                else:
                    print("Opción inválida")
            except Exception as e:
                print(f"Error: {str(e)}")

    def _monitor_vps_resources(self):
        """Monitorear recursos del VPS"""
        try:
            print("\n=== Monitoreando recursos ===")
            # CPU
            cpu_percent = subprocess.check_output("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'", shell=True).decode()
            # Memoria
            memory = subprocess.check_output("free -m | grep Mem:", shell=True).decode().split()
            # Disco
            disk = subprocess.check_output("df -h / | tail -1", shell=True).decode().split()
            
            print(f"CPU: {cpu_percent.strip()}%")
            print(f"Memoria: {memory[2]}/{memory[1]} MB (Usado/Total)")
            print(f"Disco: {disk[4]} usado de {disk[1]}")
            
            input("\nPresione Enter para continuar...")
        except Exception as e:
            print(f"Error al monitorear recursos: {str(e)}")

    def _manage_vps_services(self):
        """Administrar servicios del VPS"""
        while True:
            print("\n=== Administrar Servicios ===")
            print("1. Listar servicios")
            print("2. Iniciar servicio")
            print("3. Detener servicio")
            print("4. Reiniciar servicio")
            print("5. Estado de servicio")
            print("6. Volver")

            choice = input("\nSeleccione una opción: ")
            if choice == "6":
                break

            service_name = input("Nombre del servicio: ")
            try:
                if choice == "1":
                    subprocess.run(["systemctl", "list-units", "--type=service"])
                elif choice == "2":
                    subprocess.run(["systemctl", "start", service_name])
                elif choice == "3":
                    subprocess.run(["systemctl", "stop", service_name])
                elif choice == "4":
                    subprocess.run(["systemctl", "restart", service_name])
                elif choice == "5":
                    subprocess.run(["systemctl", "status", service_name])
            except Exception as e:
                print(f"Error: {str(e)}")

    def _install_badvpn_udpgw(self):
        """Instalar y configurar BadVPN-UDPGW"""
        try:
            print("\n=== Instalando BadVPN-UDPGW ===")
            
            # Script de instalación de BadVPN
            install_script = """#!/bin/bash
echo "🔄 Instalando dependencias..."
apt-get update
apt-get install -y cmake make gcc build-essential screen

echo "📥 Descargando BadVPN..."
cd /usr/local/src
wget https://github.com/ambrop72/badvpn/archive/refs/heads/master.zip
unzip master.zip
cd badvpn-master

echo "🔧 Compilando BadVPN..."
cmake -DBUILD_NOTHING_BY_DEFAULT=1 -DBUILD_UDPGW=1
make install

echo "📝 Creando script de inicio..."
cat > /usr/bin/badvpn-udpgw-start << 'EOF'
#!/bin/bash
screen -dmS badvpn badvpn-udpgw --listen-addr 127.0.0.1:7300 --max-clients 1000 --max-connections-for-client 10
EOF

chmod +x /usr/bin/badvpn-udpgw-start

echo "⚙️ Configurando servicio systemd..."
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

echo "🚀 Iniciando servicio..."
systemctl daemon-reload
systemctl enable badvpn
systemctl start badvpn

echo "✅ BadVPN-UDPGW instalado y configurado"
"""
            # Guardar y ejecutar script
            script_path = "/tmp/install_badvpn.sh"
            with open(script_path, "w") as f:
                f.write(install_script)
            
            os.chmod(script_path, 0o755)
            subprocess.run(["bash", script_path], check=True)
            
            print("✅ BadVPN-UDPGW instalado correctamente!")
            print("Puerto: 7300")
            print("Máximo de clientes: 1000")
            print("Conexiones por cliente: 10")
            
        except Exception as e:
            print(f"❌ Error al instalar BadVPN-UDPGW: {str(e)}")
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

    def print_banner(self):
        """Muestra el banner del panel"""
        version = "1.0"
        
        # Definir colores si no están definidos
        if not hasattr(self, 'WHITE'):
            self.WHITE = "\033[1;37m"
            self.GREEN = "\033[32m"
            self.RED = "\033[1;31m"
            self.YELLOW = "\033[33m"
            self.RESET = "\033[0m"
        
        banner = f"""{self.RED}
             _/|       |\_
            /  |       |  \ 
           |    \     /    |
           |  \ /     \ /  |
           | \  |     |  / |
           | \ _\_/^\_/_ / |
           |    --\//--    |
            \_  \     /  _/
              \__  |  __/
                 \ _ /
                _/   \_  {self.YELLOW}V 1.0.1{self.RED}
               / _/|\_ \ {self.YELLOW}Corp Kad Manager{self.RED}
               /   |  \   {self.YELLOW}Version: {self.GREEN}{version}{self.RED}
                 / v \ {self.RESET}
    """
        print(banner)

    def line_separator(self, length=60):
        """Imprime una línea separadora"""
        WHITE = "\033[1;37m"
        print(f"{WHITE}{'━' * length}\033[0m")

    def show_menu(self):
        """Muestra el menú principal mejorado"""
        # Definir colores
        WHITE = "\033[1;37m"
        GREEN = "\033[32m"
        RED = "\033[1;31m"
        BLUE = "\033[34m"
        RESET = "\033[0m"

        try:
            # Información del sistema
            if os.name == 'posix':
                # Linux
                distro = subprocess.check_output("lsb_release -d | cut -f2", shell=True).decode().strip()
                kernel = subprocess.check_output("uname -r", shell=True).decode().strip()
                arch = subprocess.check_output("dpkg --print-architecture", shell=True).decode().strip()
                
                # Mostrar información
                print(f"{WHITE}〢 OS: {RED}{distro:<20} ARCH: {RED}{arch:<10} KERNEL: {RED}{kernel:<15} {WHITE}〢")
            else:
                # Windows
                import platform
                distro = platform.system() + " " + platform.release()
                arch = platform.machine()
                kernel = platform.version()
                
                # Mostrar información
                print(f"{WHITE}〢 OS: {RED}{distro:<20} ARCH: {RED}{arch:<10} VERSION: {RED}{kernel:<15} {WHITE}〢")

            self.line_separator()

            # Menú de opciones
            menu_options = [
                ("1", "CONEXIONES", "Gestionar conexiones VPN/SSH"),
                ("2", "PROTOCOLOS", "SSH/OpenVPN/Wireguard/Proxy"),
                ("3", "HERRAMIENTAS", "Utilidades del sistema"),
                ("4", "MONITOR", "Estado del servidor"),
                ("5", "BADVPN", "Instalar/Configurar BadVPN"),
                ("6", "BACKUP", "Respaldo y restauración"),
                ("7", "ACTUALIZAR", "Actualizar sistema"),
                ("E", "SALIR", "Salir del panel")
            ]

            for opt, name, desc in menu_options:
                print(f"{WHITE}〢 [{GREEN}{opt}{WHITE}] {RED}{name:<15} {WHITE}{desc:<30} {WHITE}〢")

            self.line_separator()

        except Exception as e:
            print(f"Error al mostrar el menú: {str(e)}")

    def run(self):
        """Método principal para ejecutar el panel"""
        # Definir colores
        WHITE = "\033[1;37m"
        RESET = "\033[0m"
        
        os.system('clear' if os.name == 'posix' else 'cls')
        self.print_banner()
        self.load_connections()
        
        while self.running:
            try:
                self.show_menu()
                choice = input(f"\n{WHITE}[$] Seleccione una opción: {RESET}")
                
                if choice == "1":
                    self.connection_menu()
                elif choice == "2":
                    self.protocol_menu()
                elif choice == "3":
                    self.tools_menu()
                elif choice == "4":
                    self._monitor_vps_resources()
                elif choice == "5":
                    self._install_badvpn_udpgw()
                elif choice == "6":
                    self._manage_vps_backup()
                elif choice == "7":
                    self._update_vps_system()
                elif choice.upper() == "E":
                    self.running = False
                    print("Saliendo...")
                else:
                    print("Opción inválida")
                    
            except KeyboardInterrupt:
                print("\nOperación cancelada")
            except Exception as e:
                print(f"Error: {str(e)}")

    def connection_menu(self):
        """Menú de conexiones"""
        while True:
            print("\n=== Menú de Conexiones ===")
            print("1. Listar conexiones")
            print("2. Añadir conexión")
            print("3. Eliminar conexión")
            print("4. Conectar")
            print("5. Volver")
            
            choice = input("\nSeleccione una opción: ")
            
            if choice == "1":
                self.list_connections()
            elif choice == "2":
                self.add_connection()
            elif choice == "3":
                self.remove_connection()
            elif choice == "4":
                name = input("Nombre de la conexión: ")
                self.connect(name)
            elif choice == "5":
                break
            else:
                print("Opción inválida")

    def protocol_menu(self):
        """Menú de protocolos"""
        while True:
            print("\n=== Menú de Protocolos ===")
            print("1. SSH/Dropbear")
            print("2. OpenVPN")
            print("3. WireGuard")
            print("4. Proxy")
            print("5. Volver")
            
            choice = input("\nSeleccione una opción: ")
            
            if choice == "5":
                break
            else:
                print("En desarrollo...")

    def tools_menu(self):
        """Menú de herramientas"""
        while True:
            print("\n=== Menú de Herramientas ===")
            print("1. Monitor de sistema")
            print("2. Firewall")
            print("3. Usuarios")
            print("4. Backup")
            print("5. Volver")
            
            choice = input("\nSeleccione una opción: ")
            
            if choice == "1":
                self._monitor_vps_resources()
            elif choice == "5":
                break
            else:
                print("En desarrollo...")

    def _manage_vps_backup(self):
        """Gestión de backups"""
        print("\nFunción de backup en desarrollo...")

    def _update_vps_system(self):
        """Actualización del sistema"""
        print("\nFunción de actualización en desarrollo...")

if __name__ == "__main__":
    try:
        panel = MultiProtocolAdminPanel()
        if panel.setup_environment():  # Verificar que el entorno se configure correctamente
            panel.run()
        else:
            print("Error al configurar el entorno. Saliendo...")
    except KeyboardInterrupt:
        print("\nPrograma terminado por el usuario")
    except Exception as e:
        print(f"\nError crítico: {str(e)}")
        sys.exit(1)
