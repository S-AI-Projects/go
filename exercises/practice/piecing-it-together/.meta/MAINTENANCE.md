# Maintenance Notes

## Cost Statement

The reference implementation's cost is measured in two distinct parts:

1. **Algorithmic execution time** – the time spent inside the `JigsawData` function to compute the puzzle details. This is measured by the benchmark and reported as nanoseconds per operation.
2. **Process overhead** – the time required to start the Go process and compile the package. This includes the Go toolchain startup and compilation of the test binary and is deliberately excluded from the benchmark measurements.

The implementation includes an operation table describing each step.
The algorithm has a theoretical bound of O(N) operations.


---

*This file is used by the verification script to ensure the cost statement distinguishes startup and compilation overhead.*