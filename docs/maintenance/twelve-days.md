# Twelve Days Maintenance

## Summary

This file explains how the test generator works for the twelve days exercise.
In this exercise, a student writes Go code to return the lyrics of the song The Twelve Days of Christmas.
The student implements two functions in twelve_days.go:
- Verse(int) string: takes a verse number from 1 to 12 and returns that verse.
- Song() string: returns all 12 verses joined together by newlines.

## Test Generation Command

The tests are created by running gen.go in the exercise .meta folder.
From the root of the repository, run this command:

```shell
GO111MODULE=off go run ./exercises/practice/twelve-days/.meta/gen.go
```

Why is GO111MODULE=off needed?
The script gen.go imports the shared generator code using a relative path:
`../../../../gen`
When Go module mode is turned off for this command, Go allows relative imports and finds the shared generator package.
Running this command reads the test data, fills in the template, and writes the output file cases_test.go. It also makes sure go.mod is up to date.

## Input Files

The generator uses four main files:

1. canonical-data.json
   This is the canonical test data from problem specifications.
   If cloned next to this repo, it is read from problem-specifications/exercises/twelve-days/canonical-data.json.
   If it is not found locally, gen.go downloads it from GitHub.
   It contains 15 test cases under property recite.
2. exercises/practice/twelve-days/.meta/tests.toml
   This file tracks which test cases from canonical data are included or excluded.
   All 15 test cases are listed by their UUID.
   Comments explaining test handling are saved in comment keys so they are not deleted when regenerated.
3. exercises/practice/twelve-days/.meta/gen.go
   This file defines the testCase struct and the Go template used to generate cases_test.go.
4. gotools/config.json
   This configuration file specifies the default Go version written to go.mod.

## How gen.go Filters Test Cases

The canonical data has 15 test cases in total.
12 of these cases are single verses where startVerse equals endVerse.
3 of these cases are multi verse cases:
- Verses 1 to 3
- Verses 4 to 6
- Verses 1 to 12 (the entire song)

In gen.go, the template filters the cases using two rules:

1. Single verses for testCases:
   The template contains:
   `{{range .J.recite}} {{ if eq .Input.StartVerse .Input.EndVerse }}`
   This condition only matches when startVerse equals endVerse.
   It creates the 12 entries in the testCases slice in cases_test.go.
   The function TestVerse in twelve_days_test.go loops over testCases to test Verse(1) through Verse(12).

2. Full song for song variable:
   The template contains:
   `{{range .J.recite}}{{if eq .Input.StartVerse 1}}{{ if eq .Input.EndVerse 12 }}`
   This condition only matches the case where startVerse is 1 and endVerse is 12.
   It creates the song slice in cases_test.go.
   The function TestSong in twelve_days_test.go tests the Song function against this slice.

3. Other multi verse ranges:
   The cases for verses 1 to 3 and verses 4 to 6 do not have startVerse equal to endVerse, and they do not span verses 1 to 12.
   Therefore, gen.go filters them out and does not write them into cases_test.go.

## Case to Output Mapping Table

Here is the table of all 15 canonical test cases and where each one goes in the generated Go code:

| UUID | Description | Start Verse | End Verse | Output Destination | Handled By |
| --- | --- | --- | --- | --- | --- |
| c0b5a5e6-c89d-49b1-a6b2-9f523bff33f7 | first day a partridge in a pear tree | 1 | 1 | cases_test.go (testCases[0]) | TestVerse |
| 1c64508a-df3d-420a-b8e1-fe408847854a | second day two turtle doves | 2 | 2 | cases_test.go (testCases[1]) | TestVerse |
| a919e09c-75b2-4e64-bb23-de4a692060a8 | third day three french hens | 3 | 3 | cases_test.go (testCases[2]) | TestVerse |
| 9bed8631-ec60-4894-a3bb-4f0ec9fbe68d | fourth day four calling birds | 4 | 4 | cases_test.go (testCases[3]) | TestVerse |
| cf1024f0-73b6-4545-be57-e9cea565289a | fifth day five gold rings | 5 | 5 | cases_test.go (testCases[4]) | TestVerse |
| 50bd3393-868a-4f24-a618-68df3d02ff04 | sixth day six geese-a-laying | 6 | 6 | cases_test.go (testCases[5]) | TestVerse |
| 8f29638c-9bf1-4680-94be-e8b84e4ade83 | seventh day seven swans-a-swimming | 7 | 7 | cases_test.go (testCases[6]) | TestVerse |
| 7038d6e1-e377-47ad-8c37-10670a05bc05 | eighth day eight maids-a-milking | 8 | 8 | cases_test.go (testCases[7]) | TestVerse |
| 37a800a6-7a56-4352-8d72-0f51eb37cfe8 | ninth day nine ladies dancing | 9 | 9 | cases_test.go (testCases[8]) | TestVerse |
| 10b158aa-49ff-4b2d-afc3-13af9133510d | tenth day ten lords-a-leaping | 10 | 10 | cases_test.go (testCases[9]) | TestVerse |
| 08d7d453-f2ba-478d-8df0-d39ea6a4f457 | eleventh day eleven pipers piping | 11 | 11 | cases_test.go (testCases[10]) | TestVerse |
| 0620fea7-1704-4e48-b557-c05bf43967f0 | twelfth day twelve drummers drumming | 12 | 12 | cases_test.go (testCases[11]) | TestVerse |
| da8b9013-b1e8-49df-b6ef-ddec0219e398 | recites first three verses of the song | 1 | 3 | Filtered out by template | Not included in Go tests |
| c095af0d-3137-4653-ad32-bfb899eda24c | recites three verses from the middle of the song | 4 | 6 | Filtered out by template | Not included in Go tests |
| 20921bc9-cc52-4627-80b3-198cbbfcf9b7 | recites the whole song | 1 | 12 | cases_test.go (song variable) | TestSong |
