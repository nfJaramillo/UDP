import socket
import threading
import hashlib
import os
from datetime import datetime
import time


# Puerto inicial, cada thread del servidor escuchara en un puetro diferente
# Desde el 4001 hasta la cantidad de conexiones esperadas sumando de 1 en 1
port = 4000


# Se pregunta por consola la ubicacion/nombre del archivo y luego calcula el hash
# Si el archivo no existe vuelve a preguntar
while True:
    print("Escriba el nombre del archivo a transferir (Ej. 100.txt)")
    nombreArchivo = input()
    try:
        file = open(nombreArchivo, 'rb')
        file_data = file.read()
        m = hashlib.sha256()
        m.update(file_data)
        hash = m.hexdigest()
        break
    except Exception as e :
        print(str(e))

# Se pregunta la cantidad de las conexiones por consola
print("Escriba la cantidad de conexiones (Ej. 25)  ")
cantConexiones = int(input())

#Variable para guardar la cantidad de conexiones que efectivamente se conectaron
conexionesActuales = 0

#Variable para guardar las conexiones que ya terminaron el envio
# independientemente de si fue satisfactorio o no
conexionesCompletadas = 0

# Threadlock para modificar la variable de conexiones actuales
threadlock = threading.Lock()

# Threadlock para modificar la variable de conexiones completadas
threadlock1 = threading.Lock()



# Esta es la funcion que correra cada thread
# Aqui se crear el socket, se realiza la conexion, se transmite el archivo
# se confirma la transmicion y se cierra la conexion
def escuchar (puerto):
    # Se definen las variables que compartiran los threads
    global port
    global conexionesActuales
    global conexionesCompletadas
    global logList

    # Se crea el socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Unir el socket con una direccion ip y un puerto
    s.bind(("", puerto))

    # Acepta la conexion
    data, a = s.recvfrom(1024)
    print("Conexion con: " + str(a))
    # Se guarda en el string del log de este thread, la ip y el puetro de la conexion
    logList[puerto-4001] += ("Conexion con: " + str(a)+'\n')
    # Se aumenta la variable de conexiones actuales
    with threadlock:
        conexionesActuales += 1

    # Recibe el listo del cliente
    data = s.recvfrom(5)

    # Aqui espera a que todos lo cleintes se conecten
    while conexionesActuales < cantConexiones:
        time.sleep(1)

    # Envia el hash del archivo y recibe confirmacion de la recpcion
    s.sendto(hash.encode("utf-8"), a)
    s.recvfrom(13)

    # Envia el tamano del archivo y recibe confirmacion de la recpcion
    s.sendto(str(os.path.getsize(nombreArchivo)).encode("utf-8"), a)
    s.recvfrom(12)

    # Envia el nombre del archivo
    s.sendto(nombreArchivo.encode("utf-8"), a)
    s.recvfrom(12)

    # Comienza a correr el tiempo de transmicion
    start_time = time.time()


    # Envia el archivo
    buf = 65000
    file = open(nombreArchivo, 'rb')
    file_data = file.read(buf)
    while(file_data):
        if(s.sendto(file_data,a)):
            file_data = file.read(buf)
            time.sleep(0.02)



    # Recibe la confirmacion
    resp, a = (s.recvfrom(29))
    resp = resp.decode("utf-8")
    print(resp)
    # Recibe la cantidad de paquetes que recibio el cliente
    paquetes, a = s.recvfrom(1024)
    paquetes = int(paquetes.decode("utf-8"))
    # Termina el tiempo con la recepcion de la confirmacion
    end_time = time.time()

    # Se cambia la variable indicando que termino el envio con este cliente
    with threadlock1:
        conexionesCompletadas +=1

    # Verifica si al confirmacion del hash fue satisfactoria o no y lo guarda en el log
    if resp == ("Archivo Recibido y verificado"):
        logList[puerto - 4001] += ("Entrega exitosa" + '\n')
    else:
        logList[puerto - 4001] += ("Entrega NO exitosa" + '\n')
    # Guarda el tiempo de transmicion en el log
    logList[puerto - 4001] += ("Tiempo: " + str(end_time - start_time) + '\n')
    # Guarda la cantidad de paquetes en el log
    logList[puerto - 4001] += ("Paquetes: " +str(paquetes)+ " tamano: " +str(os.path.getsize(nombreArchivo))+ '\n' +'\n')
    # Cierra la conexion con ese cliente
    s.close()



# Variable que cuenta la cantidad de threads creados
cantConexiones2 = 0
# Lista de Strings que guarda el string del log de cada cliente
logList = []
print("Escuchando...")
# Loop que creara tantos threads como conexiones se hayan indicado
while cantConexiones2<cantConexiones:
    # Aumenta el puerto en 1 para poner a escuchar a cada thread en un puerto diferente
    port +=1
    # Aumenta la variable de threads creados
    cantConexiones2 +=1
    # Anexa un string vacio a la lista
    logList.append("")
    # Crea e inicia el tread pasandole como parametro el puerto que usara
    threading.Thread(target=escuchar, args=(port,)).start()

# El tread principal esperara a que todas las transimiciones se completen
while conexionesCompletadas < cantConexiones:
    time.sleep(1)
# Se pide y formatea la fecha actual
now = datetime.now()
dt_string = now.strftime("%Y-%m-%d-%H-%M-%S")
filename = "Logs/"+str(dt_string)+"-logServidor.txt"
file = open(filename, 'w')

# Por cada string que representa un log de un cliente en la lista de log, lo escribira en el archivo
file.write("Nombre del archivo: "+ nombreArchivo +" - Tamano del archivo: "+str(os.path.getsize(nombreArchivo))+'\n'+'\n')
for log in logList:
    file.write(log)
file.close()
print("Log registrado")





