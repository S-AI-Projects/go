# Hints

## General

- In Go, you can check whether a specific bit is set using the bitwise AND operator (`&`) with powers of two: `1` (`00001`), `2` (`00010`), `4` (`00100`), `8` (`01000`), and `16` (`10000`).
- The test suite allows returning either `nil` or an empty slice `[]string{}` when no actions are triggered.

## Decision Table

The table below illustrates how the lowest five bits map to the required output sequence:

| Input | Binary | Active Bits | Reverse Flag (16) | Unreversed Actions | Expected Handshake |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0` | `00000` | None | No | None | `[]` |
| `1` | `00001` | 1 | No | wink | `["wink"]` |
| `2` | `00010` | 2 | No | double blink | `["double blink"]` |
| `4` | `00100` | 4 | No | close your eyes | `["close your eyes"]` |
| `8` | `01000` | 8 | No | jump | `["jump"]` |
| `3` | `00011` | 1, 2 | No | wink, double blink | `["wink", "double blink"]` |
| `15` | `01111` | 1, 2, 4, 8 | No | wink, double blink, close your eyes, jump | `["wink", "double blink", "close your eyes", "jump"]` |
| `16` | `10000` | 16 | Yes | None | `[]` |
| `19` | `10011` | 1, 2, 16 | Yes | wink, double blink | `["double blink", "wink"]` |
| `24` | `11000` | 8, 16 | Yes | jump | `["jump"]` |
| `31` | `11111` | 1, 2, 4, 8, 16 | Yes | wink, double blink, close your eyes, jump | `["jump", "close your eyes", "double blink", "wink"]` |

## Subtle Contract Cases

### 1. Reversing with No Actions (Input: 16)
The binary representation of 16 is `10000`. Only bit 16 (the reverse flag) is set. Because bits 1, 2, 4, and 8 are all 0, no actions are accumulated. Reversing an empty sequence produces an empty slice (`[]string{}`).

### 2. Reversing with a Single Action (Input: 24)
The number 24 is `11000` in binary (`16 + 8`). Only the action for 8 (`"jump"`) is present, followed by the reverse flag. Reversing a sequence with a single element leaves the sequence unchanged (`["jump"]`).

### 3. Zero Input (Input: 0)
When the code is `0`, no bit flags are active, resulting in an empty sequence.

### Unspecified Behavior Statement
The exercise specification defines behavior for the rightmost 5 bits (numbers 1 to 31, with 0 yielding empty actions). The specification does not define custom error values or special handling for higher-order bits; code should inspect the relevant bitmask values without imposing extra errors or unprompted coercions.
