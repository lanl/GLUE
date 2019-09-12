# Proof of Concept Glue Code

## Purpose

Currently this is a prototype of one approach for the proof of concept mechanism to link between components of the Active Learning LDRD. This approach relies on SQL for the commuinication as it is a guaranteed atomic read and write that simplifies a lot of our efforts at the cost of performance.

## Using

The important parts of the code are ```alInterface.[cpp, h, hpp, py]```. To use those the ```bgk_request``` and ```bgk_result``` data structures need to be updated with the appropriate inputs and outputs and so too do the portions that process the SQL operations

## Building

To build the test framework the SQLITE library must be provided. One way to do this is through spack

```spack install sqlite```

Regardless, the path to the SQLITE directory must be passed to the makefile. In the spack case this can be found with ```spack find -p sqlite```

Then, to build

```make SQLITE_DIR=${PATH_TO_SQLITE}```

## Running

### With BGK

1. Have LAMMPS built and available. Using spack: ```spack install lammps```
2. Clone and build <https://github.com/lanl/Multi-BGK> on branch ```ALDR``` using ```make ALDR```
3. Set up a run directory containing the appropriate BGK directories and input deck
4. Copy ```${GLUECODE_REPO_ROOT}/slurmScripts/bgkTest.sh``` into the run directory
5. Update the ```export```ed environment variables at the start of the file to match your setup
6. Update ```${GLUECODE_REPO_ROOT}/slurmScripts/jobEnv.sh``` with any additional modules or environment variables required to run
7. ```sbatch bgkTest.sh```
