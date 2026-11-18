# 05 - Key Algorithms: commander.js

## 1. Flag & Option Normalization
- Short option grouping (e.g. `-abc` -> `-a -b -c`) and option value splitting (`--foo=bar`) in `lib/command.js:35`.
- Coercion and custom parsing functions executed sequentially (`lib/option.js:140`).

## 2. Longest Prefix Subcommand Resolution
- Matches input arguments against registered subcommand names and aliases (`lib/command.js:38`).
- Heuristic fallback to executable files matching `${scriptName}-${subcommand}` (`lib/command.js:44`).
