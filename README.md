# Proof of Concept Glue Code

## Purpose

Currently this is a prototype of one approach for the proof of concept mechanism to link between components of the Active Learning LDRD. This approach relies on SQL for the commuinication as it is a guaranteed atomic read and write that simplifies a lot of our efforts at the cost of performance.

## Using

The important parts of the code are ```alInterface.[cpp, h, hpp, py]```. To use t hse the ```icf_request``` and ```icf_result``` data structures need to be updated with the appropriate inputs and outputs and so too do the portions that process the SQL operations

## Building

To build the test framework the SQLITE library must be provided. One way to do this is through spack

```spack install sqlite```

Regardless, the path to the SQLITE directory must be passed to the makefile. In the spack case this can be found with ```spack find -p sqlite```

Then, to build

```make SQLITE_DIR=${PATH_TO_SQLITE}```
