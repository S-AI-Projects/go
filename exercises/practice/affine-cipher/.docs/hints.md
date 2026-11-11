# Hints

## Debugging

### Negative Remainder in Modular Arithmetic
- In Go, the `%` operator computes the remainder of integer division, not the mathematical Euclidean modulo. If the left-hand operand is negative, the result of `%` is negative:
  ```go
  (-18) % 26 // evaluates to -18 in Go, not 8!
  ```
- In the decryption formula $D(y) = a^{-1}(y - b) \pmod{26}$, whenever the ciphertext letter index $y$ is strictly less than the key offset $b$, the factor $(y - b)$ is negative.
- If your implementation does not normalize negative remainders into the valid alphabet range $[0, 25]$ (e.g. by adding $26$ when the remainder is negative), converting the value back to an ASCII character (`byte(temp) + 'a'`) will produce an out-of-range character or corrupted byte.
- **Diagnostic check**: Try decrypting the single letter `"f"` ($y = 5$) using keys $a = 3, b = 7$.
  - Modular inverse: $a^{-1} = 9$ (since $9 \times 3 = 27 \equiv 1 \pmod{26}$).
  - Difference: $y - b = 5 - 7 = -2$.
  - Product: $9 \times (-2) = -18$.
  - Normalized mathematical modulo: $-18 + 26 = 8$ (which corresponds to plaintext letter `'i'`).
  - If your decoder does not produce `'i'`, verify your remainder adjustment.
