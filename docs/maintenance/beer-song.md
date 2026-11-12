# Beer Song: Canonical Case Mapping & Maintenance

## Overview
The `beer-song` exercise generates lyrics to the traditional "99 Bottles of Beer" song. In the Exercism problem-specifications canonical data, test cases specify a single canonical property `recite(startBottles, takeDown)` which returns an array of strings representing individual verse lines (with empty strings separating verses).

In the Go track, the exercise exposes idiomatic Go APIs with explicit error handling:
- `Verse(n int) (string, error)`: generates verse `n` as a single string with trailing newline, returning an error for invalid verse numbers ($n < 0$ or $n > 99$).
- `Verses(start, stop int) (string, error)`: generates verses counting backwards from `start` down to `stop` separated by blank lines and trailing newline, returning an error if bounds are invalid ($start < stop$, $start > 99$, or $stop < 0$).
- `Song() string`: produces the complete song lyrics from verse 99 to verse 0.

## Canonical Case Mapping Table

| Canonical UUID | Canonical Description | Canonical Inputs (`recite`) | Go Implementation & Test Case | Coverage Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `5a02fd08-d336-4607-8006-246fe6fa9fb0` | first generic verse | `startBottles: 99, takeDown: 1` | `Verse(8)` / `Verse(3)` in `TestBottlesVerse` (`"a typical verse"`), and verse 99 in `TestEntireSong` (`Song()`) | Canonical case verifies typical multi-bottle verse phrasing without singular or zero edge cases. Go tests generic verses at 8 and 3 via `Verse(n)`, and tests verse 99 as part of `Song()`. |
| `77299ca6-545e-4217-a9cc-606b342e0187` | last generic verse | `startBottles: 3, takeDown: 1` | `Verse(3)` in `TestBottlesVerse` (`"another typical verse"`) | Directly tested by `Verse(3)` in `verseTestCases`. Validates the last verse before special grammatical transitions at 2, 1, and 0 bottles. |
| `102cbca0-b197-40fd-b548-e99609b06428` | verse with 2 bottles | `startBottles: 2, takeDown: 1` | `Verse(2)` in `TestBottlesVerse` (`"verse 2"`) | Directly tested by `Verse(2)`. Asserts plural bottles in line 1 ("2 bottles of beer") and singular bottle transition in line 2 ("1 bottle of beer"). |
| `b8ef9fce-960e-4d85-a0c9-980a04ec1972` | verse with 1 bottle | `startBottles: 1, takeDown: 1` | `Verse(1)` in `TestBottlesVerse` (`"verse 1"`) | Tests singular "1 bottle" and "take it down" transition to "no more bottles". |
| `c59d4076-f671-4ee3-baaa-d4966801f90d` | verse with 0 bottles | `startBottles: 0, takeDown: 1` | `Verse(0)` in `TestBottlesVerse` (`"verse 0"`) | Tests "No more bottles" and restocking back to 99 bottles. |
| `7e17c794-402d-4ca6-8f96-4d8f6ee1ec7e` | first two verses | `startBottles: 99, takeDown: 2` | `Verses(8, 6)` and `Verses(7, 5)` in `TestSeveralVerses` | Go tests multi-verse generation with `Verses(start, stop)`. |
| `949868e7-67e8-43d3-9bb4-69277fe020fb` | last three verses | `startBottles: 2, takeDown: 3` | `Verses(start, stop)` and `Song()` | Subsumed by `Verses` error & boundary tests and `Song()`. |
| `bc220626-126c-4e72-8df4-fddfc0c3e458` | all verses | `startBottles: 99, takeDown: 100` | `TestEntireSong` (`Song()`) | Validates full 100-verse song generation from 99 down to 0. |

## Verification
To verify the reference implementation against all test cases in an isolated sandbox without altering learner files:
```bash
python3 work/R63-T001/check.py
```
