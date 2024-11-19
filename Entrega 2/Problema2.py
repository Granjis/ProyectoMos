# from __future__ import division
from pyomo.environ import *
import pandas as pd
from pyomo.opt import SolverFactory
import networkx as nx
import matplotlib.pyplot as plt

Model = ConcreteModel()

# Datos del Problema
numCiudades = 5
numCamiones = 3 
limCiudad = 1
ciudadOrigen = 0

# Conjuntos del Problema
N = RangeSet(0, numCiudades)
C = RangeSet(1, numCamiones)

# Parametros
df = pd.read_csv('proof_case.csv')
costo = df.to_numpy()

for i in N:
    for j in N:
        if i == j:
            costo[i][j] = 999

capacidad = {}
for i in N:
    for j in N:
        if i != j:
            capacidad[(i, j)] = limCiudad
        else:
            capacidad[(i, j)] = 0

# Variable de decisión
Model.x = Var(N, N, C, domain=Binary)

# Variables adicionales para evitar subtours (MTZ)
Model.u = Var(N, bounds=(0, numCiudades), domain=NonNegativeReals)

# Función objetivo
Model.obj = Objective(expr=sum(Model.x[i, j, f] * costo[i, j] for i in N for j in N for f in C), sense=minimize)

# Restricción 1: Cada ciudad debe ser visitada exactamente una vez
Model.res_visita = ConstraintList()
for i in N:
    if i != ciudadOrigen:
        Model.res_visita.add(expr=sum(Model.x[i, j, f] for j in N for f in C) == 1)

# Restricción 2: Flujo balanceado
Model.res_flujo = ConstraintList()
for i in N:
    if i != ciudadOrigen:
        for f in C:
            Model.res_flujo.add(expr=sum(Model.x[i, j, f] for j in N) ==
                                sum(Model.x[j, i, f] for j in N))

# Restricción 3: Cada camión sale una vez de la ciudad origen
Model.res_salida_origen = ConstraintList()
for f in C:
    Model.res_salida_origen.add(expr=sum(Model.x[ciudadOrigen, j, f] for j in N) == 1)

# # Restricción 4: Cada camión regresa una vez a la ciudad origen
# Model.res_regreso_origen = ConstraintList()
# for f in C:
#     Model.res_regreso_origen.add(expr=sum(Model.x[i, ciudadOrigen, f] for i in N if i != ciudadOrigen) == 1)

# Restricción 5: Evitar subtours utlizando MTZ
Model.res_subtours = ConstraintList()
for i in N:
    for j in N:
        if i != j and i != ciudadOrigen and j != ciudadOrigen:
            for f in C:
                Model.res_subtours.add(expr=Model.u[i] - Model.u[j] + (numCiudades-1)*Model.x[i, j, f] <= numCiudades-2)

# Solución
SolverFactory('glpk').solve(Model)

# Mostrar resultados
Model.display()
# Extraer los resultados de las rutas
routes = []
for f in C:
    for i in N:
        for j in N:
            if Model.x[i, j, f].value == 1:
                routes.append((i, j, f))

# Crear el grafo
G = nx.DiGraph()

# Añadir nodos de las ciudades
for i in N:
    G.add_node(i, label=f"Ciudad {i}")

# Añadir las rutas como aristas, diferenciando entre los camiones
for route in routes:
    i, j, f = route
    G.add_edge(i, j, camion=f"Camión {f}")

# Posicionar el grafo
pos = nx.spring_layout(G)

# Dibujar nodos
nx.draw_networkx_nodes(G, pos, node_size=700, node_color="lightblue", alpha=0.8)

# Dibujar aristas (rutas de los camiones)
colors = ['r', 'g', 'b']  # Diferentes colores para cada camión
for f in C:
    camion_routes = [(i, j) for (i, j, camion) in routes if camion == f]
    nx.draw_networkx_edges(G, pos, edgelist=camion_routes, edge_color=colors[f-1], width=2, alpha=0.8)

# Etiquetas
labels = {i: f"Ciudad {i}" for i in N}
nx.draw_networkx_labels(G, pos, labels, font_size=12)

# Mostrar el grafo
plt.title("Rutas de Camiones entre Ciudades")
plt.show()