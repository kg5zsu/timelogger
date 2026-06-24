SIONS` heading
   - Numbered one-line summary per session

3. **One SESSION block per logical unit of work**, each containing:
   - 80-`=` divider
   - `SESSION N — Short title` heading
   - 80-`=` divider (repeated)
   - `START NEW CHAT` / dependency note — e.g. "START NEW CHAT for this
     session." or "START NEW CHAT. Requires SESSION 1 complete."  Each
     session is one chat by default, but multiple small independent
     sessions (e.g. a simple 2-line template change) can be grouped into
     a single chat if the prompt notes it.
   - `BACKGROUND (read before starting):` — file and repo paths to read
   - `CONTEXT:` — prose explaining current state and rationale (omit for
     trivial sessions)
   - `WHAT TO DO:` — numbered steps with sub-steps indented 2 spaces, using
     `-` for sub-bullets
   - `PROMPT FOR THIS SESSION:` — verbatim prompt block wrapped in 80-`-`
     lines (the prompt should tell the agent to read this plan file, implement
     the session, run tests, and write a HANDOFF block)
   - `HANDOFF (filled in by agent after completion):` — initially left blank
     with a `Status: TBD` placeholder; the agent fills in migration numbers,
     test results, deviations
   - 80-`=` divider

### Formatting rules
- One blank line separates sections inside a session block.
- Section labels follow the pattern shown above:
  `BACKGROUND (read before starting):`, `CONTEXT:`, `WHAT TO DO:`,
  `PROMPT FOR THIS SESSION:`, `HANDOFF (filled in by agent after
  completion):`.
- Section dividers: `================================================================================` (80 `=`)
- Prompt block fences: `--------------------------------------------------------------------------------` (80 `-`)
- Sub-step bullets under numbered steps use 2-space indent + `-`
- HANDOFF block is always the last element in each session block, left blank
  until the agent completes the session.
- End the file with `END OF PLAN` inside an 80-`=` block.

