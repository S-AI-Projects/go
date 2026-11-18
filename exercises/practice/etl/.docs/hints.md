# Hints

## General

- Your task is to transform a legacy format of Scrabble scores into a modern one-to-one mapping.
- Each uppercase letter string in the input slice needs to be converted to lowercase. The `strings.ToLower` function in the standard library can help.

## Go-Specific Guidance: Zero Values and Map Initialization

In Go, variables declared without an explicit initial value are given their [zero value](https://go.dev/ref/spec#The_zero_value).

For [map types](https://go.dev/ref/spec#Map_types), the zero value is `nil`. A `nil` map behaves differently when reading versus writing:

- **Reading** from a `nil` map is completely safe and returns the zero value of the value type (`0` for `int`, `""` for `string`, etc.).
- **Writing** to a `nil` map is not allowed and immediately causes a runtime panic: `panic: assignment to entry in nil map`.

Because `Transform` constructs and returns a new `map[string]int`, attempting to assign keys to an uninitialized map will cause a panic. You must allocate the map first using `make(map[string]int)` or a map literal `map[string]int{}`.

### Micro-Example: Initialized Map (Expected Working Behavior)

```go
package main

import "fmt"

func main() {
	out := make(map[string]int)
	out["a"] = 1
	fmt.Println(out["a"])
}
```

Expected output:
```text
1
```

### Pitfall: Zero-Value (Nil) Map

```go
package main

import "fmt"

func main() {
	var out map[string]int // out is nil (zero value)
	fmt.Println(out["a"])  // Reading returns 0 (the zero value of int)
	out["a"] = 1          // Writing panics: assignment to entry in nil map
}
```

Expected output:
```text
0
panic: assignment to entry in nil map
```

### Reference

- [The Go Programming Language Specification: The zero value](https://go.dev/ref/spec#The_zero_value)
- [The Go Programming Language Specification: Map types](https://go.dev/ref/spec#Map_types)
- [Effective Go: Maps](https://go.dev/doc/effective_go#maps)
