# Instructions

Your task is to build a stopwatch to keep precise track of lap times.

The stopwatch uses four commands (start, stop, lap, and reset) to keep track of:

1. The current lap's tracked time
2. Previously recorded lap times

What commands can be used depends on which state the stopwatch is in:

1. Ready: initial state
2. Running: tracking time
3. Stopped: not tracking time

| Command | Begin state | End state | Effect                                                   |
| ------- | ----------- | --------- | -------------------------------------------------------- |
| Start   | Ready       | Running   | Start tracking time                                      |
| Start   | Stopped     | Running   | Resume tracking time                                     |
| Stop    | Running     | Stopped   | Stop tracking time                                       |
| Lap     | Running     | Running   | Add current lap to previous laps, then reset current lap |
| Reset   | Stopped     | Ready     | Reset current lap and clear previous laps                |

---
## Alternative Implementation Hint

The reference implementation stores the start time, a map of lap indices to timestamps, and a boolean flag for whether the stopwatch is running. An alternative design can use a **slice** to record lap time offsets relative to the start, and a single `bool` for the running state.

```go
type StopWatch struct {
    start   time.Time   // when the watch was started
    laps    []time.Duration // cumulative lap durations
    running bool
}

func (sw *StopWatch) Start() {
    if sw.running { return }
    sw.start = time.Now()
    sw.running = true
    sw.laps = sw.laps[:0] // reset previous laps
}

func (sw *StopWatch) Lap() time.Duration {
    if !sw.running { return 0 }
    // elapsed since start
    elapsed := time.Since(sw.start)
    // store relative to previous lap
    if len(sw.laps) == 0 {
        sw.laps = append(sw.laps, elapsed)
    } else {
        sw.laps = append(sw.laps, elapsed-sw.total())
    }
    return elapsed
}

func (sw *StopWatch) total() time.Duration {
    var sum time.Duration
    for _, d := range sw.laps { sum += d }
    return sum
}
```

### Trade‑offs
* **Memory** – The slice grows with each lap, whereas a map allocates per key. For a typical small number of laps the difference is negligible, but a slice has lower overhead.
* **Lookup** – Accessing the *n*‑th lap is O(1) with a slice (`sw.laps[n-1]`). With a map you need the key, which is also O(1) but involves hashing.
* **Order preservation** – A slice inherently preserves insertion order, making it natural for “lap #N”. The map implementation must rely on the stored index key.
* **Reset** – Resetting is a simple slice reslice (`sw.laps = sw.laps[:0]`). The map version clears the map.

The tests in `cases_test.go` only care about the observable behaviour (lap times, total duration, reset semantics). Either representation satisfies the contract, so you can choose the one that feels clearer to you.

---
