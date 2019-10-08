#!/usr/bin/env python3

"""
Samples a mesh grid in the 2D EPP-EPS parameter space.
No MPI; different points are simulated in parallel using Python multiprocessing.

Call with double dash to specify negative values for the required positional arguments, for example:
run_grid.py -- 1.0 1.0 -3.5,-3.0
"""

from multiprocessing import Pool, current_process, cpu_count
from itertools import product
import argparse

from Simulation import Simulation


# We use a function with a global var here over a closure in __main__ because non-module level functions are not
# callable by Pool.starmap for some reason
def start_sim(epp: float, eps: float, pmu: float) -> None:
	if args.pressure is not None:
		pmu_choice = 'p'
	elif args.chemical_potential is not None:
		pmu_choice = 'mu'
	sim = Simulation(args.lammps_path, args.run, pmu_choice, args.dry_run, current_process().name)
	sim.sample_coord(epp, eps, pmu)


def init_pool(args_dict):
	global args
	args = args_dict


if __name__ == '__main__':
	# Parse CLI arguments
	parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument("epp", type=lambda s: [float(i) for i in s.split(',')],
	                    help="Comma-separated list of Epp values")
	parser.add_argument("eps", type=lambda s: [float(i) for i in s.split(',')],
	                    help="Comma-separated list of Eps values")

	pmu = parser.add_mutually_exclusive_group(required=True)
	pmu.add_argument("-p", "--pressure", type=lambda s: [float(i) for i in s.split(',')],
	                 help="Comma-separated list of pressure values")
	pmu.add_argument("-mu", "--chemical-potential", type=lambda s: [float(i) for i in s.split(',')],
	                 help="Comma-separated list of chemical potential values")

	parser.add_argument("--dry-run", action="store_true", help="Don't actually do anything productive.")
	parser.add_argument("-l", "--lammps-path", default='lmp_daily',
	                    help="Path to the LAMMPS binary. May be a command, like \"mpirun lmp\"")
	parser.add_argument("-r", "--run", type=int, default=9000000, help="Run GCMC for n timesteps")
	args = parser.parse_args()

	if args.pressure is not None:
		pmu = args.pressure
	elif args.chemical_potential is not None:
		pmu = args.chemical_potential
	
	# Create cartesian product of two parameters. Returns list of tuples (epp, eps)
	coordList = list(product(args.epp, args.eps, pmu))

	print("Got {} jobs, distributed over {} workers:".format(len(coordList), cpu_count()))
	print(*coordList, sep="\n")

	# Create pool of number of cores workers
	with Pool(cpu_count(), initializer=init_pool, initargs=(args,)) as p:
		p.starmap(start_sim, coordList)
