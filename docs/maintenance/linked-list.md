# Linked List Maintenance and Subtle Contract Cases (R63-T050)

## Overview

The `linked-list` exercise implements a generic doubly linked list in Go supporting insertion, deletion, and traversal operations:
- `Push(v any)`: append to end of list
- `Unshift(v any)`: prepend to start of list
- `Pop() (any, error)`: remove from end of list
- `Shift() (any, error)`: remove from start of list
- `Delete(v any) bool`: remove first occurrence of value
- `Count() int`: return current node count
- `Reverse()`: reverse list in place
- `First() *Node`, `Last() *Node`: return head or tail node

## Contract Decision Table

| Operation | Input State | Resulting State | Returned Value | Error Condition |
| :--- | :--- | :--- | :--- | :--- |
| `Pop()` | Empty list | Empty list | `nil` | Returns error |
| `Shift()` | Empty list | Empty list | `nil` | Returns error |
| `Pop()` | Single element list | Empty list (head=nil, tail=nil) | Element value | `nil` |
| `Shift()` | Single element list | Empty list (head=nil, tail=nil) | Element value | `nil` |
| `Push(v)` | Empty list | 1 element (head=node, tail=node) | None | `nil` |
| `Unshift(v)` | Empty list | 1 element (head=node, tail=node) | None | `nil` |
| `Delete(v)` | Value exists in single node | Empty list | `true` | `nil` |
| `Delete(v)` | Value exists multiple times | First occurrence removed | `true` | `nil` |
| `Delete(v)` | Value not present in list | List unchanged | `false` | `nil` |
| `Reverse()` | 0 or 1 node | List unchanged | None | `nil` |
| `Reverse()` | Multiple nodes | Node pointers reversed | None | `nil` |

## Subtle Contract Cases and Edge Conditions

1. **Empty list error handling:** `Pop` and `Shift` return a clean error without panic when invoked on an empty list.
2. **Re-establishing head and tail:** Popping or shifting until empty resets both pointers to `nil`. Subsequent insertions must correctly update both pointers.
3. **First-occurrence deletion:** Only the first node matching `Value == v` is deleted; subsequent duplicate values are preserved.
4. **Unspecified contract limits:** No mutex locking or thread safety is defined by the problem specifications; callers are expected to manage concurrent access if needed.

## Verification

To run all canonical tests against the reference implementation and verify that the student starter file remains unsolved:
```bash
python3 work/R63-T050/check.py
```
