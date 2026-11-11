package tournament

import (
	"encoding/csv"
	"fmt"
	"io"
	"sort"
)

type outcome int

const (
	loss outcome = iota
	draw
	win
)

type inputEntry struct {
	teams    [2]string
	outcomes [2]outcome
}

type teamResult struct {
	team   string
	played int
	wins   int
	draws  int
	losses int
	points int
}

// recordOutcome records an outcome for the team.
// Exercise invariant: Matches Played (MP) = Wins (W) + Draws (D) + Losses (L),
// and Points (P) = 3*W + 1*D.
func (tr *teamResult) recordOutcome(o outcome) {
	tr.played++
	switch o {
	case win:
		tr.wins++
		tr.points += 3
	case draw:
		tr.draws++
		tr.points++
	case loss:
		tr.losses++
	}
}

func readInput(reader io.Reader) ([]inputEntry, error) {
	var entries []inputEntry
	csvReader := csv.NewReader(reader)
	csvReader.Comma = ';'
	csvReader.Comment = '#'
	csvReader.FieldsPerRecord = -1 // Allow variable number of fields
	for {
		record, err := csvReader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		if len(record) == 3 {
			t1, t2 := record[0], record[1]
			teams := [2]string{t1, t2}
			var outcomes [2]outcome
			switch record[2] {
			case "win":
				outcomes = [2]outcome{win, loss}
			case "loss":
				outcomes = [2]outcome{loss, win}
			case "draw":
				outcomes = [2]outcome{draw, draw}
			default:
				return nil, fmt.Errorf("Invalid outcome %q", record[2])
			}
			entries = append(entries, inputEntry{teams: teams, outcomes: outcomes})
		} else {
			return nil, fmt.Errorf("Invalid record: %v", record)
		}
	}
	return entries, nil
}

// tallyEntries aggregates match results into per-team statistics.
// Invariant: each match contributes exactly one outcome to each of the two teams,
// maintaining MP = W + D + L and Points = 3*W + 1*D across all teams.
func tallyEntries(entries []inputEntry) map[string]teamResult {
	results := make(map[string]teamResult)
	for _, entry := range entries {
		for i := range 2 {
			team := entry.teams[i]
			outcome := entry.outcomes[i]
			result := results[team]
			result.team = team
			result.recordOutcome(outcome)
			results[team] = result
		}
	}
	return results
}

func report(writer io.Writer, resultMap map[string]teamResult) {
	entries := make([]teamResult, 0, len(resultMap))
	for _, entry := range resultMap {
		entries = append(entries, entry)
	}

	// Tiebreaker ordering invariant:
	// 1. Primary: Points descending
	// 2. Secondary: Wins descending
	// 3. Tertiary: Team name alphabetically ascending
	sort.Slice(entries, func(i, j int) bool {
		a, b := entries[i], entries[j]
		switch {
		case a.points != b.points:
			return a.points > b.points
		case a.wins != b.wins:
			return a.wins > b.wins
		default:
			return a.team < b.team
		}
	})

	fmt.Fprintf(writer, "Team                           | MP |  W |  D |  L |  P\n")
	for _, entry := range entries {
		fmt.Fprintf(writer, "%-30s | %2d | %2d | %2d | %2d | %2d\n",
			entry.team, entry.played, entry.wins, entry.draws, entry.losses, entry.points)
	}
}

func Tally(r io.Reader, w io.Writer) error {
	entries, err := readInput(r)
	if err != nil {
		return err
	}
	report(w, tallyEntries(entries))
	return nil
}
