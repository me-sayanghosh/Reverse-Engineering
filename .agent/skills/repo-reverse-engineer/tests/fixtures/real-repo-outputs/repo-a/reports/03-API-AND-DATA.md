# 03 - API Surface & Data Models: commander.js

## Public API Surface
Commander provides a fluent builder API for constructing CLI programs:
- `program.command(nameAndArgs)`: Registers subcommands (`lib/command.js:80`).
- `program.option(flags, description, defaultValue)`: Defines option flags (`lib/command.js:450`).
- `program.argument(name, description)`: Declares positional parameters (`lib/command.js:520`).
- `program.action(fn)`: Binds execution handler (`lib/command.js:610`).
- `program.parse(argv)`: Synchronously parses argument vector (`lib/command.js:1050`).
- `program.parseAsync(argv)`: Asynchronously parses argument vector (`lib/command.js:1110`).

## Internal Data Structures
- `registeredArguments`: Collection of `Argument` instances (`lib/command.js:31`).
- `_optionValues`: Key-value store of resolved flags (`lib/command.js:39`).
- `_optionValueSources`: Audit trail for value origin (`cli`, `env`, or `default`) (`lib/command.js:40`).
