# GLUECode Service

## Summary of Scripts

Python scripts for `GLUECode_Library` to interface with active learning libraries and job schedulers to generate fine grain simulation results to enable and accelerate multiscale scientific applications.

`initTables.py` provides basic logic to set up required SQL tables in database

`alInterface.py` is the general service that polls SQL tables for requests and interfaces directly with job scheduler specified in json file.

And `genTrainingData.py` is a utility script that uses the `GLUECode_Service` infrastructure to generate training data in a manner that simultaneously takes advantage of High Performance Computing resources while minimizing wasted resources.

## Usage

The top level `examples` directory provides examples of how these scripts interact together with `genICFTrainingData.sh` demonstrating one way to populate a database with training data and `sniffTest_serial.sh` demonstrating how `alInterface.py` would interact with a coarse grain application.

## Dependencies

All required Python packages are listed in `requirements.txt`. You can install them via: `pip3 install -r requirements.txt`
