# Hints

## General

- In Go, a string is an immutable sequence of bytes.
- When an empty name (`""`) is passed, the function should share with `"you"` as the default recipient.

## Approach Selection

There are two primary idiomatic approaches in Go to solve this exercise:

### 1. Direct String Concatenation (`+`)

You can concatenate strings directly using the `+` operator.

- **Data Representation:** Operates directly on the primitive `string` values. You determine whether the input is empty and substitute the default string before joining.
- **Trade-offs:** Direct string concatenation is extremely efficient in Go. Because the compiler optimizes joining short literal strings, this approach executes in ~25 ns/op with zero heap allocations (`0 B/op`, `0 allocs/op`). However, when building long sentences with many dynamic variables, multiple `+` symbols can become harder to read.

### 2. Formatted String Templating (`fmt.Sprintf`)

You can use `fmt.Sprintf` from the standard `fmt` package with the `%s` format verb (e.g. `"One for %s, one for me."`).

- **Data Representation:** Relies on a format template string and argument substitution handled by Go's `fmt` engine.
- **Trade-offs:** The template string clearly reflects the final sentence structure, making it easy to read and maintain. However, `fmt.Sprintf` parses format verbs at runtime and boxes parameters into `any` (`interface{}`), requiring runtime reflection and heap allocations (~108 ns/op, `128 B/op`, `6 allocs/op`).

### Worked Example

Consider the evaluation for different inputs:
- When the input argument is `"Alice"`, the name is already non-empty, so inserting `"Alice"` yields `"One for Alice, one for me."`.
- When the input argument is `""`, your logic detects the empty string and substitutes `"you"`, producing `"One for you, one for me."`.
