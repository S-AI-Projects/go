package splitsecondstopwatch

import (
    "errors"
    "fmt"
    "strconv"
    "strings"
)

// Alternative implementation using slices of strings for laps and storing elapsed as seconds.

func formatTime(t int) string { return fmt.Sprintf("%02d:%02d:%02d", t/3600, (t/60)%60, t%60) }

func parseTime(s string) int {
    parts := strings.Split(s, ":")
    total := 0
    for _, p := range parts {
        v, _ := strconv.Atoi(p)
        total = total*60 + v
    }
    return total
}

type SplitSecondStopwatch struct {
    state    string
    elapsed  int      // total elapsed seconds
    laps     []string // formatted lap strings
    lapStart int      // start time of current lap in seconds
    started  bool
}

func (sss *SplitSecondStopwatch) Start() error {
    if sss.state == "running" {
        return errors.New("cannot start an already running stopwatch")
    }
    sss.started = true
    sss.state = "running"
    // If we start from stopped, keep previous elapsed and lapStart.
    return nil
}

func (sss *SplitSecondStopwatch) Stop() error {
    if sss.state != "running" {
        return errors.New("cannot stop a stopwatch that is not running")
    }
    sss.state = "stopped"
    return nil
}

func (sss *SplitSecondStopwatch) Reset() error {
    if sss.state != "stopped" {
        return errors.New("cannot reset a stopwatch that is not stopped")
    }
    sss.laps = []string{}
    sss.state = "ready"
    sss.elapsed = 0
    sss.lapStart = 0
    sss.started = false
    return nil
}

func (sss *SplitSecondStopwatch) Lap() error {
    if sss.state != "running" {
        return errors.New("cannot lap a stopwatch that is not running")
    }
    // Record current lap duration formatted string.
    lapDur := sss.elapsed - sss.lapStart
    sss.laps = append(sss.laps, formatTime(lapDur))
    sss.lapStart = sss.elapsed
    return nil
}

func (sss *SplitSecondStopwatch) AdvanceTime(by string) {
    if sss.state == "running" {
        sss.elapsed += parseTime(by)
    }
}

func (sss *SplitSecondStopwatch) State() string { return sss.state }

func (sss *SplitSecondStopwatch) CurrentLap() string { return formatTime(sss.elapsed - sss.lapStart) }

func (sss *SplitSecondStopwatch) Total() string { return formatTime(sss.elapsed) }

func (sss *SplitSecondStopwatch) PreviousLaps() []string { return sss.laps }

func NewSplitSecondStopwatch() *SplitSecondStopwatch {
    return &SplitSecondStopwatch{state: "ready", laps: []string{}}
}
