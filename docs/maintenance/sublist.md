# Sublist — Reference Implementation Readability Refactor (`R63-T034`)

## Summary

- **Exercise:** `exercises/practice/sublist`
- **Goal:** Improve the readability of the reference implementation (`.meta/example.go`) without altering the public API or behavior.

## Concrete Readability Improvement

### Identified Ambiguity
In the original `contains(l1, l2 []int)` helper function:
1. **Ambiguous variable naming:** The parameter names `l1` and `l2` were generic, making it unclear whether `l1` was the container (haystack) or the sublist candidate (needle).
2. **Cluttered element-by-element loop:** The inner matching loop used a manual boolean accumulator (`rest := true; for j, e := range l2 { rest = rest && l1[i+j] == e }`) instead of standard slice equality.

### The Refactoring
1. **Renamed parameters:** Changed `l1, l2 []int` to `list, sublist []int`. This immediately clarifies that `sublist` is being sought within `list`.
2. **Simplified slice comparison:** Replaced the nested accumulator loop with `slices.Equal(list[i:i+len(sublist)], sublist)`. This utilizes Go's standard library `slices` package, which was already imported.
3. **Documented the exercise invariant:** Added an explicit inline comment explaining the contiguous sublist invariant:
   `// Exercise invariant: a sublist must match elements contiguously from start to end`

### Code Diff Comparison

**Before:**
```go
func contains(l1, l2 []int) bool {
	if len(l2) == 0 {
		return true
	} else if len(l2) > len(l1) {
		return false
	}
	for i := range len(l1) - len(l2) + 1 {
		if l1[i] != l2[0] {
			continue
		}
		rest := true
		for j, e := range l2 {
			rest = rest && l1[i+j] == e
		}
		if rest {
			return true
		}
	}
	return false
}
```

**After:**
```go
// contains checks if sublist appears as a contiguous subsequence within list.
func contains(list, sublist []int) bool {
	if len(sublist) == 0 {
		return true
	} else if len(sublist) > len(list) {
		return false
	}
	// Exercise invariant: a sublist must match elements contiguously from start to end
	for i := range len(list) - len(sublist) + 1 {
		if slices.Equal(list[i:i+len(sublist)], sublist) {
			return true
		}
	}
	return false
}
```

## Behavioral Equivalence

- **Public API:** `Sublist(l1, l2 []int) Relation` retains its exact signature and return values (`RelationEqual`, `RelationSublist`, `RelationSuperlist`, `RelationUnequal`).
- **Dependencies:** Uses the existing standard library `slices` package; no new dependencies.
- **Test Results:** All 18 canonical test cases pass identically before and after the refactor.
