# GLUECode Library

To build the `GLUECode_Library`, simply call `cmake` with this directory used for configuration. The only non-standard variable is `SOLVER_SIDE_DB` and is used to specify the desired SQL backend.

By default, the `GLUECode_Library` requires a C++ compiler supporting the `c++14` standard as well as MPI.

Currently `SQLITE` is the only supported backend and applies a dependency of `SQLite3`.

The resulting `libGLUECode` should be linked to the coarse grain solver with `alInterface.h` and `alInteface_f.mod` providing the user interface.
