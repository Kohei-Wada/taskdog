"""Optimization algorithm constants and default parameters."""

# Genetic Algorithm Parameters
GENETIC_POPULATION_SIZE = 20  # Number of individuals in population
GENETIC_GENERATIONS = 50  # Number of evolution generations
GENETIC_CROSSOVER_RATE = 0.8  # Probability of crossover between parents
GENETIC_MUTATION_RATE = 0.2  # Probability of mutation in offspring

# Monte Carlo Parameters
MONTE_CARLO_NUM_SIMULATIONS = 100  # Number of random simulations to run

# Round Robin Parameters
ROUND_ROBIN_MAX_ITERATIONS = 10000  # Safety limit to prevent infinite loops

# Penalty Multipliers (shared across multiple algorithms)
DEADLINE_PENALTY_MULTIPLIER = 100  # Penalty for missing deadlines in fitness calculations
