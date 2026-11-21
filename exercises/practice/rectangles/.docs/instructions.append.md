# Instructions append

## Implementation

### Rune versus Byte Handling in Go

When implementing this exercise in Go, consider how string characters are accessed and compared.

In Go:
- A `string` is a read-only slice of bytes (`[]byte`).
- Indexing a string with `s[i]` produces a single `byte` (`uint8`), representing the byte at offset `i`, rather than a `rune` (`int32` Unicode code point).
- The maintained reference implementation in `.meta/example.go` uses direct **byte indexing** of strings:
  ```go
  s := diagram[rowIndex][i]
  if s != '+' && s != '-' {
      return false
  }
  ```
  and checks corners directly via byte comparison:
  ```go
  if diagram[y][x] == '+'
  ```

#### Why This Works for This Exercise

The rectangles specification defines diagrams using standard 7-bit ASCII characters:
- Corners: `+` (byte value 43)
- Horizontal lines: `-` (byte value 45)
- Vertical lines: `|` (byte value 124)
- Spaces: `' '` (byte value 32)

In UTF-8 (Go's standard string encoding), every ASCII character occupies exactly one byte (0x00 to 0x7F). As a result:
1. `len(diagram[row])` equals the visual column count.
2. The byte at index `x` is the character in column `x`.
3. Byte comparisons against untyped byte/rune constants (like `'+'`) match directly without decoding runes.

#### Alternative Language Constructs Examined

- **Zero values**: Go initializes unassigned variables to their default zero value (`0`, `""`, `false`, `nil`). While useful for counter initializations, zero values do not drive the corner detection or side validation in the reference implementation.
- **Slice aliasing**: Slices share underlying backing arrays when sliced (`s[a:b]`). Because `diagram` is read-only and Go strings are immutable byte sequences, the algorithm does not rely on slice aliasing or in-place mutations.
- **Rune versus byte handling**: This is the construct chosen and used throughout the reference implementation.

#### Standalone Example (Reference Semantics)

```go
// Direct byte indexing on an ASCII diagram string
asciiLine := "+--+"
firstByte := asciiLine[0]
asciiMatch := firstByte == '+'
asciiLen := len(asciiLine)
// Output: firstByte=43 char=+ match=true len=4
```

#### Exercise-Relevant Pitfall: Multi-Byte Unicode Characters

A common pitfall occurs if an ASCII string indexing pattern is applied to multi-byte Unicode strings (such as box-drawing characters `┌`, `─`, `│`):

```go
// Contrasting input: Unicode box-drawing string
unicodeLine := "┌──┐"
unicodeByte := unicodeLine[0]
unicodeMatch := rune(unicodeByte) == '┌'
byteLen := len(unicodeLine)
runeCount := utf8.RuneCountInString(unicodeLine)
// Output: firstByte=226 rune=┌ match=false byteLen=12 runeCount=4
```

#### Why the Outcomes Differ

1. **Byte vs. Rune Value**: `'┌'` (Unicode U+250C, decimal 9484) is encoded in UTF-8 as three bytes: `0xE2 0x94 0x8C` (`226 148 140`). Direct indexing `unicodeLine[0]` retrieves only the first byte `226`, not the complete code point `9484`. Thus, `rune(unicodeByte) == '┌'` evaluates to `false`. In contrast, `asciiLine[0]` yields `43`, which exactly matches `'+'`.
2. **Column Misalignment**: Each Unicode box-drawing character occupies 3 bytes, so `len(unicodeLine)` is 12 bytes despite having only 4 visual characters (`utf8.RuneCountInString(unicodeLine) == 4`). Incrementing an integer index `i++` advances byte-by-byte rather than character-by-character, which breaks 2D coordinate calculations.

For this exercise, because inputs are guaranteed ASCII, direct byte indexing `diagram[y][x]` is both idiomatic and efficient.
