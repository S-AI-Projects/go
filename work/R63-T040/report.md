# R63-T040: Secret Handshake Contract Guidance Report

## Task Overview
- **Task ID:** R63-T040 (Coursework 10 of 10)
- **Exercise:** `exercises/practice/secret-handshake`
- **Goal:** Provide guidance for secret-handshake covering subtle contract cases (inputs 16, 24, and 0), build a complete decision table matching test assertions, and document boundaries for unspecified behavior.

## Subtle Cases Walkthrough
1. **Reversing with No Actions (Input: 16 / `10000`):**
   - Active bits: Only bit 16 (reverse).
   - Unreversed actions: Empty (`[]`).
   - Outcome: Reversing an empty sequence returns empty (`[]`).
2. **Reversing with One Action (Input: 24 / `11000`):**
   - Active bits: Bit 8 (`"jump"`) and bit 16 (reverse).
   - Outcome: Reversing a single action preserves order (`["jump"]`).
3. **Zero Input (Input: 0 / `00000`):**
   - Active bits: None.
   - Outcome: Returns empty sequence (`[]`).
4. **Unspecified Behavior Statement:**
   - Higher bits beyond bit 4 (values > 31) are outside the contract.
   - Go allows returning either `nil` or `[]string{}` for empty sequences.

## Canonical Test Suite Execution
- Executed Subtests: 11 / 11 passed
- Failed Subtests: 0
- Learner Stub Preserved: Unsolved in `secret_handshake.go`

## Check Outcomes
- [PASS] `tests_toml_cases`: All 11 canonical test cases verified in tests.toml (expected={'total': 11, 'included': 11}, actual={'total': 11, 'included': 11})
- [PASS] `learner_stub_unsolved`: Learner stub in the working tree is unchanged and unsolved (panics) (expected={'is_unsolved': True, 'differs_from_example': True}, actual={'is_unsolved': True, 'differs_from_example': True})
- [PASS] `hints_decision_table_present`: hints.md contains a decision table mapping inputs to expected outputs (expected=True, actual=True)
- [PASS] `hints_covers_subtle_cases`: hints.md explains subtle cases: 16 (empty reverse), 24 (single action reverse), and 0 (zero input) (expected={'subtle_16': True, 'subtle_24': True, 'subtle_0': True}, actual={'subtle_16': True, 'subtle_24': True, 'subtle_0': True})
- [PASS] `hints_unspecified_statement`: hints.md includes an explicit statement separating specified from unspecified behavior (expected=True, actual=True)
- [PASS] `reference_tests_pass`: Reference implementation passes all enabled test cases (expected={'exit_code': 0, 'passed_gt_zero': True, 'failed': 0}, actual={'exit_code': 0, 'passed': 11, 'failed': 0})
