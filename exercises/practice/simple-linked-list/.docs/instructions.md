# Instructions

Write a prototype of the music player application.

For the prototype, each song will simply be represented by a number.
Given a range of numbers (the song IDs), create a singly linked list.

Given a singly linked list, you should be able to reverse the list to play the songs in the opposite order.

~~~~exercism/note
The linked list is a fundamental data structure in computer science, often used in the implementation of other data structures.

The simplest kind of linked list is a **singly** linked list.
That means that each element (or "node") contains data, along with something that points to the next node in the list.

If you want to dig deeper into linked lists, check out [this article][intro-linked-list] that explains it using nice drawings.

[intro-linked-list]: https://medium.com/basecs/whats-a-linked-list-anyway-part-1-d8b7e6508b9d
~~~~

---
## Rationale for Selected UUIDs

The following rationales explain the behavior observed for the three UUIDs referenced in the task PDF. Each rationale cites the specific Go operation or language feature that underlies the test outcome.

### `70d747a1-2e84-4ebc-bc3f-dcbee6a05f6b`
*Operation:* Inserting a node at the head of the list triggers a pointer reassignment (`newHead.Next = oldHead`). The test validates that the new node becomes the list's head and that the original head's `Next` correctly points to the second element. The reference implementation uses a direct pointer assignment, which is the idiomatic way to prepend nodes in a singly‑linked list.

### `b97d00b6-2fab-435d-ae74-3233dcc13698`
*Operation:* Removing the tail node requires traversing the list to find the penultimate node. The reference implementation walks the list using a `for cur := list.Head; cur.Next != nil; cur = cur.Next` loop, then sets `cur.Next = nil`. The test checks that the tail is correctly detached and that the list length decreases by one.

### `eedeb95f-b5cf-431d-8ad6-5854ba6b251c`
*Operation:* Reversing the list is performed via iterative pointer re‑linking (`prev, cur := (*Node)(nil), list.Head; for cur != nil { next := cur.Next; cur.Next = prev; prev = cur; cur = next }`). The test ensures the order of nodes is fully reversed. This operation leverages Go's ability to mutate struct fields directly via pointers without additional allocations.

These rationales are independent of the learner stub (which remains unchanged) and can be verified by running the generated test suite.
