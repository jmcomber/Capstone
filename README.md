# Capstone Grupo 17 2017-2

Se asume que no se puede pasar de GAMMA bolsas, y no que se paga una multa (salía 
más fácil, hay que ver cómo adaptarlo).

Además falta modelación de fila de crossdocking (ahora se van a crossdockear instantáneamente si es que el camión está y tiene capacidad).

Restricción de velocidad de los camiones está comentada porque datos random muy exigentes hacen que el problema sea infactible.

Se definieron bloques de dos horas donde hacer recorridos para los camiones (hacerlo continuo era muy difícil, ya que se puede pasar entre 0 e infinitas veces por un arco en un intervalo cualquiera no vacío).

### Variables definidas:

- Si camión c recorre arco (i, j) en tal día y bloque horario 
x_rec = model.addVars(DIAS, CAMIONES, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.BINARY, name="x_rec")

- Cantidad de veces que camión pasa sin recoger en tal arco en tal día en tal bloque horario
x_pasa = model.addVars(DIAS, CAMIONES, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.INTEGER, lb=0, name="x_pasa")

-  ***** VARIABLE POR AHORA NO USADA: OPCIONAL ******Si camión activo en día y bloque horario
y = model.addVars(DIAS, CAMIONES, BLOQUES_HR, vtype=GRB.BINARY, name="y")

- Cantidad basura en arco de dos últimos índices en día y bloque horario
q = model.addVars(DIAS, BLOQUES_HR, range(PUNTOS), range(PUNTOS), vtype=GRB.INTEGER, lb=0, name="q")

- Cantidad basura en tal camión tal día y bloque horario
k = model.addVars(DIAS, CAMIONES, BLOQUES_HR, vtype=GRB.INTEGER, name="k")

- Si camión grande va al vertedero en tal día y bloque horario
z = model.addVars(DIAS, BLOQUES_HR, vtype=GRB.BINARY, name="z")

- Cantidad basura en camión grande en tal día y bloque horario
r = model.addVars(DIAS, BLOQUES_HR_GRANDE, vtype=GRB.INTEGER, name="r")

- Variable auxiliar de se camión pasa por centro de acopio (y se descarga, ya que por ahora se demora 0 en crossdocking)
pasa_por_acopio = model.addVars(DIAS, CAMIONES, BLOQUES_HR, vtype=GRB.BINARY, name="pasa_por_acopio")

- Variable auxiliar para resolver no linealidad de una restricción
aux = model.addVars(DIAS, CAMIONES, BLOQUES_HR, vtype=GRB.INTEGER, lb=0, name="auxiliar")


### Función objetivo:
Se puso un leve costo fijo a que un camión se ocupe en un bloque (se le paga la hora al chofer y los recolectores), y un costo variable a los recorridos (5 veces menor para cuando no se recoge). Es todo tentativo. Falta costo variable y quizás fijo de camión grande.
quicksum(x_rec[d, c, t, i, j] + 0.2 * x_pasa[d, c, t, i, j] + 0.03 * y[d, c, t] for d in DIAS for c in CAMIONES for t in BLOQUES_HR \
	for i in range(PUNTOS) for j in range(PUNTOS))
