# Temporary Flux Scheduler Instructions

This will eventually be split out into a less platform specific model

## Get instances of scripts to use when testing

1. Copy platform and app specific scripts from ```/usr/projects/aldr/exampleScripts/flux``` to run directory
2. Update all instances of ```SCRIPT_DIR``` to point to the run directory where the script files have been stored
3. Update all instances of ```CODEDIR``` similarly to point to where the glue code repo is checked out to.

## Prepare Flux because Flux

1. On a compute/backend node, ```source ${SCRIPT_DIR}/jobEnv.sh```
2. ```flux keygen```

## Run Training Job

1. ```sbatch flux_manual.sh```

## Run Something more Meaningful

1. Edit ```${SCRIPT_DIR}/flux_${app}Training.sh``` in a similar manner to existing scripts
2. ```sbatch flux_manual.sh```

