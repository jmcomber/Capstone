from random import randint
from gurobipy import *


# Se asume que no se puede pasar de GAMMA bolsas, y no que se paga una multa (salía 
# más fácil, hay que ver cómo adaptarlo)

# Además falta modelación de fila de crossdocking (ahora se van a crossdockear instantáneamente si es 
# que el camión está)

#PARÁMETROS E INTERVALO

INFINITO = 10 ** 25 #Arcos que no estén tendrán esta distancia?

DIAS = range(7)
BLOQUES_HR = range(6) # bloques de 2 horas? Rango en el que a lo más pueda hacer un viaje.
BLOQUES_HR_GRANDE = range(7)
N = 5 # número de camiones
K_C_CHICO = 35
K_C_GRANDE = 120
CAMIONES = range(N)
PUNTOS = 10
#ARCOS = [[i, j] for i in range(PUNTOS) for j in range(PUNTOS)]
ACOPIO = randint(0, PUNTOS) #Centro de acopio debe ser un vértice: se elige random por ahora

GAMMA = 15

DIST = dict()
for i in range(PUNTOS):
	DIST[i] = dict()
	for j in range(PUNTOS): # O RANGE(i)?
		DIST[i][j] = randint(15, 100)


BASURA = dict()
for t in DIAS:
	BASURA[t] = dict()
	for i in range(PUNTOS):
		BASURA[t][i] = dict()
		for j in range(PUNTOS): # O RANGE(i)?
			BASURA[t][i][j] = randint(1, 15)

model = Model("Primer Intento Basura")

#VARIABLES

#Si tal camión recoge en tal arco en tal día en tal bloque horario
x_rec = model.addVars(DIAS, CAMIONES, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.BINARY, name="x_rec")

#Cantidad de veces que camión pasa sin recoger en tal arco en tal día en tal bloque horario
x_pasa = model.addVars(DIAS, CAMIONES, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.INTEGER, lb=0, name="x_pasa")

#Si camión activo en día y bloque horario
y = model.addVars(DIAS, CAMIONES, BLOQUES_HR, vtype=GRB.BINARY, name="y")

#Cantidad basura en arco de dos últimos índices en día y bloque horario
q = model.addVars(DIAS, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.INTEGER, lb=0, name="q")

#Cantidad basura en tal camión tal día y bloque horario
k = model.addVars(CAMIONES, DIAS, BLOQUES_HR, vtype=GRB.INTEGER, name="k")

#Si camión grande va al vertedero en tal día y bloque horario
z = model.addVars(DIAS, BLOQUES_HR, vtype=GRB.BINARY, name="z")

#Cantidad basura en camión grande en tal día y bloque horario
r = model.addVars(DIAS, BLOQUES_HR_GRANDE, vtype=GRB.INTEGER, name="r")



#RESTRICCIONES

model.addConstrs((x_rec[d, c, t, i, j] == x_rec[d, c, t, j, i] for c in CAMIONES \
	for t in BLOQUES_HR for d in DIAS for i in range(PUNTOS) for j in range(PUNTOS)), name="obligar no dirigido")

model.addConstrs((x_pasa[d, c, t, i, j] == x_pasa[d, c, t, j, i] for c in CAMIONES \
	for t in BLOQUES_HR for d in DIAS for i in range(PUNTOS) for j in range(PUNTOS)), name="obligar no dirigido")


model.addConstrs((x_rec[d, c, t, i, j] + x_pasa[d, c, t, i, j] <= 1000 * y[d, c, t] for c in CAMIONES \
	for t in BLOQUES_HR for d in DIAS for i in range(PUNTOS) for j in range(PUNTOS)), name="activacion y")

model.addConstrs((q[6, 5, i, j] == q[0, 0, i, j] for i in range(PUNTOS) for j in range(PUNTOS)), name="")

model.addConstrs((q[d, t, i, j] <= GAMMA for d in DIAS for t in BLOQUES_HR for i in range(PUNTOS) \
	for j in range(PUNTOS)), name="Sin multas")

model.addConstrs((q[d, 0, i, j] == q[d-1, 5, i, j] + BASURA[d][i][j] for d in range(1, 6) for i in range(PUNTOS) \
	for j in range(PUNTOS)), name="Bolsas comienzo día")

model.addConstrs((q[d, t, i, j] >= q[d, t-1, i, j]  - GAMMA * x_rec[d, c, t, i, j] for c in CAMIONES for t in range(1, 6) \
	for d in DIAS for i in range(PUNTOS) for j in range(PUNTOS)), name="Relacion recoger y cantidad basura")

#Continuidad ciclos

#1000 en verdad es mucho menos
model.addConstrs((x_rec[d, c, t, ACOPIO, j] + x_pasa[d, c, t, ACOPIO, j] <= 1000 * y[d, c, t] for c in CAMIONES \
	for t in BLOQUES_HR for d in DIAS for j in range(PUNTOS)), name="que ciclo pase por en acopio")

# model.addConstrs((x_rec[d, c, t, i, ACOPIO] + x_pasa[d, c, t, i, ACOPIO] <= 1000 * y[c, t, d] for c in CAMIONES \
# 	for t in BLOQUES_HR for d in DIAS for i in PUNTOS), name="que ciclo termine en acopio")
#ESTA NO ES NECESARIA PORQUE SALE DE LA DE ARRIBA CON LA DE ABAJO (SI ENTRA A ACOPIO VA A SALIR DE ACOPIO, COMO EN TODOS LOS PUNTOS)

model.addConstrs(( quicksum(x_rec[d, c, t, i, j] + x_pasa[d, c, t, i, j] \
	for i in range(PUNTOS)) == quicksum(x_rec[d, c, t, j, i] + x_pasa[d, c, t, j, i] for i in range(PUNTOS)) \
	for d in DIAS for c in CAMIONES for t in BLOQUES_HR), name="entra lo mismo que sale")


model.addConstrs((k[c, d, t] <= K_C_CHICO for c in CAMIONES for t in BLOQUES_HR \
	for d in DIAS), name="No sobrepasar capacidad camiones chicos")

model.addConstrs((r[d, t] <= K_C_GRANDE for t in BLOQUES_HR \
	for d in DIAS), name="No sobrepasar capacidad camiones chicos")

# Faltan: relación de recoger con cantidad de basura en camión chico (q, x_rec y k), transferencia a camión grande 
# (k, r y {(x_rec + x_pasa) en ACOPIO})

model.addConstrs((r[d, t+1] >= r[d, t] - K_C_GRANDE for t in BLOQUES_HR \
	for d in DIAS), name="Vaciar camión grande si va al vertedero")




obj = quicksum(x_rec[d, c, t, i, j] + 0.2 * x_pasa[d, c, t, i, j] + 0.03 * y[d, c, t] for d in DIAS for c in CAMIONES for t in BLOQUES_HR \
	for i in range(PUNTOS) for j in range(PUNTOS))

model.setObjective(obj, GRB.MINIMIZE)

model.optimize()

# for v in model.getVars():
# 	if v.X != 0:
# 		print("{} {}".format(v.Varname, v.X))

