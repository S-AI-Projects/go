# Hints

## Rune versus Byte Handling in Go

### Chosen Construct: Rune versus Byte Handling

In Go, a `string` is an immutable sequence of bytes. Indexing `s[i]` accesses the byte at offset `i` (`uint8`), not a `rune` (`int32`).

The reference implementation in `.meta/example.go` relies on direct byte indexing:
```go
s := diagram[rowIndex][i]
if s != '+' && s != '-' {
    return false
}
```
and:
```go
if diagram[y][x] == '+'
```

This works because all characters in the rectangles diagrams are 7-bit ASCII (`+`, `-`, `|`, `' '`), which encode as single bytes in UTF-8.

### Standalone Example (Reference Semantics)

```go
// Direct byte indexing on an ASCII diagram string
asciiLine := "+--+"
firstByte := asciiLine[0]
asciiMatch := firstByte == '+'
asciiLen := len(asciiLine)
// Output: firstByte=43 char=+ match=true len=4
```

### Exercise-Relevant Pitfall: Multi-Byte Unicode Characters

```go
// Contrasting input: Unicode box-drawing string
unicodeLine := "┌──┐"
unicodeByte := unicodeLine[0]
unicodeMatch := rune(unicodeByte) == '┌'
byteLen := len(unicodeLine)
runeCount := utf8.RuneCountInString(unicodeLine)
// Output: firstByte=226 rune=┌ match=false byteLen=12 runeCount=4
```

### Why the Outcomes Differ

- In ASCII, each character is 1 byte: `asciiLine[0]` is `43` (`'+'`), `asciiMatch` is `true`, and `len(asciiLine)` is `4`.
- In UTF-8 multi-byte characters like `'┌'` (U+250C), the rune requires 3 bytes (`0xE2 0x94 0x8C`). Direct indexing yields only the first byte (`226`), so `rune(unicodeByte) == '┌'` is `false`. Furthermore, `len(unicodeLine)` is `12` bytes for 4 characters, disrupting column indexing.
