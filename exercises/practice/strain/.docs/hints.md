# Hints

## The Strain Contract

The `strain` exercise asks you to implement `Keep` and `Discard` as pure filtering operations on generic slices.

### Underlying Contract

1. **Predicate Application**:
   - `Keep[T any](list []T, fn func(T) bool) []T` must evaluate `fn(item)` on each element in sequence and include only those items where the predicate evaluates to `true`.
   - `Discard[T any](list []T, fn func(T) bool) []T` must evaluate `fn(item)` on each element in sequence and include only those items where the predicate evaluates to `false`.
   - The union of `Keep` and `Discard` for any list and predicate equals all original elements.

2. **Order Preservation**:
   - The relative order of kept or discarded elements must be strictly preserved.

3. **Input Immutability**:
   - The operations must be pure functions. You **must not** modify the input slice `list` in-place (for example, by reusing its backing array with `list[:0]` or writing into `list[i]`).
   - The test suite explicitly checks that the input slice remains identical before and after calling `Keep` and `Discard`.

4. **Empty Collections**:
   - If the input slice is empty or `nil`, an empty collection (or `nil`) should be returned without runtime panics.

### Small Diagnostic Example

To verify your implementation against the contract, consider a small collection:

```go
input := []int{1, 2, 3}

// Keep odd numbers:
kept := Keep(input, func(n int) bool { return n%2 == 1 })
// Expected kept:  []int{1, 3}
// Expected input: []int{1, 2, 3} (must remain unmodified!)

// Discard odd numbers:
discarded := Discard(input, func(n int) bool { return n%2 == 1 })
// Expected discarded: []int{2}
// Expected input:     []int{1, 2, 3} (must remain unmodified!)
```

### Minimal Diagnostic Case

For a single-element list:
- Input: `[]int{1}`
- Predicate: `func(n int) bool { return true }`
- `Keep` produces `[]int{1}`
- `Discard` produces `[]int{}`
