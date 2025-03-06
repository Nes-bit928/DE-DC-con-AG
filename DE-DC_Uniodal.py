# importamos las librerias necesarias
import numpy as np
from deap import base, creator, tools, algorithms
import random
import matplotlib.pyplot as plt
from case5 import case5

# Cargar datos del sistema de case#.py
datos_sistema = case5() # cambiamos el caso segun los datos 
bus_data = datos_sistema["bus"]
gen_data = datos_sistema["gen"]
gencost_data = datos_sistema["gencost"]
branch_data = datos_sistema["branch"]

# Extraer demanda total
demanda = np.sum(bus_data[:, 2])  # Pd de todos los buses

# Extraer datos de los generadores
num_generadores = len(gen_data)
limites_gen = [(gen_data[i, 9], gen_data[i, 8]) for i in range(num_generadores)]  # (Pmin, Pmax)
costos = [(gencost_data[i, 4], gencost_data[i, 5], gencost_data[i, 6]) for i in range(num_generadores)]  # Coeficientes de costos

penaliza = 1e6  # Pena de muerte

# Definimos las restricciones

def evalua_despachable(individuo):
    # Verificar límites para cada generador
    for i, p in enumerate(individuo):
        if p < limites_gen[i][0] or p > limites_gen[i][1]:
            return penaliza
    return 0

# Funciones de coste para los generadores
def coste_generador(p, idx):
    a, b, c = costos[idx][0], costos[idx][1], costos[idx][2]
    return a + b * p + c * (p ** 2) if p != 0 else 0

def crea_individuo():
    individuo = np.zeros(5)
    demanda_restante = demanda

    # Ordenar generadores por costo de producción (menor a mayor)
    generadores_ordenados = sorted(range(5), key=lambda i: costos[i][1])  # Índices ordenados por costo

    # Llenar los generadores en orden de menor costo a mayor
    for i in generadores_ordenados:
        if demanda_restante > 0:
            asignacion = min(limites_gen[i][1], demanda_restante)
            individuo[i] = asignacion
            demanda_restante -= asignacion

    return individuo

def fitness(individuo):
    # Verificar si se cumple la demanda
    if abs(sum(individuo) - demanda) > 1e-6:  # Tolerancia numérica
        return penaliza,
    # Evaluar límites de los generadores
    if evalua_despachable(individuo) == penaliza:
        return penaliza,
    # Calcular el coste
    coste = sum(coste_generador(individuo[i], i) for i in range(5))
    return coste,

def unico_objetivo_ga(c, m, toolbox):
    NGEN = 100
    MU = 100
    LAMBDA = MU 
    CXPB = c
    MUTPB = m
   
    pop = toolbox.ini_poblacion(n=MU)
    hof = tools.HallOfFame(1, similar=np.array_equal)
 
    stats = tools.Statistics(key=lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("std", np.std)
    stats.register("min", np.min)
    stats.register("max", np.max)
   
    log = tools.Logbook()
   
    pop, log = algorithms.eaMuPlusLambda(
        pop, toolbox, MU, LAMBDA, CXPB, MUTPB, NGEN, stats=stats, halloffame=hof, verbose=False
    )
   
    return pop, hof, log

# Configuración de DEAP
creator.create("FitnessMin", base.Fitness, weights=(-1,))
creator.create("Individual", np.ndarray, fitness=creator.FitnessMin)

toolbox = base.Toolbox()
toolbox.register("individual", tools.initIterate, creator.Individual, crea_individuo)
toolbox.register("ini_poblacion", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", fitness)
toolbox.register("mate", tools.cxTwoPoint)

def mutacion_ligada(individuo, mu, sigma, indpb):
    for i in range(len(individuo)):
        if random.random() < indpb:
            individuo[i] += random.gauss(mu, sigma)
            individuo[i] = max(0, min(individuo[i], limites_gen[i][1]))  # Recorta a los límites
    return individuo,

toolbox.register("mutate", mutacion_ligada, mu=0, sigma=5, indpb=0.2)
toolbox.register("select", tools.selTournament, tournsize = 3)

def plot_evolucion(log):
    gen = log.select("gen")
    fit_mins = log.select("min")
    fit_maxs = log.select("max")
    fit_ave = log.select("avg")

    fig, ax1 = plt.subplots()
    ax1.plot(gen, fit_mins, "b")
    ax1.plot(gen, fit_maxs, "r")
    ax1.plot(gen, fit_ave, "--k")
    condition = np.array(fit_maxs) >= np.array(fit_mins)
    ax1.fill_between(gen, fit_mins, fit_maxs, where=condition, facecolor='g', alpha = 0.2)
    ax1.set_xlabel("Generación")
    ax1.set_ylabel("Fitness")
    ax1.legend(["Min", "Max", "Avg"])
    ax1.set_ylim([12000, 20000])
    plt.grid(True)
    plt.savefig("convergencia.png", dpi= 300)  
    plt.show()  

if __name__ == "__main__":

    pop, hof, log = unico_objetivo_ga(0.7, 0.3, toolbox)

    if isinstance(hof[0], dict):
        print("Error: hof[0] es un diccionario.")
    else:
        # Extraer los valores de potencia generada
        for i, P in enumerate(hof[0]):
            C = coste_generador(P, i)
            print(f"Generador {i+1}: {P:.2f} MW  -> Costo: {C:.2f}")
        
        print(f"Total generado: {sum(hof[0]):.2f} MW")
        print(f"Fitness óptimo (Costo): {hof[0].fitness.values[0]:.2f}")

        plot_evolucion(log)