# Ledger Maintenance & Refactoring Guide

This document records the readability improvements made to the reference implementation in `exercises/practice/ledger/.meta/example.go`, contract baselines, and verification evidence.

---

## 1. Concrete Readability Improvement in Reference Solution

### Context & Problem
The `ledger` exercise challenges students to refactor deliberately convoluted, unmaintainable code into clean, idiomatic Go. The reference implementation in `.meta/example.go` must serve as an exemplary model of readable, idiomatic code.

In the previous reference implementation:
1. **Ambiguous Local State**: The `localeInfo` methods used the single-letter receiver name `f`, which was non-descriptive and obscured the type context.
2. **Convoluted String Chunking**: In `moneyToString`, integer cents were padded to a 3-character string, then sliced into substrings (`centsPart` and `rest`). A `while` loop peeled off 3-character groups from right to left into a slice `parts`, followed by a second loop that reversed `parts` into `revParts`, and finally buffered into a `bytes.Buffer`. This was opaque string-manipulation that masked simple monetary arithmetic.

### Refactoring & Simplification
- **Receiver Renaming**: Changed receiver `(f localeInfo)` to `(loc localeInfo)`, making the receiver purpose explicit.
- **Direct Domain Arithmetic**:
  - `wholeUnits := cents / 100` (clear domain representation of whole currency units: dollars/euros)
  - `fractionalCents := cents % 100` (clear domain representation of fractional cents)
- **Direct Left-to-Right Digit Grouping**:
  - Computed the leading group length with `len(wholeStr) % 3` and iterated forwards in 3-digit increments.
  - Formatted the result directly using `fmt.Sprintf("%s%s%02d", formattedWhole, decimalSep, fractionalCents)`, completely eliminating the reverse-indexing loop, intermediate reversing slice, and unnecessary `bytes.Buffer`.

### Why This Helps the Exercise
- Highlights proper separation of concerns between monetary decomposition and locale formatting.
- Reduces cognitive load for maintainers and students inspecting the reference solution.
- Retains 100% backward compatibility, exact byte-for-byte formatting across all currencies and locales, error semantics, and zero external dependencies.

---

## 2. Behavioral Baseline & Verification Cases

The refactored reference solution preserves identical behavior across all test cases, specifically anchoring on:
- **Currency & Locale Combinations**:
  - `euros` (`67318aad-af53-4f3d-aa19-1293b4d4c924`): `EUR` in `en-US`
  - `Dutch locale` (`bdc499b6-51f5-4117-95f2-43cb6737208e`): `USD` in `nl-NL`
  - `Dutch locale and euros` (`86591cd4-1379-4208-ae54-0ee2652b4670`): `EUR` in `nl-NL`
  - `Dutch negative number with 3 digits before decimal point` (`876bcec8-d7d7-4ba4-82bd-b836ac87c5d2`): `USD` in `nl-NL`
  - `American negative number with 3 digits before decimal point` (`29670d1c-56be-492a-9c5e-427e4b766309`): `USD` in `en-US`
- **Error Handling**: Retains all 6 validation error checks (invalid currency, invalid locale, invalid dates).
- **Immutability**: Input slice `entries` is never modified in place.

---

## 3. Reproduction Commands

1. **Run Full Test Suite Against Reference Solution**:
   ```bash
   # In a scratch module with .meta/example.go copied to ledger.go:
   go test -count=1 ./...
   ```

2. **Re-generate Tests from Canonical Specifications**:
   ```bash
   GO111MODULE=off go run exercises/practice/ledger/.meta/gen.go
   ```
