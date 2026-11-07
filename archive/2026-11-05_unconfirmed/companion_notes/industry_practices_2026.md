# Industry agent-harness practices as of 2026-11-05 (verification and extension of the 2026-11-04 notes)

Scope: material for the comparative-study section of the LAH paper. Nine vendor groups (Anthropic; OpenAI; Google; DeepSeek dsh; LangGraph/LangChain/Deep Agents; OpenHands; Manus; the MCP specification; the A2A specification), each answered against the eight design questions:

- Q1 Source of truth and context assembly
- Q2 Verification and critique
- Q3 Grounding of figures or facts at inference time
- Q4 Approvals and human-in-the-loop (exactly-once vs at-least-once)
- Q5 Durable execution
- Q6 Evaluation
- Q7 Cost and latency controls
- Q8 Security and identity

Method. Every quote below is verbatim, under 40 words, and carries its URL and the date it was read. "(read 2026-11-05)" means fetched today from the live page. "(carried over from the 2026-11-04 notes; not re-fetched)" means the quote is taken from the six notes in `research_notes/Mia harness gap analysis and harness2/` and was not re-read today. Where today's page wording differs from what the 2026-11-04 notes recorded, the difference is called out under "Verification findings" in each vendor section. Anything unreachable is marked UNVERIFIED with the date. Numbers and dates come from the vendor's own page, never from a model's summary; where a fetch tool paraphrased a figure rather than quoting it, the entry says "paraphrase".

Three cross-cutting facts the 2026-11-04 notes did not record, verified today:

1. The current MCP specification revision is `2026-07-28` (previous `2025-11-25`). It removed protocol-level sessions and made every request stateless; the draft changelog for the next revision is empty as of 2026-11-05. See the MCP section.
2. Nothing new shipped between 2026-11-04 and 2026-11-05 for ADK (still v2.13.0), Claude Code (npm `latest` 2.1.318, published 2026-11-03), the OpenAI Agents SDK (v0.24.0 stable, 0.24.0-alpha.6 pre-release 2026-11-03) or the MCP spec. DeepSeek published `@deepseek-ai/dsh@0.2.2-rc.1` to the `next` tag on 2026-11-04T09:20Z. See "What changed since 2026-11-04".
3. Only two vendors make an explicit statement about tool-execution semantics after an interruption or approval: OpenAI ("does not guarantee exactly-once execution") and Google ("may run more than once when resuming a workflow"). LangGraph says it for graph retries ("It does not make external side effects happen exactly once."). Anthropic, dsh, OpenHands and Manus leave it unstated.

---

## Anthropic (Claude Code, Agent SDK, Managed Agents, Claude API)

### Takeaway
Anthropic's harness is a thin model-plus-tools loop bounded by harness-enforced controls: hooks with an exit-code contract, deny rules that hold in every mode, a classifier that sees no tool results, dollar and turn caps, and a rubric grader run in a separate context window. Managed Agents makes the session an append-only server-side event log and the harness stateless. Exactly-once tool execution is nowhere promised; duplicate custom-tool results are accepted and ignored.

### Cited Findings

#### Q1 Source of truth and context assembly
- The Managed Agents session is "the append-only log of everything that happened" and serves "as a context object that lives outside Claude's context window." - [Scaling Managed Agents (2026-04-08)](https://www.anthropic.com/engineering/managed-agents) (read 2026-11-05)
- "Any fetched events can also be transformed in the harness before being passed to Claude's context window." - [Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents) (read 2026-11-05)
- "But irreversible decisions to selectively retain or discard context can lead to failures." - [Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents) (read 2026-11-05)
- "Event history is persisted server-side and can be fetched in full." and "The harness supports built-in prompt caching, compaction, and other performance optimizations for high-quality, efficient agent outputs." - [Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) (read 2026-11-05)
- Agent SDK session definition: "It contains your prompt, every tool call the agent made, every tool result, and every response. The SDK writes it to disk automatically so you can return to it later." - [Work with sessions](https://code.claude.com/docs/en/agent-sdk/sessions) (read 2026-11-05)
- "Claude Code stores sessions under `~/.claude/projects/<encoded-cwd>/*.jsonl`." and "Sessions persist the conversation, not the filesystem." - [Work with sessions](https://code.claude.com/docs/en/agent-sdk/sessions) (read 2026-11-05)
- Compaction in the SDK loop: "Compaction replaces older messages with a summary, so specific instructions from early in the conversation may not be preserved." and "CLAUDE.md content is re-injected on every request." - [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) (read 2026-11-05)
- API compaction: "Compaction replaces the older turns of a conversation with a summary that Claude writes on the server, so you need no summarization code of your own." and "Use on-demand compaction wherever it is available." - [Compaction overview](https://platform.claude.com/docs/en/build-with-claude/compaction) (read 2026-11-05)
- Threshold mode: "The response, appended as usual. The API drops what came before the block" - [Compaction overview](https://platform.claude.com/docs/en/build-with-claude/compaction) (read 2026-11-05)
- On-demand summarizer rules: "A summary is produced only when the summarization call ends normally with text and no tool call." and "Without `instructions`, the API uses its own summarization prompt. A non-blank `instructions` string (up to 16,384 characters) replaces that prompt entirely." - [Compaction on demand](https://platform.claude.com/docs/en/build-with-claude/compaction-on-demand) (read 2026-11-05)
- Claude Code default: "Sessions auto-compact at about 967K tokens by default." (Haiku 5.5 section; per-model table not read) - [Model configuration](https://code.claude.com/docs/en/model-config) (read 2026-11-05)
- Idle compaction (v2.1.314): "Added idle compaction to VS Code and Claude Desktop's Code tab: a 200K+ token conversation left idle is summarized" - [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) (read 2026-11-05)
- Cache-safe compaction design and the "about 20k tokens" summary size: carried over from the 2026-11-04 notes ([Prompt caching is everything, 2026-04-30](https://claude.dev/blog/lessons-from-building-claude-code-prompt-caching-is-everything/)); not re-fetched.

#### Q2 Verification and critique
- "Every instruction you give Claude Code is one of these:" ... "2. Deterministic: you configure the instruction, and Claude Code (the harness) *has* to execute this. This can be a hook, a deny rule, or a managed setting." - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- "If you keep adding emphasis to a `CLAUDE.md` line and Claude still misses it, that's a sign the line belongs in a hook." - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- "Claude stops when the work looks done. If it has nothing to run that tells it whether the work actually *is* done, "looks done" is all it has to go on." - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- Table row: "When it's done | A request for evidence, `/goal`, `/code-review` | Tests, typecheck, a `Stop` hook, CI" - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- Stop hook example: `{ "type": "command", "command": "pnpm tsc --noEmit 1>&2 || exit 2" }`; "If the hook blocks eight stops in a row with no tool call between them, Claude Code overrides the next block and ends the turn." - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- Fresh-context reviewer: "`/code-review` reviews the diff in a fresh subagent that never saw your conversation. It isn't swayed by the reasoning that produced the code." - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- Evidence over claims: "ask Claude for *evidence*: the command it ran and its output, or the screenshot. "All tests pass" on its own tells you very little" - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- "A reviewer that's asked to find problems will always find *something*." - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- "If you ever find yourself at forty of them, most are probably preferences that Claude could have weighed on its own." - [Best practices](https://code.claude.com/docs/en/best-practices) (read 2026-11-05)
- Hook contract: "**Success**: your hook exits 0." and "**Blocking error**: your hook exits 2. On events that can block, Claude Code stops the action." Stop event: "Prevents Claude from stopping, continues the conversation." PostToolUse: "Shows stderr to Claude; the tool already ran." - [Hooks reference](https://code.claude.com/docs/en/hooks) (read 2026-11-05)
- Fail-open by default: "On most events, when a hook fails or times out, Claude Code still carries out the action." Fail-closed opt-in: "To block the action instead, set `"onFailure": "block"` on a `command` or `http` hook. Requires Claude Code v2.1.295 or later." - [Hooks reference](https://code.claude.com/docs/en/hooks) (read 2026-11-05)
- Agent SDK parity (v2.1.317, 2026-11-02): "Added `onFailure: "block"` for Agent SDK hook callbacks, so a callback that fails blocks the action" - [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) (read 2026-11-05)
- Five handler types, "command", "http", "mcp_tool", "prompt", "agent"; "Defaults: 600 for `command`, `http`, and `mcp_tool`; 30 for `prompt`; 60 for `agent`." - [Hooks reference](https://code.claude.com/docs/en/hooks) (read 2026-11-05)
- Separate grader: "the harness automatically provisions a *grader* to evaluate the artifact against a rubric. The grader uses a separate context window to avoid being influenced by the main agent's implementation choices." - [Define outcomes](https://platform.claude.com/docs/en/managed-agents/define-outcomes) (read 2026-11-05)
- "The grader scores each criterion independently, so vague criteria produce noisy evaluations." and "The grader's internal reasoning is opaque: the event shows only that the grader is working." `max_iterations` "optional; default 3, max 20"; results `satisfied`, `needs_revision`, `max_iterations_reached`, `failed`, `interrupted`. - [Define outcomes](https://platform.claude.com/docs/en/managed-agents/define-outcomes) (read 2026-11-05)
- "it's often better to grade what the agent produced, not the path it took." and "Read the transcripts!" - [Demystifying evals (2026-01-09)](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (read 2026-11-05)
- `/goal` as a prompt-based Stop hook on the small fast model, cannot call tools: carried over from the 2026-11-04 notes ([/goal](https://code.claude.com/docs/en/goal)); not re-fetched.

#### Q3 Grounding of figures or facts at inference time
- No first-party inference-time figure check exists; the mechanisms are outcome graders and tool-result rewriting. Outcome over claim: "the outcome is whether a reservation exists in the environment's SQL database." - [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (read 2026-11-05)
- The artifact, not the chat, is graded: "The agent writes output files to `/mnt/session/outputs/` inside the sandbox." - [Define outcomes](https://platform.claude.com/docs/en/managed-agents/define-outcomes) (read 2026-11-05)
- Harness can rewrite what the model sees: "`PostToolUse`: `updatedToolOutput` replaces the tool's result." and "`updatedInput` directly under `hookSpecificOutput` replaces a tool's arguments before it runs." - [Hooks reference](https://code.claude.com/docs/en/hooks) (read 2026-11-05)
- Injected context must be factual, not imperative: "Write the text as factual statements rather than imperative system instructions." and "Text framed as out-of-band system commands can trigger Claude's prompt-injection defenses, which causes Claude to surface the text to you instead of treating it as context." - [Hooks reference](https://code.claude.com/docs/en/hooks) (read 2026-11-05)
- Tool-output design guidance ("Return meaningful context", 25,000-token cap): carried over from the 2026-11-04 notes ([Writing effective tools](https://www.anthropic.com/engineering/writing-tools-for-agents)); not re-fetched.
- Left to the builder: comparing reply figures to tool-result figures (no Anthropic mechanism; inference).

#### Q4 Approvals and human-in-the-loop
- Managed Agents policies: `always_allow`, `always_ask`, `auto`; "the agent toolset defaults to `always_allow`, and MCP toolsets default to `always_ask`." - [Permission policies](https://platform.claude.com/docs/en/managed-agents/permission-policies) (read 2026-11-05)
- "The session waits indefinitely for a response." and "If you send a `user.tool_confirmation` for an event whose `evaluated_permission` is not `ask`, the API rejects it with a 400 error." - [Permission policies](https://platform.claude.com/docs/en/managed-agents/permission-policies) (read 2026-11-05)
- "`auto` is not a human checkpoint. If the server determines that a call is safe, the call runs before anyone sees it, and its effects might not be reversible." - [Permission policies](https://platform.claude.com/docs/en/managed-agents/permission-policies) (read 2026-11-05)
- On deny: "Denied tools do not run, and the agent receives a tool result saying the call was rejected, including your `deny_message`." - [Permission policies](https://platform.claude.com/docs/en/managed-agents/permission-policies) (read 2026-11-05)
- Audit field: "A `reason_code` is a value for your client to branch on and keep in audit records, not text to display to end users." - [Permission policies](https://platform.claude.com/docs/en/managed-agents/permission-policies) (read 2026-11-05)
- Duplicate results are idempotent: "A second result for the same call is accepted and has no effect." (custom tools) - [Session event stream](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) (read 2026-11-05)
- Agent SDK evaluation order (hooks, deny rules, ask rules, mode, allow rules, `canUseTool`): "**Auto-approved tools never reach `canUseTool`.**" and "A hook deny applies even in `bypassPermissions` mode." - [Configure permissions](https://code.claude.com/docs/en/agent-sdk/permissions) (read 2026-11-05)
- "Deny rules block in every mode, including `bypassPermissions`." - [Permission modes](https://code.claude.com/docs/en/permission-modes) (read 2026-11-05)
- Tool denial seen by the model: "When a tool is denied, Claude receives a rejection message as the tool result and typically attempts a different approach or reports that it couldn't proceed." - [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) (read 2026-11-05)
- Exactly-once / at-least-once: no statement on any Anthropic page read. The only retry language is the session status "`rescheduling` | Transient error occurred, retrying automatically." - [Session operations](https://platform.claude.com/docs/en/managed-agents/session-operations) (read 2026-11-05)

#### Q5 Durable execution
- "Because the session log sits outside the harness, nothing in the harness needs to survive a crash." Recovery is `wake(sessionId)`; progress is written with `emitEvent(id, event)`; hands are "`execute(name, input) → string`". - [Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents) (read 2026-11-05)
- Statuses: `idle`, `running`, "`rescheduling` | Transient error occurred, retrying automatically.", "`terminated` | Session has ended, either because of an unrecoverable error or because it was archived." - [Session operations](https://platform.claude.com/docs/en/managed-agents/session-operations) (read 2026-11-05)
- "sessions are long-running, resume cleanly after pauses, and store conversation history, sandbox state, and outputs server-side." - [Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) (read 2026-11-05)
- Sandbox state limit: "Sandbox state is preserved for only 30 days after the sandbox is created, and activity does not extend this window." - [Session event stream](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) (read 2026-11-05)
- Agent SDK after a crash: "After a session crash, the final result is an `error_during_execution` whose cost fields may be zeroed and whose `stop_reason` is `null`, and the process exits after emitting it." - [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) (read 2026-11-05)
- Cross-host advice: "Don't rely on session resume." ... "This is often more robust than shipping transcript files around." A `sessionStore` adapter mirrors transcripts "so the SDK mirrors transcripts to your own backend and another host can resume them." - [Work with sessions](https://code.claude.com/docs/en/agent-sdk/sessions) (read 2026-11-05)
- At-least-once tool execution on resume: not stated anywhere read (gap).

#### Q6 Evaluation
- pass@k "measures the likelihood that an agent gets at least one correct solution in k attempts"; pass^k "measures the probability that all k trials succeed."; "the probability of passing all three is (0.75)³ ≈ 42%." - [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (read 2026-11-05)
- "20-50 simple tasks drawn from real failures is a great start."; regression evals "should have a nearly 100% pass rate."; "Each trial should be "isolated" by starting from a clean environment." - [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (read 2026-11-05)
- Judge design: "give the LLM a way out, like providing an instruction to return "Unknown""; "grade each dimension with an isolated LLM-as-judge rather than using one to grade all dimensions."; "LLM-as-judge graders should be closely calibrated with human experts" - [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (read 2026-11-05)
- Grader bugs: "Opus 4.5 initially scored 42% on CORE-Bench" ... "After fixing bugs and using a less constrained scaffold, Opus 4.5's score jumped to 95%." - [Demystifying evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (read 2026-11-05)
- Shipped CI tooling (Claude Code v2.1.269+): "One run of a non-deterministic agent tells you little, so each case runs three times by default." - [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals) (read 2026-11-05)
- "There are no custom-code graders." Six grader types: `regex`, `tool_used`, `tool_order`, `file_exists`, `llm`, `baseline`. - [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals) (read 2026-11-05)
- Baseline delta: "Their difference, `Δ`, is what the plugin contributed." and "The with-minus-without delta is reported but never changes the exit code" - [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals) (read 2026-11-05)
- Gating: `--threshold` default `1.0`; "Any case below it makes the command exit 1"; `--model`: "Pin it in CI so a model rollout isn't mistaken for a plugin regression"; exit 2 is a partial run when `--max-cost-usd` is hit. - [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals) (read 2026-11-05)
- Judge instability: "An `llm` grader asks a model for a verdict, so its answer can differ between runs, and it differs more the longer the text it has to read." and "A single run is noisy, so confirm any change at the default three runs before you trust it." - [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals) (read 2026-11-05)
- Replay fixtures: "Commit `mocks/.replay/` with the rest of `mocks/` so CI runs are repeatable." - [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals) (read 2026-11-05)

#### Q7 Cost and latency controls
- SDK caps: `max_turns` "No limit", `max_budget_usd` "No limit"; "Setting a budget is a good default for production agents." - [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) (read 2026-11-05)
- Overshoot: "Spend can therefore pass the cap by up to the cost of that one response, plus anything that subagents still running at that moment spend before they stop. Leave headroom for this when you set the cap." and "The cap-enforcement behaviors require Claude Code v2.1.217 or later." - [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) (read 2026-11-05)
- Managed Agents budget: "A budget is a hard ceiling on the session's list cost"; "`amount` is a whole number of US cents written as a string, such as `"125"` for $1.25 USD. The API takes a string rather than a number so no floating-point rounding is ever applied." - [Start a session](https://platform.claude.com/docs/en/managed-agents/sessions) (read 2026-11-05)
- "When the session reaches the cap, it pauses and goes idle with the stop reason `budget_reached`." and "The cap is enforced between model requests, so the request that crosses it completes first" - [Start a session](https://platform.claude.com/docs/en/managed-agents/sessions) (read 2026-11-05)
- Effort: "`effort` trades latency and token cost for reasoning depth within each response." Defaults: "`high` on every model that supports effort, except that Opus 5.5, Sonnet 5.5, and Haiku 5.5 default to `medium` and Opus 4.7 defaults to `xhigh`." - [Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop); [Model configuration](https://code.claude.com/docs/en/model-config) (read 2026-11-05)
- Fallback models: "Configure one or more fallback models and Claude Code tries them in order, showing a notice when it switches." and "Claude Code caps chains at three models after duplicate removal and ignores extra entries." - [Model configuration](https://code.claude.com/docs/en/model-config) (read 2026-11-05)
- Caching prices: "Cache write tokens with a 5-minute TTL are 1.25 times the base input tokens price."; "Cache read tokens are 0.1 times the base input tokens price"; "Cache hits and refreshes on Claude Fable 5.1 and Claude Mythos 5.1 are priced at 0.025x the base input price." - [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) (read 2026-11-05)
- "Cache hits require 100 percent identical prompt segments, including all text and images up to and including the block marked with cache control."; "Modifying tool definitions (names, descriptions, parameters) invalidates the entire cache"; "cache hits are not deducted against your rate limit." Minimum prefix 512 tokens on Fable 5.1 / Opus 5.5 / Sonnet 5.5 / Haiku 5.5. - [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) (read 2026-11-05)
- Compaction billing: "The summarization call is billed and rate-limited like any other request, and `usage.iterations` reports it as the `compaction` entry." - [Compaction on demand](https://platform.claude.com/docs/en/build-with-claude/compaction-on-demand) (read 2026-11-05)
- Subagent effort (v2.1.316): "Added `CLAUDE_CODE_SUBAGENT_EFFORT` to set the effort level subagents run at when nothing else names one" - [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) (read 2026-11-05)
- Parallel tools: "Read-only tools (like `Read`, `Glob`, `Grep`, and MCP tools marked as read-only) can run concurrently." and "To enable parallel execution for a custom tool, set `readOnlyHint` in its annotations." - [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop) (read 2026-11-05)
- Cache-hit monitoring as an SLO ("declare SEVs if they're too low"): carried over from the 2026-11-04 notes ([Prompt caching is everything](https://claude.dev/blog/lessons-from-building-claude-code-prompt-caching-is-everything/)); not re-fetched.

#### Q8 Security and identity
- Auto mode: "a second model, the classifier, reviews actions instead of you." and "Tool results are stripped from those requests, so hostile content in a file or web page can't manipulate the classifier directly." - [Permission modes](https://code.claude.com/docs/en/permission-modes) (read 2026-11-05)
- "if the classifier blocks an action 3 times in a row or 20 times total, auto mode pauses and Claude Code resumes prompting." and "By default, classifier requests go to Claude Sonnet 5." - [Permission modes](https://code.claude.com/docs/en/permission-modes) (read 2026-11-05)
- Conversational boundaries are not security: "a boundary can be lost if context compaction removes the message that stated it. For a hard guarantee, add a deny rule instead." - [Permission modes](https://code.claude.com/docs/en/permission-modes) (read 2026-11-05)
- "For most fetches, WebFetch runs a separate model call over the page, and Claude receives that call's answer instead of the raw page." and "**Fail-closed matching**: In Manual mode, unmatched commands require approval by default" - [Security](https://code.claude.com/docs/en/security) (read 2026-11-05)
- "Avoid piping untrusted content directly to Claude"; sandbox: "Sandbox bash commands with filesystem and network isolation, reducing permission prompts while maintaining security." - [Security](https://code.claude.com/docs/en/security) (read 2026-11-05)
- Audit: "**Audit logging**: All operations in cloud sessions are logged for compliance and audit purposes" and "Monitor Claude Code usage through OpenTelemetry metrics" - [Security](https://code.claude.com/docs/en/security) (read 2026-11-05)
- MCP trust: "Anthropic reviews connectors against its listing criteria before adding them to the Anthropic Directory, but does not security-audit or manage any MCP server." - [Security](https://code.claude.com/docs/en/security) (read 2026-11-05)
- Managed Agents credential boundary: "make sure the tokens are never reachable from the sandbox." and "The harness is never made aware of any credentials." - [Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents) (read 2026-11-05)
- `auto` policy and injected intent: "The server does not read intent from a tool result, a fetched webpage, an MCP server's response, or a message between session threads. It assesses that content but does not take instructions from it." - [Permission policies](https://platform.claude.com/docs/en/managed-agents/permission-policies) (read 2026-11-05)
- Default-blocked list includes "Downloading and executing code, like `curl | bash`," "Force push," "Production deploys and migrations," and actions that appear "driven by hostile content Claude read." - [Permission modes](https://code.claude.com/docs/en/permission-modes) (read 2026-11-05)

### Verification findings against the 2026-11-04 notes
- The notes quote the engineering post as "irreversible compaction or trimming can lose information that later turns need"; the page's wording is "But irreversible decisions to selectively retain or discard context can lead to failures." Use the latter.
- The notes quote the evals post as regression evals "should stay near 100%"; the page says "should have a nearly 100% pass rate." The notes also attribute "pin models in CI" to the evals post; that advice is on the plugin-evals page, not the evals post.
- The notes quote the auto-mode page as "Actions that look driven by content Claude read rather than by you"; today's page says the classifier blocks actions that appear "driven by hostile content Claude read". Treat the notes' phrasing as paraphrase.
- `code.claude.com/docs/en/agent-loop` (the URL in the notes) returns 404; the live page is `code.claude.com/docs/en/agent-sdk/agent-loop`.
- Everything else spot-checked (hook exit codes, onFailure v2.1.295, three-run plugin evals, budget overshoot, grader in a separate context window, classifier stripping tool results) matches.

### Inferences
- Anthropic's harness answers Q4/Q5 with idempotent acceptance of duplicate results and a replayable log, not with an exactly-once promise; a builder who needs exactly-once must add idempotency keys on side-effecting tools (OpenAI says this explicitly; Anthropic leaves it unsaid).
- The two Anthropic controls that transfer directly to a figure-grounding harness are `updatedToolOutput` (rewrite what the model sees) and a Stop/outcome check run in a fresh context; both are deterministic seams, not prompts.

### Gaps
- No Anthropic page read states what happens to an in-flight tool call when a Managed Agents environment dies mid-execution (replay vs skip). UNVERIFIED (2026-11-05).
- The per-model auto-compact table on the model-config page was past the fetch cut; only the Haiku 5.5 value (967K) is verified.

---

## OpenAI (Agents SDK, Responses API, Codex)

### Takeaway
OpenAI is the one vendor that writes down the approval semantics: approval "does not guarantee exactly-once execution", snapshots are unauthenticated, and idempotency keys are the builder's job. Context is either client sessions or server-side compaction into an opaque encrypted item; the hosted Evals product is read-only since 2026-10-31 and shuts down 2026-11-30, so the durable eval guidance is code-first (10 to 20 prompts, deterministic checks before a judge). Codex layers an OS sandbox, an approval policy, an LLM reviewer with published recall, and an async monitor, and says none of the model-based layers is a security guarantee.

### Cited Findings

#### Q1 Source of truth and context assembly
- Sessions: "The runner automatically retrieves the conversation history for the session and prepends it to the input items." - [Sessions](https://openai.github.io/openai-agents-python/sessions/) (read 2026-11-05)
- Integrity of the store is the builder's: the SQLite backend "does not authenticate stored rows or detect external edits" - [Sessions](https://openai.github.io/openai-agents-python/sessions/) (read 2026-11-05)
- `OpenAIResponsesCompactionSession` "can automatically compact after each turn based on should_trigger_compaction."; "compaction_mode="input" rebuilds the compaction request from the current session items instead" - [Sessions](https://openai.github.io/openai-agents-python/sessions/) (read 2026-11-05)
- Mutual exclusion: "a session cannot be combined with the run-level continuation options" (`conversation_id`, `previous_response_id`, `auto_previous_response_id`) - [Sessions](https://openai.github.io/openai-agents-python/sessions/) (read 2026-11-05)
- Server-side compaction: "When the rendered token count crosses the configured threshold, the server runs server-side compaction."; the item "is opaque and not intended to be human-interpretable" and "carries forward key prior state and reasoning using fewer tokens" - [Context management](https://developers.openai.com/api/docs/guides/context-management) (read 2026-11-05)
- "If you use `previous_response_id` chaining, do not manually prune." and "server-side compaction is ZDR-friendly when you set `store=false` on your Responses create requests." - [Context management](https://developers.openai.com/api/docs/guides/context-management) (read 2026-11-05)
- Last-mile edit hook: "Use call_model_input_filter to edit the model input right before the model call." - [Running agents](https://openai.github.io/openai-agents-python/running_agents/) (read 2026-11-05)
- Codex hooks: "`PreCompact` runs before Codex compacts the chat." - [Codex hooks](https://learn.chatgpt.com/codex/hooks) (read 2026-11-05)
- v0.24.0 (2026-10-15): "defer automatic compaction for pending approvals" and "replace Redis compaction history atomically" - [openai-agents-python releases](https://github.com/openai/openai-agents-python/releases) (read 2026-11-05)
- "evals showed performance declining with more /compact or auto-compactions per session": carried over from the 2026-11-04 notes (Ghosts in the Codex Machine mirror); not re-fetched.

#### Q2 Verification and critique
- "Input guardrails run only for the first agent in the chain." Output guardrails run only on the agent producing the final output; "The runner immediately raises an `InputGuardrailTripwireTriggered` or `OutputGuardrailTripwireTriggered` exception." - [Guardrails](https://openai.github.io/openai-agents-python/guardrails/) (read 2026-11-05)
- Optimistic by default: "if the guardrail's tripwire is triggered, the agent may have already consumed tokens and executed tools before being cancelled." - [Guardrails](https://openai.github.io/openai-agents-python/guardrails/) (read 2026-11-05)
- Tool-level guards: input guardrails "can skip the call, replace the output with a message, or raise a tripwire."; output guardrails "can replace the output or raise a tripwire."; withheld placeholder "Output withheld by an output guardrail." - [Guardrails](https://openai.github.io/openai-agents-python/guardrails/) (read 2026-11-05)
- Ordering with approvals: `pre_approval_tool_input_guardrails=True` runs input checks "before the pending approval interruption is emitted." - [Guardrails](https://openai.github.io/openai-agents-python/guardrails/) (read 2026-11-05)
- Codex Stop hook: "For this event, `decision: "block"` doesn't reject the turn." Codex "automatically creates a new continuation prompt that acts as a new user prompt"; exit code: "You can also use exit code `2` and write the blocking reason to `stderr`."; "Non-managed hooks must be reviewed and trusted before they run." - [Codex hooks](https://learn.chatgpt.com/codex/hooks) (read 2026-11-05)
- Reviewer model: "It replaces user approval at the sandbox boundary with review by a separate agent." - [Auto-review (2026-04-30)](https://alignment.openai.com/auto-review) (read 2026-11-05)
- Deterministic first: "They give you fast, explainable signals before you add any model-based grading." - [Testing Agent Skills Systematically with Evals (2026-01-22)](https://learn.chatgpt.com/blog/eval-skills) (read 2026-11-05)

#### Q3 Grounding of figures or facts at inference time
- No first-party figure check. The levers are tool output guardrails ("can replace the output or raise a tripwire.", above), strict structured outputs ("ensures the model will always generate responses that adhere to your supplied JSON Schema", carried over from the 2026-11-04 notes, [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), not re-fetched) and `tool_use_behavior="stop_on_first_tool"` (carried over, [Agents](https://openai.github.io/openai-agents-python/agents/), not re-fetched).
- Codex cloud evidence citations ("verifiable evidence of its actions through citations of terminal logs and files"): carried over from the 2026-11-04 notes (system card addendum via search summary); UNVERIFIED against the primary page (2026-11-05).

#### Q4 Approvals and human-in-the-loop
- "Callable approval rules fail closed when the SDK cannot safely inspect the arguments" - [Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/) (read 2026-11-05)
- "Approval permits a tool call to execute; it does not guarantee exactly-once execution." and "assign a stable idempotency key to each logical action." - [Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/) (read 2026-11-05)
- "resuming from the older approved snapshot can execute the tool again." - [Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/) (read 2026-11-05)
- "`RunState.from_json()` and `RunState.from_string()` do not authenticate the snapshot or the person submitting it." - [Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/) (read 2026-11-05)
- Server-side validation: "Validate the submitted decision identifiers and boolean decisions against the pending requests stored on the server." and "use an atomic owner-checked transition before starting resumed execution" - [Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/) (read 2026-11-05)
- Scoping: "sticky decisions are scoped to the agent that requested approval."; for shell/file tools an `always_approve=True` decision "can apply to another agent's tool of the same type and name after a handoff." - [Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/) (read 2026-11-05)
- Codex annotations: "Destructive app/MCP tool calls always require approval when the tool advertises a destructive annotation" (a read annotation takes priority). - [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security.md) (read 2026-11-05)
- Auto-review fail-closed: "Prompt-build, review-session, and parse failures fail closed." and "Timeouts are surfaced separately, but the action still does not run." - [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security.md) (read 2026-11-05)
- v0.23.0: "core: scope function tool approvals to their owning agent" - [releases](https://github.com/openai/openai-agents-python/releases) (read 2026-11-05)

#### Q5 Durable execution
- "The integrations below are for durable orchestration when runs may span long waits, retries, or process restarts." (Dapr, Temporal, Restate, DBOS) - [Running agents](https://openai.github.io/openai-agents-python/running_agents/) (read 2026-11-05)
- `RunState` is used "when resuming a paused run or a run stopped with cancel(mode="after_turn")" - [Running agents](https://openai.github.io/openai-agents-python/running_agents/) (read 2026-11-05)
- Compaction failure: "If the underlying backend also fails during recovery, the previous history can remain unrestored." - [Sessions](https://openai.github.io/openai-agents-python/sessions/) (read 2026-11-05)
- Pre-release 0.24.0-alpha.6 (2026-11-03): "Add idle forks, caller-supplied compaction summaries, and checks for feature support and checkpoint readiness." and "Add `LocalStorage` to reopen conversations from a local profile" - [releases](https://github.com/openai/openai-agents-python/releases) (read 2026-11-05)
- Background mode (`background: true`, `starting_after` cursor, idempotent `/cancel`) and the April 2026 sandbox snapshot/resume: carried over from the 2026-11-04 notes; not re-fetched.

#### Q6 Evaluation
- Product status: "Evals will become read-only for existing users on October 31, 2026" and "the platform is scheduled to shut down on November 30, 2026." - [Deprecations, 2026-06-03 entry](https://developers.openai.com/api/docs/deprecations#2026-06-03-evals-platform) (the `/guides/evals` URL redirects here; read 2026-11-05)
- "Concretely, an eval is: a prompt → a captured run (trace + artifacts) → a small set of checks → a score" - [Testing Agent Skills Systematically with Evals](https://learn.chatgpt.com/blog/eval-skills) (read 2026-11-05)
- "a small set of 10–20 prompts is enough to surface regressions"; "Including at least one `should_trigger=false` case helps catch"; four check categories: outcome, process, style, efficiency. - [Eval skills post](https://learn.chatgpt.com/blog/eval-skills) (read 2026-11-05)
- "Instead of asking "does this feel better?" (or relying on vibes)" and "Every manual fix is a signal. Turn it into a test so the skill keeps getting it right." - [Eval skills post](https://learn.chatgpt.com/blog/eval-skills) (read 2026-11-05)
- Trials per case: not stated; examples run each prompt once. CI: "If you later move this eval suite into CI, the Codex GitHub Action explicitly supports passing" (sentence continues on the page). - [Eval skills post](https://learn.chatgpt.com/blog/eval-skills) (read 2026-11-05)
- Effort tied to evals: `xhigh` "Only use when your evals show a clear benefit that justifies the extra latency and cost." - [Reasoning](https://developers.openai.com/api/docs/guides/reasoning) (read 2026-11-05)
- Safety eval data: "Internal OpenAI traffic undersamples the long tail of possibly dangerous scenarios." - [Auto-review](https://alignment.openai.com/auto-review) (read 2026-11-05)
- Tracing (the substrate for trace grading): "Tracing is enabled by default."; "By default, `trace_include_sensitive_data` is `True`."; "Tracing is unavailable for organizations that use OpenAI's APIs under a Zero Data Retention (ZDR) policy." - [Tracing](https://openai.github.io/openai-agents-python/tracing/) (read 2026-11-05)

#### Q7 Cost and latency controls
- "Supported values are model-dependent and can include `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, and `max`."; "GPT-6.1 Sol does not support `none` or `minimal` and defaults to `medium`." - [Reasoning](https://developers.openai.com/api/docs/guides/reasoning) (read 2026-11-05)
- `low` is "Ideal for use cases requiring tool-use, planning, search, or multi-step decision making"; "OpenAI recommends reserving at least 25,000 tokens for reasoning and outputs" - [Reasoning](https://developers.openai.com/api/docs/guides/reasoning) (read 2026-11-05)
- Caching: "For GPT-5.6 and later, cache writes cost 1.25× the standard, uncached input-token rate for the default 30-minute lifetime."; "In the Responses API, you can choose a 12-hour minimum lifetime at a write rate of 2.5× ordinary input."; reads "0.1× the ordinary input rate on most of these models and 0.05× on" GPT-6.1 Sol and Terra. - [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) (read 2026-11-05)
- "The minimum cacheable prompt length is 1,024 tokens for GPT-5.6 and later"; "Cache reuse requires the entire rendered prefix to match."; "Cached input tokens still count toward tokens-per-minute limits." - [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) (read 2026-11-05)
- "Preserve tool definitions, ordering, and schemas."; "Append new messages rather than rewriting earlier turns."; "Summarization, compaction, or context truncation can change the prefix and reset cache reuse." - [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching) (read 2026-11-05)
- Mid-conversation effort change: "This preserves the original prompt prefix for prompt caching" (`configuration_update`) - [Reasoning](https://developers.openai.com/api/docs/guides/reasoning) (read 2026-11-05)
- Loop cap: "If we exceed the max_turns passed, we raise a MaxTurnsExceeded exception."; `RunConfig.model` "Allows setting a global LLM model to use, irrespective of what model each Agent has." - [Running agents](https://openai.github.io/openai-agents-python/running_agents/) (read 2026-11-05)
- Flex tier at Batch rates, background mode, Codex subagent model/effort overrides: carried over from the 2026-11-04 notes; not re-fetched.

#### Q8 Security and identity
- Codex sandbox modes: read-only "The agent can inspect files, but it can't edit files or run commands without approval."; workspace-write "The agent can read files, edit within the workspace, and run routine local commands inside that boundary."; danger-full-access "The agent runs without sandbox restrictions." - [Sandboxing](https://learn.chatgpt.com/docs/sandboxing.md) (read 2026-11-05)
- "The sandbox applies to spawned commands, not just to built-in file operations." and "On macOS, sandboxing works out of the box using the built-in Seatbelt framework." - [Sandboxing](https://learn.chatgpt.com/docs/sandboxing.md) (read 2026-11-05)
- Network: "By default, the agent runs with network access turned off." and "`deny` always wins over `allow`, and global `*` is only valid for allow rules." - [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security.md) (read 2026-11-05)
- Injection: "Treat web results as untrusted." and "Prompt injection can cause the agent to fetch and follow untrusted instructions." - [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security.md) (read 2026-11-05)
- Async monitor: "Monitoring runs asynchronously and can pause a task if it detects potentially unsafe model behavior." - [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security.md) (read 2026-11-05)
- Cloud secrets: "Secrets configured for cloud environments are available only during setup and are removed before the agent phase starts." - [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security.md) (read 2026-11-05)
- Audit/telemetry defaults: "Codex turns off OTel export by default to keep local runs self-contained." and "Keep `log_user_prompt = false` unless policy explicitly permits storing prompt contents." - [Agent approvals and security](https://learn.chatgpt.com/docs/agent-approvals-security.md) (read 2026-11-05)
- Auto-review numbers: "Codex sessions stop for human approval roughly 200x less often than in manual approval mode"; auto-approval rate on escalated actions 99.1%, effective approval rate on all actions 99.93%; recall "Overeagerness Recall" 90.3%, "Prompt Injection Recall" 99.3%, "MonitoringBench [Hard] Recall" 96.1%. - [Auto-review](https://alignment.openai.com/auto-review) (read 2026-11-05)
- "Auto-review should not be treated as a guarantee of security." and "Today, a majority of Codex Desktop token usage within OpenAI comes from Auto-review mode, and that share is growing" - [Auto-review](https://alignment.openai.com/auto-review) (read 2026-11-05)
- Tracing processors: "The default provider catches a processor's callback exceptions and continues calling the other registered processors." - [Tracing](https://openai.github.io/openai-agents-python/tracing/) (read 2026-11-05)

### Verification findings against the 2026-11-04 notes
- The notes' caching quotes "Keep tool definitions, ordering, and schemas stable. Use `tool_choice: 'none'` ..." and "Append new messages instead of rewriting earlier turns. Summarization or compaction can reduce reuse." are paraphrases; today's wording is "Preserve tool definitions, ordering, and schemas." / "Append new messages rather than rewriting earlier turns." / "Summarization, compaction, or context truncation can change the prefix and reset cache reuse."
- The notes' Codex line "Destructive app or MCP tools always require approval, unless they also advertise a read annotation" is a paraphrase of "Destructive app/MCP tool calls always require approval when the tool advertises a destructive annotation".
- The notes attribute "Authorization and impact are assessed separately" to the alignment post; it is from the Kundel talk. The alignment post contains no fail-closed language; fail-closed is on the approvals doc.
- Everything else spot-checked (exactly-once sentence, unauthenticated snapshots, Evals dates, 200x / 99.1% / recall figures, context-management do-not-prune rule) matches.

### Inferences
- OpenAI's HITL page is the most complete public statement of approval semantics in the field: approval is permission, not execution; the state snapshot is untrusted input; idempotency and atomic ownership transitions are the application's job. A comparative table should cite it as the reference wording for "at-least-once with idempotency keys".
- With the hosted Evals product gone, OpenAI's eval guidance converges with Anthropic's and Google's: a small repo-owned suite, deterministic checks before a judge, baseline before change.

### Gaps
- No OpenAI page read states a default `max_turns` for the Python SDK (the 2026-11-04 notes cite the JS docs' default of 10).
- The Agents SDK sandbox docs (`/sandbox/`) were not re-fetched; the April 2026 snapshot/resume claims rest on secondary coverage. UNVERIFIED (2026-11-05).
- No OpenAI statement of a numeric release gate for Codex or the SDK was found (unchanged from 2026-11-04).

---

## Google (ADK 2.x, Agent Platform / Agent Runtime, Gemini API)

### Takeaway
ADK's source of truth is the session event log; compaction, caching and resumability are `App`-level configs with versioned semantics. Resume is explicitly at-least-once ("may run more than once when resuming a workflow"). Tool confirmation still lists `VertexAiSessionService` and `DatabaseSessionService` as unsupported. `FallbackModel` is `@experimental`, tries each model once, and never fails over after the first streamed chunk. Evaluation defaults are `tool_trajectory_avg_score` 1.0 and `response_match_score` 0.8, two runs per case in `AgentEvaluator`, and `adk conformance test` as the PR gate. Gemini 2.5 Flash and 2.5 Pro auto-route to 3.5 Flash-Lite and 3.8 Flash on 2026-12-01; promotional 4 Argon and 3.8 Flash prices end 2026-11-30 and 2026-12-31.

### Cited Findings

#### Q1 Source of truth and context assembly
- Compaction purpose: "reduce the size of context as an agent is running by summarizing older session history" - [Compress agent context](https://adk.dev/context/compaction/index.md) (read 2026-11-05)
- Sliding window: `compaction_interval` "Set the number of completed events that triggers compaction of the prior event data."; `overlap_size` "Set how many of the previously compacted events are included in a newly compacted context set." - [Compress agent context](https://adk.dev/context/compaction/index.md) (read 2026-11-05)
- Token mode: `token_threshold` "The safety limit of tokens that automatically triggers tail-retention compaction once reached."; `event_retention_size` "This maintains immediate conversational context and pronoun resolution." - [Compress agent context](https://adk.dev/context/compaction/index.md) (read 2026-11-05)
- Priority: "the system prioritizes token-based compaction" and "skips sliding-window compaction for that turn"; execution: "the ADK `Runner` handles the compaction process in the background each time the session reaches the interval"; summarizer customisation: "the property is `prompt_template` in Python". Version banner: "Supported in ADK Python v1.16.0 Go v2.3.0 Java v0.2.0 TypeScript v0.6.0 Kotlin v0.7.0". - [Compress agent context](https://adk.dev/context/compaction/index.md) (read 2026-11-05)
- Where the summary is stored (as a session event) is not stated on the compaction page; the BigQuery Agent Analytics `EVENT_COMPACTION` event type (carried over from the 2026-11-04 notes) implies it is logged.
- Loading a tail: "Use `num_recent_events` or `after_timestamp` to avoid loading the full event history on every invocation." and "These filters limit the loaded view without deleting stored events."; `context_window_compression` "Enables context window compression for LLM input, useful when sessions approach model context limits." - [RunConfig](https://adk.dev/runtime/runconfig/index.md) (read 2026-11-05)
- Stable prefix: "If your use case requires that you provide instructions that are used throughout a session" ... "consider using the `static_instruction` parameter for an agent" - [Context caching with Gemini](https://adk.dev/context/caching/index.md) (read 2026-11-05). The LLM-agents page does not document `static_instruction` (read 2026-11-05); a docs issue proposes it as "static content that can be cached, while the instruction field is for dynamic content" (search snippet, [google/adk-docs issue 720](https://github.com/google/adk-docs/issues/720), UNVERIFIED verbatim 2026-11-05).
- Changelog hardening: 2.13.0 "**compaction:** isolate event compaction by isolation_scope" and "**telemetry:** count conversation compactions per workflow"; 2.12.0 "skip a compaction that cannot shrink the request" and "skip compaction instead of failing when summarization errors"; 2.11.0 "keep credential-request events out of the compaction prompt" - [adk-python CHANGELOG](https://github.com/google/adk-python/blob/main/CHANGELOG.md) (read 2026-11-05)
- "a compiled view over stateful sources, not a mutable string buffer" and the 2.0 event-schema warning: carried over from the 2026-11-04 notes ([Google Developers Blog, 2025-12-04](https://developers.googleblog.com/en/architecting-efficient-context-aware-multi-agent-framework-for-production/); [adk.dev/2.0](https://adk.dev/2.0/index.md)); not re-fetched.

#### Q2 Verification and critique
- Plugin precedence: "Any Plugin callbacks code is executed *before* any Agent, Model, or Tool objects callbacks are executed." and, when a plugin returns a value, "the Agent, Model, or Tool-level callback is *not executed* (skipped)." - [Plugins](https://adk.dev/plugins/index.md) (read 2026-11-05)
- Error hooks: `on_model_error` "Returns an `LlmResponse` object to **suppress the exception** and provide a fallback result."; `on_tool_error` "Return a `dict` to **suppress the exception**, provide a fallback result." - [Plugins](https://adk.dev/plugins/index.md) (read 2026-11-05)
- Built-in plugins: "Reflect and Retry Tools", "BigQuery Analytics", "Model Armor", "Context Filter", "Global Instruction", "Save Files as Artifacts", "Auto Tracing", "Multimodal Tool Results", "Logging", "Debug Logging", "Reflect and Retry Model", "Tool Call Integrity". - [Plugins](https://adk.dev/plugins/index.md) (read 2026-11-05)
- "Tool Call Integrity" "runs a tool only when its call's signature verifies." and "Tools that run as workflow nodes are not checked."; "Reflect and Retry Model" "Asks the model to try again when a response ends with an error, such as a malformed function call." - [Plugins](https://adk.dev/plugins/index.md) (read 2026-11-05)
- Deterministic first: "we can deterministically eliminate classes of rogue actions that we never want the agent to take." and a cheap second model: "Implement an additional safety layer using a cheap and fast model (like Gemini Flash Lite)" - [Safety and security](https://adk.dev/safety/index.md) (read 2026-11-05)
- Behavioural regression gate: "adk conformance test command verifies that your AI agents behave consistently over time." Replay mode "compares its live LLM requests, responses, and tool calls directly against your previously recorded interactions"; it is "a command-line tool that fails if things don't match" - [Evaluate agents](https://adk.dev/evaluate/index.md) (read 2026-11-05)
- No first-party critic or grader model runs at inference time; `hallucinations_v1` is an eval-time criterion (see Q3, Q6).

#### Q3 Grounding of figures or facts at inference time
- Eval-time only: "This criterion assesses whether a model response contains any false, contradictory, or unsupported claims." and "Each sentence is labeled as `supported`, `unsupported`, `contradictory`, `disputed` or `not_applicable`." (`hallucinations_v1`) - [Evaluation criteria](https://adk.dev/evaluate/criteria/index.md) (read 2026-11-05)
- Model Armor does not see tool results: "Tool results reach the request as a `function_response` part, which the plugin skips." - [Model Armor](https://adk.dev/integrations/model-armor/index.md) (read 2026-11-05)
- Seams for a builder's own check: `after_model` for "sanitise outputs, add disclaimers or restructure responses" and `after_tool` to post-process outputs: carried over from the 2026-11-04 notes ([Callbacks](https://adk.dev/callbacks/index.md)); not re-fetched.
- Gemini Search grounding returns `url_citation` spans: carried over from the 2026-11-04 notes ([Grounding](https://aistudio.google.com/docs/grounding)); not re-fetched.

#### Q4 Approvals and human-in-the-loop
- Tool confirmation banner: "Supported in ADK Python v1.14.0 TypeScript v0.2.0 Go v0.3.0 Kotlin v0.1.0 Experimental"; "The Tool Confirmation feature is experimental and has some known limitations." - [Get action confirmation](https://adk.dev/tools-custom/confirmation/index.md) (read 2026-11-05)
- Still listed: "DatabaseSessionService is not supported by this feature." and "VertexAiSessionService is not supported by this feature." - [Get action confirmation](https://adk.dev/tools-custom/confirmation/index.md) (read 2026-11-05)
- Resume binding: "The Invocation ID you provide must be the same invocation that generated the confirmation request" ... "otherwise the system starts a new invocation with the confirmation response" - [Get action confirmation](https://adk.dev/tools-custom/confirmation/index.md) (read 2026-11-05)
- The confirmation page says nothing about idempotency or duplicate execution (read 2026-11-05).
- Workflow gates: 2.12.0 "Require human confirmation before executing workflow nodes via `require_confirmation`."; 2.11.0 "Tool confirmation in workflows: Tool nodes now pause for user approval via `RequestInput`" and "persist sibling tool results before a tool confirmation request" - [adk-python CHANGELOG](https://github.com/google/adk-python/blob/main/CHANGELOG.md) (read 2026-11-05)
- At-least-once on resume: "may run more than once when resuming a workflow"; "you should modify the Tool to check for and prevent duplicate runs"; "If your agent uses Tools where duplicate runs would have a negative impact, such as purchases" - [Resume stopped agents](https://adk.dev/runtime/resume/index.md) (read 2026-11-05)

#### Q5 Durable execution
- "In ADK Python 1.16 and higher, you can configure an ADK workflow to be resumable" (`ResumabilityConfig(is_resumable=True)` on the `App`); banner "Supported in ADK Python v1.16.0 Kotlin v0.1.0" - [Resume stopped agents](https://adk.dev/runtime/resume/index.md) (read 2026-11-05)
- What is checkpointed: "Event logging includes results from Tools which successfully returned a result." - [Resume stopped agents](https://adk.dev/runtime/resume/index.md) (read 2026-11-05)
- Limits: "Resume is not supported by default for Custom Agents."; "Resuming a workflow from the ADK Web user interface or using the ADK command line (CLI) tool is not currently supported."; "Do not modify a stopped agent workflow before resuming it." - [Resume stopped agents](https://adk.dev/runtime/resume/index.md) (read 2026-11-05)
- Non-resumable path still replays: 2.12.0 "**flows:** replay sub-branch interrupted tool calls when is_resumable is False" and "**runners:** resolve invocation_id from FunctionResponse when is_resumable is False" - [adk-python CHANGELOG](https://github.com/google/adk-python/blob/main/CHANGELOG.md) (read 2026-11-05)
- Only built-in budget: "Caps the total number of LLM calls per run (default: 500)." and "Set to 0 or negative for unlimited calls, though this is not recommended for production." - [RunConfig](https://adk.dev/runtime/runconfig/index.md) (read 2026-11-05)
- 2.6.0 resumability checkpoints, 2.9.0 failed nodes re-run on resume, `AGENT_STATE_CHECKPOINT` events in BigQuery: carried over from the 2026-11-04 notes; not re-fetched.

#### Q6 Evaluation
- CI gate: "run automatically whenever someone opens a pull request, blocking any code from merging"; live mode "Runs evaluation-based verification against active environments" (marked work in progress). - [Evaluate agents](https://adk.dev/evaluate/index.md) (read 2026-11-05)
- Defaults: "Defaults to 1.0, requiring a 100% match in the tool usage trajectory." (`tool_trajectory_avg_score`) and "Defaults to 0.8, allowing for a small margin of error in the agent's natural language responses." (`response_match_score`); "These criteria are fast, predictable, and suitable for frequent automated checks." - [Evaluate agents](https://adk.dev/evaluate/index.md) (read 2026-11-05)
- Trials per case: `AgentEvaluator.evaluate(... num_runs: int = NUM_RUNS ...)` with `NUM_RUNS = 2`; docstring "Number of times all entries in the eval dataset should be assessed."; per-metric score is `statistics.mean(scores)` across runs. - [agent_evaluator.py](https://github.com/google/adk-python/blob/main/src/google/adk/evaluation/agent_evaluator.py) (read 2026-11-05)
- Empty set fails loudly: "No eval cases were evaluated, so there is nothing to report a pass or a failure for." - [agent_evaluator.py](https://github.com/google/adk-python/blob/main/src/google/adk/evaluation/agent_evaluator.py) (read 2026-11-05)
- Judge sampling: "This is repeated multiple times for robustness (configurable via `num_samples`)" and "a majority vote determines if the invocation receives a score of 1.0 (valid) or 0.0 (invalid)."; examples use `gemini-flash-latest`. - [Evaluation criteria](https://adk.dev/evaluate/criteria/index.md) (read 2026-11-05)
- Trajectory match: "Requires a perfect match between the actual and expected tool calls, with no extra or missing tool calls." (`EXACT`, the default) - [Evaluation criteria](https://adk.dev/evaluate/criteria/index.md) (read 2026-11-05)
- Efficiency metrics: "They are *informational* in that they report a value, but never pass or fail an eval case" and "Supplying a threshold is an error rather than a no-op." - [Evaluation criteria](https://adk.dev/evaluate/criteria/index.md) (read 2026-11-05)
- User simulation: "user prompts that are dynamically generated by an AI model."; trajectory and match criteria are "not supported in combination with User Simulation." - [Evaluate agents](https://adk.dev/evaluate/index.md) (read 2026-11-05)
- Optimisation: "you can use the `adk optimize` command to quickly optimize simple agents based on ADK evaluation results"; "An agent optimizer reviews the evaluation results from the sampler and uses them to improve the agent."; usage "adk optimize [OPTIONS] AGENT_MODULE_FILE_PATH"; "The `agent` module must contain a `root_agent`."; banner "Supported in ADK Python v1.24.0". - [Optimize agents](https://adk.dev/optimize/index.md) (read 2026-11-05)
- Release notes: 2.10.0 "Optimize agent execution costs and latency with new evaluation metrics"; 2.11.0 "make conformance runs report replay and recording failures" - [adk-python releases](https://github.com/google/adk-python/releases) (read 2026-11-05)

#### Q7 Cost and latency controls
- `FallbackModel` (source docstrings): "A model that falls back to backup models when a call fails."; "Tries a sequence of models in order, moving on when one fails."; "Each model is tried exactly once."; "Only failures that carry one of :attr:`retriable_status_codes` move on to the next model." - [_fallback_model.py](https://github.com/google/adk-python/blob/main/src/google/adk/models/_fallback_model.py) (read 2026-11-05)
- Streaming rule: "Once a model has yielded its first response the turn belongs to it:" "a later failure propagates rather than falling back"; "A model that fails to connect is passed over for the next one, since nothing has crossed the connection yet"; decorated `@experimental(FeatureName.FALLBACK_MODEL)`; fields `models` ("The models to try, in order. The first entry is the primary model.") and `retriable_status_codes`. - [_fallback_model.py](https://github.com/google/adk-python/blob/main/src/google/adk/models/_fallback_model.py) (read 2026-11-05)
- Changelog: 2.9.0 "add FallbackModel for automatic failover between models" - [adk-python releases](https://github.com/google/adk-python/releases) (read 2026-11-05)
- Per-request routing is TypeScript-only: "Supported in ADK TypeScript v1.0.0 Experimental"; "the router is re-called with `errorContext` only if the selected model fails before yielding any response"; "The router can return `undefined` to stop retrying and propagate the last error."; "Model routing is experimental and may change in future releases." - [Route between models](https://adk.dev/agents/models/routing/index.md) (read 2026-11-05)
- `ContextCacheConfig`: `min_tokens` "Defaults to `0`."; `ttl_seconds` "Defaults to `1800` (30 minutes)."; `cache_intervals` "Defaults to `10`."; `create_http_options` "defaults to none"; metrics: "an event backed by an LLM response can carry a `CacheMetadata` reporting what the cache did for that call." and "Token counts are not on `CacheMetadata`; read them from `LlmResponse.usageMetadata`."; banner "Supported in ADK Python v1.15.0 Java v0.1.0 Kotlin v0.7.0". - [Context caching with Gemini](https://adk.dev/context/caching/index.md) (read 2026-11-05)
- Gemini implicit caching: "Implicit caching is enabled by default for all Gemini 2.5 and newer models."; minimums 4,096 tokens (Gemini 4 Argon, 3.8 Flash, 3.6 Flash, 3.1 Pro Preview), "Gemini 2.5 Flash | 2,048"; "Gemini caches the full previous request only if the new request adds at least 2,050 tokens."; "The Interactions API only supports implicit caching."; hits reported in `usage.total_cached_tokens`. - [Gemini API caching](https://aistudio.google.com/docs/caching) (read 2026-11-05)
- Off-peak tier: "`ServiceTier.DEFERRED` queues each model call to run on off-peak capacity" (not combinable with SSE). No token or currency budget field exists on `RunConfig`; `max_llm_calls` is the only ceiling. - [RunConfig](https://adk.dev/runtime/runconfig/index.md) (read 2026-11-05)
- Pricing and dates: "Gemini 2.5 Flash (`gemini-2.5-flash`) is deprecated and is no longer available to select in Google AI Studio."; "Effective December 1, 2026, all API requests to `gemini-2.5-flash` will automatically route to" `gemini-3.5-flash-lite`; 2.5 Pro routes to `gemini-3.8-flash` the same day. - [Gemini API pricing](https://aistudio.google.com/docs/pricing); [Deprecations](https://aistudio.google.com/docs/deprecations) (read 2026-11-05)
- "`gemini-2.5-flash-lite` is not deprecated and remains available through the API until further notice."; for 3.5 Flash "the endpoint is not shutting down and automatically routes API requests to" `gemini-3.6-flash`; policy "We will communicate the exact shutdown date to users with advance notice" - [Deprecations](https://aistudio.google.com/docs/deprecations) (read 2026-11-05)
- Promotional prices: 3.8 Flash input "$0.75 through December 31, 2026." output "$3.75 through December 31, 2026." cached "$0.075 through December 31, 2026."; 4 Argon input "$2.00 through November 30, 2026." output "$10.00 through November 30, 2026."; 2.5 Flash cached "$0.03 (text / image / video)". - [Gemini API pricing](https://aistudio.google.com/docs/pricing) (read 2026-11-05)
- `thinking_level` per model and thinking tokens billed as output: carried over from the 2026-11-04 notes ([Thinking](https://aistudio.google.com/docs/thinking)); not re-fetched.

#### Q8 Security and identity
- Identity: "The tool interacts with external systems using the agent's own identity" (agent-auth) vs "User auth has the advantage that agents only perform actions that the user could have performed themselves." - [Safety and security](https://adk.dev/safety/index.md) (read 2026-11-05)
- "The callback has access to the agent's state, the requested tool and parameters."; "sandboxing must be used to prevent model-generated code to compromise the local environment"; "Confine agent activity within secure perimeters (like VPC Service Controls) to prevent data exfiltration" - [Safety and security](https://adk.dev/safety/index.md) (read 2026-11-05)
- Injection example: "an indirect prompt injection can trick a model to include an img tag"; audit: "ensure that logs are created to maintain attribution of actions to users" - [Safety and security](https://adk.dev/safety/index.md) (read 2026-11-05)
- Model Armor: "inspects text for prompt injection and jailbreak attempts, harmful content, and sensitive data."; "It screens user input before the model sees it and model output before or during delivery"; "The default blocks unscreened content."; "Set `block_on_screening_failure=False` to keep the agent answering while Model Armor is unavailable."; "A blocked turn carries `custom_metadata['model_armor_blocked']`"; banner "Supported in ADK Python v2.8.0". - [Model Armor](https://adk.dev/integrations/model-armor/index.md) (read 2026-11-05)
- Logging plugin: "Log important information at each agent workflow callback point."; Debug Logging "Captures complete debug information for each invocation to a YAML file." - [Plugins](https://adk.dev/plugins/index.md) (read 2026-11-05)
- 2.13.0 breaking telemetry default: "Telemetry: Defaults to OpenTelemetry GenAI v2 (otel_semconv_1_44, removing call_llm)" - [adk-python releases](https://github.com/google/adk-python/releases) (read 2026-11-05)
- SPIFFE Agent Identity (24-hour X.509, no long-lived keys) and BigQuery Agent Analytics as the audit sink: carried over from the 2026-11-04 notes; not re-fetched.

### Verification findings against the 2026-11-04 notes
- The notes said `FallbackModel` API details were not found; the source file `_fallback_model.py` documents them (quoted above). Note the `@experimental` decorator, which the changelog line does not mention.
- The notes date `adk optimize` to v1.27.0 from the changelog; the optimize page's banner says "Supported in ADK Python v1.24.0". Both are Google's own statements; cite the page for the feature and the changelog for the command.
- The notes did not record the `AgentEvaluator` default of two runs (`NUM_RUNS = 2`); verified from source today.
- The tool-confirmation limitation on `VertexAiSessionService` is still on the page on 2026-11-05 (the notes flagged it as possibly stale).
- Release dating: GitHub shows v2.13.0 on 23 Oct and PyPI "Released: Oct 23, 2026"; the changelog heading reads 2026-10-22. Both are Google's; use 2026-10-22/23.

### Inferences
- Google documents the at-least-once contract more plainly than any vendor except OpenAI; the duplicate-prevention burden is explicitly on the tool author.
- `FallbackModel`'s "never after the first chunk" rule is the right primitive for a streaming harness and is the first-party answer to vendor failover on Python; per-request routing remains a harness-level concern on Python.
- Google's grounding story is entirely offline (`hallucinations_v1`) plus content safety (Model Armor, which skips tool results); an inference-time figure check has no first-party component.

### Gaps
- Where `EventsCompactionConfig` writes the summary (session event vs in-memory) is not stated on the compaction page. UNVERIFIED (2026-11-05).
- `static_instruction` has no reference-page definition on adk.dev beyond the caching page's one sentence; the docs issue was not read verbatim. UNVERIFIED (2026-11-05).
- Agent Runtime limits, Sessions TTL and Agent Platform pricing remain unread (unchanged from 2026-11-04).

---

## DeepSeek Harness (dsh)

### Takeaway
dsh is the clearest "log is the model's context" design: every model request must be reconstructable from an append-only JSONL session log, failed attempts are retained without entering model history, approval decisions are log-only audit events, and compaction is a logged start/end pair whose summary is a `user/message` with a `replace` surface operation. Approvals fail closed unless `allowed-once`. There is no statement on duplicate tool execution, no critic model, no inference-time grounding, no cost budget, and benchmarks are run on a minimal JSON-RPC agent. Session logs are contributed to official DeepSeek requests by default.

### Cited Findings

#### Q1 Source of truth and context assembly
- "The session log is the source of the context the model sees." and "Every model request must be reconstructable from the log." - [docs/architecture.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md) (read 2026-11-05)
- "`deriveMessages()` projects model history from it." and "`assistant/attempt` retains settled failed, retried, cancelled, and stream-error attempts without adding model history." - [docs/architecture.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md) (read 2026-11-05)
- Surface vs log-only: "A surface event produces model history; a log-only event does not."; `assistant/message` "Assembled assistant message for one step (derived history uses this)."; `assistant/attempt` "One model attempt that committed no surface message."; feedback "Log-only human feedback; never enters model history." - [docs/persistence-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/persistence-catalog.md) (read 2026-11-05)
- Storage: "an append-only logical JSONL log per session" and "the append-only `SessionEvent` log that is the source of truth." - [docs/subsystems/persistence.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/persistence.md) (read 2026-11-05)
- Compaction as log events: "`compaction/start` is appended first."; the summary replaces the range through a `user/message` carrying "`surfaceOp: { op: 'replace', startSeq, endSeq }`"; "A live unmatched start blocks every entry point;"; failed attempts: "`changed` and `summary` close and persist the failed attempt without a summary replacement."; the summarize request is "reconstructable from log + code". - [docs/subsystems/compaction.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/compaction.md) (read 2026-11-05)
- Pruning before summarising: "compaction-basic invokes optional `ctx.toolResultPruner` before range selection." - [docs/subsystems/compaction.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/compaction.md) (read 2026-11-05)
- Trigger: "`dsh-compaction-basic` uses `agent/pre-step` for pressure before request derivation and `agent/request-error` only for canonical context overflow." - [docs/agent-lifecycle.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/agent-lifecycle.md) (read 2026-11-05)
- Thresholds: `thresholdRatio` "Window fraction for pressure; capped at context window minus reserved output and `headroomTokens`. Defaults to `0.8`."; `retainRatio` "Recent context retained as a fraction of context window minus reserved output tokens. Defaults to `0.16`."; `maxTokens` "Provider generation cap for summarization. Defaults to the resolved `headroomTokens`; an explicit cap must be positive."; `headroomTokens` "Non-negative integer; defaults to `65536`."; "Exact provider/model overrides; duplicate targets fail plugin load." - [docs/config-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/config-catalog.md) (read 2026-11-05)
- Loop vocabulary: step is "one model request plus the tool executions caused by its response; a turn contains zero or more steps."; turn is "one drain of admitted input in a session, ending after the model and its tools stop or a terminal policy intervenes." - [docs/glossary.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/glossary.md) (read 2026-11-05)
- Profiles and layering: "the profile's ordered bundles, its `cordis.patch.yml`, the home patch, then `--patch` overlays." and "Layers apply to an empty entry list." - [docs/architecture.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md) (read 2026-11-05)
- Cordis kernel: "plugins contribute services, typed events, and reversible effects to a shared context." and "registrations are effects that unwind when their plugin unloads." - [docs/architecture.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md) (read 2026-11-05)
- Cordis paper (arXiv 2608.25512, submitted 2026-08-26, Yifan Shi, Wei Zhang, Tianyi Cui): "Modern software -- from plugin systems to self-evolving agent harnesses -- increasingly requires dynamic composition"; "temporal composability, the ability to completely revert a component's side effects upon removal"; "spatial composability, the ability to declare and reactively manage inter-component dependencies."; "We implement these ideas in Cordis, a meta-framework of spatiotemporal composability"; "a declarative component loader with configuration reconciliation and hot module replacement." - [arXiv 2608.25512](https://arxiv.org/abs/2608.25512) (read 2026-11-05)

#### Q2 Verification and critique
- Hooks are waterfalls: "Listeners on the waterfall events must call `next()` to delegate."; the stop check is "natural stop and next-step inbox empty," firing `agent/turn-stopping`; "The returned `agent/pre-step` decision is authoritative" - [docs/architecture.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md); [docs/agent-lifecycle.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/agent-lifecycle.md) (read 2026-11-05)
- Tool pipeline: "The `tools/pre-execute` waterfall runs first, monotonic guards run next"; "`tools/result` then observes the immutable, lossless-JSON outcome"; "pipeline/result snapshot throws become isError." - [docs/tool-execution-pipeline.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/tool-execution-pipeline.md) (read 2026-11-05)
- Model-based review exists only as an approval reviewer: the product page lists "Auto approval reviewer" marked "Experimental" with no description. - [deepseek.com/en/harness](https://www.deepseek.com/en/harness/) (read 2026-11-05)
- No critic, grader or Stop-style verifier is documented in the architecture, lifecycle, pipeline or subsystem pages read (2026-11-05).

#### Q3 Grounding of figures or facts at inference time
- None documented. Tool results are kept lossless and size-capped: `maxResultChars` "Rendered-result ceiling, in characters: a longer JSON value is truncated with a notice (default 50000)."; spill policy `maxInlineTokens` "Maximum estimated tokens in a retained result, including image descriptors and omission notices." - [docs/config-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/config-catalog.md) (read 2026-11-05)

#### Q4 Approvals and human-in-the-loop
- The approval subsystem "answers one question: may this specific action proceed?" Outcomes are `allowed-once`, `rejected`, `cancelled`, `unavailable`; callers "fail closed unless it is `allowed-once`." - [docs/subsystems/approval.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/approval.md) (read 2026-11-05)
- Policies: "`never` deterministically returns `rejected` without dispatching any answerer." and "`ask` delegates to the composed answerer chain, whose no-answer default is `unavailable`."; "A missing, non-owning, throwing, or non-conforming answerer becomes `unavailable` rather than opening the gate."; "Aborting withdraws the question: the request settles `'cancelled'` immediately." - [docs/subsystems/approval.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/approval.md) (read 2026-11-05)
- Audit, not model-visible: "The audit events are log-only and do not enter the model transcript." (`approval/asked`, `approval/decided`) - [docs/subsystems/approval.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/approval.md) (read 2026-11-05)
- Presets: "`workspace-write` (`workspace-write` + `ask`)" and "`danger-full-access` (`danger-full-access` + `never`)"; "Default for new sessions. When omitted, the preset matching the composed sandbox and approval defaults is used."; "The names `custom` and `auto` are reserved for derived state and the Auto review integration respectively." - [docs/subsystems/permission-presets.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/permission-presets.md) (read 2026-11-05)
- Retry semantics: "Retries do not repeat assembly or `agent/pre-step`." and "Each retry prepares its call and reconciles the retained rendered assembly before request derivation, without repeating assembly, pre-step, or user admission." - [docs/agent-lifecycle.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/agent-lifecycle.md) (read 2026-11-05)
- Exactly-once / duplicate execution after approval: not stated in approval.md, agent-lifecycle.md, tool-execution-pipeline.md or persistence.md (read 2026-11-05).

#### Q5 Durable execution
- "a hard process loss before settlement leaves no durable attempt stream." - [docs/architecture.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md) (read 2026-11-05)
- "a session that never materialized before a crash never existed."; "a torn physical tail is never returned to a reader."; "only the incomplete fragment of a torn physical tail, belonging to an append that never resolved, is discarded." - [docs/subsystems/persistence.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/persistence.md) (read 2026-11-05)
- Flush: "on resolution every acknowledged append is durable and the session is materialized for other processes"; "The first pending event starts a fixed internal batching window"; "The loop does not await a flush at turn boundaries." - [docs/subsystems/persistence.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/persistence.md); [docs/persistence-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/persistence-catalog.md) (read 2026-11-05)
- Fork: "Fork at a turn boundary"; "only agent-loop-published sessions persist."; "A seeded creation requires an explicit seed equal to its inherited prefix and an exact cut." - [docs/architecture.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md); [docs/subsystems/persistence.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/persistence.md) (read 2026-11-05)
- Sub-agent caps: `maxActiveSubagents` "Maximum live children sharing uninterrupted continuable parent links; defaults to 8."; `maxDepth` "Default delegation depth for tools without an explicit limit; defaults to 1." - [docs/config-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/config-catalog.md) (read 2026-11-05)
- Resume of an interrupted turn across process restart: not described in the pages read (gap).

#### Q6 Evaluation
- "Use separate workspaces and session IDs for independent benchmark tasks." (run via the Python SDK's `jsonrpc-agent` minimal variant) - [BENCHMARK.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/BENCHMARK.md) (read 2026-11-05)
- BENCHMARK.md names no benchmark list, trial count, pass^k, CI gate, temperature or effort (read 2026-11-05).
- Vendor-minimal-harness reporting (V4 model cards "with the minimal mode of DeepSeek Harness"): carried over from the 2026-11-04 notes; not re-fetched.

#### Q7 Cost and latency controls
- No cost or currency budget: the config catalogue's second half "contains no cost limits"; token controls are `headroomTokens` (65536 default), `thresholdRatio`, `retainRatio`, `maxInlineTokens`, `referenceContextFraction` "Fraction of the model context window per source, estimated at four bytes per token; between zero and one." - [docs/config-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/config-catalog.md) (read 2026-11-05)
- Provider seam: providers are "pi-ai provider routes, keyed by provider."; retry: `dsh-llm-replay` "Optional provider-owned retry policy used by assembled recovery snapshots."; MCP reconnect "Consecutive failed attempts per outage before giving up for good (default 10)." - [docs/config-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/config-catalog.md) (read 2026-11-05)
- No model fallback setting was found in the config catalogue (first 200k of 244k characters read; UNVERIFIED for the tail, 2026-11-05).
- DeepSeek list prices (50x cache-hit/miss gap on V4.1 Flash): carried over from the 2026-11-04 notes, secondary source; not re-fetched.

#### Q8 Security and identity
- Backends: "[dsh-sandbox-local] supplies Linux bwrap/Landlock, macOS Seatbelt, and the Windows ACL restricted-token backend"; "`danger-full-access` bypasses confinement."; "rejects with `SandboxUnavailableError` and code `SANDBOX_UNAVAILABLE` when no usable backend exists"; "Silent unconfined passthrough is never legal for a confined policy." - [docs/subsystems/sandbox.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/sandbox.md) (read 2026-11-05)
- Scope limit: "Network and process visibility are outside this vocabulary." and "callers requiring an absolute boundary must not treat it as `full`."; policy default "`mode: 'read-only'` is the fail-safe default" - [docs/subsystems/sandbox.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/sandbox.md); [docs/config-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/config-catalog.md) (read 2026-11-05)
- SAFETY.md: sandboxes "do not guarantee isolation or prevent damage."; "Run the project with the least privileges and access required."; "Prefer a disposable virtual machine, container, or dedicated environment."; "Review plugins, configuration, and proposed commands before allowing them to run."; "Do not expose sensitive credentials or data unless you accept the risk." - [SAFETY.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/SAFETY.md) (read 2026-11-05)
- Telemetry defaults: `dsh-session-telemetry-otel` mode "Defaults to `FEEDBACK_ONLY`: capture session history only when feedback is explicitly submitted."; `dsh-session-log-deepseek` "Contribute `dsh_session_log` to official DeepSeek requests. Defaults to `true`." - [docs/config-catalog.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/config-catalog.md) (read 2026-11-05)
- Product telemetry: "The exporter collects no Session data or identifiers automatically." and "Mounting alone sends nothing" - [docs/subsystems/product-telemetry.md](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/subsystems/product-telemetry.md) (read 2026-11-05)
- Status: "DeepSeek Harness is in developer preview and iterating rapidly." and "THERE WILL BE COMPATIBILITY-BREAKING CHANGES." Repo shows 272.4k stars, 33.2k forks, 25,848 commits, MIT, no GitHub releases. - [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) (read 2026-11-05)

### Verification findings against the 2026-11-04 notes
- The notes' compaction defaults came from npm package READMEs (secondary) and gave a summary `maxTokens` default of 8192; the primary config catalogue says `maxTokens` "Defaults to the resolved `headroomTokens`" (65536 default). Prefer the primary; the 8192 figure may belong to an older package version. UNVERIFIED which is current for the published package (2026-11-05).
- The notes' claim that session logs upload to DeepSeek by default (from eesel.ai) is now confirmed from the primary config catalogue (`dsh-session-log-deepseek` defaults to `true`).
- The notes' approval description (secondary) is now replaced by primary wording: outcomes `allowed-once` / `rejected` / `cancelled` / `unavailable`, fail-closed callers, log-only audit events.
- The notes' sandbox claim that "bwrap hides host processes, Landlock and macOS Seatbelt do not" is not on the primary sandbox page, which says process visibility is "outside this vocabulary". Keep as secondary.
- Commit count moved from 25,588 (2026-11-04 notes) to 25,848 (2026-11-05 page).

### Inferences
- dsh's log discipline (surface vs log-only, attempts kept out of history, compaction as a replace op with a lock) is the closest published analogue to an event-sourced harness; its approval model is an audit-first gate with no execution-semantics promise.
- The absence of any budget, grader, or grounding component is consistent with a developer-preview coding harness; a comparative table should mark Q3, Q6 and Q7 as "left to the builder" for dsh.

### Gaps
- `docs/subsystems/subagent.md`, `session.md`, `otel.md` and `agent-team.md` exist in the README index but were not read; the user guide tree (`docs/user/guide`) has no approvals or telemetry page by name. UNVERIFIED (2026-11-05).
- `session-format-status.md` covers versioning only; the format references it links to were not read.

---

## LangGraph, LangChain 1.x middleware, Deep Agents, LangSmith

### Takeaway
LangGraph's unit of durability is a per-super-step checkpoint on a `thread_id`, not an append-only log; nodes re-run from the start on resume, so side effects before an `interrupt()` must be idempotent and the docs say retries "do not make external side effects happen exactly once". LangChain 1.x ships the harness controls as middleware (summarization, HITL, PII, model fallback, call limits, tool retry, context editing); Deep Agents packages them as "the agent harness for complex, multi-step work". LangSmith adds `num_repetitions` for variance and side-by-side experiment comparison; nothing first-party grounds figures.

### Cited Findings

#### Q1 Source of truth and context assembly
- "**Checkpointers** persist a thread's graph state as checkpoints." and "Pass a `thread_id` in graph config."; "**Stores** persist application-defined data outside the graph state." - [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) (read 2026-11-05)
- "`MemorySaver` and `InMemorySaver` store checkpoints in RAM."; "Use a persistent checkpointer for production:"; "`PostgresSaver`: PostgreSQL with async support"; a troubleshooting heading reads "Checkpoints growing unboundedly". - [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) (read 2026-11-05)
- Summarization middleware: trigger "Condition(s) for triggering summarization. Can be:"; "If `trigger` is not provided, summarization will not trigger automatically."; keep "How much context to preserve after summarization. Specify exactly one of:"; `max_tokens_before_summary` is deprecated: "Use `trigger: ("tokens", value)` instead." - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)
- Context editing: "Manage conversation context by clearing older tool call outputs when token limits are reached" with `trigger` "Token count that triggers the edit." and `keep` "Number of most recent tool results that must be preserved." - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)
- Deep Agents: "Deep Agents is the agent harness for complex, multi-step work."; "Built-in offloading and summarization compress conversation history and large intermediate results."; "Memory uses AGENTS.md files that you pass through the memory parameter when creating the agent."; "Starting in v0.7 task planning is opt-in only." - [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) (read 2026-11-05)
- Subagent context: "By default, each invocation creates a new agent instance with its own context." and "Use mode: "fork" to inherit the parent's full conversation history instead." - [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) (read 2026-11-05)
- Summarization trigger thresholds for Deep Agents are not stated on the overview (read 2026-11-05; unchanged gap from 2026-11-04).

#### Q2 Verification and critique
- HITL middleware: "Pause agent execution for human approval, editing, or rejection of tool calls before they execute."; "The middleware pauses once per model turn by default."; "Human-in-the-loop middleware requires a checkpointer to maintain state across interruptions." - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)
- Deep Agents: "interrupt_on accepts a mapping of tool names to interrupt configurations." - [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) (read 2026-11-05)
- LLM tool selector (a model deciding the tool menu): "Use an LLM to intelligently select relevant tools before calling the main model." - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)
- No first-party critic or Stop-style verifier; trajectory evaluators (`agentevals`) are offline: carried over from the 2026-11-04 notes; not re-fetched.

#### Q3 Grounding of figures or facts at inference time
- None documented. PII middleware strategies are the only output-rewriting control: "`'block'` - Raise exception when detected"; "`'redact'` - Replace with `[REDACTED_{PII_TYPE}]`"; "`'mask'` - Partially mask (e.g., `****-****-****-1234`)"; "`'hash'` - Replace with deterministic hash" - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)

#### Q4 Approvals and human-in-the-loop
- "Interrupts allow you to pause graph execution at specific points and wait for external input."; requires "A **checkpointer** to persist the graph state (use a durable checkpointer in production)." - [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) (read 2026-11-05)
- "You must use the same thread ID when resuming that was used when the interrupt occurred" and "Graph waits indefinitely until you resume execution with a response" - [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) (read 2026-11-05)
- Re-execution: "The node restarts from the beginning of the node where the interrupt was called when resumed, so any code before the interrupt runs again."; "Place side effects after interrupt calls."; "side effects called before interrupt should (ideally) be idempotent."; "retrying the node can repeat the effect." - [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) (read 2026-11-05)
- "Static interrupts are **not** recommended for human-in-the-loop workflows."; approve/reject: "When you resume the graph, pass True to approve or False to reject" - [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) (read 2026-11-05)
- Not exactly-once: "It does not make external side effects happen exactly once."; "Send a stable idempotency key with the side effect so the provider can deduplicate retries."; "Application code must make those effects idempotent." - [Fault tolerance](https://docs.langchain.com/oss/python/langgraph/fault-tolerance) (read 2026-11-05)

#### Q5 Durable execution
- "After an interrupt or retry, the affected node runs again from the start of its function."; "Side effects before the pause run again."; "Design node logic so re-execution is safe."; "With a checkpointer, completed task results are saved, so a resumed thread can skip finished work inside the node."; "If a node calls tasks or interrupt, stricter determinism rules apply on resume." - [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) (read 2026-11-05)
- Failed attempts: "Graph writes from a failed attempt are discarded."; "so resume can skip completed units"; drained runs: "Resume a drained run with `invoke(None, config)` using the same `thread_id`." - [Fault tolerance](https://docs.langchain.com/oss/python/langgraph/fault-tolerance) (read 2026-11-05)
- Durability modes (quoted from a search snippet of the durable-execution page; direct fetches of `/durable-execution` and `/durable-execution.md` served the Persistence page on 2026-11-05, so verbatim status is UNVERIFIED): "sync": "LangGraph persists changes synchronously before the next step starts. This ensures that LangGraph writes every checkpoint before continuing execution, providing high durability at the cost of some performance overhead."; "async": "LangGraph persists changes asynchronously while the next step executes. This provides good performance and durability, but there's a small risk..."; "exit": "LangGraph persists changes only when graph execution exits either successfully, with an error, or due to a human in the loop interrupt." - [Durable execution](https://docs.langchain.com/oss/python/langgraph/durable-execution) (search snippet, 2026-11-05)
- "Persistence lets LangGraph applications keep useful information beyond a single graph run." with use cases "conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance." - [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) (read 2026-11-05)

#### Q6 Evaluation
- "LLM outputs are not deterministic. Outputs can differ from one repetition to the next." and "Repetitions are a way to reduce noise in systems prone to high variability, such as agents."; "Add the optional `num_repetitions` param to the `evaluate` / `aevaluate` function"; "LangSmith displays the average for each feedback score in the table." plus "the standard deviation across repetitions." - [Repetitions](https://docs.langchain.com/langsmith/repetition) (read 2026-11-05)
- Evaluators are "workspace-level resources that score application performance." (human, code, LLM-as-judge, pairwise); "Regression testing: Ensure new versions don't degrade quality."; "LangSmith displays all experiments associated with a dataset and supports comparing multiple experiments side-by-side." - [Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts) (read 2026-11-05)
- "Use offline evaluations for pre-deployment testing."; "Use online evaluations for production monitoring."; "Evaluations can be written using standard testing tools like pytest or Vitest/Jest." - [Evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts) (read 2026-11-05)
- Deep Agents: "Trace requests, debug agent behavior, and evaluate outputs with LangSmith." - [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) (read 2026-11-05)
- No numeric CI gate or pass^k guidance was found on LangSmith pages read (2026-11-05).

#### Q7 Cost and latency controls
- Model fallback: "Automatically fallback to alternative models when the primary model fails."; `first_model` "First fallback model to try when the primary model fails." - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)
- Call limits: `thread_limit` "Maximum model calls across all runs in a thread. Defaults to no limit."; `run_limit` "Maximum model calls per single invocation. Defaults to no limit."; `exit_behavior` "Behavior when limit is reached. Options: `'end'` (graceful termination) or `'error'` (raise exception)" - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)
- Tool limits and retries: tool-call `exit_behavior` "`'continue'` (default) - Block exceeded tool calls with error messages, let other tools and the model continue."; retry "Maximum number of retry attempts after the initial call (3 total attempts with default)" with `backoff_factor` "Multiplier for exponential backoff." - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)
- Deep Agents: "Prompt caching is enabled by default when using an Anthropic model, or a Bedrock model (Claude or Nova)." - [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) (read 2026-11-05)
- No currency budget exists in the middleware set; limits are counts of calls (read 2026-11-05).

#### Q8 Security and identity
- Sandboxed execution: "Run shell commands in the environment (available with sandbox backends only)." (`execute` tool) - [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) (read 2026-11-05)
- PII strategies as above; OpenAI-specific "Content moderation middleware for OpenAI models." is the only content-filter middleware listed. - [Built-in middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in) (read 2026-11-05)
- No prompt-injection guidance, audit-log statement or identity model was found on the LangGraph/LangChain pages read (2026-11-05).

### Verification findings against the 2026-11-04 notes
- The notes cite "durability modes exit / async / sync" from the durable-execution page; today both URL forms of that page served the Persistence page, and the mode definitions only reached this session via a search snippet. Keep the notes' citation but treat the exact wording as UNVERIFIED until the page is re-read.
- The notes' `SummarizationMiddleware` defaults (`max_tokens_before_summary=4000`, `messages_to_keep=20`) are now deprecated parameter names; the current API is `trigger` / `keep`, with no automatic trigger unless set.
- Everything else (interrupt re-execution, checkpointer requirement, fork subagents, prompt caching default) matches.

### Inferences
- LangGraph's checkpoint model gives durability at step granularity but puts both idempotency and determinism on application code; it is the opposite end of the spectrum from dsh/OpenHands event sourcing and from Managed Agents' server-side log.
- The middleware catalogue is the most complete first-party set of count-based limits (model calls, tool calls, retries) among the open frameworks, but none is a currency budget.

### Gaps
- Durability-mode wording: UNVERIFIED verbatim (2026-11-05, see above).
- No LangSmith page read states a default for `num_repetitions` (the 2026-11-04 notes and a search snippet say 1).

---

## OpenHands (Software Agent SDK V1)

### Takeaway
OpenHands V1 is event-sourced: all interactions are immutable events appended to a log, `ConversationState` is the only stateful component, condensation is itself an event with `forgotten_event_ids` and the model's view is derived at read time. Security is a risk label the model emits per tool call plus a confirmation policy (default threshold HIGH, UNKNOWN confirms). The paper reports a 61% drop in system-attributable failures over a 15-day parallel rollout and negligible persistence overhead. No statement on duplicate execution, budgets, inference-time grounding or CI gating.

### Cited Findings

#### Q1 Source of truth and context assembly
- "At V1's core lies an event-sourcing pattern treating all interactions as immutable events appended to a log." and "all changing variables live in ConversationState, making it the only stateful component." - [arXiv 2511.03690v2, section 4.2](https://arxiv.org/html/2511.03690v2) (read 2026-11-05)
- "the Condenser system drops events and replaces them with summaries whenever the history grows too large." - [arXiv 2511.03690v2, section 4.6](https://arxiv.org/html/2511.03690v2) (read 2026-11-05)
- "The Condenser system manages conversation history compression to keep agent context within LLM token limits."; "Wrap summary in `Condensation` event with `forgotten_event_ids`."; "`View.from_events()` processes Condensation to filter events and insert summary." - [Condenser architecture](https://docs.openhands.dev/sdk/arch/condenser) (read 2026-11-05)
- Defaults: `max_size` "Event count threshold before condensation triggers (default: 120)"; `keep_first` "Number of initial events to preserve verbatim (default: 4)"; `NoOpCondenser` "Pass-through condenser that performs no compression" - [Condenser architecture](https://docs.openhands.dev/sdk/arch/condenser) (read 2026-11-05)
- "The most recent exchanges remain unchanged for immediate context." and the condenser "replaces the dropped events with an LLM-generated summary." - [Context condenser guide](https://docs.openhands.dev/sdk/guides/context-condenser) (read 2026-11-05)
- Persistence contents: events "Complete event log including user messages, agent responses, and system events."; base state "The core conversation state including agent configuration, execution status, statistics, and metadata."; default location "the persistence directory is `workspace/conversations/`" - [Conversation persistence](https://docs.openhands.dev/sdk/guides/convo-persistence) (read 2026-11-05)
- Cost effect of the default condenser (up to 2x API cost reduction with no performance degradation): paraphrase of the paper by the fetch tool, section 4.6; verbatim UNVERIFIED (2026-11-05).

#### Q2 Verification and critique
- "Capture and validate LLM-provided risk levels for actions"; "Determine when user approval is required based on risk"; "Enforce security policies before execution"; "Record security decisions in event history" - [Security architecture](https://docs.openhands.dev/sdk/arch/security) (read 2026-11-05)
- "Risk assessment happens inline—no separate analysis step." (the analyzer "returns the pre-assigned risk level") - [Security architecture](https://docs.openhands.dev/sdk/arch/security) (read 2026-11-05)
- "the SecurityAnalyzer, which rates each tool call as low, medium, high, or unknown risk" and "the ConfirmationPolicy, which determines whether user approval is required before execution" - [arXiv 2511.03690v2, section 4.9](https://arxiv.org/html/2511.03690v2) (read 2026-11-05)
- Trained critic for best-of-N selection (SWE-bench Verified 60.6% to 66.4%, best-of-5): carried over from the 2026-11-04 notes ([OpenHands blog, 2025-04-17](https://www.openhands.dev/blog/sota-on-swe-bench-verified-with-inference-time-scaling-and-critic-model)); not re-fetched.

#### Q3 Grounding of figures or facts at inference time
- None documented on the pages read (2026-11-05).

#### Q4 Approvals and human-in-the-loop
- Policies: `AlwaysConfirm` "Requires confirmation for all actions"; `NeverConfirm` "Never requires confirmation"; `ConfirmRisky` "Configurable risk-based policy." with threshold HIGH "Risk level at or above which confirmation is required." and `confirm_unknown` True "Whether `UNKNOWN` risk requires confirmation." - [Security architecture](https://docs.openhands.dev/sdk/arch/security) (read 2026-11-05)
- The conversation "Pauses for user confirmation when required."; the analyzer "can be disabled for trusted environments." - [Security architecture](https://docs.openhands.dev/sdk/arch/security) (read 2026-11-05)
- Pause/resume: "Pause the agent from another thread or after a delay using `conversation.pause()`" and "Resume the paused conversation after performing operations by calling `conversation.run()` again." - [Pause and resume](https://docs.openhands.dev/sdk/guides/convo-pause-and-resume) (read 2026-11-05)
- Exactly-once / duplicate execution after confirmation: not stated (read 2026-11-05).

#### Q5 Durable execution
- State is saved as it changes, so it is recoverable "even if the process crashes unexpectedly."; "Restore a conversation using the same ID and persistence directory." - [Conversation persistence](https://docs.openhands.dev/sdk/guides/convo-persistence) (read 2026-11-05)
- "All persist and recovery latencies are negligible relative to LLM round-trip times" - [arXiv 2511.03690v2, section 5.2](https://arxiv.org/html/2511.03690v2) (read 2026-11-05); sub-millisecond persist and under-20 ms crash recovery are the fetch tool's paraphrase of the same section (verbatim UNVERIFIED).
- "V1 reduces system-attributable failures by 61% (from 78.0 to 30.0 errors per 1k conversations)." (15-day parallel rollout, paraphrase) - [arXiv 2511.03690v2, section 5.1](https://arxiv.org/html/2511.03690v2) (read 2026-11-05)
- Portability: "can scale to distributed production simply by swapping the workspace type."; "Runs inside containers (via `DockerWorkspace`) or as standalone process (connected via `RemoteWorkspace`)." - [arXiv 2511.03690v2, section 4.10](https://arxiv.org/html/2511.03690v2); [SDK architecture overview](https://docs.openhands.dev/sdk/arch/overview) (read 2026-11-05)
- In-flight tool execution during a crash: not described (gap).

#### Q6 Evaluation
- "The SDK achieves SOTA on 3 of 5 benchmarks and remains competitive on the other two"; best SWE-Bench Verified result 76.6% (Table 5); V1 72.8% vs V0 64.6% with Claude Sonnet 4.5 (Table 4, paraphrase). - [arXiv 2511.03690v2, section 5.4](https://arxiv.org/html/2511.03690v2) (read 2026-11-05)
- Paper metadata: title "The OpenHands Software Agent SDK: A Composable and Extensible Foundation for Production Agents", v1 2025-11-05, v2 2026-04-22, "Accepted at MLSys 2026". - [arXiv 2511.03690](https://arxiv.org/abs/2511.03690) (read 2026-11-05)
- Current harness: the benchmarks repository is "the evaluation harness for OpenHands V1" and the old docs say "for current SDK-based evaluations, use the OpenHands benchmarks repository" (search snippets; [OpenHands/benchmarks](https://github.com/OpenHands/benchmarks); verbatim UNVERIFIED 2026-11-05).
- No CI gate, trial count or pass^k statement found (2026-11-05).

#### Q7 Cost and latency controls
- "Provider-agnostic language model interface with retry and telemetry." - [SDK architecture overview](https://docs.openhands.dev/sdk/arch/overview) (read 2026-11-05)
- Abstract: "model-agnostic multi-LLM routing, and built-in security analysis." - [arXiv 2511.03690](https://arxiv.org/abs/2511.03690) (read 2026-11-05)
- No budget, cache or effort control documented on the pages read (2026-11-05).

#### Q8 Security and identity
- "OpenHands uniquely integrates native sandboxed execution, lifecycle control," - [arXiv 2511.03690](https://arxiv.org/abs/2511.03690) (read 2026-11-05)
- Audit trail is a named responsibility ("Record security decisions in event history", above); no prompt-injection or identity statement on the security page (read 2026-11-05).

### Verification findings against the 2026-11-04 notes
- The notes carried the "61% reduction" as an unverified figure from an MLSys listing; it is now confirmed from the paper HTML with its absolute numbers (78.0 to 30.0 per 1k conversations).
- The notes' token-based condenser triggers (`max_tokens`, `llm.max_input_tokens`, from PR descriptions) are not on the architecture page, which is event-count based (default 120 / keep 4). Treat token triggers as UNVERIFIED on current docs.
- The notes list condenser example `max_size=10, keep_first=2`; the architecture page's defaults are 120 and 4.

### Inferences
- OpenHands is the strongest public evidence that event sourcing in the harness measurably reduces harness-attributable failures; the number is production telemetry, not a benchmark.
- The "risk level emitted by the model, enforced by code" pattern costs no extra model call and is the cheapest confirmation design in this survey; its weakness (the model rates its own action) is unaddressed in the docs.

### Gaps
- Pause granularity (whether a running tool completes before pause takes effect) is not stated. UNVERIFIED (2026-11-05).
- No OpenHands eval guide for the SDK beyond the benchmarks repository README (search snippet only).

---

## Manus

### Takeaway
Manus publishes one durable engineering statement (2025-07-18) on context assembly for cost: cache-hit rate as the primary metric, append-only context, logit masking instead of tool removal, restorable compression, recitation and keeping failures in context; and one sandbox post (2026-01-14) asserting Zero Trust and per-task isolated VMs. Nothing public covers verification, approvals, durable execution or evaluation.

### Cited Findings

#### Q1 Source of truth and context assembly
- "KV-cache hit rate is the single most important metric" and "the average input-to-output token ratio is around 100:1." - [Context Engineering for AI Agents (2025-07-18, Yichao 'Peak' Ji)](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) (read 2026-11-05)
- "A common mistake is including a timestamp"; "Ensure your serialization is deterministic"; "Our compression strategies are always designed to be restorable." - [Manus context post](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) (read 2026-11-05)
- "By constantly rewriting the todo list, Manus is reciting its objectives into the end of the context."; "leave the wrong turns in the context."; "don't few-shot yourself into a rut" - [Manus context post](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) (read 2026-11-05)

#### Q2, Q3, Q4, Q5, Q6
- No public Manus statement found on verification loops, inference-time grounding, approval semantics, durable execution or evaluation (searches and the two official posts, 2026-11-05). A search surfaced a third-party claim of an official post on approval mechanisms for the desktop "My Computer" feature; the post itself was not located. UNVERIFIED (2026-11-05).

#### Q7 Cost and latency controls
- "cached input tokens cost 0.30 USD/MTok, while uncached ones cost 3 USD/MTok" (Claude Sonnet, 2025 prices); tool masking: "it masks the token logits during decoding" - [Manus context post](https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) (read 2026-11-05)

#### Q8 Security and identity
- "Our Manus Sandbox follows the Zero Trust principle."; "your session/account data cannot be accessed from the Sandbox."; each sandbox is "a fully isolated cloud virtual machine that Manus allocates for each task"; "you and Manus have full control over this computer."; "Connectors will be automatically disabled once collaboration is enabled." - [Understanding Manus sandbox (2026-01-14)](https://manus.im/blog/manus-sandbox) (read 2026-11-05)
- Secondary and interested: a security vendor reports a class of zero-click indirect prompt-injection issues ("SilentBridge") in Manus; vendor report, UNVERIFIED (2026-11-05).

### Verification findings against the 2026-11-04 notes
- All Manus quotes in the notes re-verified verbatim today. The sandbox post is new to this file.

### Inferences
- Manus's contribution to the comparison is prefix stability and masking as cost controls; it should be cited for Q1/Q7 only.

### Gaps
- Approval and audit design for the desktop agent: UNVERIFIED (2026-11-05).

---

## MCP specification (revision 2026-07-28)

### Takeaway
The current revision is `2026-07-28`. It made MCP stateless (no `initialize` handshake, no `Mcp-Session-Id`), removed SSE resumability so a broken stream loses the in-flight request and must be re-issued with a new id, replaced server-initiated requests with the multi-round-trip `InputRequiredResult` pattern, moved tasks to an extension, deprecated Roots/Sampling/Logging and Dynamic Client Registration, and added `ttlMs`/`cacheScope`, deterministic tool ordering for prompt-cache hits and OpenTelemetry context propagation. Tool annotations (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) are hints that clients must treat as untrusted; `structuredContent` plus `outputSchema` carry typed results; there is no provenance field.

### Cited Findings

#### Version, scope and changelog
- The `latest` URL serves the schema at `schema/2026-07-28/schema.ts`; the changelog "lists changes made to the Model Context Protocol (MCP) specification since the previous revision, 2025-11-25." - [Specification](https://modelcontextprotocol.io/specification/latest); [Key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog) (read 2026-11-05)
- Draft for the next revision: "Changes since the most recent release will accumulate here." (page otherwise empty) - [Draft changelog](https://modelcontextprotocol.io/specification/draft/changelog) (read 2026-11-05)
- Stateless: "Remove protocol-level sessions and the `Mcp-Session-Id` header from the Streamable HTTP transport."; "Make MCP stateless: remove the `initialize`/`notifications/initialized` handshake."; "Add `server/discover`: servers MUST implement this RPC to advertise their supported protocol versions, capabilities, and identity." - [Key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog) (read 2026-11-05)
- Delivery semantics (Q5): "A broken response stream loses the in-flight request; clients **MUST** re-issue it as a new request with a new request ID" - [Key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog) (read 2026-11-05)
- Tasks: "Move experimental tasks out of the core protocol and into an official extension (`io.modelcontextprotocol/tasks`)." with polling via `tasks/get`; extensions index describes Tasks as "Asynchronous execution of long-running operations, with polling, mid-flight input, and durable handles" - [Key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog); [Specification](https://modelcontextprotocol.io/specification/latest) (read 2026-11-05)
- MRTR: "Servers return an `InputRequiredResult` (`resultType: "input_required"`) whose `inputRequests` field carries the requests for the additional information needed to process the request."; "All results now carry a required `resultType` field" - [Key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog) (read 2026-11-05)
- Caching and ordering (Q7): "Servers **SHOULD** return tools from `tools/list` in a deterministic order to enable client-side caching and improve LLM prompt cache hit rates."; "Require `ttlMs` and `cacheScope` fields on results returned by `tools/list`, `prompts/list`, `resources/list`, `resources/read`, and `resources/templates/list`" - [Key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog) (read 2026-11-05)
- Observability: "Document OpenTelemetry trace context propagation conventions for `_meta` keys (`traceparent`, `tracestate`, `baggage`)" - [Key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog) (read 2026-11-05)
- Deprecations: "Deprecate the Roots, Sampling, and Logging features"; "Deprecate the OAuth 2.0 Dynamic Client Registration Protocol ... as a client registration mechanism in favor of Client ID Metadata Documents"; policy "a minimum twelve-month deprecation window" - [Key changes](https://modelcontextprotocol.io/specification/2026-07-28/changelog) (read 2026-11-05)

#### Tool annotations (Q4, Q7)
- "NOTE: all properties in `ToolAnnotations` are **hints**." ... "Clients should never make tool use decisions based on `ToolAnnotations` received from untrusted servers." - [Schema, ToolAnnotations](https://modelcontextprotocol.io/specification/2026-07-28/schema) (read 2026-11-05)
- `readOnlyHint`: "If true, the tool does not modify its environment. Default: false"; `destructiveHint`: "If true, the tool may perform destructive updates to its environment. If false, the tool performs only additive updates. (This property is meaningful only when `readOnlyHint == false`) Default: true" - [Schema](https://modelcontextprotocol.io/specification/2026-07-28/schema) (read 2026-11-05)
- `idempotentHint`: "If true, calling the tool repeatedly with the same arguments will have no additional effect on its environment. (This property is meaningful only when `readOnlyHint == false`) Default: false"; `openWorldHint`: "If true, this tool may interact with an "open world" of external entities. If false, the tool's domain of interaction is closed." "Default: true" - [Schema](https://modelcontextprotocol.io/specification/2026-07-28/schema) (read 2026-11-05)
- Tools page: "For trust & safety and security, clients **MUST** consider tool annotations to be untrusted unless they come from trusted servers." - [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) (read 2026-11-05)

#### Structured content and provenance (Q3)
- `structuredContent`: "An optional JSON value that represents the structured result of the tool call. This can be any JSON value (object, array, string, number, boolean, or null) that conforms to the tool's outputSchema if one is defined." - [Schema, CallToolResult](https://modelcontextprotocol.io/specification/2026-07-28/schema) (read 2026-11-05)
- "Servers **MUST** provide structured results that conform to this schema." and "Clients **SHOULD** validate structured results against this schema."; "`structuredContent` is server-produced result data and is unrelated to LLM "structured outputs" (schema-constrained model generation)." - [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) (read 2026-11-05)
- Errors: "Any errors that originate from the tool SHOULD be reported inside the result object, with `isError` set to true, *not* as an MCP protocol-level error response." - [Schema, CallToolResult](https://modelcontextprotocol.io/specification/2026-07-28/schema) (read 2026-11-05)
- Provenance: no provenance or source-attribution field exists on tool results; content annotations carry only `audience`, `priority` and `lastModified` ("annotations that provide metadata about audience, priority, and modification times"). - [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) (read 2026-11-05)
- Stateful tools guidance (Q4/Q5): "MCP has no protocol-level session, so a server cannot rely on implicit per-connection state to relate one tool call to the next."; handles: "For authenticated servers, a handle is a name, not a capability." - [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) (read 2026-11-05)

#### Elicitation (Q4)
- Two modes: "**Form mode**: Servers can request structured data from users with optional JSON schemas to validate responses"; "**URL mode**: Servers can direct users to external URLs for sensitive interactions that must *not* pass through the MCP client" - [Elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation) (read 2026-11-05)
- "Servers **MUST NOT** use form mode elicitation to request sensitive information such as passwords, API keys, access tokens, or payment credentials"; clients "**MUST**" "Provide UI that makes it clear which server is requesting information"; three actions "accept", "decline", "cancel". - [Elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation) (read 2026-11-05)
- Form schemas are "limited to flat objects with primitive properties only." URL mode "is introduced in the `2025-11-25` version"; under MRTR the client learns the outcome "by retrying the original request". - [Elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation) (read 2026-11-05)
- Identity: "Servers **MUST NOT** rely on client-provided user identification without server verification, as this can be forged." - [Elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation) (read 2026-11-05)

#### Authorization and security (Q8)
- "Authorization is **OPTIONAL** for MCP implementations."; STDIO "**SHOULD NOT** follow this specification, and instead retrieve credentials from the environment."; "Authorization servers **MUST** implement OAuth 2.1 with appropriate security measures for both confidential and public clients." - [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) (read 2026-11-05)
- "MCP servers **MUST** implement OAuth 2.0 Protected Resource Metadata (RFC9728)."; clients "**MUST** implement Resource Indicators for OAuth 2.0 as defined in RFC 8707"; "MCP servers **MUST NOT** accept or transit any other tokens."; "Access tokens **MUST NOT** be included in the URI query string" - [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) (read 2026-11-05)
- Registration: "Authorization servers and MCP clients **SHOULD** support OAuth Client ID Metadata Documents"; Dynamic Client Registration "is deprecated and retained for backwards compatibility". Scope: clients "**SHOULD** follow the principle of least privilege by requesting only the scopes necessary for their intended operations." - [Authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization) (read 2026-11-05)
- Token passthrough: "MCP servers **MUST NOT** accept any tokens that were not explicitly issued for the MCP server."; confused deputy: "MCP proxy servers **MUST** implement per-client consent and proper security controls"; state handles: "MCP servers **MUST NOT** treat possession of a state handle as authentication." - [Security best practices](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices) (read 2026-11-05)
- Local servers: a one-click client "**MUST** implement proper consent mechanisms prior to executing commands." and should "Execute MCP server commands in a sandboxed environment with minimal default privileges" - [Security best practices](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices) (read 2026-11-05)
- Tool security: servers "**MUST**" "Validate all tool inputs", "Implement proper access controls", "Rate limit tool invocations", "Sanitize tool outputs"; clients "**SHOULD**" "Show tool inputs to the user before calling the server, to avoid malicious or accidental data exfiltration", "Validate tool results before passing to LLM", "Log tool usage for audit purposes". - [Tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) (read 2026-11-05)
- Key principle: "descriptions of tool behavior such as annotations should be considered untrusted, unless obtained from a trusted server." and "Hosts must obtain explicit user consent before invoking any tool" - [Specification](https://modelcontextprotocol.io/specification/latest) (read 2026-11-05)

### Verification findings against the 2026-11-04 notes
- The notes never recorded the MCP revision; the 2026-07-28 changes (stateless, no sessions, MRTR, SSE resumability removed, DCR deprecated) materially affect any harness that relied on `Mcp-Session-Id` or `Last-Event-ID`. Google's changelog shows ADK 2.9.0 adding "MCP SDK 2.x alongside 1.x" (carried over), which is the ADK path to this revision.

### Inferences
- For a harness, the two load-bearing MCP facts are: `idempotentHint` exists but is an untrusted hint, so the harness must enforce idempotency itself; and a dropped HTTP stream means the request may have executed server-side yet must be re-issued with a new id, which is at-least-once by construction.
- `structuredContent` plus `outputSchema` is the only standard place to carry typed figures; provenance must be encoded inside the schema by the server.

### Gaps
- The Tasks extension page and the `basic/patterns/mrtr` page were not read; "durable handles" is quoted from the index only. UNVERIFIED detail (2026-11-05).

---

## A2A protocol (1.0.0)

### Takeaway
A2A 1.0.0 models work as stateful tasks with interrupted states (`INPUT_REQUIRED`, `AUTH_REQUIRED`), leaves authorization to the server, signs agent cards with JWS, and states idempotency as MAY for sends and SHOULD for webhook consumers "as duplicate deliveries may occur".

### Cited Findings
- Version: 1.0.0 (previous 0.3.0, 0.2.6, 0.1.0). "Tasks are stateful and progress through a defined lifecycle." States include `INPUT_REQUIRED` ("Indicates that the agent requires additional user input to proceed. This is an interrupted state.") and `AUTH_REQUIRED` ("Indicates that authentication is required to proceed. This is an interrupted state."). - [A2A specification](https://a2a-protocol.org/latest/specification/) (read 2026-11-05)
- Q4/Q5 idempotency: "Send Message operations MAY be idempotent. Agents may utilize the messageId to detect duplicate messages."; webhooks: "Clients SHOULD process notifications idempotently, as duplicate deliveries may occur" and "Agents MAY implement retry logic with exponential backoff for failed deliveries." - [A2A specification, 4.3.3 and 13.2](https://a2a-protocol.org/latest/specification/) (read 2026-11-05)
- Q8 identity: "The client discovers the server's required authentication schemes via the `securitySchemes` field in the AgentCard."; "Once authenticated, the A2A Server authorizes requests based on the authenticated identity and its own policies."; "Servers MUST return an authorization error when the authenticated client lacks required permissions." - [A2A specification, 7.3 and 7.5](https://a2a-protocol.org/latest/specification/) (read 2026-11-05)
- Card integrity: "Signatures allow clients to verify that an Agent Card has not been tampered with." (JWS over a JCS-canonicalized card); "Clients SHOULD verify signatures when present to ensure the Agent Card has not been tampered with" - [A2A specification, 8.4 and 14.3](https://a2a-protocol.org/latest/specification/) (read 2026-11-05)
- Webhook security: "Agents SHOULD validate webhook URLs to prevent SSRF (Server-Side Request Forgery) attacks:" and "Clients MUST validate webhook authenticity using the provided authentication credentials" - [A2A specification, 13.2](https://a2a-protocol.org/latest/specification/) (read 2026-11-05)
- Input hygiene: "Agents MUST validate all input parameters before processing"; "Implementations MUST sanitize user-provided content to prevent injection attacks" - [A2A specification, 13.4 and 14.1.1](https://a2a-protocol.org/latest/specification/) (read 2026-11-05)
- Credential chains: in-band credential exchange can expose "those credentials to each agent participating in the chain." (7.6.3); `AUTH_REQUIRED` alone grants no authorization (7.6.4, paraphrase). - [A2A specification](https://a2a-protocol.org/latest/specification/) (read 2026-11-05)
- Enterprise page: "All A2A communication in production environments must occur over `HTTPS`."; "Once a client is authenticated, the A2A server is responsible for authorizing the request."; "use OpenTelemetry to propagate trace context, including trace IDs and span IDs, through standard HTTP headers"; "Audit significant events, such as task creation, critical state changes, and agent actions"; agents are "opaque" and "Agents must grant only the necessary permissions required for a client or user" - [Enterprise-ready features](https://a2a-protocol.org/latest/topics/enterprise-ready/) (read 2026-11-05)
- Relation to MCP: "A2A and MCP are complementary protocols designed for different aspects of agentic systems:" - [A2A specification, Appendix B](https://a2a-protocol.org/latest/specification/) (read 2026-11-05)
- Governance (Linux Foundation, Agentic AI Foundation banner 2026-08-27) and ADK's `to_a2a` support: carried over from the 2026-11-04 notes; not re-fetched.

### Inferences
- A2A gives a harness a standard vocabulary for "paused for a human" (`INPUT_REQUIRED`) and "paused for credentials" (`AUTH_REQUIRED`) but no execution-semantics guarantee; the duplicate-delivery SHOULD mirrors MCP's at-least-once reality.

### Gaps
- Prompt-injection guidance between agents is absent from the spec and the enterprise page (read 2026-11-05); only generic sanitisation MUSTs exist.

---

## What changed since 2026-11-04

### Takeaway
Between the 2026-11-04 notes and 2026-11-05 nothing shipped for ADK, Claude Code, the OpenAI Agents SDK stable line or the MCP spec; DeepSeek pushed a dsh pre-release on 2026-11-04. The dated events that matter for the paper are the Gemini 2.5 routings (2026-12-01), the Gemini price step-ups (2026-12-01 and 2027-01-01), the OpenAI Evals shutdown (2026-11-30), and the MCP 2026-07-28 revision, which the notes had not recorded.

### Cited Findings
- ADK Python: PyPI "Released: Oct 23, 2026." for 2.13.0; prior 2.12.0 Oct 13, 2.11.0 Oct 2; no 2.14.0 found. - [PyPI google-adk](https://pypi.org/project/google-adk/) (read 2026-11-05)
- Claude Code: npm `dist-tags` `{'stable': '2.1.311', 'latest': '2.1.318', 'next': '2.1.318'}`; 2.1.317 published `2026-11-02T23:57:53Z`, 2.1.318 `2026-11-03T21:55:17Z`; registry `modified` `2026-11-04T00:01:06Z`; no version newer than 2.1.318. - [npm registry @anthropic-ai/claude-code](https://registry.npmjs.org/@anthropic-ai/claude-code) (read 2026-11-05)
- OpenAI Agents SDK: v0.24.0 released 15 Oct; "Agents SDK v0.24.0-alpha.6" pre-release 03 Nov; v0.23.1 and v0.23.0 02 Oct. - [openai-agents-python releases](https://github.com/openai/openai-agents-python/releases) (read 2026-11-05)
- OpenAI Evals: read-only since 2026-10-31; "the platform is scheduled to shut down on November 30, 2026." - [Deprecations](https://developers.openai.com/api/docs/deprecations#2026-06-03-evals-platform) (read 2026-11-05)
- DeepSeek dsh: npm `dist-tags` `{'next': '0.2.2-rc.1', 'latest': '0.2.1-rc.5', 'alpha': '0.2.2-alpha.3'}`; `0.2.2-rc.1` published `2026-11-04T09:20:32Z`, `0.2.1-rc.5` `2026-10-29T14:15:23Z`; description "dsh CLI: profile boot, plugin management, and the browser UI alias"; license MIT. - [npm registry @deepseek-ai/dsh](https://registry.npmjs.org/@deepseek-ai/dsh) (read 2026-11-05)
- Gemini API changelog entries after 2026-10-15: 2026-10-27 Gemini API CLI beta; 2026-11-02 deprecation notices for Gemini 2.5 Pro and 2.5 Flash with 2026-12-01 routing; 2026-11-04 "Voice remixing for Gemini 3.8 TTS". - [Gemini API changelog](https://aistudio.google.com/docs/changelog) (read 2026-11-05)
- Gemini pricing dates: 4 Argon promotional input/output "through November 30, 2026."; 3.8 Flash "through December 31, 2026."; 2.5 Flash routes to 3.5 Flash-Lite and 2.5 Pro to 3.8 Flash "Effective December 1, 2026". - [Pricing](https://aistudio.google.com/docs/pricing); [Deprecations](https://aistudio.google.com/docs/deprecations) (read 2026-11-05)
- MCP: revision 2026-07-28 is current; the draft changelog is empty. - [Draft changelog](https://modelcontextprotocol.io/specification/draft/changelog) (read 2026-11-05)
- Managed Agents still beta under `managed-agents-2026-04-01`; request examples carry `anthropic-version: 2026-10-21`. - [Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview) (read 2026-11-05)

### Inferences
- Any cost table in the paper built on Gemini 3.8 Flash or 4 Argon list prices should carry the promotional end dates; a table built on 2.5 Flash should state that the endpoint routes to 3.5 Flash-Lite from 2026-12-01.

### Gaps
- Claude Code CHANGELOG entries carry no dates on the page; dates above come from npm publish timestamps, which can lag the changelog by hours.

---

## Cross-vendor summary (for the comparative-study table)

### Takeaway
Across the nine groups, the only universally shared design is a harness-enforced control layer above the prompt; the field splits on whether the source of truth is a log (Managed Agents, dsh, OpenHands, ADK events) or a state snapshot (LangGraph checkpoints, OpenAI RunState), and only OpenAI, Google and LangGraph write down that tool execution is at-least-once.

### Cited Findings
- See the vendor sections above; this table is an index of the strongest statement per cell and names what is left to the builder.

| Question | Anthropic | OpenAI | Google ADK | dsh | LangGraph/LC | OpenHands | Manus | MCP / A2A |
|---|---|---|---|---|---|---|---|---|
| Q1 source of truth | append-only server log; events transformed before the window | client session or opaque server compaction item | session event log; `EventsCompactionConfig` token/sliding | JSONL log; "model-visible means logged"; attempts kept out | per-step checkpoint on `thread_id`; summarization middleware | immutable event log; `Condensation` event; derived View | append-only prefix, restorable compression | MCP stateless; `ttlMs`/`cacheScope` |
| Q2 verification | Stop hooks exit 2; rubric grader in separate context | tripwire guardrails; Stop hook continuation; Auto-review agent | plugin-before-callback order; conformance replay; no inference-time critic | fail-closed approval gate; no critic | HITL middleware; no critic | model-emitted risk label enforced by code | none public | n/a |
| Q3 figure grounding | left to builder (`updatedToolOutput` seam) | left to builder (tool output guardrail) | eval-time `hallucinations_v1` only | left to builder | left to builder | left to builder | none | `structuredContent`+`outputSchema`; no provenance field |
| Q4 approvals | waits indefinitely; duplicate results ignored; no exactly-once claim | "does not guarantee exactly-once"; idempotency keys | "may run more than once"; builder checks duplicates | audit-only decisions; no claim | "does not make external side effects happen exactly once" | ConfirmRisky, UNKNOWN confirms; no claim | none | `idempotentHint` untrusted; A2A MAY/SHOULD idempotent |
| Q5 durable execution | stateless harness, `wake(sessionId)`; `rescheduling` | Temporal/DBOS integrations; RunState | `ResumabilityConfig`; not for custom agents or CLI | torn-tail discard; no resume-of-turn story | sync/async/exit durability; nodes re-run | crash-recoverable state; 61% fewer system failures | none | stream loss = re-issue with new id |
| Q6 evaluation | pass^k; 3 runs/case; delta never gates | 10-20 prompts; deterministic first; Evals product retired | 1.0/0.8 defaults; 2 runs; conformance on PRs; `adk optimize` | minimal JSON-RPC agent; no CI statement | `num_repetitions`; pytest/Vitest | paper benchmarks; no CI statement | none | n/a |
| Q7 cost | USD cap with overshoot; effort; cache 0.1x/0.025x | effort levels; cache 1,024-token prefix; reads 0.1x/0.05x | `max_llm_calls` 500; `FallbackModel` experimental; promo prices end Nov/Dec | token ratios only; no cost cap | call-count limits; model fallback middleware | retry; no budget | cache-hit rate as the metric | deterministic tool order for cache hits |
| Q8 security | classifier sees no tool results; deny rules in every mode; vault proxy | OS sandbox; reviewer "not a guarantee"; OTel off by default | Model Armor skips tool results; VPC-SC; SPIFFE identity | bwrap/Landlock/Seatbelt; never silent passthrough; logs uploaded by default | PII middleware; sandbox backends | risk analyzer; audit events | Zero Trust VM per task | OAuth 2.1, RFC 8707, no token passthrough |

### Inferences
- The strongest public statements per question come from different vendors: Anthropic (Q2, Q6 methodology), OpenAI (Q4 semantics, Q7 caching rules), Google (Q5 at-least-once wording, Q6 CI gate), dsh and OpenHands (Q1 log discipline), MCP (Q8 protocol-level MUSTs). No vendor answers Q3 at inference time.

### Gaps
- None beyond those listed per vendor.

---

## Source index (all read 2026-11-05 unless marked carried over)

Anthropic: https://code.claude.com/docs/en/agent-sdk/agent-loop ; https://code.claude.com/docs/en/hooks ; https://code.claude.com/docs/en/best-practices ; https://code.claude.com/docs/en/permission-modes ; https://code.claude.com/docs/en/security ; https://code.claude.com/docs/en/model-config ; https://code.claude.com/docs/en/agent-sdk/sessions ; https://code.claude.com/docs/en/agent-sdk/permissions ; https://code.claude.com/docs/en/plugin-evals ; https://platform.claude.com/docs/en/managed-agents/overview ; https://platform.claude.com/docs/en/managed-agents/sessions ; https://platform.claude.com/docs/en/managed-agents/session-operations ; https://platform.claude.com/docs/en/managed-agents/events-and-streaming ; https://platform.claude.com/docs/en/managed-agents/permission-policies ; https://platform.claude.com/docs/en/managed-agents/define-outcomes ; https://platform.claude.com/docs/en/build-with-claude/compaction ; https://platform.claude.com/docs/en/build-with-claude/compaction-on-demand ; https://platform.claude.com/docs/en/build-with-claude/prompt-caching ; https://www.anthropic.com/engineering/managed-agents ; https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents ; https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md ; https://registry.npmjs.org/@anthropic-ai/claude-code

OpenAI: https://openai.github.io/openai-agents-python/human_in_the_loop/ ; https://openai.github.io/openai-agents-python/guardrails/ ; https://openai.github.io/openai-agents-python/sessions/ ; https://openai.github.io/openai-agents-python/running_agents/ ; https://openai.github.io/openai-agents-python/tracing/ ; https://developers.openai.com/api/docs/guides/context-management ; https://developers.openai.com/api/docs/guides/prompt-caching ; https://developers.openai.com/api/docs/guides/reasoning ; https://developers.openai.com/api/docs/deprecations#2026-06-03-evals-platform ; https://alignment.openai.com/auto-review ; https://learn.chatgpt.com/docs/agent-approvals-security.md ; https://learn.chatgpt.com/docs/sandboxing.md ; https://learn.chatgpt.com/codex/hooks ; https://learn.chatgpt.com/blog/eval-skills ; https://github.com/openai/openai-agents-python/releases

Google: https://adk.dev/runtime/resume/index.md ; https://adk.dev/context/compaction/index.md ; https://adk.dev/context/caching/index.md ; https://adk.dev/tools-custom/confirmation/index.md ; https://adk.dev/evaluate/index.md ; https://adk.dev/evaluate/criteria/index.md ; https://adk.dev/optimize/index.md ; https://adk.dev/runtime/runconfig/index.md ; https://adk.dev/plugins/index.md ; https://adk.dev/agents/models/index.md ; https://adk.dev/agents/models/routing/index.md ; https://adk.dev/agents/llm-agents/index.md ; https://adk.dev/safety/index.md ; https://adk.dev/integrations/model-armor/index.md ; https://github.com/google/adk-python/blob/main/src/google/adk/models/_fallback_model.py ; https://github.com/google/adk-python/blob/main/src/google/adk/evaluation/agent_evaluator.py ; https://github.com/google/adk-python/releases ; https://github.com/google/adk-python/blob/main/CHANGELOG.md ; https://pypi.org/project/google-adk/ ; https://aistudio.google.com/docs/pricing ; https://aistudio.google.com/docs/deprecations ; https://aistudio.google.com/docs/changelog ; https://aistudio.google.com/docs/caching

DeepSeek: https://github.com/deepseek-ai/deepseek-harness ; docs/architecture.md, docs/glossary.md, docs/agent-lifecycle.md, docs/tool-execution-pipeline.md, docs/persistence-catalog.md, docs/config-catalog.md, docs/subsystems/{approval,compaction,sandbox,persistence,permission-presets,product-telemetry}.md, SAFETY.md, BENCHMARK.md under that repository ; https://www.deepseek.com/en/harness/ ; https://arxiv.org/abs/2608.25512 ; https://registry.npmjs.org/@deepseek-ai/dsh

LangChain: https://docs.langchain.com/oss/python/langgraph/interrupts ; https://docs.langchain.com/oss/python/langgraph/persistence ; https://docs.langchain.com/oss/python/langgraph/graph-api ; https://docs.langchain.com/oss/python/langgraph/fault-tolerance ; https://docs.langchain.com/oss/python/langgraph/durable-execution (search snippet only) ; https://docs.langchain.com/oss/python/langchain/middleware/built-in ; https://docs.langchain.com/oss/python/deepagents/overview ; https://docs.langchain.com/langsmith/repetition ; https://docs.langchain.com/langsmith/evaluation-concepts

OpenHands: https://docs.openhands.dev/sdk/arch/security ; https://docs.openhands.dev/sdk/arch/condenser ; https://docs.openhands.dev/sdk/guides/context-condenser ; https://docs.openhands.dev/sdk/arch/overview ; https://docs.openhands.dev/sdk/guides/convo-persistence ; https://docs.openhands.dev/sdk/guides/convo-pause-and-resume ; https://arxiv.org/abs/2511.03690 ; https://arxiv.org/html/2511.03690v2

Manus: https://manus.im/en/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus ; https://manus.im/blog/manus-sandbox

MCP: https://modelcontextprotocol.io/specification/latest ; https://modelcontextprotocol.io/specification/2026-07-28/changelog ; https://modelcontextprotocol.io/specification/2026-07-28/server/tools ; https://modelcontextprotocol.io/specification/2026-07-28/schema ; https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation ; https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization ; https://modelcontextprotocol.io/specification/latest/basic/security_best_practices ; https://modelcontextprotocol.io/specification/draft/changelog

A2A: https://a2a-protocol.org/latest/specification/ ; https://a2a-protocol.org/latest/topics/enterprise-ready/

Carried over without re-fetch (2026-11-04 notes): Anthropic engineering posts on prompt caching (2026-04-30), writing tools (2025-09-11), /goal docs; OpenAI structured outputs, agents, background and flex guides, Ghosts in the Codex Machine mirror, Kundel talk; Google Developers Blog context post (2025-12-04), adk.dev/2.0, callbacks, grounding, thinking, Agent Identity, BigQuery Agent Analytics; OpenHands critic blog (2025-04-17); DeepSeek V4 model cards and pricing (secondary); A2A governance.
