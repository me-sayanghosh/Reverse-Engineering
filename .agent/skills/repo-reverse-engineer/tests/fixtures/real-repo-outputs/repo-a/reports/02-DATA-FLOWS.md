# 02 - Core Data Flows: commander.js

## 1. CLI Execution & Option Parsing Flow
When a user invokes a command built with Commander:
1. Invocation enters `program.parseAsync(process.argv)` (`lib/command.js:1110`).
2. Arguments normalized via `_prepareUserArgs` (`lib/command.js:1112`).
3. Options split and mapped to flags (`lib/option.js:112`).
4. Matched action callback triggered or help screen rendered (`lib/command.js:42`, `lib/help.js:150`).

```
process.argv
     │
     ▼
lib/command.js:1112 (_prepareUserArgs)
     │
     ▼
lib/command.js:1113 (_parseCommand)
     │
     ├─► lib/option.js:112 (parse options)
     └─► lib/command.js:42 (_actionHandler execute)
```
