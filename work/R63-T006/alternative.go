package parallelletterfrequency

import (
	"slices"
	"strings"
	"sync"
)

// FreqMap records the frequency of each rune in a given text.
type FreqMap map[rune]int

var Ignore = []rune{' ', '\t', '\n', '\r', '!', '?', '.', ',', ':', '-', ';', '"', '\'', '(', ')'}

// Frequency counts the frequency of each rune in a given text and returns this
// data as a FreqMap.
func Frequency(text string) FreqMap {
	frequencies := FreqMap{}
	for _, r := range strings.ToLower(text) {
		if r >= '0' && r <= '9' || slices.Contains(Ignore, r) {
			continue
		}
		frequencies[r]++
	}
	return frequencies
}

// ConcurrentFrequency implements Approach 2: Disjoint pre-allocated slice indexing with sync.WaitGroup.
func ConcurrentFrequency(texts []string) FreqMap {
	results := make([]FreqMap, len(texts))
	var wg sync.WaitGroup
	wg.Add(len(texts))

	for i, text := range texts {
		go func(idx int, t string) {
			defer wg.Done()
			results[idx] = Frequency(t)
		}(i, text)
	}

	wg.Wait()

	total := make(FreqMap)
	for _, fmap := range results {
		for r, count := range fmap {
			total[r] += count
		}
	}

	return total
}
