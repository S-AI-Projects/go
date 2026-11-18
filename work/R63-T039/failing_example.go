package accumulate

// Deliberately incorrect reference implementation that returns nil to test failure propagation.
func Accumulate(s []string, f func(st string) string) []string {
	return nil
}
