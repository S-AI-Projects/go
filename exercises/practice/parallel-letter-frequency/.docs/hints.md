# Hints

## Approach Selection

When counting letter frequencies across multiple texts concurrently, there are two primary concurrency patterns in Go:

### 1. Fan-Out / Fan-In via Buffered Channel
- **Mechanism**: A worker goroutine is spawned for each input text string. Each worker computes a local `FreqMap` and transmits it over a Go channel (e.g. `chan FreqMap`). A separate background goroutine waits on a `sync.WaitGroup` to close the channel when all workers finish. The consumer loop reads maps off the channel as they arrive and merges them into the final accumulator map.
- **Trade-off**: 
  - *Advantages*: Highly idiomatic Go pipeline pattern; provides streaming aggregation as workers complete without waiting for the slowest text.
  - *Costs*: Allocates channel buffer and requires coordination across three phases (producer, closer, consumer).

### 2. Disjoint Slice Indexing with `sync.WaitGroup`
- **Mechanism**: Pre-allocate a slice of `FreqMap` of length equal to `len(texts)`. Each worker is assigned a unique index `i` and assigns its computed map directly to `results[i]`. Because each goroutine writes to a distinct slice index, this is race-free without mutexes. A `sync.WaitGroup` synchronizes completion before sequentially summing the results.
- **Trade-off**:
  - *Advantages*: Eliminates channel synchronization and context-switch overhead; simple deterministic memory layout.
  - *Costs*: Cannot stream aggregation progressively; must wait until all workers finish before beginning the map merge pass.

---

## Worked Example

Consider processing two short text slices:
```go
texts := []string{"cat", "car"}
```

1. **Partitioning**:
   - Worker 0 receives `"cat"`. Local frequency count: `{'c': 1, 'a': 1, 't': 1}`.
   - Worker 1 receives `"car"`. Local frequency count: `{'c': 1, 'a': 1, 'r': 1}`.
2. **Aggregation Phase**:
   - In both patterns, the reduction loop iterates over the keys of each worker's local map and increments the global count:
     - `'c'` appears in both maps $\to$ final count: $1 + 1 = 2$.
     - `'a'` appears in both maps $\to$ final count: $1 + 1 = 2$.
     - `'t'` appears only in Worker 0 $\to$ final count: $1$.
     - `'r'` appears only in Worker 1 $\to$ final count: $1$.
3. **Final Result**:
   - `FreqMap{'a': 2, 'c': 2, 'r': 1, 't': 1}`.
