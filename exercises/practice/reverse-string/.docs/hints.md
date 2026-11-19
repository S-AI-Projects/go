# Hints

## General

- In Go, strings are sequences of bytes.
- Many characters in UTF 8 need more than one byte. For example, Japanese characters or accented letters use multiple bytes.
- If you reverse the bytes in a string directly, characters made of multiple bytes will be split up and ruined.
- In Go, a rune represents a single Unicode character. You can convert a string to a slice of runes with `[]rune(s)`.
- If you work with runes instead of bytes, each whole character stays together when reversed.
- You can test your thinking on a small string with a multi byte character, like `"子"` or `"猫"`. If byte reversal is used, the result will have broken characters.
