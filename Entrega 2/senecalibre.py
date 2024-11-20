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

###################################################
# CARGA DE DATOS
#################################################
clientes = pd.read_csv(".\data_generator_first_case\Proyecto Seneca Libre\clients.csv")
#vehicles = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\drone_only.csv')
#vehicles = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\ev_only.csv')
#vehicles = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\gas_car_only.csv')
vehicles = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\multi_vehicles.csv')
depots = pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\multi_depots.csv')
# depots= pd.read_csv('.\data_generator_first_case\Proyecto Seneca Libre\single_depot.csv')
vehicles_data = pd.read_csv(".\data_generator_first_case\Proyecto Seneca Libre\data_vehicles.csv")

###################################################
# DATOS Y PARAMETROS 
###################################################

# Datos del problema
num_clientes = len(clientes)
num_vehiculos = len(vehicles)
num_depositos = len(depots)

# Conjunto del problema
C = RangeSet(0, num_clientes-1)
D = RangeSet(0, num_depositos-1)
X = RangeSet(0, num_vehiculos-1)

# Parametros
condicion = False
if condicion:
    distancias_tierra, tiempos_tierra = cdt(num_clientes, num_depositos, depots, clientes)
else:
    distancias_tierra, tiempos_tierra = csv_distancia_tiempo(num_depositos, num_clientes)

distancias_vuelos, tiempos_vuelos = haversine_distance(num_clientes, num_depositos, depots, clientes)

dist_client_depo = {'Gas Car': distancias_tierra, 'EV': distancias_tierra, 'drone': distancias_vuelos}
time_client_depo = {'Gas Car': tiempos_tierra, 'EV': tiempos_tierra, 'drone': tiempos_vuelos}

vehicles_data = vehicles_data.set_index("Vehicle").to_dict(orient="index")

###################################################
# VARIABLES y FUNCIONES
###################################################

# Variable Objetivo
Model.x = Var(C, D, X, domain = Binary)

# Variables auxiliares para evitar subtours
Model.u = Var(C, domain=NonNegativeReals, bounds=(1, num_clientes - 1))

# Funciones Costos Distancia
Model.d = sum(Model.x[i, j, v] * dist_client_depo[vehicles['VehicleType'][v]][i][j] * vehicles_data[vehicles['VehicleType'][v]]['Freight Rate [COP/km]'] for i in C for j in D for v in X)

# Funcion Costos Tiempo
Model.t = sum(Model.x[i, j, v] * time_client_depo[vehicles['VehicleType'][v]][i][j] * vehicles_data[vehicles['VehicleType'][v]]['Time Rate [COP/min]'] for i in C for j in D for v in X)

# Funcion Costos Mantenimiento
Model.m = sum(Model.x[i, j, v] * vehicles_data[vehicles['VehicleType'][v]]['Daily Maintenance [COP/day]'] for i in C for j in D for v in X)

# Funcion Costos Carga
Model.c = sum(Model.x[i, j, v] * clientes['Demand'][i] * 100 for i in C for j in D for v in X)

# Funcion Objetivo General
Model.obj = Objective(expr=Model.d + Model.t + Model.m + Model.c, sense=minimize)

###################################################
# RESTRICCIONES
###################################################

# Cada cliente debe ser atendido exactamente una vez
Model.Constraint1 = ConstraintList()
for i in C:
    Model.Constraint1.add(sum(Model.x[i, j, v] for j in D for v in X) == 1)

# Un depósito solo puede ser usado por los vehículos que salgan de él
Model.Constraint2 = ConstraintList()
for j in D:
    for v in X:
        Model.Constraint2.add(sum(Model.x[i, j, v] for i in C) <= 1)

# Restricción de distancia máxima para cada vehículo
# Model.Constraint3 = ConstraintList()
# for v in X:
#     Model.Constraint3.add(
#         sum(Model.x[i, j, v] * dist_client_depo[vehicles['VehicleType'][v]][i][j] for i in C for j in D) <= vehicles['Range'][v]
#     )

# Restricción de capacidad de carga
Model.Constraint4 = ConstraintList()
for v in X:
    Model.Constraint4.add(
        sum(Model.x[i, j, v] * clientes['Demand'][i] for i in C for j in D) <= vehicles['Capacity'][v]
    )

# Restricciones MTZ para evitar subtours
Model.ConstraintSubtour = ConstraintList()
for i in C:
    for j in D:
        if i != j:
            for v in X:
                Model.ConstraintSubtour.add(
                    Model.u[i] - Model.u[j] + (num_clientes - 1) * Model.x[i, j, v] <= num_clientes - 2
                )

solver = SolverFactory('appsi_highs')
result = solver.solve(Model)
print(f"Valor final de la función objetivo: {Model.obj.expr()}")
# Mostrar las variables activas de Model.x
active_vars = []
for i in C:
    for j in D:
        for v in X:
            if Model.x[i, j, v].value > 0.5:  # Umbral de 0.5 para considerar que está activada
                active_vars.append((i, j, v, Model.x[i, j, v].value))

# Mostrar las variables activas
print(f"Total de variables activas: {len(active_vars)}")
for var in active_vars:
    print(f"Variable activa: x[{var[0]}, {var[1]}, {var[2]}] = {var[3]}")
# Model.display()