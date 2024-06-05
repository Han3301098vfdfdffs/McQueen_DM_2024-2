import jetson_inference
import jetson_utils
import cv2
import socket

#host = '192.168.113.125'
host = '192.168.1.71'
port = 65438

# Declaramos el detector de objetos
net = jetson_inference.detectNet(argv=['--model=REDDM.onnx', '--label=labels.txt', '--input-blob=input_0', '--output-cvg=scores', '--output-bbox=boxes'])

# Configura la cámara para capturar imágenes con resolución reducida
camara = jetson_utils.videoSource("/dev/video0", argv=['--input-width=640', '--input-height=480'])

# Tamaño real de los objetos en metros
tamano_real_objetos = {
    'Class #1': 0.05,  # Por ejemplo, 7 cm
    'Class #2': 0.06,
    'Class #3': 0.047,
    'Class #4': 0.06,
    'Class #5': 0.055,
    'Class #6': 0.061,
    'Class #7': 0.04, 
    'Class #8': 0.06,  
}

# Distancia focal de la cámara (en píxeles)
# Puedes ajustar este valor según las características de tu cámara y lente
distancia_focal = 1000

# Variable para almacenar el número de clase correspondiente si se cumple la condición
V = None
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    print("Conectado a locomocion.py (senales)")
    while True:
        # Captura de frames
        img = camara.Capture()

        # Detección de objetos
        detections = net.Detect(img)

        # Reiniciar V a 0
        V = 0

        # Procesar detecciones
        if detections:
            for detect in detections:
                # Verificar si el intervalo de confianza es mayor que 0.8
                confidence = detect.Confidence
                if confidence > 0.8:
                    # Imprimir la clase detectada, el intervalo de confianza, la distancia y el valor de V
                    class_id = detect.ClassID
                    etiqueta = net.GetClassDesc(class_id)
                    
                    # Obtener las coordenadas de la caja delimitadora
                    left = int(detect.Left)
                    top = int(detect.Top)
                    right = int(detect.Right)
                    bottom = int(detect.Bottom)
                    
                    # Calcular el tamaño aparente del objeto en píxeles
                    tamano_aparente_objeto = right - left
                    
                    # Verificar si la etiqueta del objeto está en la lista de tamaños reales conocidos
                    if etiqueta in tamano_real_objetos:
                        # Obtener el tamaño real del objeto
                        tamano_real_objeto = tamano_real_objetos[etiqueta]
                        
                        # Calcular la distancia al objeto utilizando la fórmula de distancia
                        distancia = (tamano_real_objeto * distancia_focal) / tamano_aparente_objeto
                        
                        # Verificar si la distancia está entre 0.28 m y 0.35 m
                        if 0.28 <= distancia <= 0.35:
                            # Almacenar el número de clase correspondiente en la variable V
                            V = class_id
                            print(f'Detección: Clase {etiqueta}, Confidence: {confidence:.2f}, Distancia: {distancia:.2f} metros, V = {V}')

        # Si no se detecta ningún objeto que cumpla con las condiciones, imprimir un mensaje
        if V == 0:
            print("No se detectó ningún objeto que cumpla con las condiciones.")
        value = int(V)
        s.sendall(str(value).encode())
        print(f'V = {V}')
        # Mostrar la imagen utilizando OpenCV
        img_np = jetson_utils.cudaToNumpy(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGBA2BGR)
        cv2.imshow('Detecciones', img_bgr)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Imprimir la variable V
    cv2.destroyAllWindows()

