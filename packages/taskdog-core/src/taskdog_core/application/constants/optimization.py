"""Optimization algorithm constants and default parameters."""

# Genetic Algorithm Parameters
GENETIC_POPULATION_SIZE = 20  # Number of individuals in population
GENETIC_GENERATIONS = (
    30  # Number of evolution generations (reduced from 50 for performance)
)
GENETIC_CROSSOVER_RATE = 0.8  # Probability of crossover between parents
GENETIC_MUTATION_RATE = 0.2  # Probability of mutation in offspring
GENETIC_TOURNAMENT_SIZE = 3  # Number of individuals in tournament selection
GENETIC_EARLY_TERMINATION_GENERATIONS = (
    10  # Stop if no improvement for this many generations
)

# Monte Carlo Parameters
MONTE_CARLO_NUM_SIMULATIONS = (
    50  # Number of random simulations to run (reduced from 100 for performance)
)

# Round Robin Parameters
ROUND_ROBIN_MAX_ITERATIONS = 10000  # Safety limit to prevent infinite loops

# Penalty Multipliers (shared across multiple algorithms)
DEADLINE_PENALTY_MULTIPLIER = (
    100  # Penalty for missing deadlines in fitness calculations
)

# Scheduling Precision
SCHEDULING_EPSILON = 0.001  # Minimum hours threshold for scheduling calculations
