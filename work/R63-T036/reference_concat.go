package twofer

// ShareWith apportions the goods between two people using string concatenation.
func ShareWith(name string) string {
	if name == "" {
		name = "you"
	}
	return "One for " + name + ", one for me."
}
