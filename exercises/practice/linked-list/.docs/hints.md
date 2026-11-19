# Hints

## General

- A doubly linked list consists of nodes where each node has a value, a pointer to the next node, and a pointer to the previous node.
- The list struct maintains pointers to both the first node (head) and last node (tail), as well as a count of elements.

## Decision Table of Operations

The table below summarizes the expected behavior of each linked list operation in Go:

| Operation | Arguments | Mutates List | Empty List Behavior | Non-Empty Behavior | Return Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Push` | `v any` | Yes | Node becomes both head and tail | Appends new node after tail, updates tail | None |
| `Unshift` | `v any` | Yes | Node becomes both head and tail | Inserts new node before head, updates head | None |
| `Pop` | None | Yes | Does not modify list | Removes tail node, updates tail | `(value, nil)` or `(nil, error)` |
| `Shift` | None | Yes | Does not modify list | Removes head node, updates head | `(value, nil)` or `(nil, error)` |
| `Count` | None | No | Returns 0 | Returns number of nodes | `int` |
| `Delete` | `v any` | Yes | Returns false | Removes first matching node from head to tail | `bool` |
| `Reverse` | None | Yes | Leaves empty list unchanged | Swaps next and prev pointers for all nodes | None |

## Subtle Contract Cases

### 1. Popping or Shifting an Empty List
When the list is empty (`head == nil` and `tail == nil`), calling `Pop()` or `Shift()` cannot remove an element. Instead of panicking, the function returns `(nil, errors.New("empty list"))`. The list remains empty with count 0.

### 2. Popping or Shifting to Empty
When removing the last remaining element from a list with 1 node:
- The removed node's value is returned.
- Both `head` and `tail` pointers must be reset to `nil`.
- The count resets to 0.
- A subsequent `Push` or `Unshift` must treat the list as fresh, setting both `head` and `tail` to the new node.

### 3. Deleting the Only Element
If a list contains a single node whose value matches the delete target:
- The node is unlinked.
- Both `head` and `tail` pointers become `nil`.
- The count becomes 0, and `Delete` returns `true`.

### 4. Deleting with Duplicate Values
If multiple nodes have the same value, `Delete` scans from head to tail and removes only the first matching node it encounters. Remaining duplicate nodes stay in the list.

### 5. Deleting a Non-Existent Element
If the target value does not match any node in the list, `Delete` leaves the list structure and count completely unchanged and returns `false`.

## Unspecified Behavior Statement

The exercise contract specifies behavior for doubly linked lists holding values of type `any`. The specification does not define thread safety or concurrency synchronization (no mutex locks required), nor does it require custom type assertions on stored values. Pointers to deleted nodes are garbage collected normally by the Go runtime.
