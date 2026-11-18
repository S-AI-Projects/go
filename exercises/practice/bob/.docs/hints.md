# Hints

## General

- Pay close attention to remarks that contain no letters at all, such as `"1, 2, 3"` or `"4?"`.
- A common mistake is assuming that any string where `strings.ToUpper(remark) == remark` counts as shouting. However, numbers and symbols have no uppercase or lowercase distinction in Go, so `strings.ToUpper("1, 2, 3") == "1, 2, 3"` evaluates to `true` even though no letters are present.
- Shouting requires at least one letter and no lowercase letters. As a small diagnostic check, test your solution against `"1, 2, 3"`: Bob should reply `"Whatever."` instead of classifying it as shouting.
