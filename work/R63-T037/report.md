# R63-T037: ETL Go-Specific Guidance Report

## Task Overview
- **Task ID:** R63-T037 (Coursework 7 of 10)
- **Exercise:** `exercises/practice/etl`
- **Goal:** Connect etl specification to Go by explaining the zero values of maps and initialization pitfall with executable micro-examples and official specification links.

## Language Construct Identified
- **Construct:** Map Zero Value (`nil`) and Initialization (`make(map[string]int)`).
- **In Reference:** `exercises/practice/etl/.meta/example.go` allocates the map with `out = make(map[string]int)` because the named return variable `(out map[string]int)` defaults to `nil`.
- **Pitfall:**
  - Reading a key from a `nil` map is safe and returns the zero value (`0`).
  - Writing to a `nil` map results in a runtime panic: `panic: assignment to entry in nil map`.

## Executed Micro-Examples
1. **Working Initialized Map (`work/R63-T037/micro_working.go`):**
   - Output: `1` (Expected: `1`)
2. **Pitfall Read Nil Map (`work/R63-T037/micro_pitfall_read.go`):**
   - Output: `0` (Expected: `0`)
3. **Pitfall Write Nil Map (`work/R63-T037/micro_pitfall_write.go`):**
   - Result: Panic observed (`True`)

## Reference Test Execution
- Executed Subtests: 4 / 4 passed
- Failed Subtests: 0
- Learner Stub Preserved: Unsolved in `exercises/practice/etl/etl.go`

## Check Outcomes
- [PASS] `tests_toml_cases`: All 4 canonical test cases verified in tests.toml (expected={'total': 4, 'included': 4}, actual={'total': 4, 'included': 4})
- [PASS] `learner_stub_unsolved`: Learner stub in the working tree is unchanged and unsolved (panics) (expected={'is_unsolved': True, 'differs_from_example': True}, actual={'is_unsolved': True, 'differs_from_example': True})
- [PASS] `hints_construct_and_reference_link`: hints.md explains map zero values and links to the Go language specification (expected={'construct_named': True, 'reference_link': True}, actual={'construct_named': True, 'reference_link': True})
- [PASS] `hints_micro_examples_and_outputs`: hints.md includes working and pitfall micro-examples with expected outputs while avoiding a full solution (expected={'micro_examples': True, 'outputs': True, 'avoids_full_solution': True}, actual={'micro_examples': True, 'outputs': True, 'avoids_full_solution': True})
- [PASS] `micro_example_working_output`: Working micro-example successfully initializes map and prints 1 (expected={'exit_code': 0, 'stdout': '1'}, actual={'exit_code': 0, 'stdout': '1'})
- [PASS] `micro_example_pitfall_read_output`: Pitfall reading from nil map safely returns zero value 0 (expected={'exit_code': 0, 'stdout': '0'}, actual={'exit_code': 0, 'stdout': '0'})
- [PASS] `micro_example_pitfall_write_output`: Pitfall writing to nil map triggers expected runtime panic (expected={'non_zero_exit': True, 'has_panic': True}, actual={'exit_code': 1, 'has_panic': True})
- [PASS] `reference_tests_pass`: Reference implementation passes all enabled test cases (expected={'exit_code': 0, 'passed_gt_zero': True, 'failed': 0}, actual={'exit_code': 0, 'passed': 4, 'failed': 0})
