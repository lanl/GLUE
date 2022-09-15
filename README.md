# Generic Learning User Enablement Code

The Generic Learning User Enablement Code (GLUE Code) is a modular framework designed to couple different scientific applications to support use cases including multiscale methods and various forms of machine learning. The workflow was initially designed around supporting active learning as an alternative to coupled applications to support multiscale methods but has been written in a sufficiently modular way that different machine learning methods can be utilized. Application programming interfaces (API) are available for C, C++, Fortran, and Python with support for various storage formats. The code also provides direct coupling with high performance computing job schedulers such as Slurm and Flux.

## Repository Structure

`GLUECode_Library` contains the C++ library that is meant to be linked to the coarse grain solver. This allows existing applications to couple to the `GLUECode_Service` with minimal code alterations.

`GLUECode_Service` contains the python scripts that the library communicates with and uses a combination of active learning and spawning of fine grain simulation jobs to enable and accelerate multiscale scientific applications.

## Running

`examples/sniffTest_serial.sh` demonstrates the basic workflow to run a coupled simulation.

1. Prepare a json file with the desired configuration for the `GLUECode_Service`. See `docs/inputSchema.json`
2. Use `GLUECode_Service/initTables.py` to prepare SQL tables in the specified database.
3. Start `GLUECode_Service/alInterface.py` to listen for requests from the coarse grain solver.
4. Finally, start the coarse grain solver itself.

## License

The GLUE Code is provided under a BSD-3 license. See [LICENSE](https://github.com/lanl/GLUE/blob/main/LICENSE) for more details.

© 2021. Triad National Security, LLC. All rights reserved.

This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.