package isbnverifier

import (
	"errors"
	"math"
	"strconv"
	"unicode"
)

// IsValidISBN verifies whether a string represents a valid ISBN-10 number.
//
// Complexity:
//   - Time Complexity: O(L) where L is the character length of the input string.
//     Because valid ISBN-10 representations have a fixed bounded length (10 digits
//     and at most a few hyphens, typically L <= 13), the execution time is strictly
//     O(1) constant time with respect to the input domain.
//   - Space Complexity: O(1) auxiliary space, allocating a fixed slice of 10 integers
//     for the digits and small string buffers.
//
// Invariant: An ISBN-10 must contain exactly 10 digits (where 'X' can only be the
// 10th check digit representing the value 10) such that the weighted sum modulo 11 equals 0.
func IsValidISBN(isbn string) bool {
	isbn = dropHyphen(isbn)

	ary, err := strToSlice(isbn)
	if len(ary) != 10 || err != nil {
		return false
	}

	return calcCheckDigit(ary)
}

func dropHyphen(isbn string) string {
	var result string
	for _, char := range isbn {
		if char == '-' {
			continue
		}
		result += string(char)
	}
	return result
}

func strToSlice(isbn string) (result []int, err error) {
	for pos, char := range isbn {
		switch {
		case unicode.IsLetter(char) && (char != 'X' || pos != 9):
			err = errors.New("invalid character")
			return result, err
		case char == 'X':
			result = append(result, 10)
		default:
			i, _ := strconv.Atoi(string(char))
			result = append(result, i)
		}
	}
	return result, err
}

func calcCheckDigit(isbn []int) bool {
	var pool int
	for idx, value := range isbn {
		pool += int(math.Abs(float64(idx)-10)) * value
	}
	result := pool % 11

	return result == 0
}
