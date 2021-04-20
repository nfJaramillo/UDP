import socket
import threading
import hashlib
import time
import os
from datetime import datetime


# Puerto inicial, cada thread cliente estara en un puerto diferente
# Desde el 4001 hasta la cantidad de conexiones esperadas sumando de 1 en 1
port = 4000

# Pide la direccion del servidor por consola
print("Escriba la direccion ip del servirdor (Ej. 127.0.0.1)")
ip = input()

# Pide la cantidad de clientes por consola
print("Escriba la cantidad de clientes (Ej. 25)")
cantClientes = int(input())

# Crea una variable que contara la cantidad de clientes creados
clientesActuales = 0

#Crea una variable que cuenta cada que un cliente termina la descarga, sea exitosa o no
clientesTerminaron = 0

# Threadlock para modificar la variable de clientes terminaron
threadlock = threading.Lock()

# Funcion que ejecutaran los threads, donde ocurre la conexion, la recepcion y la confirmacion
def recibir (num):
    # Defino esta variable comun para los threads
    global clientesTerminaron
    global logList

    # Crea el socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    direccionServidor = (ip, port+num)
    # Se conecta al servidor
    s.sendto(str.encode("Hola"), direccionServidor)

    #Escribe que cliente es en el log
    logList[num-1] += ("Cliente #: " + str(num) + " - puerto: " + str(port+num) + '\n')

    #Envia el listo al servidor
    s.sendto(str.encode("Listo"), direccionServidor)

    # Recibe el hash esperado del archivo
    hash, a = s.recvfrom(1024)
    hash = hash.decode("utf-8")
    s.sendto(str.encode("Hash Recibido"), direccionServidor)

    # Recibe el tamano esperado del archivo
    tamEsperado,a = s.recvfrom(1024)
    tamEsperado = int(tamEsperado.decode("utf-8"))
    s.sendto(str.encode("Tam Recibido"), direccionServidor)

    # Recibe el nombre del archivo
    nombreArchivo, a = s.recvfrom(1024)
    nombreArchivo = nombreArchivo.decode("utf-8")
    s.sendto(str.encode("nom Recibido"), direccionServidor)

    # Crea un archivo para guardar la descarga
    filename = "ArchivosRecibidos/Cliente"+str(num)+"-Prueba-"+str(cantClientes)+"."+nombreArchivo[-3:]
    file = open(filename, 'wb')

    # Escribe el nombre y tamano esperado del archivo
    logList[num - 1] += ("Nombre del archivo: "+ filename +" - Tamano del archivo: "+str(tamEsperado)+'\n')

    # Variable que cuenta el tamano del archivo que se va recibiendo
    tam = 0
    # Contador para los paquetes que se recibieron
    contador = 0
    # Comienza a correr el tiempo de transmicion
    start_time = time.time()
    # Guarda la descarga por chunks de 512B hasta que el tamano en Bytes recibido sea igual al esperado
    while True:
        contador += 1
        s.settimeout(2)
        try:
            data, a = s.recvfrom(65000)
        except Exception as e:
            print(str(e))
            break

        tam += len(data)
        if (tam == tamEsperado):
            file.write(data)
            break
        file.write(data)
    file.close()
    print("Archivo recibido")
    # Reabrir archivo para el hash
    file = open(filename, 'rb')
    file_data = file.read()
    m = hashlib.sha256()
    m.update(file_data)
    # Calcula el hash del archivo recibido
    hash2 = m.hexdigest()

    # Confirma que sean inguales los hash y envia la confirmacion de si es correcto o no
    if(hash == hash2):
        print("El hash es igual" + " - " +"Hash recibido: " + str(hash) + " - " + "Hash calculado: " + str(hash2) )
        s.sendto(("Archivo Recibido y verificado").encode("utf-8"), direccionServidor)
        # Escribe en el log si la descarga fue exitosa
        logList[num-1] += ("Archivo Recibido y verificado" + '\n')

    else:
        print("El hash esta mal" + " - " + "Hash recibido: " + str(hash) + " - " + "Hash calculado: " + str(hash2))
        s.sendto(("Archivo Recibido y con fallo ").encode("utf-8"), direccionServidor)
        # Escribe en el log si la descarga NO fue exitosa
        logList[num-1] += ("Archivo Recibido y con fallo " + '\n')

    # Termina el tiempo con la recepcion de la confirmacion
    end_time = time.time()

    # Guarda el tiempo de transmicion en el log
    logList[num-1] += ("Tiempo: " + str(end_time - start_time) + '\n')

    # Guarda la cantidad de paquetes en el log
    logList[num-1] += ("Paquetes: " + str(contador) + " tamano descargado: " + str(os.path.getsize(filename)) + '\n' + '\n')

    # Envia la cantidad de paquetes recibidos
    s.sendto(str(contador).encode("utf-8"), direccionServidor)

    # Cierra la conexion con el servidor
    s.close()

    with threadlock:
        clientesTerminaron +=1

# Loop que crea y ejecuta tantos cleintes como fueron indicados por consola
# Les pasa por parametro un id de cliente
print("Esperando para recibir...")

# Lista de Strings que guarda el string del log de cada cliente
logList = []
while clientesActuales<cantClientes:
    # Anexa un string vacio a la lista
    logList.append("")
    clientesActuales +=1
    threading.Thread(target=recibir, args=(clientesActuales,)).start()

# El main espera a que todos los clientes terminen
while clientesTerminaron < cantClientes:
    time.sleep(1)
# Se pide y formatea la fecha actual
now = datetime.now()
dt_string = now.strftime("%Y-%m-%d-%H-%M-%S")
filename = "Logs/"+str(dt_string)+"-logCliente.txt"
file = open(filename, 'w')

# Por cada string que representa un log de un cliente en la lista de log, lo escribira en el archivo
for log in logList:
    file.write(log)
file.close()
print("Log registrado")
