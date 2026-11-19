# Perfect Numbers Maintenance

## Summary

This file explains the test cases for the perfect numbers exercise.
A perfect number is a positive number where the sum of all its factors except the number itself equals the number.
For example, the factors of 6 are 1, 2, and 3. When we add them together, 1 + 2 + 3 = 6, which equals 6.

In Go, the function Classify takes an int64 number and returns a Classification type and an error.
The three classifications are:
- ClassificationPerfect
- ClassificationAbundant
- ClassificationDeficient

If the number is zero or negative, Classify returns an error called ErrOnlyPositive.

## Case Counts

| Type | Before | After | Change |
| --- | --- | --- | --- |
| Total test cases | 14 | 14 | 0 |
| Included cases | 14 | 14 | 0 |
| Excluded cases | 0 | 0 | 0 |

All 14 test cases are included and pass. No cases were excluded.

## Reviewed Test Cases

Here is a table showing the three perfect number test cases:

| UUID | Test Name | Number | Factor Sum | How Go Code Checks It |
| --- | --- | --- | --- | --- |
| 163e8e86-7bfd-4ee2-bd68-d083dc3381a3 | Smallest perfect number is classified correctly | 6 | 1 + 2 + 3 = 6 | It calls Classify(6). The code adds factors 1, 2, and 3 to get sum 6. Since sum equals 6, it returns ClassificationPerfect. |
| 169a7854-0431-4ae0-9815-c3b6d967436d | Medium perfect number is classified correctly | 28 | 1 + 2 + 4 + 7 + 14 = 28 | It calls Classify(28). The code adds factors 1, 2, 4, 7, and 14 to get sum 28. Since sum equals 28, it returns ClassificationPerfect. |
| ee3627c4-7b36-4245-ba7c-8727d585f402 | Large perfect number is classified correctly | 33550336 | Sum of factors = 33550336 | It calls Classify(33550336). The loop finds factors and sums them. The sum equals 33550336, so it returns ClassificationPerfect. |

## How the Go Code Works

1. The function Classify receives a number n of type int64.
2. First, it checks if n is less than or equal to 0. If it is, it returns ErrOnlyPositive.
3. Next, it starts a variable sum at 0 and loops through numbers i starting from 1 up to n minus 1.
4. If n is divisible by i (using remainder check n % i == 0), i is a factor, so i is added to sum.
5. If sum grows bigger than n, it can return ClassificationAbundant early.
6. When the loop finishes:
   - If sum equals n, it returns ClassificationPerfect and no error.
   - If sum is less than n, it returns ClassificationDeficient and no error.
   - Otherwise, it returns ClassificationAbundant and no error.
