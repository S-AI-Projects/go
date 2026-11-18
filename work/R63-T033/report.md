# R63-T033 Verification Report

- **Overall status:** PASS
- **Python version:** `3.14.6`
- **Go version:** `go version go1.27.4 darwin/arm64`
- **Reference executed subtests:** 26
- **Mutant rejected by:** `['TestHey/question_with_no_letters', 'TestHey/non-letters_with_question', 'TestHey/no_letters']`

## Checks

| Check | Status | Expected | Actual |
| --- | --- | --- | --- |
| `tests_toml_parsed` | PASS | `"total > 0"` | `27` |
| `uuid_f7bc4b92-bdff-421e-a238-ae97f230ccac_comment` | PASS | `"non-empty comment key"` | `"Validates that non-question remarks without letters default to Whatever rather than shouting; rejects mutants lacking letter-presence checks."` |
| `learner_stub_unsolved` | PASS | `{"is_unsolved": true, "differs_from_example": true}` | `{"is_unsolved": true, "differs_from_example": true}` |
| `hints_file` | PASS | `{"has_letters_guidance": true, "has_diagnostic_input": true, "does_not_leak_solution": true}` | `{"has_letters_guidance": true, "has_diagnostic_input": true, "does_not_leak_solution": true}` |
| `maintenance_doc` | PASS | `{"has_rejecting_uuid": true, "has_mutant_code": true, "has_rejected_status": true, "has_reduced_input": true}` | `{"has_rejecting_uuid": true, "has_mutant_code": true, "has_rejected_status": true, "has_reduced_input": true}` |
| `reference_go_test_exit_code` | PASS | `0` | `0` |
| `reference_go_test_executed_count` | PASS | `{"passed_count_gt_zero": true, "failed_count": 0}` | `{"passed_count": 26, "failed_count": 0}` |
| `mutant_fails_tests` | PASS | `"non-zero exit with failing subtests"` | `"exit=1, failed_count=3"` |
| `mutant_rejected_by_named_case` | PASS | `"TestHey/no_letters in failed subtests"` | `["TestHey/question_with_no_letters", "TestHey/non-letters_with_question", "TestHey/no_letters"]` |
