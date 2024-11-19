from pyomo.environ import ConcreteModel, Var, Objective, SolverFactory, Constraint

# Modelo de prueba lineal
model = ConcreteModel()
model.x = Var(bounds=(0, 10))
model.y = Var(bounds=(0, 10))
model.obj = Objective(expr=model.x + model.y)

# Restricción lineal simple
model.constraint = Constraint(expr=model.x + 2 * model.y <= 5)

solver = SolverFactory('appsi_highs')
result = solver.solve(model)
model.display()
