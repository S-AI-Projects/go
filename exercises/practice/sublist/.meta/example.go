package sublist

import "slices"

// Sublist checks difference of two lists and
// returns equal, sublist, superlist or unequal according
// to their relation to each other.
func Sublist(l1, l2 []int) Relation {
	switch {
	case slices.Equal(l1, l2):
		return RelationEqual
	case contains(l1, l2):
		return RelationSuperlist
	case contains(l2, l1):
		return RelationSublist
	default:
		return RelationUnequal
	}
}

// contains checks if sublist appears as a contiguous subsequence within list.
func contains(list, sublist []int) bool {
	if len(sublist) == 0 {
		return true
	} else if len(sublist) > len(list) {
		return false
	}
	// Exercise invariant: a sublist must match elements contiguously from start to end
	for i := range len(list) - len(sublist) + 1 {
		if slices.Equal(list[i:i+len(sublist)], sublist) {
			return true
		}
	}
	return false
}
