# Hints

## General

- The chessboard has 64 squares numbered 1 through 64.
- Any square number less than 1 or greater than 64 is invalid and should return an error.
- Because the numbers double on every square, the count grows very quickly and requires an unsigned 64 bit integer (`uint64`).

## Approach Selection

There are two common ways to implement this exercise in Go:

### 1. Bitwise Shift Approach

A left shift by 1 position multiplies an integer by 2. 
- Square 1 has 1 grain, which is 2 to the power of 0.
- Square 2 has 2 grains, which is 2 to the power of 1.
- In general, square n has 2 to the power of (n - 1) grains.
- In Go, you can compute this directly using the left shift operator `1 << (n - 1)`.

**Trade-offs:** 
- The bitwise shift executes in a single CPU cycle, making it extremely fast (under 1 nanosecond per operation) with zero memory allocations.
- For `Total()`, the sum of the first 64 powers of 2 is `2^64 - 1`, which is all 64 bits set to 1. In Go, this is simply the maximum value of a 64 bit unsigned integer.

### 2. Iterative Loop Approach

Instead of bitwise operations, you can start with a count of 1 grain and use a loop to multiply by 2 for each square from 1 up to n.

**Trade-offs:**
- The loop approach is very easy to visualize for beginners because it directly mimics placing grains on the board square by square.
- However, it executes in O(n) loop steps instead of a single CPU instruction, requiring slightly more computation time (around 10 to 15 nanoseconds).

### Worked Example

Consider square 4:
- Using the iterative doubling method: start at 1 (square 1), multiply by 2 to get 2 (square 2), multiply by 2 to get 4 (square 3), and multiply by 2 to get 8 (square 4).
- Using the bitwise shift method: shift 1 to the left by (4 - 1) = 3 positions (`1 << 3`), which directly gives 8.
Both methods arrive at 8 grains for square 4.
