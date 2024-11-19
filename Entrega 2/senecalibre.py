from pyomo.environ import *
import pandas as pd
from pyomo.opt import SolverFactory
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import numpy
import csv
from osrm import cargar_distancias_y_tiempos as cdt
from osrm import csv_distancia_tiempo
from osrm import haversine_distance

Model = ConcreteModel()

# Carga de datos del problema
clientes = pd.read_csv(".\data_generator_first_case\Proyecto Seneca Libre\Clients.csv")
#vehicles = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\drone_only.csv')
#vehicles = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\ev_only.csv')
#vehicles = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\gas_car_only.csv')
vehicles = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\multi_vehicles.csv')
depots = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\multi_depots.csv')
#single_depot = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\single_depot.csv')
vehicles_data = pd.read_csv(".\data_generator_first_case\Proyecto Seneca Libre\data_vehicles.csv")
# print(clientes['DepotID'][0])

# Datos del problema
num_clientes = len(clientes)
num_vehiculos = len(vehicles)
num_depositos = len(depots)

# Conjunto del problema
C = RangeSet(num_clientes)
D = RangeSet(num_depositos)
X = RangeSet(num_vehiculos)

# Parametros
condicion = False
if condicion:
    distancias_tierra, tiempos_tierra = cdt(num_clientes, num_depositos, depots, clientes)
else:
    distancias_tierra, tiempos_tierra = csv_distancia_tiempo(num_depositos)

distancias_vuelos, tiempos_vuelos = haversine_distance(num_clientes, num_depositos, depots, clientes)

d = {'Gas Car': distancias_tierra, 'EV': distancias_tierra, 'drone': distancias_vuelos}
t = {'Gas Car': tiempos_tierra, 'EV': tiempos_tierra, 'drone': tiempos_vuelos}

print(vehicles_data)
# print(d[vehicles['VehicleType'][0]][0][0])
# print(distancias, tiempos)

# Variable Objetivo
Model.x = Var(C, D, X, domain = Binary)

# Funcion Objetivo
