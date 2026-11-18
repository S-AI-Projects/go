# R63-T035 Verification Report

- **Overall status:** PASS
- **Python version:** `3.14.6`
- **Go version:** `go version go1.27.4 darwin/arm64`
- **Reference executed subtests:** 54
- **Scaling measurements:** {"Small": {"tokens": 3, "median_ns": 346, "reps": [308, 332, 346, 353, 377]}, "Medium": {"tokens": 9, "median_ns": 795, "reps": [650, 659, 795, 847, 1142]}, "Large": {"tokens": 27, "median_ns": 1869, "reps": [1414, 1648, 1869, 1910, 1994]}}

## Checks

| Check | Status | Expected | Actual |
| --- | --- | --- | --- |
| `tests_toml_parsed` | PASS | `"total > 0 and included > 0"` | `{"total": 55, "included": 54, "excluded": 1}` |
| `learner_stub_unsolved` | PASS | `{"is_unsolved": true, "differs_from_example": true}` | `{"is_unsolved": true, "differs_from_example": true}` |
| `example_complexity_comment` | PASS | `{"has_time_complexity": true, "has_space_complexity": true, "has_invariant": true}` | `{"has_time_complexity": true, "has_space_complexity": true, "has_invariant": true}` |
| `maintenance_doc` | PASS | `{"has_three_sizes": true, "has_repetitions": true, "has_cost_statement": true, "has_limits": true}` | `{"has_three_sizes": true, "has_repetitions": true, "has_cost_statement": true, "has_limits": true}` |
| `reference_go_test_exit_code` | PASS | `0` | `0` |
| `reference_go_test_executed_count` | PASS | `{"passed_count_gt_zero": true, "failed_count": 0}` | `{"passed_count": 54, "failed_count": 0}` |
| `scaling_study_measurements` | PASS | `{"three_sizes_measured": true, "returncode": 0}` | `{"measured_sizes": ["Small", "Medium", "Large"], "returncode": 0}` |
