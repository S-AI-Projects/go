package resistorcolorduo

var colorMap = map[string]int{
	"black":  0,
	"brown":  1,
	"red":    2,
	"orange": 3,
	"yellow": 4,
	"green":  5,
	"blue":   6,
	"violet": 7,
	"grey":   8,
	"white":  9,
}

// Value returns the resistance value of a resistor with the given colors.
// In resistor color duo, only the first two color bands determine the value.
// Any extra colors after the second band are ignored.
func Value(colors []string) int {
	tens := colorMap[colors[0]]
	ones := colorMap[colors[1]]
	return tens*10 + ones
}
