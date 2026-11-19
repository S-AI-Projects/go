package grains

import (
	"fmt"
)

// Square returns the number of grains on square number using an iterative loop.
func Square(number int) (uint64, error) {
	if number < 1 || number > 64 {
		return 0, fmt.Errorf("square %d out of range (must be 1-64)", number)
	}
	var grains uint64 = 1
	for i := 1; i < number; i++ {
		grains *= 2
	}
	return grains, nil
}

// Total returns the total number of grains on all 64 squares using an iterative loop.
func Total() uint64 {
	var total uint64
	var current uint64 = 1
	for i := 1; i <= 64; i++ {
		total += current
		current *= 2
	}
	return total
}
