import socket

# IP e porta que você quer testar
ip = "200.128.111.66"
port = 9000

# Cria o socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)  # tempo limite de 5 segundos

try:
    sock.connect((ip, port))
    print(f"✅ Conexão bem-sucedida com {ip}:{port}")
except socket.timeout:
    print(f"⏱️ Tempo esgotado ao tentar conectar a {ip}:{port}")
except socket.error as e:
    print(f"❌ Falha na conexão com {ip}:{port} - Erro: {e}")
finally:
    sock.close()

