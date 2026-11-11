# Circular Buffer — Canonical Case Rationale (`R63-T031`)

## Summary

- **Exercise:** `exercises/practice/circular-buffer`
- **Go API Adaptation:** `Buffer` implements `io.ByteReader` and `io.ByteWriter` (`NewBuffer`, `ReadByte`, `WriteByte`, `Overwrite`, `Reset`). As defined in `exercises/practice/circular-buffer/.meta/gen.go`, canonical integer items are mapped to ASCII bytes (`byte(n + '0')`), and the canonical `clear` operation maps to `Reset()`.

## Included / Excluded Counts

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Total canonical cases | 14 | 14 | 0 |
| Included cases | 14 | 14 | 0 |
| Excluded cases (`include = false`) | 0 | 0 | 0 |

No canonical inclusions or exclusions were changed; all 14 canonical cases remain enabled and supported by `cases_test.go`, `circular_buffer_test.go`, and `.meta/example.go`.

## Reviewed UUID Mapping Table

| UUID | Canonical Description | Status | Go Test & Operations | Rationale |
| --- | --- | --- | --- | --- |
| `28268ed4-4ff3-45f3-820e-895b44d53dfa` | `reading empty buffer should fail` | Included | `TestRun/reading_empty_buffer_should_fail` (`cases_test.go`): `NewBuffer(1)`, `ReadByte()` (`wantErr: true`) | `NewBuffer` initializes `b.start == b.end` in `.meta/example.go`; `ReadByte()` checks `b.start == b.end` and returns `errors.New("buffer empty")`, matching the `io.ByteReader` error contract. |
| `2e6db04a-58a1-425d-ade8-ac30b5f318f3` | `can read an item just written` | Included | `TestRun/can_read_an_item_just_written` (`cases_test.go`): `NewBuffer(1)`, `WriteByte('1')`, `ReadByte()` (`value: '1'`, `wantErr: false`) | `.meta/gen.go` adapts canonical integer item `1` to `'1'`. `WriteByte('1')` stores the byte at `b.end.Value` and advances `b.end`, and `ReadByte()` returns `'1'` from `b.start.Value`. |
| `90741fe8-a448-45ce-be2b-de009a24c144` | `each item may only be read once` | Included | `TestRun/each_item_may_only_be_read_once` (`cases_test.go`): `NewBuffer(1)`, `WriteByte('1')`, `ReadByte()` (`'1'`), `ReadByte()` (`wantErr: true`) | The first `ReadByte()` consumes `'1'` and advances `b.start = b.start.Next()`, restoring `b.start == b.end` so the second `ReadByte()` returns an empty-buffer error. |

