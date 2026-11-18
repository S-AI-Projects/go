# Bob — Mutation-Driven Regression & Contract Verification (`R63-T033`)

## Summary

- **Exercise:** `exercises/practice/bob`
- **Objective:** Evaluate the regression sensitivity of the test suite by creating a deliberate mutant of the reference implementation (`.meta/example.go`), identifying the rejecting canonical test cases, and documenting the mistaken assumption and diagnostic hint.

## The Deliberate Mutant

### Mistaken Assumption
A frequent learner implementation mistake in Bob is checking for shouting using only `strings.ToUpper(remark) == remark` without verifying that the remark contains at least one alphabetic character.

In Go:
- For letters: `strings.ToUpper("A") == "A"` and `strings.ToLower("A") != strings.ToUpper("A")`
- For numbers and symbols: `strings.ToUpper("1, 2, 3") == "1, 2, 3"` and `strings.ToLower("1, 2, 3") == strings.ToUpper("1, 2, 3")`

Omitting the check for the presence of letters causes any remark composed purely of digits, whitespace, or punctuation to be falsely classified as shouting.

### Reference Code vs. Mutant Code

**Original (`.meta/example.go`):**
```go
func yelling(remark string) bool {
	return strings.ToUpper(remark) == remark && strings.ToLower(remark) != strings.ToUpper(remark)
}
```

**Mutant:**
```go
func yelling(remark string) bool {
	// Mutant: assumes ToUpper equality alone indicates shouting
	return strings.ToUpper(remark) == remark
}
```

## Rejecting Test Cases

The existing canonical test suite successfully detects and rejects this mutant with multiple assertions:

| Test UUID | Description | Input | Expected Output | Mutant Output | Status |
| --- | --- | --- | --- | --- | --- |
| `f7bc4b92-bdff-421e-a238-ae97f230ccac` | `no letters` | `"1, 2, 3"` | `"Whatever."` | `"Whoa, chill out!"` | **Fails (Rejected)** |
| `bb0011c5-cd52-4a5b-8bfb-a87b6283b0e2` | `question with no letters` | `"4?"` | `"Sure."` | `"Calm down, I know what I'm doing!"` | **Fails (Rejected)** |
| `9bfc677d-ea3a-45f2-be44-35bc8fa3753e` | `non-letters with question` | `":) ?"` | `"Sure."` | `"Calm down, I know what I'm doing!"` | **Fails (Rejected)** |

### Smallest Reduced Diagnostic Input

- **For non-question non-letter remarks:** `"1"` (smallest string where `ToUpper(s) == s` with no letters; expected: `"Whatever."`, mutant: `"Whoa, chill out!"`).
- **For questions with non-letters:** `"4?"` (smallest question where `ToUpper(s) == s` with no letters; expected: `"Sure."`, mutant: `"Calm down, I know what I'm doing!"`).

## Contract Behavior

- **Shouting Contract:** A remark is shouting if and only if it contains at least one letter and all letters are uppercase.
- **Question Contract:** A remark is a question if, after trimming trailing whitespace, it ends with a question mark (`?`).
- **Forceful Question:** A remark that is both shouting and a question replies with `"Calm down, I know what I'm doing!"`.
- **Silence Contract:** A remark that contains only whitespace replies with `"Fine. Be that way!"`.
- **Default:** Anything else replies with `"Whatever."`.
