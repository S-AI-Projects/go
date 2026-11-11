# Affine Cipher: Mutation Analysis & Regression Guide

## Overview
This document records a deliberate mutant of the `affine-cipher` reference implementation, identifies the canonical test case that rejects it, and documents the expected vs actual behaviors.

---

## The Mutant

### Location
In `.meta/example.go`, within the `decryptionFunc` helper:

```go
// Original reference implementation:
func decryptionFunc(letter byte, mmi, num2 int) byte {
	temp := (mmi * (int(letter-'a') - num2)) % _totalAlphabets
	if temp < 0 {
		temp += _totalAlphabets
	}
	return byte(temp) + 'a'
}

// Deliberate Mutant:
// Omit negative remainder normalization:
func decryptionFunc(letter byte, mmi, num2 int) byte {
	temp := (mmi * (int(letter-'a') - num2)) % _totalAlphabets
	// Omitted: if temp < 0 { temp += _totalAlphabets }
	return byte(temp) + 'a'
}
```

### Underlying Defect
In Go, integer `%` is the remainder operator, which preserves the sign of the dividend. When $y < b$, $(y - b) < 0$, making `temp` negative. Casting a negative integer offset to `byte` causes underflow wrap-around (e.g. `byte(-18) + 'a'` becomes `238 + 97 = 79` (`'O'`) or invalid UTF-8 bytes).

---

## Rejecting Test Case

- **Test Name:** `decode exercism`
- **Canonical UUID:** `3f0ac7e2-ec0e-4a79-949e-95e414953438`
- **Input:**
  - `inputPhrase`: `"tytgn fjr"`
  - `a`: 3
  - `b`: 7
- **Expected Outcome:** `"exercism"` (no error)
- **Mutant Outcome:** Fails with corrupted character on letter `'f'` (where $y = 5 < b = 7$), returning an unexpected decrypted string.

### Minimal Diagnostic Input
- **Input:** `Decode("f", 3, 7)`
- **Expected:** `"i"`
- **Mutant Result:** `"\x4f"` (`"O"`) or invalid byte.

---

## Verification
Run the automated mutation regression check:
```bash
python3 work/R63-T003/check.py
```
This check verifies that:
1. The original reference implementation passes all test cases.
2. The mutated reference fails specifically on test case `3f0ac7e2-ec0e-4a79-949e-95e414953438` (`decode exercism`).
3. The learner starter file remains unsolved.
