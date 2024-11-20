import pandas as pd
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import csv
import math

def cargar_distancias_y_tiempos(num_clientes, num_depositos, depots, clientes):
    count = 0
    distancias = []
    tiempos = []

    for client in range(num_clientes):
        fila_distancias = []
        fila_tiempos = []

        for depo in range(num_depositos):
            count +=1
            source = (depots['Longitude'][depo], depots['Latitude'][depo])
            dest = (clientes['Longitude'][client], clientes['Latitude'][client])
            start = "{},{}".format(source[0], source[1])
            end = "{},{}".format(dest[0], dest[1])
            
            # URL de la API de OSRM
            url = 'http://router.project-osrm.org/route/v1/driving/{};{}?alternatives=false&annotations=nodes,distance,duration'.format(start, end)

            headers = { 'Content-type': 'application/json'}
            r = requests.get(url, headers=headers)
            
            if r.status_code == 200:
                routejson = r.json()
                # Asegurarse de que hay rutas válidas
                if routejson['routes']:
                    # Inicializar acumuladores de distancia y tiempo
                    distancia_total = 0.0
                    tiempo_total = 0.0
                    
                    # Recorrer todos los tramos (legs) para sumar distancias y tiempos
                    for leg in routejson['routes'][0]['legs']:
                        distancia_total += float(leg['distance'])  # Distancia en metros
                        tiempo_total += float(leg['duration'])*60    # Tiempo en minutos
                    
                    fila_distancias.append(distancia_total)
                    #print(fila_distancias)
                    fila_tiempos.append(tiempo_total)
                    #print(fila_tiempos)
                
            else:
                print(f"Error al obtener los datos para el depósito {depo} y cliente {client}. Código de estado: {r.status_code}")
                fila_distancias.append(0)
                fila_tiempos.append(0)

        distancias.append(fila_distancias)
        tiempos.append(fila_tiempos)

    # Guardar en un archivo CSV
    with open('distancias_y_tiempos.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Escribimos los encabezados (depósitos)
        encabezados = ['Cliente/Depósito'] + [f'Depósito {i+1}' for i in range(num_depositos)]
        writer.writerow(encabezados)
        
        # Escribimos las filas de distancias
        writer.writerow(['Distancia (m)'] + [f'{distancia}' for distancia in distancias[0]])
        for i in range(num_clientes):
            writer.writerow([f'Cliente {i+1}'] + distancias[i])
        
        # Escribimos las filas de tiempos
        writer.writerow(['Tiempo (s)'] + [f'{tiempo}' for tiempo in tiempos[0]])
        for i in range(num_clientes):
            writer.writerow([f'Cliente {i+1}'] + tiempos[i])

    print("Datos guardados en 'distancias_y_tiempos.csv'.")
    return distancias, tiempos

def csv_distancia_tiempo(num_depositos, num_clientes):
    # Listas para almacenar los datos
    distancias_leidas = []
    tiempos_leidos = []

    # Leer el archivo CSV y manejar la codificación
    with open('distancias_y_tiempos.csv', mode='r') as file:
        reader = csv.reader(file)
        
        # Saltar las cabeceras hasta encontrar los datos de distancias
        next(reader)  # Saltar primera fila (Cliente/Depósito, Depósito 1, ...)
        distancias_row = next(reader)  # Leer la fila con "Distancia (m)"
        
        # Procesar las filas con distancias
        for i in range(num_clientes):
            row = next(reader)
            distancias = list(map(float, row[1:num_depositos + 1]))  # Filtrar columnas de depósitos
            distancias_leidas.append(distancias)

        # Saltar hasta la fila con "Tiempo (s)"
        tiempos_row = next(reader)  # Leer la fila con "Tiempo (s)"
        
        # Procesar las filas con tiempos
        for i in range(num_clientes):
            row = next(reader)
            tiempos = list(map(float, row[1:num_depositos + 1]))  # Filtrar columnas de depósitos
            tiempos_leidos.append(tiempos)

    return distancias_leidas, tiempos_leidos


def haversine_distance(num_clientes, num_depositos, depots, clientes):
    
    # Radio de la Tierra en kilómetros
    R = 6371.0

    distancias = []
    tiempos = []

    for client in range(num_clientes):
        fila_distancias = []
        fila_tiempos = []

        for depo in range(num_depositos):

            # Convertir coordenadas de grados a radianes
            lat1_rad = depots['Latitude'][depo]
            lon1_rad = depots['Longitude'][depo]
            lat2_rad = clientes['Latitude'][client]
            lon2_rad = clientes['Longitude'][client]

            # Calcular diferencias
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad

            # Fórmula Haversiana
            a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            # Distancia en kilómetros
            distance = R * c
            time = (distance/40)*60

            fila_distancias.append(distance)
            fila_tiempos.append(time)
        distancias.append(fila_distancias)
        tiempos.append(fila_tiempos)
    return distancias, tiempos



# source_lat, source_lon = 40.7128, -74.0060  # Punto de origen (Nueva York)
# dest_lat, dest_lon = 40.7831, -73.9712  # Punto de destino (cerca de Central Park)

# # Generar la URL para la API OSRM
# start = f"{source_lat},{source_lon}"
# end = f"{dest_lat},{dest_lon}"
# url = f'http://router.project-osrm.org/route/v1/driving/{start};{end}?alternatives=false&overview=full&annotations=true'
# print(url)
# # Realizar la solicitud a la API
# headers = {'Content-type': 'application/json'}
# response = requests.get(url, headers=headers)

# # Procesar la respuesta
# if response.status_code == 200:
#     data = response.json()

#     if data.get('code') == 'Ok' and data['routes']:
#         # Obtener distancias y duraciones de 'annotation'
#         annotation = data['routes'][0]['legs'][0]['annotation']
#         distances = annotation.get('distance', [])
#         durations = annotation.get('duration', [])

#         # Sumar las distancias y duraciones si existen
#         total_distance = sum(distances)
#         total_duration = sum(durations)

#         print(f"Distancia total: {total_distance} metros")
#         print(f"Duración total: {total_duration} segundos")
#     else:
#         print("No se encontró una ruta válida entre los puntos.")
# else:
#     print(f"Error al llamar a la API. Código de estado: {response.status_code}")
#     print("Contenido de la respuesta:", response.text)