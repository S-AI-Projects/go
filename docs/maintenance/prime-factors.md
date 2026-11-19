# Prime Factors Go-Specific Guidance and Maintenance (R63-T047)

## Overview

The `prime-factors` exercise computes the prime factors of a given natural number `n int64` in increasing numerical order.
For example:
- `Factors(1)` returns `[]int64{}` (no prime factors)
- `Factors(60)` returns `[]int64{2, 2, 3, 5}`
- `Factors(93819012551)` returns `[]int64{11, 9539, 894119}`

## Language Construct: Zero Values and Slice Initialization

In the reference implementation (`.meta/example.go`), the slice of factors is declared and initialized as:
```go
factors := []int64{}
```
rather than:
```go
var factors []int64
```

### Why This Matters in Go

In Go, `var factors []int64` creates a `nil` slice (the zero value of slices).
- While built-in functions like `len()`, `cap()`, and `append()` accept `nil` slices safely, comparing a `nil` slice with `[]int64{}` using `reflect.DeepEqual` evaluates to `false`.
- The canonical test case for `n = 1` specifies an expected result of `[]int64{}`. Initializing `factors := []int64{}` guarantees that an allocated empty slice is returned.

### Micro-Examples Comparison

1. **Initialized Empty Slice (Working Behavior):**
   - Declared as `factors := []int64{}`
   - `len(factors) == 0`: `true`
   - `factors != nil`: `true`

2. **Uninitialized Nil Slice (Pitfall):**
   - Declared as `var factors []int64`
   - `len(factors) == 0`: `true`
   - `factors == nil`: `true`
   - `reflect.DeepEqual(factors, []int64{})`: `false`

## Verification

To run all canonical tests against the reference implementation and verify both micro-examples, run:
```bash
python3 work/R63-T047/check.py
```
