package twofer

import "fmt"

// ShareWith apportions the goods between two people using fmt.Sprintf.
func ShareWith(name string) string {
	if name == "" {
		name = "you"
	}
	return fmt.Sprintf("One for %s, one for me.", name)
}
