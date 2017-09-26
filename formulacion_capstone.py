from random import randint, random
from gurobipy import *


# Se asume que no se puede pasar de GAMMA bolsas, y no que se paga una multa (salía 
# más fácil, hay que ver cómo adaptarlo)

# Además falta modelación de fila de crossdocking (ahora se van a crossdockear instantáneamente si es 
# que el camión está)

#PARÁMETROS E INTERVALO

INFINITO = 10 ** 10 #Arcos que no existan tendrán esta distancia?

DIAS = range(7)
BLOQUES_HR = range(6) # bloques de 2 horas? Rango en el que a lo más pueda hacer un viaje.
BLOQUES_HR_GRANDE = range(7)
N = 10 # número de camiones
K_C_CHICO = 250
K_C_GRANDE = 1300
CAMIONES = range(N)
PUNTOS = 10
#ARCOS = [[i, j] for i in range(PUNTOS) for j in range(PUNTOS)]
ACOPIO = 0 

GAMMA = 10

DIST = dict()
for i in range(PUNTOS):
	DIST[i] = dict()
	for j in range(PUNTOS): # O RANGE(i)?
		if i == j:
			DIST[i][j] = 0
		# if i == PUNTOS:
		# 	if j == 0:
		# 		# DIST[i][j] = DIST[j][i] = 0.8333 # 10 mins idea y 10 de vuelta para crossdocking
		# 		DIST[i][j] = DIST[j][i] = 1 # 10 mins idea y 10 de vuelta para crossdocking
		# 	else:
		# 		DIST[i][j] = INFINITO
		# elif j == PUNTOS:
		# 	DIST[i][j] = INFINITO
		# if j < i:
		# 	DIST[i][j] = DIST[j][i]
		if random() <= 0.3: #Solo un 30% de los arcos posibles existen (ciudad no es grafo completo)
			DIST[i][j] = 100
		else:
			DIST[i][j] = INFINITO

print("Distancias listas")

BASURA = dict()
for t in DIAS:
	BASURA[t] = dict()
	for i in range(PUNTOS):
		BASURA[t][i] = dict()
		for j in range(PUNTOS): # O RANGE(i)?
			# if DIST[i][j] < INFINITO and ((i == 0 and j == PUNTOS) or (i == PUNTOS and j == 0)):
			if DIST[i][j] < INFINITO and i != j:
				if j < i:
					BASURA[t][i][j] = BASURA[t][j][i]
				else:
					BASURA[t][i][j] = int(randint(1, 9) / 2 + 0.5)
			else:
				BASURA[t][i][j] = 0

print("Basura lista")


model = Model("Primer Intento Basura")

# setParam('OutputFlag', 0)
# setParam('Heuristics', 0)


#VARIABLES

#Si tal camión recoge en tal arco en tal día en tal bloque horario
x_rec = model.addVars(DIAS, CAMIONES, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.BINARY, name="x_rec")

#Cantidad de veces que camión pasa sin recoger en tal arco en tal día en tal bloque horario
x_pasa = model.addVars(DIAS, CAMIONES, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.INTEGER, lb=0, name="x_pasa")

#Cantidad basura en arco de dos últimos índices en día y bloque horario
q = model.addVars(DIAS, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.INTEGER, lb=0, name="q")

#Cantidad basura en tal camión tal día y bloque horario
k = model.addVars(DIAS, CAMIONES, BLOQUES_HR, vtype=GRB.INTEGER, name="k")

#Si camión grande va al vertedero en tal día y bloque horario
z = model.addVars(DIAS, BLOQUES_HR, vtype=GRB.BINARY, name="z")

#Cantidad basura en camión grande en tal día y bloque horario
r = model.addVars(DIAS, BLOQUES_HR_GRANDE, vtype=GRB.INTEGER, name="r")

pasa_por_acopio = model.addVars(DIAS, CAMIONES, BLOQUES_HR, vtype=GRB.BINARY, name="pasa_por_acopio")

aux = model.addVars(DIAS, CAMIONES, BLOQUES_HR, vtype=GRB.INTEGER, lb=0, name="auxiliar")

print("Variables listas")

#RESTRICCIONES

# model.addConstrs((pasa_por_acopio[d, c, t] >= x_pasa[d, c, t, 0, PUNTOS] / 1000 \
# 	for d in DIAS for c in CAMIONES for t in BLOQUES_HR), name="alias pasa_por_acopio")

# model.addConstrs((x_rec[d, c, t, i, j] == x_rec[d, c, t, j, i] for c in CAMIONES \
# 	for t in BLOQUES_HR for d in DIAS for i in range(PUNTOS) for j in range(PUNTOS)), name="obligar no dirigido")

# model.addConstrs((x_pasa[d, c, t, i, j] == x_pasa[d, c, t, j, i] for c in CAMIONES \
# 	for t in BLOQUES_HR for d in DIAS for i in range(PUNTOS) for j in range(PUNTOS)), name="obligar no dirigido")


model.addConstrs((q[6, 5, i, j] == q[0, 0, i, j] for i in range(PUNTOS) for j in range(PUNTOS)), name="")

model.addConstrs((q[d, t, i, j] <= GAMMA for d in DIAS for t in BLOQUES_HR for i in range(PUNTOS) \
	for j in range(PUNTOS)), name="Sin multas")

model.addConstrs((q[d, 0, i, j] == q[d-1, 5, i, j] + BASURA[d][i][j] for d in range(1, 6) for i in range(PUNTOS) \
	for j in range(PUNTOS)), name="Bolsas comienzo día")

# FALLA SI GAMMA * (x_rec[d, c, t, i, j] + x_rec[d, c, t, j, i])
model.addConstrs((q[d, t, i, j] >= q[d, t-1, i, j]  - GAMMA * (x_rec[d, c, t, i, j] ) for c in CAMIONES for t in range(1, 6) \
	for d in DIAS for i in range(PUNTOS) for j in range(PUNTOS)), name="Relacion recoger y cantidad basura")

#Continuidad ciclos
model.addConstrs((quicksum(x_rec[d, c, t, i, j] + x_pasa[d, c, t, i, j] \
	for i in range(PUNTOS)) == quicksum(x_rec[d, c, t, j, i] + x_pasa[d, c, t, j, i] for i in range(PUNTOS)) \
	for d in DIAS for c in CAMIONES for t in BLOQUES_HR for j in range(PUNTOS)), name="entra lo mismo que sale")

model.addConstrs((k[d, c, t] <= K_C_CHICO for c in CAMIONES for t in BLOQUES_HR \
	for d in DIAS), name="No sobrepasar capacidad camiones chicos")

model.addConstrs((r[d, t] <= K_C_GRANDE for t in BLOQUES_HR \
	for d in DIAS), name="No sobrepasar capacidad camiones chicos")

model.addConstrs((r[d, t+1] >= r[d, t] - K_C_GRANDE * z[d, t] for t in BLOQUES_HR \
	for d in DIAS), name="Vaciar camión grande si va al vertedero")

model.addConstrs((k[d, c, t+1] >= k[d, c, t] + q[d, t, i, j] - K_C_CHICO * (1 - x_rec[d, c, t, i, j]) for t in range(5) \
	for d in DIAS for c in CAMIONES for i in range(PUNTOS) for j in range(PUNTOS)), name="Basura sube a camión que pasa")

model.addConstrs((pasa_por_acopio[d, c, t] >= x_rec[d, c, t, ACOPIO, j] for d in DIAS for c in CAMIONES \
	for t in BLOQUES_HR for j in range(PUNTOS)), name="Construcción 1")

model.addConstrs((pasa_por_acopio[d, c, t] >= x_pasa[d, c, t, ACOPIO, j] / 1000 for d in DIAS for c in CAMIONES \
	for t in BLOQUES_HR for j in range(PUNTOS)), name="Construcción 2")

model.addConstrs((k[d, c, t] >= k[d, c, t-1] - K_C_CHICO * pasa_por_acopio[d, c, t-1] for d in DIAS \
	for c in CAMIONES for t in range(1, 6)), name="Descargar en ACOPIO 1")

model.addConstrs((k[d, c, t] >= k[d, c, t-1] + q[d, t-1, i, j] - K_C_CHICO * x_rec[d, c, t-1, i, j] for d in DIAS \
	for c in CAMIONES for t in range(1, 6)), name="Descargar en ACOPIO 2")

model.addConstrs((aux[d, c, t] >= k[d, c, t] - K_C_CHICO * pasa_por_acopio[d, c, t] for d in DIAS \
	for c in CAMIONES for t in BLOQUES_HR), name="Construcción variable auxiliar para crossdocking")

model.addConstrs((r[d, t+1] >= r[d, t] + quicksum(aux[d, c, t] for c in CAMIONES) for d in DIAS \
	for t in BLOQUES_HR), name="Crossdocking")

model.addConstrs((k[d, c, t] >= k[d, c, t-1] - K_C_CHICO * (1 - z[d, t]) for d in DIAS \
	for c in CAMIONES for t in range(1, 6)), name="Crossdocking si es que está el camión grande")

#DA INFACTIBLE CON LÍMITE DE "VELOCIDAD"

# model.addConstrs((quicksum(DIST[i][j] * (1 * x_rec[d, c, t, i, j] + (1 / 8.333) * x_pasa[d, c, t, i, j]) for i in range(PUNTOS) \
# 	for j in range(PUNTOS)) <= 120 for d in DIAS for c in CAMIONES for t in BLOQUES_HR), \
# 	name="límite dists físicas en 2 horas")

print("Restricciones listas")

#FUNCIÓN OBJETIVO

obj = quicksum(x_rec[d, c, t, i, j] + 0.16 * x_pasa[d, c, t, i, j] for d in DIAS for c in CAMIONES for t in BLOQUES_HR \
	for i in range(PUNTOS) for j in range(PUNTOS))

model.setObjective(obj, GRB.MINIMIZE)

model.optimize()

for v in model.getVars():
	# if v.X != 0 and ("x_rec" in v.Varname or "x_pasa" in v.Varname):
	if v.X != 0:
		print("{} {}".format(v.Varname, v.X))

