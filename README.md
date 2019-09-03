# Proof of Concept Glue Code

## Purpose

Currently this is a prototype of one approach for the proof of concept mechanism to link between components of the Active Learning LDRD. This approach relies on SQL for the commuinication as it is a guaranteed atomic read and write that simplifies a lot of our efforts at the cost of performance.

## Using

The important parts of the code are ```alInterface.[cpp, h, hpp, py]```. To use those the ```icf_request``` and ```icf_result``` data structures need to be updated with the appropriate inputs and outputs and so too do the portions that process the SQL operations

## Building

To build the test framework the SQLITE library must be provided. One way to do this is through spack

```spack install sqlite```

Regardless, the path to the SQLITE directory must be passed to the makefile. In the spack case this can be found with ```spack find -p sqlite```

Then, to build

```make SQLITE_DIR=${PATH_TO_SQLITE}```

## Running

### Running with BGK

#### Pre-requisites

1. Have LAMMPS built and available. Using spack: ```spack install lammps```
2. Clone and build <https://github.com/lanl/Multi-BGK> on branch ```ALDR``` using ```make ALDR```

#### Running

Initially we will assume that two seperate terminal tabs are used. In the future this will be streamlined in to a single slurm script. ```tmux``` is a useful tool for this.

On the first (BGK) tab:

1. From the BGK checkout directory, call ```python ${GLUE_CODE_DIR}/initTables.py```
2. From the BGK directory, start ```./exec/MultiBGK_AL_``` with the desired input file

On the second (Glue) tab:

From the BGK checkout directory, call ```python ${GLUE_CODE_DIR}/alInterface.py -l ${PATH_TO_LAMMPS}/bin/lmp -u $USER -j 4 -d testDB.db -t dummy```

This calls the ```alInterface.py``` script and tells it which ```LAMMPS``` binary to use. We specify that all jobs are to be launched as our current ```$USER``` and to have, at most, ```4``` concurrent SLURM jobs at once. Finally, we specify the path to the database and the tag (```dummy```) to be used to match the requests to this run.

When the run is complete, manually terminate the ```alInterface.py``` task.
