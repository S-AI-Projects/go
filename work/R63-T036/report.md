# R63-T036: Two-Fer Implementation Comparison Report

## Task Overview
- **Task ID:** R63-T036 (Coursework 6 of 10)
- **Exercise:** `exercises/practice/two-fer`
- **Goal:** Compare the reference string concatenation approach with an alternative `fmt.Sprintf` approach, document trade-offs and worked input in `hints.md`, and verify with automated checks.

## Approaches Evaluated

### Approach 1: Direct String Concatenation (`+`)
- **File:** `work/R63-T036/reference_concat.go` (and `.meta/example.go`)
- **Technique:** `if name == "" { name = "you" }` followed by `"One for " + name + ", one for me."`
- **Performance:**
  - Time: **53.92 ns/op**
  - Heap Memory: **0 B/op**
  - Allocations: **0 allocs/op**

### Approach 2: Formatted String (`fmt.Sprintf`)
- **File:** `work/R63-T036/alternative_sprintf.go`
- **Technique:** `fmt.Sprintf("One for %s, one for me.", name)`
- **Performance:**
  - Time: **219.6 ns/op**
  - Heap Memory: **128 B/op**
  - Allocations: **6 allocs/op**

## Benchmark Comparison Table
| Metric | Approach 1 (`+` Concatenation) | Approach 2 (`fmt.Sprintf`) | Difference |
| :--- | :--- | :--- | :--- |
| Execution Time | 53.92 ns/op | 219.6 ns/op | ~4.1x slower |
| Heap Memory | 0 B/op | 128 B/op | +128 B |
| Heap Allocations | 0 allocs/op | 6 allocs/op | +6 allocs |

## Test Outcomes
- Reference Tests Passed: 3 / 3
- Alternative Tests Passed: 3 / 3
- Learner Stub Preserved: Unsolved in `two_fer.go`
- Hints File Created: `exercises/practice/two-fer/.docs/hints.md`

## Check Summary
- [PASS] `tests_toml_cases`: All canonical test cases verified in tests.toml (expected={'total': 3, 'included': 3}, actual={'total': 3, 'included': 3})
- [PASS] `learner_stub_unsolved`: Learner stub in the working tree is unchanged and unsolved (expected={'is_unsolved': True, 'differs_from_example': True}, actual={'is_unsolved': True, 'differs_from_example': True})
- [PASS] `hints_approach_selection_present`: hints.md contains an Approach Selection section (expected=True, actual=True)
- [PASS] `hints_explains_both_approaches`: hints.md explains string concatenation and fmt.Sprintf (expected={'concat': True, 'sprintf': True}, actual={'concat': True, 'sprintf': True})
- [PASS] `hints_covers_tradeoffs_and_example`: hints.md justifies trade-offs and includes worked input without full solution code (expected={'tradeoffs': True, 'worked_example': True, 'avoids_full_solution': True}, actual={'tradeoffs': True, 'worked_example': True, 'avoids_full_solution': True})
- [PASS] `reference_tests_pass`: Reference implementation passes all enabled test cases (expected={'exit_code': 0, 'passed_gt_zero': True, 'failed': 0}, actual={'exit_code': 0, 'passed': 3, 'failed': 0})
- [PASS] `alternative_tests_pass`: Alternative fmt.Sprintf implementation passes all enabled test cases (expected={'exit_code': 0, 'passed_gt_zero': True, 'failed': 0}, actual={'exit_code': 0, 'passed': 3, 'failed': 0})
- [PASS] `benchmarks_completed`: Benchmarked both reference and alternative implementations (expected={'both_benchmarked': True}, actual={'ref': {'iterations': 22095801, 'ns_per_op': 53.92, 'bytes_per_op': 0, 'allocs_per_op': 0}, 'alt': {'iterations': 5837020, 'ns_per_op': 219.6, 'bytes_per_op': 128, 'allocs_per_op': 6}})
