# Hints

## Binary Search Contract & Walkthrough

### Go Representation & Return Convention
In the Go track, `SearchInts` has the signature:
```go
func SearchInts(list []int, key int) int
```
- **Found**: Returns the 0-based integer index `h` where `list[h] == key`.
- **Not Found**: Rather than returning an error object, the track convention returns the sentinel value `-1`.
- **Ordering Requirement**: The input slice `list` is guaranteed by the specification to be sorted in ascending order. If an unsorted slice is supplied, binary search behavior is undefined.

---

### Decision Table & Case Walkthrough

| Input Condition | Input Slice (`list`) | Target (`key`) | Expected Return | Rationale / Specification Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Single element match** | `[6]` | `6` | `0` | Midpoint `(0+0)/2 = 0` matches target immediately. |
| **Middle element** | `[1, 3, 4, 6, 8, 9, 11]` | `6` | `3` | Odd-length array bisected directly at index 3 (`6`). |
| **First element** | `[1, 3, 4, 6, 8, 9, 11]` | `1` | `0` | Search window shifts left until low bound index 0 matches. |
| **Last element** | `[1, 3, 4, 6, 8, 9, 11]` | `11` | `6` | Search window shifts right until high bound index 6 matches. |
| **Odd length array** | `[1, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 634]` | `144` | `9` | Standard logarithmic binary partitioning. |
| **Even length array** | `[1, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]` | `21` | `5` | Integer division `(i+j)/2` truncates downwards cleanly. |
| **Value missing (interior)** | `[1, 3, 4, 6, 8, 9, 11]` | `7` | `-1` | Bounds narrow until `low > high`, returning `-1`. |
| **Value smaller than minimum** | `[1, 3, 4, 6, 8, 9, 11]` | `0` | `-1` | `high` drops below index 0 (`high = -1`), returning `-1`. |
| **Value larger than maximum** | `[1, 3, 4, 6, 8, 9, 11]` | `13` | `-1` | `low` exceeds last index (`low = 7`), returning `-1`. |
| **Empty array** | `[]` | `1` | `-1` | Initial state `low = 0`, `high = -1`; loop does not execute, returning `-1`. |
| **Bounds cross (2 elements)** | `[1, 2]` | `0` | `-1` | Rapid boundary crossing when key is absent. |

---

### Unspecified Behavior & Edge Cases Outside the Contract
- **Unsorted slices**: Binary search assumes monotonic non-decreasing order ($s[i] \le s[i+1]$). The behavior on unsorted slices is deliberately undefined by the specification; implementations are not required to validate sorting beforehand.
- **Multiple occurrences**: When duplicate values exist, returning the index of any matching element satisfies the contract.
- **Nil vs Empty slice**: Both `nil` and `[]int{}` have `len(s) == 0` and return `-1` without error or panic.
