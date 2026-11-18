# 01 - Architecture & Component Decomposition: commander.js

## Component Overview
Commander is organized around five primary core classes exposed at root:
1. **Command** (`lib/command.js:25`): Central orchestrator managing options, arguments, actions, and subcommand dispatch.
2. **Option** (`lib/option.js:3`): Definition and validation model for flags and switches.
3. **Argument** (`lib/argument.js:3`): Positional argument parsing, default values, and variadic capture.
4. **Help** (`lib/help.js:22`): Terminal output formatter generating styled manual pages.
5. **CommanderError** (`lib/error.js:12`): Structured exit codes and error encapsulation.

```
index.js:7 (program)
    │
    ▼
lib/command.js:25 (Command)
    ├── lib/argument.js:18 (Argument)
    ├── lib/option.js:25 (Option)
    ├── lib/help.js:22 (Help)
    └── lib/error.js:12 (CommanderError)
```

## Module Interactions
- **Export Façade**: `index.js:19-21` re-exports all core classes.
- **Factory Functions**: `index.js:9-13` exposes `createCommand`, `createOption`, and `createArgument`.
- **Subcommand Hierarchy**: `lib/command.js:45` supports executable subcommands spawned via Node subprocesses.
