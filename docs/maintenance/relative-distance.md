# Relative Distance: Test Generation & Maintenance Guide

## Overview
The `relative-distance` exercise computes the shortest degree of separation between two people in a family tree using breadth-first search or graph traversal.

The test cases in `exercises/practice/relative-distance/cases_test.go` are generated automatically from canonical problem specifications using the Go track generator.

---

## Generation Route & Command
The generation route proceeds as follows:
1. `configlet sync --offline --update -e relative-distance` synchronizes `tests.toml` against canonical specifications.
2. The Go generator script parses `canonical-data.json`, filters cases through `.meta/tests.toml`, and renders the Go template defined in `.meta/gen.go` via `gen/gen.go`.

### Exact Command
From the repository root:
```bash
GO111MODULE=off go run ./exercises/practice/relative-distance/.meta/gen.go
```
Or directly within the exercise directory:
```bash
cd exercises/practice/relative-distance
GO111MODULE=off go run .meta/gen.go
```

---

## Input & Output Files

### Input Files:
1. `exercises/practice/relative-distance/.meta/tests.toml`: Contains the case UUIDs and descriptions used by `gen` to select/include canonical cases.
2. `exercises/practice/relative-distance/.meta/gen.go`: Defines the Go-specific `tmpl` text template, `testCase` struct, and mapping for property `degreeOfSeparation`.
3. `gen/gen.go`: The shared track generator framework responsible for fetching or reading canonical data, filtering through `tests.toml`, executing the template, formatting with `gofmt`, and emitting output files.
4. `canonical-data.json`: The upstream source from `exercism/problem-specifications` (fetched from local checkout or via HTTP).

### Output Files:
1. `exercises/practice/relative-distance/cases_test.go`: The generated Go source file defining `testCases = []testCase{...}`.
2. `exercises/practice/relative-distance/go.mod`: Maintained module metadata.

---

## Canonical Case-to-Output Mapping

All 7 canonical cases defined in `tests.toml` map directly to the `testCase` slice in `cases_test.go`:

| Canonical UUID | Description | Inputs (`personA`, `personB`) | Expected (`Degree`, `Ok`) | Generated Struct in `cases_test.go` |
| :--- | :--- | :--- | :--- | :--- |
| `4a1ded74-5d32-47fb-8ae5-321f51d06b5b` | Direct parent-child relation | "Vera", "Tomoko" | 1, `true` | `description: "Direct parent-child relation"` |
| `30d17269-83e9-4f82-a0d7-8ef9656d8dce` | Sibling relationship | "Olga", "Yassin" | 1, `true` | `description: "Sibling relationship"` |
| `8dffa27d-a8ab-496d-80b3-2f21c77648b5` | Two degrees of separation, grandchild | "Khadija", "Rami" | 2, `true` | `description: "Two degrees of separation, grandchild"` |
| `34e56ec1-d528-4a42-908e-020a4606ee60` | Unrelated individuals | "Khadija", "Tomoko" | 0, `false` | `description: "Unrelated individuals"` |
| `93ffe989-bad2-48c4-878f-3acb1ce2611b` | Complex graph, cousins | "Khadija", "Aditi" | 4, `true` | `description: "Complex graph, cousins"` |
| `2cc2e76b-013a-433c-9486-1dbe29bf06e5` | Complex graph, no shortcut, far removed nephew | "Patrick", "Gala" | 7, `true` | `description: "Complex graph, no shortcut, far removed nephew"` |
| `46c9fbcb-e464-455f-a718-049ea3c7400a` | Complex graph, some shortcuts, cross-down and cross-up, cousins several times removed, with unrelated family tree | "Gala", "Danielle" | 6, `true` | `description: "Complex graph, some shortcuts..."` |

---

## Source of the Three Anchoring Rules

The three rules:
1. **Recreate every `description` key/value pair**
2. **Recreate every `reimplements` key/value pair, where they exist in problem-specifications**
3. **Preserve any other key/value pair**

originate directly from the Exercism `configlet sync` specification documented in `.meta/tests.toml`:
- When `configlet sync --offline --update -e relative-distance` is executed, it synchronizes keys against `problem-specifications`.
- It updates or adds canonical `description` strings.
- It recreates any `reimplements` mappings where specified in canonical data.
- It removes explicit `include = true` (since omitted implies included), while strictly preserving all user-added keys (such as `comment` or explicit `include = false` exclusions).

---

## Reproducible Regeneration Verification
Run the automated verification script:
```bash
python3 tools/course_checks/r63-t002.py
```
Or run the full course verification:
```bash
python3 work/R63-T002/check.py
```
