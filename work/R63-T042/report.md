# Test Report for R63-T042 (twelve-days)

## Overview

This report shows the verification results for Task 2 (R63-T042) on exercises/practice/twelve-days.
The goal of this task is to document and verify that test generation is reproducible,
explain how gen.go filters test cases, and make sure all tests pass against the example solution.

## Tool Versions

- Go: go version go1.27.3 darwin/arm64
- Python: 3.9.6 (default, Aug 25 2026, 21:26:21)  [Clang 21.0.0 (clang-2100.3.34.2)]

## Generation Reproducibility Check

Script: tools/course_checks/r63-t042.py
Result: PASS (exit code 0)

The script performed two fresh generations in temporary directories using:
GO111MODULE=off go run ./exercises/practice/twelve-days/.meta/gen.go

Both runs produced identical test outputs after timestamp and commit line normalization.
No test cases were silently dropped:
- 12 single verse test cases are present in testCases for TestVerse.
- 12 song lines are present in the song variable for TestSong.
- 2 multi verse cases (verses 1 to 3, and verses 4 to 6) are filtered out by gen.go as intended.

## Go Test Execution

The exercise was copied to a temporary folder and tested against the example solution (.meta/example.go).
Command: go test -count=1 -v ./...
Result: PASS (exit code 0)
Passed test cases: 14

The following tests passed:
- --- PASS: TestVerse (0.00s)
- --- PASS: TestVerse/first_day_a_partridge_in_a_pear_tree (0.00s)
- --- PASS: TestVerse/second_day_two_turtle_doves (0.00s)
- --- PASS: TestVerse/third_day_three_french_hens (0.00s)
- --- PASS: TestVerse/fourth_day_four_calling_birds (0.00s)
- --- PASS: TestVerse/fifth_day_five_gold_rings (0.00s)
- --- PASS: TestVerse/sixth_day_six_geese-a-laying (0.00s)
- --- PASS: TestVerse/seventh_day_seven_swans-a-swimming (0.00s)
- --- PASS: TestVerse/eighth_day_eight_maids-a-milking (0.00s)
- --- PASS: TestVerse/ninth_day_nine_ladies_dancing (0.00s)
- --- PASS: TestVerse/tenth_day_ten_lords-a-leaping (0.00s)
- --- PASS: TestVerse/eleventh_day_eleven_pipers_piping (0.00s)
- --- PASS: TestVerse/twelfth_day_twelve_drummers_drumming (0.00s)
- --- PASS: TestSong (0.00s)

## Learner Stub Verification

The original learner stub at exercises/practice/twelve-days/twelve_days.go was checked.
It remains untouched and contains the original panic calls.
The student solution is still unsolved as required.

## Conclusion

All checks for R63-T042 passed cleanly.
