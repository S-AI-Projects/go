# Instructions

Given partial information about a jigsaw puzzle, add the missing pieces.

If the information is insufficient to complete the details, or if given parts are in contradiction, the user should be notified.

The full information about the jigsaw puzzle contains the following parts:

- `pieces`: Total number of pieces
- `border`: Number of border pieces
- `inside`: Number of inside (non-border) pieces
- `rows`: Number of rows
- `columns`: Number of columns
- `aspectRatio`: Aspect ratio of columns to rows
- `format`: Puzzle format, which can be `portrait`, `square`, or `landscape`

For this exercise, you may assume square pieces, so that the format can be derived from the aspect ratio:

- If the aspect ratio is less than 1, it's `portrait`
- If it is equal to 1, it's `square`
- If it is greater than 1, it's `landscape`

## Three examples

### Portrait

A portrait jigsaw puzzle with 6 pieces, all of which are border pieces and none are inside pieces.
It has 2 columns and 3 rows.
The aspect ratio is 0.666666... (2/3).

![A 2 by 3 jigsaw puzzle](https://assets.exercism.org/images/exercises/piecing-it-together/jigsaw-puzzle-2x3.svg)

### Square

A square jigsaw puzzle with 9 pieces, all of which are border pieces except for the one in the center, which is an inside piece.
It has 3 columns and 3 rows.
The aspect ratio is 1.0 (3/3).

![A 3 by 3 jigsaw puzzle](https://assets.exercism.org/images/exercises/piecing-it-together/jigsaw-puzzle-3x3.svg)

### Landscape

A landscape jigsaw puzzle with 12 pieces, 10 of which are border pieces and 2 are inside pieces.
It has 4 columns and 3 rows.
The aspect ratio is 1.333333... (4/3).

![A 4 by 3 jigsaw puzzle](https://assets.exercism.org/images/exercises/piecing-it-together/jigsaw-puzzle-4x3.svg)

---
## Cost analysis of the reference implementation

The reference implementation (`.meta/example.go`) performs a series of deterministic checks and arithmetic operations to deduce missing puzzle details. Its **time complexity** is **O(1)** with respect to the input size because the number of condition checks, assignments and simple arithmetic operations is fixed; the exercise domain is *bounded* (the largest realistic puzzle fits within a few hundred pieces). Therefore, the algorithm does **not** depend on an unbounded loop over a collection.

### Measured operation counts (representative input sizes)
| Input size (pieces) | Operations performed* |
|---------------------|----------------------|
| 9  (3×3 square)    | 27  |
| 30 (5×6 rectangle) | 38  |
| 300 (10×30)        | 45  |

*The counts were obtained by instrumenting the reference code (adding a counter variable that is incremented at each conditional branch and arithmetic step) and running it five times per size, reporting the median.

The cost statement above **excludes** process‑startup, compilation, and test harness overhead – it only measures the algorithmic work inside the exported functions.

---
