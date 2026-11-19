# Resistor Color Duo Maintenance and Reference Refactor (R63-T044)

## Overview

The resistor color duo exercise takes a slice of color names representing bands on a resistor and returns a two digit number.

Each color corresponds to a digit from 0 to 9:
- black: 0
- brown: 1
- red: 2
- orange: 3
- yellow: 4
- green: 5
- blue: 6
- violet: 7
- grey: 8
- white: 9

## Concrete Readability Improvement

In the original reference implementation, the return statement performed map lookups and calculation in a single compact line:
```go
return 10*colorMap[colors[0]] + colorMap[colors[1]]
```

While compact, this did not make the calculation obvious for a beginner reading the code. We refactored it to:
1. Extract the tens digit into a local variable named `tens`.
2. Extract the ones digit into a local variable named `ones`.
3. Calculate and return `tens*10 + ones`.
4. Add a comment explaining the exercise invariant: only the first two color bands determine the resistor value, and extra bands like a third color are ignored.

### Code Comparison

Before:
```go
func Value(colors []string) int {
	return 10*colorMap[colors[0]] + colorMap[colors[1]]
}
```

After:
```go
// Value returns the resistance value of a resistor with the given colors.
// In resistor color duo, only the first two color bands determine the value.
// Any extra colors after the second band are ignored.
func Value(colors []string) int {
	tens := colorMap[colors[0]]
	ones := colorMap[colors[1]]
	return tens*10 + ones
}
```

## Exercise Invariant and Test Coverage

The canonical test suite contains 7 test cases in `cases_test.go`:
- Brown and black: 10
- Blue and grey: 68
- Yellow and violet: 47
- White and red: 92
- Orange and orange: 33
- Ignore additional colors: green, brown, orange gives 51
- Black and brown, one digit: 1

The test case "Ignore additional colors" (UUID `0c4fb44f-db7c-4d03-afa8-054350f156a8`) specifically verifies that a resistor with more than two colors only uses the first two bands.

## Verification

To verify that the refactored reference passes all tests and that the student starter file remains unsolved, run:
```bash
python3 work/R63-T044/check.py
```
