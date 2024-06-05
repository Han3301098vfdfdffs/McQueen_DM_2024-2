import socket
import threading
import serial
import time

import numpy as np

# Configuración socket
#host = '192.168.113.125'
host = '192.168.1.71'
port_carriles = 65439
port_senales = 65438

direccion = None
comando = None
valor = None
espera = 2
pwmMax = 170  # Cambia este valor según tu necesidad
pwmMin = 85
velocidad1 = 0
velocidad2 = 0
in1 = 0
in2 = 0
renaudar1 = 0
renaudar2 = 0
giroderecha = 120
giroizquierda = 45
alpha = 0.1  # Factor de suavizado
previous_direccion = 90  # Valor inicial de la dirección
power = 0

# Creación de un lock para evitar conflictos en arduino.write
arduino_lock = threading.Lock()

def exponential_moving_average(prev_avg, new_value, alpha=0.1):
    return alpha * new_value + (1 - alpha) * prev_avg

def map_value_to_direccion(value):
    if value < -15 and value != None and value > -200:
        return 60
    elif 15 < value and value != None and value < 200:
        return 120
    elif -15 <= value <= 15 and value != None:
        return 90
    else:
        return 90  # Default to previous if out of bounds

def go():
    global in1, in2
    in1 = 0
    in2 = 1
    return in1, in2

def reverse():
    global in1, in2
    in1 = 1
    in2 = 0
    return in1, in2

def vel(vel1, vel2):
    global velocidad1, velocidad2
    velocidad1 = vel1
    velocidad2 = vel2
    return velocidad1, velocidad2

def actualizar():
    global in1, in2, velocidad1, velocidad2, direccion, comando, arduino, valor
    arduino.write(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{direccion}\n'.encode())
    print(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{direccion}   value = {valor}    comando = {comando}\n'.encode())

def sleep(espera):
    global pwmMin, velocidad1, velocidad2, renaudar1, renaudar2
    arduino.write(f'{in1}:{in2}:{velocidad1}:{velocidad2}:90\n'.encode())
    if in1 == 0 and in2 == 0:
        go()
        actualizar()
        if (velocidad1 == 0 or velocidad1 <= 40) and (velocidad2 == 0 or velocidad2 <= 40):
            vel(0, 0)
            actualizar()
            time.sleep(espera)
            actualizar()
            vel(pwmMin, pwmMin)
        else:
            renaudar1 = velocidad1
            renaudar2 = velocidad2
            vel(0, 0)
            actualizar()
            time.sleep(espera)
            actualizar()
            vel(renaudar1, renaudar2)
    else:
        if (velocidad1 == 0 or velocidad1 <= 40) and (velocidad2 == 0 or velocidad2 <= 40):
            vel(pwmMin, pwmMin)
            renaudar1 = velocidad1
            renaudar2 = velocidad2
            vel(0, 0)
            actualizar()
            time.sleep(espera)
            actualizar()
            vel(renaudar1, renaudar2)
        else:
            renaudar1 = velocidad1
            renaudar2 = velocidad2
            vel(0, 0)
            actualizar()
            time.sleep(espera)
            actualizar()
            vel(renaudar1, renaudar2)
def derecha():
    global in1, in2, velocidad1, velocidad2, pwmMin, direccion, valor, comando
    arduino.write(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{giroderecha}\n'.encode())
    print(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{giroderecha}   value = {valor}    comando = {comando}\n'.encode())
    time.sleep(3)

def izquierda():
    global in1, in2, velocidad1, velocidad2, pwmMin, direccion, valor, comando
    arduino.write(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{giroizquierda}\n'.encode())
    print(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{giroizquierda}   value = {valor}    comando = {comando}\n'.encode())
    time.sleep(3)

    
def rutinaderecha():
    global in1, in2, velocidad1, velocidad2, pwmMin, direccion, valor, comando
    vel(0, 0)
    time.sleep(1)
    arduino.write(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{giroderecha}\n'.encode())
    vel(pwmMin, pwmMin)
    print(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{giroderecha}   value = {valor}    comando = {comando}\n'.encode())
    time.sleep(3)


def rutinaizquierda():
    global in1, in2, velocidad1, velocidad2, pwmMin, direccion, valor, comando
    vel(0, 0)
    time.sleep(1)
    arduino.write(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{giroizquierda}\n'.encode())
    vel(pwmMin, pwmMin)
    print(f'{in1}:{in2}:{velocidad1}:{velocidad2}:{giroizquierda}   value = {valor}    comando = {comando}\n'.encode())
    time.sleep(3)

def desviar():
    vel(0, 0)
    actualizar()
    time.sleep(1)
    reverse()
    vel(pwmMin, pwmMin)
    actualizar()

def handle_carriles_connection(conn):
    global direccion, valor
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            valor = int(data.decode())
            direccion = int(map_value_to_direccion(valor))

def handle_senales_connection(conn):
    global comando
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            comando = int(data.decode('utf-8'))

def main():
    global direccion, comando, arduino, power
    senales_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    carriles_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    senales_server.bind((host, port_senales))
    carriles_server.bind((host, port_carriles))

    senales_server.listen()
    carriles_server.listen()

    
    print("Esperando conexiones...")
    
    senales_conn, _ = senales_server.accept()
    print("Conexión con senales.py exitosa")

    carriles_conn, _ = carriles_server.accept()
    print("Conexión con carriles.py exitosa")

    senales_thread = threading.Thread(target=handle_senales_connection, args=(senales_conn,))    
    carriles_thread = threading.Thread(target=handle_carriles_connection, args=(carriles_conn,))

    senales_thread.start()    
    carriles_thread.start()
    direccion = 90

    try:
        arduino = serial.Serial('/dev/ttyUSB0', 115200)  # LINUX
        # arduino = serial.Serial('COM8', 115200) #WINDOWS
        print("Conexión Establecida con ESP32")
        
        while True:
            if power == 0:
                direccion = 90
                velocidad1 = 0
                velocidad2 = 0
                actualizar()
            else:
                actualizar()
            if comando == 6:
                power = 1
                vel(pwmMin,pwmMin)
                if in1 == 0 and in2 == 0:
                    go()
            elif comando == 5:
                power = 1
                vel(pwmMin,pwmMin)
                if in1 == 0 and in2 == 0:
                    go()
            elif comando == 4:
                power = 1
                vel(pwmMax,pwmMax)
                if in1 == 0 and in2 == 0:
                    go()
            elif comando == 3:
                power = 0
                vel(0,0)
                actualizar()
                time.sleep(0.3)
            elif comando == 1:
                sleep(espera)
            elif comando == 7:
                rutinaderecha()
            elif comando == 8:
                rutinaizquierda()
            elif comando == 2:
                derecha()
            time.sleep(0.1)  # Ajusta el tiempo de espera según sea necesario
            
    except serial.SerialException as e:
        print('Error al abrir puerto serial:', e)
    finally:
        if 'arduino' in globals() and arduino.is_open:
            arduino.close()
            print("Conexión cerrada con la ESP32")
            
    senales_thread.join()
    carriles_thread.join()

if __name__ == "__main__":
    main()
