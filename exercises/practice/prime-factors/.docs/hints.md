# Hints

## General

- A prime factor is a factor that is a prime number.
- Prime numbers are natural numbers greater than 1 that have no positive divisors other than 1 and themselves.
- The number 1 has no prime factors, so passing 1 should return an empty slice.

## Go-Specific Guidance: Zero Values and Slice Initialization

In Go, variables declared without an explicit initial value receive their [zero value](https://go.dev/ref/spec#The_zero_value).

For [slice types](https://go.dev/ref/spec#Slice_types), the zero value is `nil`. 

In Go, an uninitialized slice declared as `var factors []int64` is `nil`. While `len(factors)` is 0 and `cap(factors)` is 0, `factors == nil` evaluates to `true`.

By contrast, an empty slice literal `factors := []int64{}` allocates an empty slice that is not `nil`. 

When testing with `reflect.DeepEqual` or serializing data, a `nil` slice and an empty slice `[]int64{}` are treated differently. For this reason, the reference implementation initializes `factors := []int64{}` so that when the input has no prime factors (like `n = 1`), an empty slice is returned rather than `nil`.

### Working Micro-Example: Initialized Empty Slice

```go
package main

import "fmt"

func main() {
	factors := []int64{}
	fmt.Println(len(factors) == 0)
	fmt.Println(factors != nil)
}
```

Expected output:
```text
true
true
```

### Pitfall Micro-Example: Nil Slice Zero Value

```go
package main

import (
	"fmt"
	"reflect"
)

func main() {
	var factors []int64
	fmt.Println(len(factors) == 0)
	fmt.Println(factors == nil)
	fmt.Println(reflect.DeepEqual(factors, []int64{}))
}
```

Expected output:
```text
true
true
false
```

Notice that although `len(factors) == 0` is true in both cases, `reflect.DeepEqual` between `nil` and `[]int64{}` evaluates to `false`. Initializing `factors := []int64{}` ensures consistent behavior.

### Reference Links

- [The Go Programming Language Specification: Slice types](https://go.dev/ref/spec#Slice_types)
- [The Go Programming Language Specification: The zero value](https://go.dev/ref/spec#The_zero_value)
- [Effective Go: Slices](https://go.dev/doc/effective_go#slices)
