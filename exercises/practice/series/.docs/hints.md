# Hints

## Go-Specific Language Guidance

### String Slicing: Bytes vs Runes

In Go, strings are read-only byte slices (`[]byte`) holding UTF-8 encoded text. The reference implementation extracts contiguous substrings using native Go string slicing expressions:
```go
s[low:high]
```
See the official [Go Language Specification on Slice expressions](https://go.dev/ref/spec#Slice_expressions) and [The Go Blog: Strings, bytes, runes and characters in Go](https://go.dev/blog/strings).

---

### Executable Micro-Examples

#### 1. Valid ASCII Substrings (The Happy Path)
Because ASCII digits (`'0'` through `'9'`) are each exactly one byte long in UTF-8, indexing by byte directly corresponds to character indexing:

```go
package main

import "fmt"

func main() {
    s := "49142"
    sub := s[0:3]
    fmt.Printf("%s\n", sub)
}
```
**Expected Output:**
```text
491
```

---

#### 2. Contrasting Pitfall: Multi-Byte Rune Boundary Slicing
If input strings contain non-ASCII runes (such as unicode symbols or non-Latin digits), a single rune occupies multiple bytes. Byte-level slicing `s[low:high]` cuts across byte boundaries rather than rune boundaries:

```go
package main

import "fmt"

func main() {
    // '€' is 3 bytes (0xE2, 0x82, 0xAC)
    s := "491€2"
    // Slicing bytes 0..4 cuts '€' after its first byte (0xE2)
    sub := s[0:4]
    fmt.Printf("%q\n", sub)
}
```
**Expected Output:**
```text
"491\xe2"
```

Because `sub` contains an incomplete multi-byte sequence, it results in an invalid UTF-8 string. For general unicode text, one must convert to `[]rune(s)` before slicing, although for ASCII digits byte-slicing $O(1)$ without heap allocation is standard.
