# Development Instructions

Use CodeGraph for structural search and refactoring. Use native text search only for literal strings, comments, generated output, and already-open files.

Commit messages must explain intent and impact: why the change exists, and what behavior or workflow it affects.

## CodeGraph

This project has a CodeGraph MCP server configured. CodeGraph is a tree-sitter parsed knowledge graph of project files. It is the first tool to use for structural questions such as where a symbol is defined, what calls a function, or what will be affected by changing a module.

If the index is empty or stale, run:

```bash
codegraph init -i
codegraph index
```

Running CodeGraph commands is always allowed.

Prefer:

- `codegraph_context` for architecture, feature, and bug context.
- `codegraph_search` for finding a symbol by name.
- `codegraph_callers` and `codegraph_callees` for call relationships.
- `codegraph_impact` before changing shared helpers.
- `codegraph_files` for project structure.

Do not grep first for symbols. Do not loop over many `codegraph_node` calls when one `codegraph_explore` can show related source.
