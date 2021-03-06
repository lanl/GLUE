#!/bin/bash
#SBATCH -N 1

# Adjust according to your checkout
export GLUE_DIR=${PATH_TO_GLUECODE_CHECKOUT}
export BGK_DIR=${PATH_TO_BGK_CHECKOUT}
export LAMMPS_DIR=${PATH_TO_LAMMPS_INSTALL}

# Ensure required directories exist and input deck is available
export BGK_INP="H-C_test_HHM_TR 0 3"

# Control variables
export ALDR_MAX_CONCURRENT_JOBS=4

# Get any required modules
source ${GLUE_DIR}/slurmScripts/darwin-gnu.sh

# Set up database
python ${GLUE_DIR}/initTables.py -d dummy.db

# Start up Glue Code As A Service
python ${GLUE_DIR}/alInterface.py -l ${LAMMPS_DIR}/bin/lmp -u $USER -j ${ALDR_MAX_CONCURRENT_JOBS} -d dummy.db -t dummy &

# Call BGK
srun -n 1 ${BGK_DIR}/exec/MultiBGK_AL_ ${BGK_INP}

# Verify completion
echo "Finished BGK. Cleaning up"
