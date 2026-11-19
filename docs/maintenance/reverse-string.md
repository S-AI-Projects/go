# Reverse String Maintenance

## Summary

This document explains the test cases for the reverse string exercise and records a deliberate mutant test.
The reverse string exercise asks us to reverse a string in Go.
In Go, strings are made of bytes, but many Unicode characters are made of multiple bytes.
To reverse a string correctly, we need to reverse its runes, not its raw bytes.

## Reference Implementation

The reference solution in `exercises/practice/reverse-string/.meta/example.go` reverses the string by converting it to a slice of runes:

```go
package reversestring

// Reverse reverses given string
func Reverse(s string) string {
	runes := []rune(s)
	for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
		runes[i], runes[j] = runes[j], runes[i]
	}
	return string(runes)
}
```

This works for all valid UTF 8 strings because each Unicode code point is treated as one unit.

## Deliberate Mutant

To test if our test suite can catch mistakes, we created a small mutant that reverses bytes instead of runes:

```go
package reversestring

// Reverse reverses given string by bytes instead of runes
func Reverse(s string) string {
	bytes := []byte(s)
	for i, j := 0, len(bytes)-1; i < j; i, j = i+1, j-1 {
		bytes[i], bytes[j] = bytes[j], bytes[i]
	}
	return string(bytes)
}
```

This mutant works fine for plain ASCII strings like "robot" or "racecar" where every character is exactly one byte.
However, it fails when a string contains characters made of more than one byte.

## Rejecting Test Case

The canonical test suite contains a test case that catches this bug and rejects the mutant.

- UUID: 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2
- Description: "wide characters"
- Input: `"子猫"`
- Expected Result: `"猫子"`
- Actual Result with Mutant: `"\xab\x8c琭\xe5"`
- Test Failure: `Reverse("子猫") = "\xab\x8c琭\xe5", want: "猫子"`

### Why It Fails

In UTF 8:
- The character `子` is encoded using 3 bytes: `0xE5 0xAD 0x90`
- The character `猫` is encoded using 3 bytes: `0xE7 0x8C 0xAB`
- Together, `"子猫"` has 6 bytes: `[0xE5, 0xAD, 0x90, 0xE7, 0x8C, 0xAB]`

When we reverse runes:
1. `s` becomes two runes: `['子', '猫']`
2. Swapping the runes gives: `['猫', '子']`
3. Converting back to string gives: `"猫子"` (bytes `[0xE7, 0x8C, 0xAB, 0xE5, 0xAD, 0x90]`)

When the mutant reverses bytes:
1. The 6 raw bytes are reversed directly: `[0xAB, 0x8C, 0xE7, 0x90, 0xAD, 0xE5]`
2. The byte `0xAB` is not a valid start byte in UTF 8, so the bytes no longer represent the characters
3. The resulting string is corrupted and does not match `"猫子"`

Therefore, test case 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2 properly rejects the mutant.

## Reduced Input

We can reduce the rejecting case to a smaller input that still catches the byte reversal mistake.

- Smallest input from test suite: `"子"` (one 3 byte character)
  - Input: `"子"`
  - Expected: `"子"`
  - Mutant output: `"\x90\xad\xe5"` (fails because bytes `0xE5 0xAD 0x90` reversed to `0x90 0xAD 0xE5`)
- Or a 2 byte character:
  - Input: `"é"` (bytes `0xC3 0xA9`)
  - Expected: `"é"`
  - Mutant output: `"\xa9\xc3"` (fails because bytes are reversed to invalid UTF 8)

Even a single multi byte character is enough to break byte level reversal.

## Test Case Results Table

Here is how each test case behaves with the reference solution versus the mutant:

| UUID | Description | Input | Expected | Reference Result | Mutant Result |
| --- | --- | --- | --- | --- | --- |
| c3b7d806-dced-49ee-8543-933fd1719b1c | an empty string | `""` | `""` | Pass | Pass |
| 01ebf55b-bebb-414e-9dec-06f7bb0bee3c | a word | `"robot"` | `"tobor"` | Pass | Pass |
| 0f7c07e4-efd1-4aaa-a07a-90b49ce0b746 | a capitalized word | `"Ramen"` | `"nemaR"` | Pass | Pass |
| 71854b9c-f200-4469-9f5c-1e8e5eff5614 | a sentence with punctuation | `"I'm hungry!"` | `"!yrgnuh m'I"` | Pass | Pass |
| 1f8ed2f3-56f3-459b-8f3e-6d8d654a1f6c | a palindrome | `"racecar"` | `"racecar"` | Pass | Pass |
| b9e7dec1-c6df-40bd-9fa3-cd7ded010c4c | an even-sized word | `"drawer"` | `"reward"` | Pass | Pass |
| 1bed0f8a-13b0-4bd3-9d59-3d0593326fa2 | wide characters | `"子猫"` | `"猫子"` | Pass | Fail (Rejects mutant) |

The test suite also includes an extra track test:
- "a multi-byte test case" (`"Hello, 世界"` -> `"界世 ,olleH"`): Pass with reference, Fail with mutant.

## Expected Behavior

The specification requires `Reverse(input)` to reverse the order of characters in any valid string.
Because Go strings can contain multi byte UTF 8 characters, implementations must handle runes rather than raw bytes.
