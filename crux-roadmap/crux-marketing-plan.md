# Crux Marketing Plan: Building in Public with AI

## 0. The Core Message: Your AI Tools Are Disposable. Your Intelligence Shouldn't Be.

Before anything else, understand the positioning shift that changes everything about how Crux goes to market.

**The `.crux` directory is the product.** Not Claude Code integration. Not OpenCode support. Not any single tool. The `.crux` directory — both `~/.crux/` (global, cross-project intelligence) and `.crux/` (per-project state and knowledge) — is where all your AI-assisted development intelligence lives. Every correction the AI makes, every pattern it learns, every security audit it runs, every mode handoff it executes — all of it accumulates in `.crux/`. Not in `.claude/`. Not in `.cursor/`. Not in `.opencode/`. In `.crux/`.

**Why this matters for marketing:** Every other AI coding tool locks your intelligence into their ecosystem. You build up context in Cursor, you lose it when you try Claude Code. You accumulate knowledge in Claude Code, it doesn't transfer to Aider. Your corrections, your learned patterns, your project context — all trapped in vendor-specific directories that die when you switch tools.

Crux is the intelligence layer that sits underneath ALL of them. `.crux/` is the source of truth. The **Crux MCP Server** is the universal brain — one server, all logic, every tool connects to it via standard MCP protocol. Tools with hook support (Claude Code, OpenCode) add paper-thin shims (5-10 lines each, zero logic) that forward events to the MCP server for correction detection and safety interception. Tools without hooks (Cursor, Cline, Roo Code) connect via MCP alone and still get the majority of Crux's value — knowledge, session state, modes, safety validation, digests. Adding support for a new tool goes from "write a full adapter" to "add one line to the tool's MCP config." When you run `crux switch opencode` after working in Claude Code, your session state, knowledge, corrections, and context come with you. Seamlessly. No re-teaching. No lost context. No starting over.

**The one-liner:** "Crux is the `.git` for AI coding intelligence — it travels with you, no matter what tool you use."

**This is the through-line for every piece of content.** Every X thread, every blog post, every HN launch, every comparison post. The message is: stop letting your AI tools own your intelligence. Own it yourself. `.crux/` is how.

**The messaging pillars:**

1. **Tool-agnostic intelligence** — "Works with Claude Code, OpenCode, Cursor, Aider, Roo Code. Switch freely. Lose nothing."
2. **Self-improving safety** — "Seven-stage pipeline that learns from your corrections and gets smarter over time."
3. **Sovereign development** — "Your knowledge, your corrections, your infrastructure. No vendor lock-in. Ever."
4. **Seamless switching** — "Start a project in Claude Code at work. Pick it up in OpenCode at home. `crux switch` — that's it."

**The architecture that backs this up:**

```
┌─────────────────────────────────────────────┐
│              Crux MCP Server                 │
│         (ALL logic lives here)               │
│                                              │
│  Knowledge, session, corrections, digest,    │
│  safety, modes, project context              │
│                                              │
│  Reads/writes: ~/.crux/ and .crux/           │
└──────────────┬──────────────────────────────┘
               │ MCP protocol (stdio/HTTP)
    ┌──────────┼──────────────────┐
    │          │                  │
    ▼          ▼                  ▼
┌────────┐ ┌────────┐    ┌──────────────┐
│ Claude │ │OpenCode│    │Cursor/Cline/ │
│  Code  │ │        │    │Roo Code/etc  │
│        │ │        │    │              │
│ hooks: │ │plugins:│    │  MCP only    │
│ ~10 LOC│ │~10 LOC │    │ (no hooks)   │
│  each  │ │ each   │    │              │
└────────┘ └────────┘    └──────────────┘

~/.crux/                          # Global: cross-project intelligence
├── knowledge/shared/             # Patterns that transcend any project
├── modes/                        # 21 canonical mode definitions
├── corrections/                  # Cross-project correction patterns
└── mcp/server.json               # MCP server config

.crux/                            # Per-project: state + knowledge
├── knowledge/                    # Project-specific learned patterns
├── sessions/state.json           # THE bridge between tools
├── corrections/                  # Project correction log
├── scripts/                      # Safety-first script pipeline
└── context/PROJECT.md            # Auto-generated project context
```

The MCP server exposes all Crux operations as tools: `crux_lookup_knowledge`, `crux_get_session_state`, `crux_update_session`, `crux_get_mode_prompt`, `crux_validate_script`, `crux_detect_correction`, `crux_get_digest`, `crux_write_handoff`, `crux_promote_knowledge`, `crux_get_project_context`. The key file is `.crux/sessions/state.json` — it captures what you're working on, key decisions made, files touched, pending tasks, and a context window summary. When you switch tools, Crux injects this state so the new tool knows exactly where you left off.

**What MCP handles (the LLM calls Crux):** Knowledge lookup, session state, mode definitions, safety validation, digest, project context — roughly 60% of Crux's value. One server. Every tool. Zero adapters.

**What hooks handle (Crux observes the LLM):** Correction detection (watching user messages for "no, wrong, actually"), session logging (capturing every interaction), safety interception (blocking unsafe commands before execution), compaction injection (preserving state during context compression), auto-mode detection. These require push, not pull — Crux needs to observe events the LLM doesn't control. The hooks are 5-10 line shims that forward to the MCP server. Zero logic in the hooks themselves.

**Content strategy implication:** Every comparison post ("Crux vs. X") now has a devastating closer: "And when you outgrow X, or want to try Y, your intelligence comes with you. Because it lives in `.crux/`, not in their proprietary directory."

---

## 1. The Build-in-Public Philosophy

You're sitting on an unfair advantage, and you might not even realize it yet.

Most AI tools have a problem: they're built by people who don't use them. They hire "growth hackers" who write marketing copy about features they don't understand. They run ads to people who don't care. They hire sales teams. It costs millions. And developers smell the inauthenticity from a mile away.

You have the opposite problem: no budget, but a solution. You're building Crux because you use Crux every single day. Every commit is proof. Every bug you fix solves your own problem. Every feature you ship is something you needed. That's the most credible marketing asset you have.

And now you have a second unfair advantage: **you're not tied to any single tool.** You're building Crux across Claude Code and OpenCode simultaneously — dogfooding the exact `crux switch` workflow you're selling. Every time you switch tools mid-project without losing context, that's a demo. Every time `.crux/` carries your corrections from one tool to another, that's proof. You're not just building the product — you're living the pitch.

Build-in-public works because it taps into something primal in the developer community: we trust builders, not marketers.

**The case studies prove this.**

Railway built from $0 to 2M monthly API calls without a CMO. No performance marketing budget. They posted shipping updates, architecture decisions, and technical deep-dives. Developers watched a real team build a real product. It compounded. Now they're a unicorn.

Cursor didn't spend venture capital on ads in the traditional sense. They shipped a product so good that developers paid for it. They wrote about how they built it, why certain architectural choices matter, and what they learned. Product-led growth. Now they're valued at $1.2B.

Supabase has 81,000 GitHub stars. They got there through the same playbook: honest technical content, shipping every week, showing the work, not hiding behind marketing speak.

You have an even bigger advantage: Crux is philosophically aligned with this approach. You preach "infrastructure beats prompts." You're building a tool that gets better with usage and learns from corrections. The way you market it should mirror the product itself: show the infrastructure, not the marketing layers.

Here's the psychological truth: a developer reading about how you fixed a memory leak in your AI inference pipeline learns more about Crux than any feature list could tell them. They see the rigorous thinking. They see the priorities. They understand the architecture because you're explaining real decisions, not abstract benefits.

The best part? This isn't theoretical for you. Every single day, you're generating marketing content accidentally. Every commit is a story. Every closed issue is a win. Every performance improvement is proof that Crux works. You're not starting from zero—you're starting with the most authentic narrative in tech: a solo founder shipping.

## 2. The AI-Assisted Content Pipeline

Here's the core innovation: Crux's philosophy about infrastructure beats prompts applies to marketing. You don't need more prompts, you need better infrastructure.

The traditional approach: Bryan works all day building, then has to manually write posts, manage social media, and juggle multiple platforms. It's a context switch tax that drains energy from the actual product. So you don't do it, and Crux stays invisible.

The infrastructure approach: Your work generates content automatically. Your builds, commits, and shipping become the input. AI drafts. You review and refine. That's it.

And here's the kicker: because `.crux/` tracks your sessions, corrections, and knowledge across tools, the marketing command can pull from a richer source than just git. It knows what modes you used, what corrections the AI made, what knowledge entries were generated. That's content that no other tool can auto-generate — because no other tool has a cross-tool intelligence layer to pull from.

**The Continuous Flow (Event-Driven, Typefully-Integrated)**

You don't work 9-5. You work around the clock. The marketing system matches your rhythm: continuous, event-driven, rate-limited. No "end of session" — there is no end of session. You sleep, you wake up, you continue. Crux watches what you're shipping and generates posts as material accumulates.

**Target cadence: ~1 post per hour while you're working. Never more than 1 per 15 minutes.**

```
You're building. Crux is watching.

     → Every 3-5 commits, Crux checks: enough material for a post?
     → Every ~50K tokens or ~30 tool calls, Crux surfaces a draft
     → When a high-signal event fires (tests pass after failure,
       new MCP tool created, git tag, PR merge), Crux auto-drafts
     → You can always type `crux marketing` manually

     When a draft is ready:
     → Crux presents it inline in your terminal (2-3 sentences max)
     → [a]pprove  [e]dit  [s]kip  — one keystroke, back to work
     → Approved post queues to Typefully API
     → Cooldown gate: minimum 15 min between queued posts
     → Posts drip out ~1/hour while you're shipping

     You never stop building. Posts happen alongside your work.
```

**Trigger System (all event-driven, no clock-based triggers):**

1. **Commit threshold**: Every N commits (default: 3-5), Crux evaluates if there's a postable story. Configurable per project.

2. **Token/interaction threshold**: After ~50K tokens of conversation or ~30 substantive interactions (tool calls, code edits — not just chat), Crux surfaces: "Enough material for a post. Want to review?"

3. **High-signal event detection**: Crux watches for events that are inherently interesting:
   - Test suite goes green after being red
   - New file created matching patterns (new MCP tool, new mode, new test file)
   - Git tag created (release)
   - PR merged
   - Error fixed after multiple attempts (great debugging story)
   - `crux adopt` or `crux switch` executed (tool-switching content)
   - New knowledge entry promoted (architecture story)
   - New correction pattern detected (learning story)

4. **Manual**: `crux marketing` anytime you feel like something's worth posting.

5. **Cooldown gate (hard floor)**: No matter what triggers, minimum 15 minutes between queued posts. Crux tracks `last_queued_at` in `.crux/marketing/state.json` and enforces the floor. Target is ~1/hour, but if you're shipping fast, 1 per 15-20 min is fine.

6. **Quiet hours (optional)**: If you want to pause posting while you sleep, set `quiet_hours` in config. Posts generated during quiet hours queue for the next active window. Or don't — round-the-clock posting is fine for #buildinpublic.

**The Critical Insight:** You review every post before it queues. The approve step is mandatory. But it's ONE KEYSTROKE — `a` to approve, `s` to skip — and you're back to building. No context switch. No web app. The draft appears inline, you decide in 5 seconds, it queues automatically.

**Implementation Details**

The `crux marketing` system (MCP tool + mode + event hooks):

1. **Trigger evaluation** (runs automatically or manually):
   - Checks commit count since last post (threshold: 3-5)
   - Checks token/interaction count since last post (threshold: ~50K tokens or ~30 tool calls)
   - Checks for high-signal events (test green, new file, tag, merge, correction, knowledge promotion)
   - Checks cooldown: `last_queued_at` must be >15 min ago
   - If triggered, proceeds to step 2. If not, stays quiet.

2. **Reads sources** (all from `.crux/` — this is why tool-agnostic matters):
   - `git log` since last marketing post (not since "1 day ago" — since last post)
   - `.crux/sessions/` for session context: modes used, tool switches, corrections
   - `.crux/corrections/corrections.jsonl` for AI correction stories (great content)
   - `.crux/knowledge/` for newly promoted knowledge entries
   - Commit messages and diffs for technical context
   - `.crux/marketing/history.json` to avoid repeat content

3. **Generates 1 draft** (not 3-5 — one at a time, matching the continuous rhythm):
   - Single X tweet (280 chars, punchy) OR
   - X thread (4-8 tweets, if enough material for a narrative arc)
   - Saved to `.crux/marketing/drafts/[timestamp].md`

4. **Inline review** (minimal interruption):
   - Presents draft in 2-3 lines with character count
   - `[a]pprove` — queue to Typefully immediately
   - `[e]dit` — open in $EDITOR or edit inline, then approve
   - `[s]kip` — discard, Crux won't resurface this material for 6 hours
   - One keystroke. Back to building.

5. **Queue to Typefully** (automatic on approve):
   - `POST https://api.typefully.com/v2/social-sets/288244/drafts`
   - Auth: `Bearer` token from `.crux/marketing/typefully.key` (gitignored)
   - Sets `publish_at` to max(now + 5min, last_queued_at + stagger_minutes)
   - Threads: multiple objects in `platforms.x.posts[]`
   - Updates `last_queued_at` in `.crux/marketing/state.json`
   - Stores draft ID in `.crux/marketing/queued/[date].json` for tracking

6. **Confirms** with one line: "Queued: [preview] → 7:42 PM"

**Typefully API Integration (live, tested, working):**

```
Endpoint: POST https://api.typefully.com/v2/social-sets/{social_set_id}/drafts
Auth:     Authorization: Bearer {api_key}
Content:  application/json

# Single tweet
{
  "platforms": { "x": { "enabled": true, "posts": [{"text": "..."}] }},
  "publish_at": "2026-03-06T00:20:00Z"
}

# Thread (multiple posts)
{
  "platforms": { "x": { "enabled": true, "posts": [
    {"text": "Tweet 1..."},
    {"text": "Tweet 2..."},
    {"text": "Tweet 3..."}
  ]}},
  "publish_at": "2026-03-06T00:35:00Z"
}

# Update existing draft
PATCH /v2/social-sets/{id}/drafts/{draft_id}

# List drafts (check status)
GET /v2/social-sets/{id}/drafts
```

**Config stored in `.crux/marketing/config.json` (gitignored):**
```json
{
  "typefully": {
    "social_set_id": 288244,
    "api_key_path": ".crux/marketing/typefully.key",
    "account": "@splntrb",
    "plan": "creator"
  },
  "triggers": {
    "commit_threshold": 4,
    "token_threshold": 50000,
    "interaction_threshold": 30,
    "high_signal_events": ["test_green", "new_mcp_tool", "git_tag", "pr_merge", "crux_switch", "crux_adopt", "knowledge_promoted", "correction_detected"],
    "cooldown_minutes": 15,
    "target_posts_per_hour": 1,
    "quiet_hours": null
  },
  "defaults": {
    "platforms": ["x"],
    "schedule_mode": "now"
  },
  "state_path": ".crux/marketing/state.json",
  "history_path": ".crux/marketing/history.json"
}
```

**Periodic Generation (every ~50-100 commits)**

When enough material accumulates, extend the scope:

- Claude reads all git activity since the last periodic generation
- Generates one comprehensive blog post (1500-2500 words)
- Drafts an X thread (10-15 tweets) summarizing the chunk of work
- Creates a Reddit post for r/SideProject or r/LocalLLaMA
- Suggests discussion topics for GitHub Discussions
- Extracts "good first issue" candidates for attracting contributors

**Monthly Generation**

Once a month:

- Claude generates a full changelog entry (detailed, organized by feature/bug/perf)
- Drafts a dev.to article about the month's biggest architectural decision
- Creates a retrospective post (what went well, what was hard, what's next)
- Compiles metrics (stars gained, users, revenue, etc.)

**Milestone-Based Content**

When specific events happen:

- 1K stars: pre-drafted celebration thread (you can personalize)
- 5K stars: blog post on "how we hit 5K stars in 60 days"
- First paying customer: story-driven post about the customer's use case
- First open source contributor: thank you post + profile link
- Each release: changelog + feature highlights + demo link

**Content Types Auto-Generated**

```
SHIPPING UPDATES
- New feature launched
- Example: "Just shipped self-improving safety pipeline. Takes corrections
  and bakes them into the base model. Here's why this matters... [thread]"

BUG FIX STORIES
- Real problem, real solution
- Example: "Spent 4 hours tracking down memory leak in token caching.
  Turns out LRU eviction was triggering during inference. Now handles
  10x load. Here's the fix... [code snippet]"

ARCHITECTURE DECISIONS
- Why you chose X over Y
- Example: "We're not using vLLM. Here's why. We needed fine-grained
  control over the safety pipeline, which required... [thread]"

PERFORMANCE IMPROVEMENTS
- Benchmarks, comparisons, proof
- Example: "Cut inference latency by 40% by... [metrics + code]"

WEEKLY DIGESTS
- Summary of week's work + direction ahead
- Example: "This week we shipped 3 features, fixed 12 bugs, and gained
  200 stars. Next week: scaling the safety pipeline. [thread]"

COMPARISON POSTS
- Crux vs. Cursor, Replit, etc.
- Example: "I built Crux because Claude Code doesn't let me control the
  safety rules. Here's what's different... [honest comparison]"
- NEW: "I use Claude Code AND OpenCode on the same project. Here's how
  .crux/ makes them interchangeable... [thread]"

TOOL-SWITCHING STORIES
- Real workflow, showing seamless tool transitions
- Example: "Started this feature in Claude Code this morning. Switched to
  OpenCode after lunch. `crux switch opencode` — it picked up exactly
  where I left off. Same knowledge. Same corrections. Same context.
  This is why .crux/ exists."

LEARNING POSTS
- What went wrong and why
- Example: "We tried approach X for multi-agent coordination. It failed
  because... Here's what we learned... [technical deep-dive]"

COMMUNITY SPOTLIGHTS
- User success stories, contributors, forks
- Example: "Someone just built a VSCode extension for Crux. Here's what
  it does... [feature showcase]"
```

**What Bryan Does vs. What AI Does**

You're not abdicating your voice. You're outsourcing the low-leverage work.

**AI handles:**
- Initial draft generation from commits
- Hashtag research and suggestions
- Optimal posting time calculation
- Multiple format variations (Twitter thread vs. Reddit vs. blog)
- Bulk of the writing (saves you 2-3 hours/week)

**You handle (~5 seconds per draft, inline):**
- Read the draft when it appears between commits
- One keystroke: [a]pprove, [e]dit, or [s]kip
- Edit if the AI missed nuance or voice
- Personalize with real details only you know

**You absolutely never automate:**
- Replies to people's comments (engage manually, every time)
- DMs to potential users or collaborators
- Comments on other people's posts (always authentic)
- Community engagement on Discord/GitHub (real human time)

The rule: AI creates, you connect. AI writes, you relate.

## 3. Platform Playbook

Not all platforms are equal for Crux. Some are high-leverage, some are nice-to-have. Some require different content approaches. Here's how to use each platform without burning out.

### X (Twitter)

**Why it matters:**
X is where developers hang out. Where technical discussions happen. Where your potential users spend 30 minutes every morning. The algorithm rewards shipping updates and technical insights. Most importantly, X conversations get indexed by Google—your thread about why you chose local LLMs over cloud APIs might be someone's answer to "should I use cloud or local?"

**Posting frequency:**
~1 post per hour while you're working, minimum 15 min between posts. You work around the clock, so posts go out around the clock. This is actually ideal for #buildinpublic — followers in different timezones always have something fresh. Crux generates drafts continuously from your actual work, you approve with one keystroke, Typefully queues them. On a heavy shipping day that's 10-15 posts. On a slower research day, maybe 3-5. The cadence matches your actual output, not an arbitrary schedule.

**Content format that works:**
- Shipping threads (your main content type). Structure: Problem → Solution → Impact → What's next
- Single tweets for quick wins (bug fixed, minor feature, code snippet, question to community)
- Threads for deep dives (architecture decisions, comparisons, retrospectives)
- Questions that prompt discussion (no answers in the tweet, let the community fill it)
- Retweets of community wins (someone shipped Crux extension, someone deployed it, someone contributed)

**Example Posts (actually use these):**

**THREAD 1: Shipping Update**

"just shipped multi-agent coordination in Crux. this is the feature that makes it actually feel like rails for AI.

here's the problem: every AI tool treats each task in isolation. call function. wait for result. call next function. stupid. humans don't work like that.

with multi-agent coordination, your AI can:
- spawn sub-agents for parallel work
- have agents negotiate with each other
- share context across a session
- handle interrupts and reprioritization

example: you ask Crux to 'refactor this codebase and deploy it.' instead of doing it sequentially, it spawns 3 agents: one reads the codebase, one designs the refactor, one writes the deploy config. they work in parallel. they share findings. if the reader finds something important, the writer knows about it.

this is infra, not prompts. the agents are running in the same context window, share memory, can interrupt each other.

why does this matter? because real engineering isn't linear. it's parallel, collaborative, and adaptive. we built the infra to make it native to Crux.

code: [GitHub link]. install: `pip install crux`. docs: [link].

next: distributed coordination (agents running on different machines)."

**TWEET 2: Bug Fix**

"spent 3 hours on a wild goose chase. Crux inference was getting slower every hour. memory leak, right? nope. cache eviction was triggering garbage collection during token generation. one line of code: `gc.disable()` during inference, re-enable after. 10x latency improvement. shipped."

**THREAD 3: Architectural Decision**

"why we built Crux's safety pipeline from scratch instead of using existing alignment frameworks.

here's the heresy: most safety frameworks are built for deployment. they assume: you have a frozen model, users query it, you filter outputs.

Crux is different. the model learns from corrections. every user interaction feeds back into the model's internal rules. so a static safety layer breaks immediately.

we needed:
- dynamic rule learning (from corrections)
- context-aware safety (rules change based on task)
- user-specific rules (your safety preferences aren't mine)
- verifiable reasoning (why did it block that? you need to know)

so we built a safety pipeline that:
1. generates internal rules from user corrections
2. verifies rules don't contradict each other
3. allows user overrides with auditing
4. makes reasoning transparent

result: safer AI that actually improves over time. instead of frozen constraints, living governance.

this is the real difference from Claude, Cursor, every other tool. they safety-check at the output layer. we safety-check at the learned-rule layer.

code shipping tomorrow."

**TWEET 4: Contrarian Take**

"hot take: if you're still waiting for ChatGPT's API to be cheaper, you're missing the point. local LLMs + Crux = 90% of the capability at 5% of the cost. and you own your data. why are we still queuing requests to cloud APIs in 2026?"

**TWEET 5: Question to Community**

"what's the biggest thing stopping you from using local LLMs in production? for us it was latency. solved that. what's your blocker?"

**THREAD 6: Tool-Agnostic Intelligence (NEW — use this one early and often)**

"your AI coding tool is a rental. your intelligence should be an asset.

every time you teach Cursor a pattern, that knowledge is trapped in .cursor/. switch to Claude Code? start over. try Aider? start over. your corrections, your context, your learned patterns — gone.

we built .crux/ to fix this.

.crux/ is a directory that lives in your project (and globally at ~/.crux/). it stores everything your AI learns: corrections, knowledge entries, session state, mode definitions, security audit results.

when you run `crux switch opencode` after working in Claude Code, here's what happens:
1. Crux reads .crux/sessions/state.json (what you were working on, decisions made, files touched)
2. generates OpenCode-native configs from your .crux/ knowledge
3. writes handoff context so OpenCode picks up exactly where Claude Code left off

same project. same intelligence. different tool.

we support Claude Code, OpenCode, Cursor, Aider, and Roo Code today. any tool with MCP support can connect via `crux mcp start`.

your tools are disposable. your intelligence isn't.

GitHub: [link]"

**TWEET 7: The Switching Demo (NEW)**

"just did this:
- 9am: started auth refactor in Claude Code
- 12pm: `crux switch opencode`
- 12:01pm: OpenCode knew i was mid-refactor, which files i'd touched, which JWT library i'd chosen, what was left to do

zero re-explaining. zero lost context. that's .crux/"

**Rules to follow:**
- Never sell on X. Share insights. The selling happens later.
- Always link back to GitHub, docs, and examples. Make it easy to try.
- Engage with competitor threads (Cursor, Replit, etc.) but never link Crux. Comment with genuine insight. People check your profile.
- Use threads for anything longer than a single tweet. Single tweets are for memes, questions, and quick wins.
- Retweet good discussions in your space (LLMs, open source, AI engineering). Add a quote tweet with your take.
- Hashtags: #buildinpublic #vibecoding #opensource #localllm #aitools #developertoosl. Use 3-4 per post, not more.

**Growth timeline:**
- Week 1-2: 10-50 followers (your friends, early users)
- Week 3-4: 50-200 followers (early traction on shipping threads)
- Month 2: 200-500 followers (compound effect from consistent posting)
- Month 3: 500-2K followers (if you ship something notable, maybe 5K)
- Month 6: 2K-5K followers
- Month 12: 5K-10K followers (if you hit 30K+ stars)

This is not viral growth. It's compounding. Each post reaches 10-50 new people. They follow. They see you ship next week. They share. You ship again. Repeat.

### Reddit

**Why it matters:**
Reddit is where honest technical discussions happen. Where developers ask real questions. Where spam gets destroyed. But if you show up as genuine, helpful, and not trying to sell, Reddit is incredibly valuable. r/SideProject alone gets millions of views.

**Posting frequency:**
2-4 posts per month. Not more. Reddit has finely tuned spam detection, and it penalizes self-promotion hard. The algorithm favors community members who comment on others' posts. So your real strategy is: comment on 20 posts, then share your own.

**Content format that works:**
Long-form technical posts. Not marketing. Not "check out my cool startup." Instead: "I built X because Y. Here's how it works and what I learned." The Crux mention is casual, not the point.

**Rules to follow (critical):**
- Read the subreddit's rules first. Some don't allow self-promotion at all.
- Participate in the community for at least 2 weeks before posting your own stuff. Comment on others' posts. Be helpful.
- Never post the same thing to multiple subreddits at once. It looks spammy.
- Always assume good faith. If someone asks a critical question, answer it in detail. Don't get defensive.
- Your post should be useful to people who never click your link. The value is in the explanation, not the product.

**Best Subreddits:**
- r/SideProject (2.5M members, very relevant)
- r/LocalLLaMA (1.2M members, exact audience)
- r/selfhosted (1.8M members, your users are here)
- r/opensource (800K, very receptive)
- r/programming (3.5M, high bar, but high reward)
- r/ClaudeAI (growing fast, tool-switching angle resonates hard here)
- r/cursor (users frustrated with vendor lock-in)

**Example Posts (use exactly this format):**

**POST 1: r/SideProject**

**Title:** "i built rails for AI coding tools that learns from corrections. spent 6 months on it solo. here's what i learned about AI safety."

"i got frustrated with every AI coding tool being basically a glorified autocomplete. they don't learn from feedback. you correct them, and the next time you ask a similar question, they make the same mistake.

so i built Crux: an intelligence framework for AI coding tools that learns from corrections and bakes them into the model's rules. every time you tell it to do something differently, it updates its internal understanding.

**the architecture:**
- inference happens in a custom safety layer (not OpenAI's safety filters)
- when you correct the AI, we generate a rule: "when the user says X, do Y instead"
- these rules are verified for conflicts and stored in the model's context
- next time it faces a similar situation, it applies the learned rule

**what made this hard:**
- most ML frameworks don't let you modify model behavior at runtime
- safety is usually a binary filter: approve or block. we needed ranked safety (some rules matter more than others)
- testing: how do you verify an AI system is actually learning correctly?

**results:**
- 1500+ GitHub stars in 2 months
- users reporting that Crux fixes bugs 30% of the time on second attempt (vs 5% for other tools)
- open source, MIT licensed

**what's next:**
- multi-agent coordination (agents can spawn sub-agents and coordinate)
- distributed inference (agents on different machines)
- Crux Vibe: commercial version for teams (launching soon)

happy to answer technical questions. the codebase is messy but real.

[GitHub link]
[Docs link]
[Install: pip install crux]"

**POST 2: r/LocalLLaMA**

**Title:** "Why I'm betting on local LLMs instead of cloud APIs (and how Crux makes it practical)"

"every benchmarking article i read says the same thing: GPT-4 is smarter than local models. fine. sure. but that's one dimension.

here's what cloud APIs don't tell you:
- latency: OpenAI API adds 200-500ms to every request. local is 50ms.
- cost: $0.03/1K tokens with OpenAI. local LLM on your machine is basically free.
- privacy: everything you send to OpenAI is probably logged somewhere.
- dependency: if their API is down, you're stuck. local model? always up.
- customization: you can't modify the safety rules in Claude's API. you can in local models.

here's the catch: local LLMs are a pain to work with. bad inference libraries, no safety pipeline, slow integration. that's why most people still use cloud APIs despite the downsides.

so i built Crux to make local LLMs practical. it gives you:
- fast inference (batching, caching, GPU optimization)
- safety pipeline (learn rules from corrections, no static filters)
- IDE integration (VSCode plugin, CLI, API)
- monitoring (see what the model is doing, why)

**honest comparison:**
- if you need state-of-the-art reasoning, use Claude API
- if you need something that works 90% of the time at 1% of the cost, use local + Crux
- if you need privacy and control, local + Crux is the only answer

Crux is open source. you can fork it, modify it, deploy it anywhere.

[GitHub link]
[Benchmarks link]
[Docker setup for one-click deployment]"

**POST 3: r/selfhosted**

**Title:** "Self-hosted AI coding assistant that actually learns from you (Crux)"

"i'm tired of paying $20/month for coding assistants that make the same mistakes repeatedly. so i built an intelligence layer that learns.

it runs on any machine with a GPU (or CPU, slower but works). you point it at your codebase. it learns the architecture, your coding style, your preferences. when it makes a mistake, you correct it, and it learns.

unlike other tools, Crux doesn't just predict the next token. it reasons about what you asked for, checks its reasoning against learned rules, and iterates. that's why it gets better over time.

**self-hosting benefits:**
- complete privacy (everything stays on your machine)
- no API costs (local inference is free)
- can modify behavior (learn custom rules, no restrictions)
- offline mode (works without internet)
- no rate limits

**requirements:**
- 4GB+ RAM
- GPU optional (8GB VRAM gives decent speed)
- 5 minutes to install

**community:**
- 1500+ people using it
- active Discord
- frequent releases

i'm the solo maintainer, so releases come when i ship, not on a schedule. but it's stable enough for production use. tons of people are running it locally or on servers.

[Install link]
[Documentation]
[Docker image]"

### Hacker News

**Why it matters:**
Hacker News is the hardest audience to crack, but it's the most credible. A launch on HN can bring 2000+ visitors in a day, with disproportionate weight on technical credibility. Every engineer with influence reads HN. If a post makes it to the front page, startup investors see it. Job offers come from it. Partnerships happen.

**Posting frequency:**
2-3 times per year. Not more. HN has strong rules about self-promotion, and the community hates people who spam the site with updates about their own project. You save HN posts for major milestones: first public release, 5K stars, revenue hitting a threshold, major architectural achievement.

**Best times to post:**
Tuesday, Wednesday, or Thursday, 8-9 AM EST. Submit at 8:02 AM EST and you hit the early wave of readers (usually 200K+ daily active on HN). Later in the day = lower visibility.

**Title format:**
"Show HN: [Name] – [One sentence description]"

Example: "Show HN: Crux – Rails for AI Coding Tools"

Never use hype words (revolutionary, game-changing, disrupting). Be precise. The description should be specific enough that someone unfamiliar with the space understands what it does.

**Example HN Posts:**

**POST 1: Initial Launch**

**Title:** "Show HN: Crux – Tool-Agnostic Intelligence Layer for AI Coding"

"i built Crux because i got tired of losing context every time i switched AI coding tools.

here's the problem nobody talks about: every AI coding tool traps your intelligence. you spend weeks teaching Cursor your codebase patterns. then you try Claude Code. everything you taught Cursor? gone. you start over. try Aider next? start over again. your corrections, your project context, your learned patterns — all locked in vendor-specific directories that don't talk to each other.

so i built `.crux/`.

**what .crux/ is:**

a directory structure (global `~/.crux/` + per-project `.crux/`) that stores everything your AI learns — corrections, knowledge entries, session state, mode definitions, safety rules. it's the source of truth.

**how it connects to tools:**

the Crux MCP Server is the brain. all logic lives in one place. every tool connects to it via standard MCP protocol. tools with hook support (Claude Code, OpenCode) add paper-thin shims (5-10 lines, zero logic) that forward events for correction detection and safety interception. tools without hooks (Cursor, Cline) connect via MCP alone.

adding support for a new AI tool = one line in the tool's MCP config. not a full adapter. not a sync script. one config line.

when you switch tools:
```
$ crux switch opencode    # saves session state, OpenCode connects to same MCP server
```

OpenCode picks up exactly where Claude Code left off. same knowledge. same corrections. same context. same MCP server. the session state file (`.crux/sessions/state.json`) captures what you were working on, key decisions, files touched, and pending tasks.

**what else Crux does:**

- seven-stage safety pipeline (preflight → test-spec → security-audit → second-opinion → human-approval → DRY_RUN → design-validation)
- self-improving from corrections (the AI learns from mistakes, generates knowledge entries)
- 21 specialized modes (build-py, debug, security, design-ui, infra-architect, etc.)
- TDD/BDD enforcement gate (tests written before implementation)
- recursive security audit loop (audit → fix → re-audit until convergence)
- MCP server exposes 10+ tools: knowledge lookup, session state, correction detection, safety validation, mode prompts, project context

**currently supported tools:** Claude Code, OpenCode, Cursor, Aider, Roo Code, Qwen-Agent. any MCP-compatible tool can connect.

**the philosophy:** your AI tools are disposable. your intelligence is not. `.crux/` is the `.git` for AI coding intelligence — it belongs to you, travels with your project, and works with whatever tool you choose today or tomorrow.

MIT licensed, fully open source.

happy to answer architecture questions. code is on GitHub."

**Rules to follow:**
- If you post to HN, you must be present in the comments for 24 hours. Answer every question, especially critical ones. This is non-negotiable.
- Never get defensive. If someone points out a flaw, say "good catch, here's how we might fix it."
- Don't try to game the algorithm. Don't post at the same time every time (mods notice). Don't ask people to upvote (against the rules).
- If it doesn't hit the front page (top 30), don't try again for 3 months. Reposting quickly is seen as spammy.

### Product Hunt

**Why it matters:**
Product Hunt is discovery. Thousands of people on PH are specifically looking for new tools. If you launch on a Tuesday morning, you'll get 500+ visitors in the first hour. If your product resonates, you'll land in the top 10 of the day.

PH is also credible currency in VC and tech circles. A successful PH launch is leverage in conversations with partners, investors, and high-profile users.

**When to launch:**
Launch Crux first (when it's stable, feature-complete, documented). That's maybe 1-2 months from now. Launch Crux Vibe (commercial version) 3-6 months after.

**Pre-launch (1 month before):**
- Build your PH following (comment on 5 products every day for 2 weeks, give real feedback)
- Collect testimonials from early users ("Crux cut my coding time in half")
- Record a 2-3 minute demo video
- Write a compelling tagline and description
- Design a cover image
- Prepare a launch day thread explaining the vision

**Launch day execution:**
- Post at 12:01 AM PT (Tuesday)
- Title: "Crux – Your AI Coding Intelligence, Independent of Any Tool"
- Tagline: "Open source intelligence layer for AI coding. Works with Claude Code, Cursor, OpenCode, Aider. Switch tools freely, lose nothing."
- Description: The narrative, not features. Why you built it, what makes it different.
- Be online 24 hours. Reply to every comment, answer every question.
- Pin your founder story at the top (5-10 min read, honest, personal)

**Example PH Launch Post:**

"i spent the last 6 months building Crux because i got tired of AI coding tools that don't learn.

every tool out there has the same problem: when you correct them, they forget. the next time you ask a similar question, they make the same mistake. it's like they were designed to be stateless.

so i built something different.

Crux is an intelligence framework for AI coding tools that learns from corrections. every time you tell it to do something differently, it updates its internal rules. next time it faces a similar situation, it applies what it learned.

**how it works:**

you install Crux locally (one command). it runs on your machine with any open model (Llama, Mistral, etc.). it integrates with VSCode, your terminal, your IDE.

you ask it to solve a problem. it gives a solution. if it's wrong, you explain why. Crux generates a rule: "when the user says X, do Y instead." this rule is stored and applied to future requests.

it's not magic—it's infrastructure. we made it fast (rule checking happens during token generation), safe (rules are verified for conflicts), and practical (you can override rules, see the reasoning, export them).

**what i'm proud of:**

- built in 6 months solo (no team, no funding)
- 1500+ stars, 800+ active users already
- code is real (not a demo), 10K+ lines, tested
- architecture is clean enough to fork and modify
- every component is documented

**what's next:**

- multi-agent coordination (agents can spawn and coordinate sub-agents)
- distributed inference (inference on separate hardware)
- Crux Vibe: paid version for teams (launching Q2)

i'm asking for help with one specific thing: documentation. if you use Crux, you'll find gaps in the docs. file issues, open PRs, help make it better.

[GitHub] [Docs] [Discord]"

### YouTube

**Why it matters:**
YouTube is underused by developer tool founders. There's basically no competition for "building rails for AI coding" content. You post one 5-minute video showing the feature, and it stays relevant for months. People search "how to setup local LLM" and find your tutorial. You get 50-100 views per video, which seems low, but those are engaged developers.

Plus, YouTube videos are incredibly good for SEO. A 5-minute video about "local LLM setup" can outrank 10 blog posts because Google favors video results.

**Posting frequency:**
1 video per week. Minimum. 5-8 minutes each.

**Content format:**
- Setup tutorials (install Crux, setup, first run)
- Feature walkthroughs (here's the multi-agent system, here's the safety layer, here's how rules work)
- Architecture breakdowns (why we built it this way, performance gains, tradeoffs)
- User spotlights (here's someone's cool setup, here's their workflow)
- Debugging sessions (live debugging a bug, showing how we solve problems)

No need for on-camera presence. Screen recordings + voiceover is perfect.

**Example video ideas:**

1. "Install Crux in 5 Minutes" – Just record screen, show the install command, show it working
2. "How the Safety System Works in Crux" – Show the code, explain the logic, show it learning a rule
3. "Crux vs. Cursor: Architecture Comparison" – Side-by-side comparison of how they differ
4. "Building a Multi-Agent System with Crux" – Walkthrough of the API, code examples
5. "Performance: Local LLM vs. Cloud API" – Benchmarks, cost comparison, latency

**AI handles:**
- Script outlines
- Video titles and descriptions (SEO optimized)
- Thumbnail suggestions
- Timestamps and chapters
- YouTube metadata and tags

**You handle:**
- Screen recording (10-15 min of recording, 5-8 min of editing)
- Voiceover (can use AI voice if you prefer, but human voice is better)
- Publishing and promotion

### GitHub

**Why it matters:**
GitHub IS your marketing platform. Your README is your landing page. Your releases are content. Your GitHub discussions are your community. Every developer looking at your project will spend 30 seconds reading the README. If it's good, they star, fork, and try it. If it's bad, they leave.

**Best practices:**

**README:**
- Start with a 1-sentence description
- Show an animated GIF or short demo video (people scroll past walls of text)
- Problem/solution (why you built this)
- Quick start (copy-paste installable in <1 minute)
- Feature list (5-7 highlights, not 50)
- Architecture diagram (if you can, doesn't have to be fancy)
- Contributing guide (encourage PRs)
- License, links to docs, Discord

**Releases:**
Every release is a social media post. When you ship a release:
1. Write the changelog (detailed but readable)
2. AI drafts an X thread
3. You review and post
4. Link from X to the GitHub release

This doubles the visibility of each release.

**GitHub Discussions:**
Enable them. Use them. Encourage users to post ideas, ask questions, share what they built. Respond quickly. This is your community.

**Issues:**
Tag issues with "good first issue" to attract contributors. When someone opens an issue, respond within 24 hours. Even if you don't fix it immediately, acknowledge it and explain your thinking.

**Submissions:**
Submit Crux to:
- awesome-llm
- awesome-agents
- awesome-ai-tools
- awesome-self-hosted
- awesome-open-source

Each submission gets you 10-50 new stars from people browsing these lists.

### Dev.to / Hashnode

**Why it matters:**
These platforms have built-in audiences. Write a good technical post and Dev.to's trending page shows it to thousands of developers. Hashnode is growing but smaller. Both support SEO (your own domain on Hashnode compounds SEO value over time).

**Posting frequency:**
1-2 posts per week. Same content, cross-posted to both.

**Content format:**
Long-form technical posts (1500-2500 words).

**Topics that work:**
- Tutorials ("How to Setup Local LLMs with Crux")
- Architecture deep-dives ("Why We Built a Custom Safety Pipeline Instead of Using Alignment Frameworks")
- Comparisons ("Crux vs. Cursor: Technical Architecture Breakdown")
- Retrospectives ("6 Months Building Crux Solo: What I Learned")
- Learning posts ("Why Our First Approach to Multi-Agent Coordination Failed")

**Example post structure:**

**Title:** "Why We Built Crux's Safety Pipeline From Scratch (Instead of Using Existing Frameworks)"

**Introduction:**
- Hook: "Most AI safety frameworks are built for static models and frozen rules."
- Problem: "Crux learns from corrections, so static safety breaks immediately."
- Promise: "Here's how we built a safety system that improves with usage."

**Body (organized by section):**
1. Problem explanation (why existing safety frameworks don't work for Crux)
2. Architecture overview (the safety pipeline components)
3. Technical deep-dive (how rule generation works, how conflict detection works)
4. Performance tradeoffs (speed vs. safety comprehensiveness)
5. Lessons learned (what went wrong, how we fixed it)
6. Code examples (real snippets from the codebase)

**Conclusion:**
- Recap: "This approach lets us build safety that adapts to user preferences while remaining verifiable."
- Call to action: "Try it on GitHub. Open issues for edge cases we missed."

### Discord

**Why it matters:**
Discord is where your community hangs out. It's not for promoting (no one wants to join a Discord to see ads). It's for helping users, answering questions, showing work-in-progress, and building relationship with early adopters.

**When to start:**
Only start a Discord when you have 500+ Twitter followers or 2000+ GitHub stars. Before that, use GitHub Discussions and email. A dead Discord looks worse than no Discord.

**Channels to create:**
- #announcements (release notes, major updates)
- #general (chat, off-topic okay)
- #help-and-questions (support)
- #showcase (users sharing what they built with Crux)
- #contribute (for people thinking about contributing code)
- #ideas (feature requests and discussion)
- #roadmap (your upcoming work)

**What to do:**
- Post periodic updates (here's what shipped recently, here's what's next)
- Monthly office hours (1 hour video call, any questions, no structure)
- Respond to questions within 24 hours
- Celebrate community wins (someone contributed a feature? announce it)
- Never ghost Discord. If you join, stay active.

### LinkedIn

**Why it matters:**
LinkedIn is lower priority for Crux, but it's worth 1 post per week. Especially if/when Crux Vibe (the commercial version) launches. LinkedIn is where B2B decisions happen.

**Strategy:**
Repurpose your X content to LinkedIn. Same shipping updates, architecture posts, lessons learned. LinkedIn's audience appreciates more detailed posts, so you can expand slightly.

**Posting frequency:**
1 post per week (repurpose from X or Dev.to).

**Topics:**
- Building in public (why it works, metrics, learnings)
- Solo founder challenges (burnout, prioritization, technical debt)
- Crux Vibe announcements (when available)
- Hiring (when you're ready to bring on team members)

## 4. The Continuous Cadence

You work 7 days a week, around the clock. The marketing system matches that — no day-of-week assignments, no time blocks. Here's how the different content types layer in:

**Continuous (event-driven, automatic):**
- Shipping tweets fire as you commit (~1/hour target)
- Bug fix stories, architecture decisions, tool-switching demos
- All generated by triggers, approved with one keystroke
- This is 80% of your content volume

**Periodic (manual trigger or scheduled check):**
- **Every ~50-100 commits**: Crux suggests a digest thread (8-12 tweets summarizing a chunk of work). Good for when you've been heads-down for a while and followers need a catch-up narrative.
- **Every ~week of commits**: Crux suggests a Reddit post (long-form, technical) and a blog post outline (Dev.to/Hashnode). You finalize these when you feel like writing prose.
- **Every release tag**: Changelog + thread auto-drafted.

**Human-only (when you feel like it):**
- Community engagement: comment on competitor threads, answer questions on Reddit/HN, respond to issues. Do this whenever you take a break from coding. 15-20 min bursts.
- DMs to influencers, podcast pitches, conference talk applications: batch these monthly.

**The key shift:** There's no "content creation time block." Content generation is woven into your building flow. Approve a tweet between commits. Review a thread while tests run. The overhead per post is ~5 seconds (one keystroke). The overhead per thread is ~2 minutes (quick read + approve/edit). That's it.

## 5. The Monthly Cadence

One layer above the continuous flow. These are monthly content targets — hit them whenever they fit your rhythm, not on assigned days:

**Ship & Announce (whenever a major release lands):**
- Biggest release of the month (5-10 features, or 1 major breaking change)
- X threads, Reddit posts, blog post, YouTube video
- Preparation: documentation, examples, demo

**Technical Content & Community Engagement (once per month):**
- Deep technical post (Dev.to article on architecture decision)
- Community spotlights (retweet contributors, feature users)
- GitHub discussions (start a discussion on the biggest technical decision recently)
- Discord: monthly office hours

**Competitor Analysis & Contrarian Takes (once per month):**
- Write a comparison post (Crux vs. X, Y, or Z)
- Honest assessment of where Crux is weaker
- Why certain tradeoffs make sense for your philosophy
- These posts generate discussion and build credibility (you're not pretending to be perfect)

**Retrospective & Metrics (once per month):**
- Blog post: monthly retrospective ("here's what we shipped, what went wrong, what's next")
- X thread with metrics (stars, users, revenue, etc.)
- Email update (if you have a mailing list) with same content
- Document lessons learned for the next month

**Metrics Review (once per month, ~15 min):**
- Compile: stars gained, forks, users, revenue, blog views, social followers
- Goal: identify what worked and what didn't
- Adjust next month's strategy based on what resonated

## 6. Guerrilla Tactics

The scrappy stuff that punches above its weight.

**Competitor Thread Commenting (now your highest-leverage tactic)**
- Find threads about Cursor, Replit, Copilot, Claude Code, OpenCode, Aider
- Read carefully and comment with genuine insight
- Example: If someone complains about losing context when switching tools: "Yeah, this is the fundamental problem — every tool traps your intelligence in their directory. I built something that decouples knowledge from the tool. [your profile]"
- Example: If someone asks "Cursor or Claude Code?": "Why choose? I use both on the same project. Different tools for different phases. The key is having your knowledge portable. [your profile]"
- Never link to Crux directly. People check profiles of smart commenters.
- Time: 15-20 min per day, 4-5 threads
- **NEW high-value targets:** Any thread asking "which AI coding tool should I use?" or "switching from X to Y" or "lost my Cursor rules when I tried Claude Code" — these are PERFECT for Crux's message

**Stack Overflow Authority Building**
- Search for questions about "AI agents," "local LLMs," "safety in AI," etc.
- Answer with detail, rigor, and insight
- Link to Crux in your profile, not in answers (unless directly relevant)
- Answering 3-5 questions per week builds authority and drives profile clicks
- Takes 30 min per week, high leverage

**Meme Marketing**
- 1-2 developer memes per week (takes 5 min in Figma)
- Format: screenshot of error, relatable developer joke
- Example: "When someone asks 'why don't you just use the cloud API' and your power bill is $200/month"
- Post on X with no explanation
- These get 50-200 likes, low engagement rate, but viral potential is high
- The upside: if it goes viral, thousands see your profile

**Contrarian Takes**
- 1 per week: a technical opinion that challenges the status quo
- Example: "Prompt engineering is dead. Infrastructure is everything." [thread]
- Generates discussion, makes you look like a thought leader
- Take real positions. Wishy-washy posts get no engagement.

**Open Source Contributions**
- Contribute 1 PR per month to adjacent projects (LangChain, LlamaIndex, transformers, etc.)
- Make it real. Solve an actual bug, implement a small feature, improve docs.
- Your GitHub profile links to Crux. Every PR is visibility.
- Contributes 5-10 new developers to your project per PR

**Cold DM to Influencers**
- List 5-10 dev influencers (2K-50K followers, active in AI/LLM space)
- Once per month: genuine DM. "I built Crux, thought you'd find the architecture interesting. [link]"
- Not spam. Not asking for anything. Just sharing your work.
- If they care, they'll look. If not, they'll ignore. No harm.
- Success rate: ~5% (1 out of 20 checks it out). But that 1 person might have 10K followers.

**Free Tool as Awareness Driver**
- Build a small, standalone tool that solves a real problem
- Example: "AI Code Auditor" (analyzes your code, finds anti-patterns, suggests improvements)
- NEW Example: "crux init --import" — a free CLI that reads your .cursor/rules/ or .claude/ agents, generates a .crux/ directory, and starts the Crux MCP server. Your existing AI configs become portable instantly. Any tool with MCP support can now access your knowledge.
- This is the ultimate trojan horse: developers run it once, their existing configs are unified, and every tool they use is now connected to the same intelligence layer
- Free tool, works in browser or CLI
- Footer: "Built with Crux. Learn more: [link]"
- Market the free tool, not Crux directly
- Free tools get 10x more shares than product pitches

**`crux adopt` — The Mid-Session Onboarding Story (NEW — highest-leverage onboarding tool)**
- `crux adopt` is designed for the most common real-world scenario: you're deep into a project, you discover Crux, and you want to start using it without losing everything you've already built
- Two-phase capture: (1) mechanical — parses git log for files touched, commit messages as decisions, detects tech stack, generates PROJECT.md, imports existing CLAUDE.md; (2) LLM brain dump — the current session's LLM writes its own handoff context, session state, knowledge entries, pending tasks, and discovered patterns using CLI args
- The LLM brain dump is the key insight: the LLM knows things git log doesn't — WHY decisions were made, what corrections happened, what patterns were discovered, what's still pending
- After `crux adopt`, the current session does a planned exit. Next session starts with full Crux MCP server + hooks active, seeded with rich context from the previous session
- **Marketing angle**: This is a perfect demo video and blog post — "I was 3 hours into a Claude Code session. Ran `crux adopt`. It captured everything. New session picked up exactly where I left off, but now with correction detection, safety pipeline, and knowledge accumulation running."
- **Content format**: Screen recording showing the adopt flow is the single most compelling demo you can create. Real project. Real context. Real continuity.
- This solves the cold-start problem that kills most developer tools — you don't have to start a new project to try Crux

**Conference Talks**
- Apply to PyCon, AI conferences, etc. (April-June deadlines for fall conferences)
- Topic: "Building Rails for AI Coding Tools" or "Portable Intelligence Across AI Tools"
- If accepted: 50-500 live viewers, video on YouTube (5K+ views typical), speaking credibility
- Effort: 5 hours prep, 1 hour presentation, 2 hours travel
- ROI: massive credibility, direct access to engineers in the room

**Podcast Appearances**
- List 10-15 relevant podcasts (AI engineering, developer tools, open source, indie hacking)
- Pitch 3-5 per quarter
- Format: 45-60 min conversation about building Crux, why you chose local LLMs, architecture decisions
- Each episode: 500-5000 listeners, typically 10-20% follow the link
- Recorded = evergreen content (people find it months later)

## 7. The OpenClaw Multiplier

OpenClaw is the fastest-growing open source project in history — 250K+ GitHub stars in 60 days. It's a self-hosted autonomous AI agent that runs locally on Mac Mini + Ollama. 5,400+ skills marketplace. Connects to WhatsApp, Slack, Telegram, Discord, iMessage.

This is not a side channel for Crux. This is the largest organic funnel available.

### Why OpenClaw Matters for Crux

**The Alignment is Perfect:**
- 250K+ developers already using the exact hardware and local LLM stack Crux targets
- OpenClaw's #1 problem: security (63% of deployments vulnerable, 820 malicious skills in ClawHub)
- Crux's safety pipeline is the EXACT solution to OpenClaw's biggest weakness
- Crux skills published to ClawHub marketplace = free distribution to 250K+ users
- The OpenClaw community already runs Mac Mini + Ollama = natural Crux Vibe premium tier customers

This is the fastest way to reach your target audience at scale.

### Strategy: "Fix OpenClaw's Security Crisis"

Crux becomes the trusted security layer for the entire OpenClaw ecosystem. Not through marketing. Through solving their biggest problem.

**Execution (Month 1):**

1. **Publish Free Crux Safety Pipeline as OpenClaw Skill**
   - Create `crux-safety` skill on ClawHub
   - Includes token validation, jailbreak detection, output filtering
   - Free, open source, fully audited
   - Documentation: how to install, how to use, how it works

2. **Write Blog Post: "How We Made OpenClaw 10x Safer"**
   - Post to Dev.to, Hashnode, cross-post to Medium
   - Case study: analyzed 820 malicious skills, showed common attack vectors
   - Demonstrate how Crux's safety layer prevents each one
   - Include benchmarks: before/after safety analysis
   - Call to action: install crux-safety skill

3. **Show HN: "Crux — Safety Pipeline for OpenClaw Agents"**
   - Target security angle (this is what HN cares about)
   - "250K OpenClaw users, 63% vulnerable. Here's how I fixed mine."
   - Expect 5K-20K upvotes, 200+ comments, 10K+ views
   - Drives 500-2000 new users directly to Crux

4. **X Thread: "OpenClaw has 250K stars but 63% are vulnerable"**
   - Show real statistics from ClawHub security audit
   - Thread: "Here's how I secured mine. 8-tweet technical breakdown."
   - Tailor for OpenClaw community (tag @OpenClaw, tag @SkillDevs)
   - High engagement from security-conscious developers

5. **Contribute Security Fixes to OpenClaw Core**
   - Find 2-3 real security bugs in OpenClaw itself
   - Submit PRs with detailed security analysis
   - Build credibility as someone who understands their codebase
   - Every PR = visibility in OpenClaw's GitHub activity

6. **Offer Free Security Audits of Popular ClawHub Skills**
   - Pick 5 of the most-downloaded skills
   - Audit for common vulnerabilities (prompt injection, jailbreaks, token stealing)
   - Publish audit findings (name the skill, describe vulnerabilities, suggest fixes)
   - Offer authors: "Here's how Crux's safety layer would prevent this"
   - Builds goodwill + awareness

7. **Engage Authentically in OpenClaw Community**
   - GitHub Discussions: answer security questions with depth and insight
   - ClawHub Discord: comment on skill releases, offer security feedback
   - Reddit r/OpenClaw: participate in discussions, share expertise
   - 30 min/day, genuine helpfulness, never self-promotional
   - When people ask about security, Crux is the obvious answer

8. **Propose "Crux-Audited" Badge for ClawHub**
   - Work with OpenClaw foundation to create a security badge
   - Skills that pass Crux audit get the badge
   - Skill developers want the badge = incentive to use Crux
   - Crux becomes essential to ClawHub's ecosystem

**Content Calendar (Month 1-3):**

- Week 1 (of OpenClaw integration): Publish crux-safety skill to ClawHub + announcement thread on X
- Week 2: "Making OpenClaw Safe" blog post on Dev.to + Hashnode + Medium
- Week 3: Show HN post about Crux for OpenClaw
- Week 4: Reddit r/LocalLLaMA post about Mac Mini + OpenClaw + Crux stack
- Month 2, Week 1: Publish first security audit of popular ClawHub skills
- Month 2, Week 3: Contribute security PR to OpenClaw core
- Month 3: Monthly audit report of top 5 ClawHub skills, security trends, Crux improvements

**Metrics to Track:**

- ClawHub skill installs: target 1,000 in Month 1, 10,000 by Month 3
- OpenClaw GitHub mentions of Crux (track via GitHub search)
- r/LocalLLaMA post engagement (upvotes, comments, profile clicks)
- r/OpenClaw community growth from security discussions
- Conversion: OpenClaw user → Crux GitHub star
- Conversion: Crux user → Crux Vibe subscriber (the revenue goal)

**Revenue Path:**

- Free Crux skills on ClawHub → 250K potential users discover Crux
- Users love the safety features + elegant design → want more
- Users want managed experience → Crux Vibe subscription (Mac Mini preset, automatic updates, support)
- Crux Vibe Mac Mini ($125-349/month) = 1-2% conversion from 250K users = 2,500-5,000 potential revenue targets
- Conservative estimate: 50-100 Crux Vibe subscribers from OpenClaw community alone = $6K-35K MRR

OpenClaw community is not a marketing channel. It's your primary distribution mechanism.

### Update: Guerrilla Tactics Now Include "OpenClaw Security Angel"

In addition to the existing guerrilla tactics, add:

**OpenClaw Security Angel**
- Publish free security audits of popular ClawHub skills (1-2 per week)
- Comment on OpenClaw security CVE threads with concrete solutions: "Here's how Crux prevents this vulnerability"
- Create `awesome-openclaw-security` GitHub list (curated resources, tools, best practices)
- Feature Crux security patterns in the list
- Offer to help OpenClaw foundation with security infrastructure
- Position Crux as the trusted security layer for the entire OpenClaw ecosystem
- Time: 1-2 hours per week, extremely high leverage in the community

## 8. The Tool-Agnostic Multiplier

The `.crux/` architecture creates an entirely new content category and community engagement angle that compounds with everything else in this plan.

### Why This Is Your Biggest Marketing Asset

Every developer using AI coding tools right now faces the same frustration: vendor lock-in of their intelligence. They've built up context in one tool, and switching means starting over. This is a universal pain point across every AI coding community — Cursor users, Claude Code users, Copilot users, Aider users, Roo Code users. That's millions of developers who all share the same problem.

Crux is the only solution. Not "one of several solutions." The only one. Nobody else has built a tool-agnostic intelligence layer with portable state, cross-tool knowledge, and seamless switching. This is a blue ocean for content.

### Content Opportunities Unique to Tool-Agnostic Positioning

**The "Which Tool?" Posts (infinite content supply)**

Every week, someone posts "Cursor vs Claude Code?" or "Should I switch from Copilot to Aider?" or "Best AI coding tool in 2026?" These threads get hundreds of comments and thousands of views. Your answer is always: "Use both. Here's how."

This is content that ONLY you can create. Nobody else has the infrastructure to make tool-switching seamless. Every one of these posts is a distribution opportunity.

**The "Switching Story" Series (weekly recurring content)**

Document your own real tool-switching workflows. Every time you use `crux switch`, that's a story:
- "Started debugging in Claude Code, switched to OpenCode for the refactor. Here's what the handoff looked like."
- "Used Cursor for the UI work, switched to Claude Code for the backend. .crux/ carried the design decisions."
- "Tested Aider for the first time on an existing project. Added one line to Aider's MCP config. It connected to the same Crux server. Knew my entire project context in seconds."

These are authentic, unique, and impossible for anyone else to replicate.

**The Tool-Specific Community Infiltration**

Each AI tool has its own community. Cursor has a subreddit and Discord. Claude Code has r/ClaudeAI and the Anthropic Discord. Aider has a GitHub community. OpenCode has its own channels. You can engage in ALL of them authentically, because Crux works with all of them. You're not a competitor in any of these communities — you're an enhancement.

This means:
- r/cursor: "here's how i use Cursor rules with Crux's safety pipeline"
- r/ClaudeAI: "i carry my Claude Code project knowledge to OpenCode and back using .crux/"
- Aider GitHub Discussions: "here's how Crux modes map to Aider's conventions"
- OpenCode Discord: "using Crux MCP server with OpenCode for cross-project knowledge"
- Qwen-Agent community: "Crux MCP server works with Qwen-Agent out of the box — one config line, full intelligence layer"

You're welcome in every community because you help every community.

**The "Freedom" Narrative**

Developers hate lock-in. It's in the DNA. Open source exists because of it. Linux exists because of it. Git exists because of it. Crux taps into this same instinct: your intelligence should be free. Not trapped in `.cursor/` or `.claude/` or any vendor directory. Free, portable, yours.

This narrative resonates on HN (where freedom is religion), on r/selfhosted (where sovereignty is the whole point), on r/opensource (where vendor independence is assumed), and on r/LocalLLaMA (where running your own models is the entire philosophy).

**MCP Server as the Universal Brain (this is now the core architecture, not an add-on)**

The Crux MCP Server IS the product. All logic lives in one place. Every tool connects to it. This is the simplest possible architecture: one server, one protocol, every tool.

For tools with hook support (Claude Code, OpenCode), paper-thin shims (5-10 lines, zero logic) forward events to the MCP server for correction detection and safety interception. For tools without hooks (Cursor, Cline, Roo Code), MCP alone provides knowledge, session state, modes, safety validation, and digests.

**Adding support for a new AI tool = one config line.** Not a full adapter. Not a sync script. One line in the tool's MCP config pointing to the Crux server. This is the marketing nuclear weapon:

- Publish "Crux MCP server" in MCP directories and registries
- Write "Add Crux intelligence to [tool name] in 30 seconds" tutorials — one tutorial per tool, each targeting that tool's community
- The server exposes 10+ tools: `crux_lookup_knowledge`, `crux_get_session_state`, `crux_update_session`, `crux_detect_correction`, `crux_validate_script`, `crux_get_mode_prompt`, `crux_get_digest`, `crux_write_handoff`, `crux_promote_knowledge`, `crux_get_project_context`
- Each integration tutorial is content that targets a new tool's audience
- As MCP adoption grows, Crux's addressable market grows automatically — zero additional development needed

### The Qwen-Agent Opportunity (14K stars, MCP-native, Alibaba-backed)

Qwen-Agent is Alibaba's open-source framework for building AI agent apps on Qwen models (Qwen 3.0+). 14K GitHub stars, 1.3K forks, active development. It matters for Crux for three reasons:

**1. MCP-native = instant Crux integration.** Qwen-Agent already speaks MCP. That means connecting it to the Crux MCP server is literally one config line. No adapter needed. This is the "rails for AI" thesis working in real time — any tool that speaks the protocol gets the full Crux brain.

**2. Different community, same pain point.** Qwen-Agent's community is developer-oriented, heavily international (China + global). These developers also use Claude Code, Cursor, or Copilot for other work. Their intelligence is fragmented across tools. Crux bridges that gap. The messaging: "build your Qwen-Agent apps with full context from your Claude Code sessions — .crux/ carries it."

**3. The contrast with OpenClaw is content gold.** Qwen-Agent = structured developer framework (14K stars, enterprise/research). OpenClaw = consumer personal assistant (200K+ stars, viral growth). Both are agent frameworks. Both need Crux. But for completely different reasons:
- Qwen-Agent devs need Crux because they work across multiple tools and want portable intelligence
- OpenClaw users need Crux because their agent ecosystem has security problems Crux solves
- The comparison blog post writes itself: "Qwen-Agent vs OpenClaw — two agent frameworks, one intelligence layer"

**Content plays:**
- "add Crux intelligence to Qwen-Agent in 30 seconds" tutorial (targets Qwen dev community)
- Blog post: "Qwen-Agent, OpenClaw, and the case for portable AI intelligence" (positions Crux above both)
- r/LocalLLaMA post about Qwen models + Crux (Qwen is popular in the local LLM community)
- GitHub Discussion in Qwen-Agent repo offering MCP integration help

**Add to the "works with" list:** Claude Code, OpenCode, Cursor, Aider, Roo Code, **Qwen-Agent**. Six tools. One `.crux/` directory. One MCP server. That's the pitch.

### Updated Example Posts for Tool-Agnostic Angle

**Reddit r/SideProject (NEW post):**

**Title:** "I built the .git for AI coding intelligence — your corrections and knowledge travel with you across tools"

"every AI coding tool creates its own knowledge silo. i've been building with Claude Code, OpenCode, and Cursor on the same projects, and i was constantly re-explaining context when switching between them.

so i built Crux, which puts all AI intelligence in a `.crux/` directory that any tool can read. when you switch tools, `crux switch <tool>` generates the right configs and injects your session state. the new tool picks up exactly where the old one left off.

it also has a seven-stage safety pipeline, 21 specialized modes, TDD enforcement, recursive security audits, and self-improving knowledge from corrections. but the killer feature is portability. your intelligence is yours.

works with Claude Code, OpenCode, Cursor, Aider, Roo Code. any MCP-compatible tool can connect.

open source, MIT licensed. [GitHub link]"

**Reddit r/LocalLLaMA (NEW post):**

**Title:** "Using .crux/ to carry local LLM intelligence between OpenCode, Aider, and Claude Code on the same project"

"for those running local models with Ollama — i built Crux to make your local LLM intelligence portable across tools. whether you're using OpenCode with a local model or Claude Code with Anthropic's API, your project knowledge, corrections, and session state live in `.crux/` and transfer seamlessly.

the session state file tracks what you were working on, decisions made, files touched, and pending tasks. when you switch tools, that context comes with you. no re-teaching the model your codebase. no lost corrections.

also includes: safety pipeline, TDD gates, security auditing, 21 modes. but the portability is what sold me on building this — i was tired of re-explaining my own project to AI every time i tried a different tool.

open source. [GitHub link]"

## 9. Updated Continuous Cadence

All content generation is event-driven and continuous — no day-of-week assignments. You work 7 days a week, around the clock. The system matches that.

**Continuous (automatic, trigger-driven):**
- Shipping tweets fire as you commit (~1/hour while active)
- Architecture decisions, bug fixes, tool-switching demos — all auto-drafted
- Approved with one keystroke, queued to Typefully

**Periodic (batched when material accumulates):**
- Every ~50-100 commits: digest thread + Reddit post + blog post outline
- Every release tag: changelog thread auto-drafted
- Community engagement: comment on competitor threads, answer questions on Reddit/HN — do this in short bursts whenever you take a break from coding

**Monthly:**
- OpenClaw community content (skill audit, tutorial, stack comparison)
- Metrics review + strategy adjustment
- Influencer DMs, podcast pitches, conference talk applications

## 10. Updated Monthly Cadence

No week-by-week assignments — you ship continuously. Instead, these are monthly content targets to hit whenever they fit your flow:

**Monthly content targets:**
- 1 OpenClaw community piece (security audit of ClawHub skill, tutorial, or comparison post)
- 1 "switching story" blog post (real workflow, real tools, real handoff)
- 1 metrics review + strategy adjustment (compile stars, followers, engagement — identify what worked)
- 1 deep technical post (Dev.to/Hashnode architecture deep-dive)
- Post to whichever tool community is most active that month

**Monthly ops (batch when convenient):**
- ClawHub skill maintenance
- Content retrospective (which posts drove GitHub stars?)
- Influencer outreach, podcast pitches

## 11. Updated Metrics Dashboard

Add OpenClaw-specific tracking to your metrics:

**New OpenClaw Metrics:**
- ClawHub skill installs (monthly, target: 1K Month 1 → 10K Month 3)
- ClawHub skill rating/reviews
- OpenClaw GitHub mentions of Crux
- OpenClaw Discord messages mentioning Crux
- r/OpenClaw engagement (upvotes, comments)
- r/LocalLLaMA Crux + OpenClaw post performance
- OpenClaw user → Crux repo click-through rate
- OpenClaw user → Crux Vibe conversion rate

**New Tool-Agnostic Metrics:**
- `crux switch` usage (which tool pairs are most common?)
- MCP server connections (which tools are connecting?)
- Tool-community thread engagement (r/cursor, r/ClaudeAI, etc.)
- "Switching story" blog post views and GitHub referrals
- Adapter downloads/usage (claude-code, opencode, cursor, aider, roo-code)
- Knowledge portability stories shared by users

Add to your monthly review:
- Which ClawHub skills are most popular? (audit opportunities)
- What are OpenClaw developers asking about security?
- Which Crux safety features are most valued?
- How many users discovered Crux via OpenClaw?
- What's the conversion rate from Crux user → Crux Vibe subscriber?
- Which tool-community engagement drove the most new users?
- What's the most common tool-switching pair? (informs content priorities)

## 12. Updated Growth Timeline

With OpenClaw integration, your growth projections shift dramatically:

**Month 1 (March):**
- X followers: 100 → potentially 300 (OpenClaw community boost)
- GitHub stars: 500 → potentially 1.5K (ClawHub distribution, Show HN impact)
- Active users: 50 → potentially 200 (OpenClaw user funnel)
- ClawHub skill installs: 1K
- First security audit published

**Month 2 (April):**
- X followers: 300 → potentially 1K (compounding OpenClaw engagement)
- GitHub stars: 1.5K → potentially 5K (multiple security audits, blog posts)
- Active users: 200 → potentially 1K (growing funnel)
- ClawHub skill installs: 5K
- 3-4 security audits published

**Month 3 (May):**
- X followers: 500 → potentially 2K (OpenClaw credibility)
- GitHub stars: 3K → potentially 10K-15K (compounding network effect)
- Active users: 500 → potentially 2.5K
- ClawHub skill installs: 10K
- Crux Vibe: first 10-50 subscribers from OpenClaw community

**Month 6 (August):**
- X followers: 2K → potentially 5-8K
- GitHub stars: 8K → potentially 20K-30K (OpenClaw multiplier effect)
- Active users: 1.5K → potentially 5-8K
- ClawHub skill installs: 25K+
- Crux Vibe: 50-150 subscribers = $6K-52K MRR

**Month 12 (March 2027):**
- X followers: 5-10K → potentially 10-20K
- GitHub stars: 20-40K → potentially 50-80K (OpenClaw + other channels)
- Active users: 3-5K → potentially 8-15K
- ClawHub skill installs: 50K+
- Crux Vibe: 300-500 subscribers = $37K-175K MRR
- Speaking at conference (OpenClaw security track?)
- Multiple podcasts (AI agents, security, local LLMs)

**The OpenClaw effect:**
- OpenClaw community could 3-5x all growth projections
- Largest single lever: ClawHub distribution + community network effect
- Revenue path becomes clear: 250K potential users, 0.1-1% conversion = $6K-175K MRR upside

**The Tool-Agnostic effect (NEW — potentially larger than OpenClaw):**
- Every AI coding tool community is a distribution channel (Cursor, Claude Code, OpenCode, Aider, Roo Code, Copilot, Cline)
- Combined addressable community: millions of developers across all tools
- Crux is welcome in EVERY community because it enhances, doesn't compete
- "Which tool should I use?" threads generate permanent SEO-indexed content
- Tool-switching pain is universal — every developer who's tried 2+ tools has felt it
- The MCP server creates a long tail of integrations that compound over time
- Each new tool Crux supports adds another community to the distribution network

## 13. Full Metrics Dashboard Reference

Track these weekly:

**Social Media:**
- X: followers, weekly impressions, engagement rate, click-throughs to GitHub
- Reddit: upvotes on posts, comments, karma earned
- GitHub: stars (daily count), forks, new contributors, open issues trend
- Dev.to: total followers, post views, engagement

**Product:**
- GitHub stars (cumulative)
- Forks
- Open issues
- Pull requests (from community)
- Monthly active users (track via Discord, downloads, or telemetry if you have it)
- Revenue (Crux Vibe, when available)

**Content:**
- Blog posts: total views, average time on page, referrals to GitHub
- YouTube: total subscribers, views per video, click-throughs to GitHub
- Email subscribers (if you start a list)

**Business:**
- MRR (monthly recurring revenue from Crux Vibe)
- Paying customers
- Churn rate

**Periodic Review (every ~7 days, 15 min whenever it fits):**
- Record all metrics in a simple spreadsheet
- Identify patterns (what content type drove the most GitHub stars?)
- Adjust strategy based on what worked

**Growth Timeline (realistic)**

Month 1 (March):
- 100 X followers
- 500 GitHub stars
- 50 active users
- Stable product

Month 2 (April):
- 300 X followers
- 1500 GitHub stars
- 200 active users
- First 5K upvotes on HN post

Month 3 (May):
- 500 X followers
- 3K GitHub stars
- 500 active users
- Product Hunt launch (top 10 for the day)
- First blog post with 1K views

Month 6 (August):
- 2K X followers
- 8K GitHub stars
- 1.5K active users
- $500-2K MRR (if Crux Vibe launches)

Month 12 (March 2027):
- 5-10K X followers
- 20K-40K GitHub stars
- 3K-5K active users
- $5K-20K MRR
- Speaking at a conference
- Multiple podcasts

This assumes consistent execution (4-6 hours/week on content creation, handled by AI) and shipping every week.

## 14. Crux Marketing Mode (Live Infrastructure)

Crux marketing mode is live infrastructure, not a proposal. The Typefully API integration is tested and working. The workflow runs inside your Claude Code session — generate, review, approve, queue. No context-switching.

**The Command (manual trigger):**
```
crux marketing [--platform x|reddit|blog|all] [--force]
```

Most of the time you don't run this manually — Crux triggers automatically based on events. `--force` bypasses the cooldown gate.

**End-to-End Workflow (continuous, event-driven):**

```
┌─────────────────────────────────────────────────────────────┐
│              crux marketing (continuous)                     │
│                                                             │
│  TRIGGERS (any of these fire the pipeline):                 │
│     ├── 3-5 commits since last post                        │
│     ├── ~50K tokens or ~30 tool calls since last post      │
│     ├── high-signal event (tests green, new tool, tag,     │
│     │   merge, crux switch, correction, knowledge)         │
│     ├── manual: `crux marketing`                           │
│     └── cooldown check: last post >15 min ago?             │
│                                                             │
│  1. GATHER (since last post, not since "today")             │
│     ├── git log (commits since last marketing post)         │
│     ├── .crux/sessions/ (modes, tool switches, context)     │
│     ├── .crux/corrections/ (new correction stories)         │
│     ├── .crux/knowledge/ (newly promoted entries)           │
│     └── .crux/marketing/history.json (avoid repeats)        │
│                                                             │
│  2. GENERATE → 1 draft (matching continuous rhythm)         │
│     └── .crux/marketing/drafts/[timestamp].md               │
│                                                             │
│  3. REVIEW (inline, one keystroke)                          │
│     ┌──────────────────────────────────────────────┐        │
│     │ DRAFT: tweet (247 chars)                     │        │
│     │                                              │        │
│     │ just shipped `crux adopt` — two-phase        │        │
│     │ mid-session onboarding. start using crux     │        │
│     │ on an existing project without losing         │        │
│     │ context. phase 1: mechanical capture.         │        │
│     │ phase 2: brain dump. #buildinpublic           │        │
│     │                                              │        │
│     │ [a]pprove  [e]dit  [s]kip                    │        │
│     └──────────────────────────────────────────────┘        │
│                                                             │
│  4. QUEUE (automatic on approve)                            │
│     └── POST to Typefully API                              │
│         publish_at = max(now+5min, last_post+15min)        │
│                                                             │
│  5. CONFIRM (one line, back to work)                        │
│     "queued: crux adopt tweet → 7:42 PM"                   │
│                                                             │
│  Target: ~1 post/hour. Floor: 15 min between posts.        │
│  You never stop building. Posts drip alongside your work.   │
└─────────────────────────────────────────────────────────────┘
```

**What Gets Generated (by trigger type):**

**Commit-triggered (most common):**
- shipping updates — what just landed, why it matters
- bug fix stories — the hunt, the fix, the result
- architecture decisions — why X over Y

**High-signal event triggered:**
- test suite green after red — debugging story
- new MCP tool created — capability expansion story
- `crux switch` or `crux adopt` — tool-switching demo content
- knowledge promoted — architecture/learning story
- correction detected — "the AI learned something" story

**Manually triggered (threads, longer content):**
- architecture deep-dive threads (6-10 tweets)
- weekly digest threads (when you feel like reflecting)
- comparison posts, contrarian takes

**Milestone-triggered (automatic detection):**
- star count milestones (100, 500, 1K, 5K): celebration + retrospective
- first external contributor: thank-you post + spotlight
- each release tag: changelog + feature highlights
- tool switch count milestones: "crux switch has been run N times" stories

**Draft File Format:**

```markdown
---
type: thread
platform: x
suggested_time: 2026-03-06T12:00:00-05:00
hashtags: [buildinpublic, opensource, aitools]
sources: [git:abc123, correction:2026-03-05-001, knowledge:mcp-architecture]
char_count: [247, 280, 195, 260, 198, 245]
---

[1/6]
today i started building Crux — a self-improving intelligence framework for AI coding tools.

Not another AI wrapper. Not another coding assistant.

rails that make every AI coding tool smarter, and get smarter themselves every time you use them.

[2/6]
The core idea: a ~/.crux/ directory that stores everything your AI learns...
```

**Repeat-Prevention:**

Crux tracks what's been posted in `.crux/marketing/history.json` — keyed by source (commit hash, correction ID, knowledge entry). If you already posted about commit `abc123`, it won't generate another post about it tomorrow. This prevents the "same shipping update three days in a row" problem.

**Typefully API Reference (tested, live):**

```
Base URL:     https://api.typefully.com/v2
Social Set:   288244 (@splntrb)
Auth:         Bearer token in .crux/marketing/typefully.key (gitignored)

POST   /social-sets/{id}/drafts          Create + optionally schedule
PATCH  /social-sets/{id}/drafts/{did}    Update or schedule existing draft
GET    /social-sets/{id}/drafts          List all drafts (filter by status)
DELETE /social-sets/{id}/drafts/{did}    Delete a draft

Scheduling: set "publish_at" (ISO 8601 UTC) to schedule
Threads:    multiple objects in platforms.x.posts[]
Platforms:  x, linkedin, threads, bluesky, mastodon (x only for now)
```

**Config: `.crux/marketing/config.json` (gitignored)**
```json
{
  "typefully": {
    "social_set_id": 288244,
    "api_key_path": ".crux/marketing/typefully.key",
    "account": "@splntrb",
    "plan": "creator"
  },
  "triggers": {
    "commit_threshold": 4,
    "token_threshold": 50000,
    "interaction_threshold": 30,
    "high_signal_events": ["test_green", "new_mcp_tool", "git_tag", "pr_merge", "crux_switch", "crux_adopt", "knowledge_promoted", "correction_detected"],
    "cooldown_minutes": 15,
    "target_posts_per_hour": 1,
    "quiet_hours": null
  },
  "voice": {
    "style": "all lowercase except proper nouns",
    "tone": "technical, direct, no hype, builder energy",
    "never": ["Revolutionary", "Game-changing", "Excited to announce", "I'm thrilled"],
    "examples_path": ".crux/marketing/voice-samples.md"
  },
  "defaults": {
    "platforms": ["x"],
    "schedule_mode": "now"
  },
  "state_path": ".crux/marketing/state.json",
  "history_path": ".crux/marketing/history.json"
}
```

**State: `.crux/marketing/state.json` (tracks continuous rhythm)**
```json
{
  "last_queued_at": "2026-03-06T00:35:00Z",
  "last_queued_id": 8281849,
  "commits_since_last_post": 0,
  "tokens_since_last_post": 0,
  "interactions_since_last_post": 0,
  "posts_today": 3,
  "posts_this_hour": 1
}
```

**Implementation in Crux MCP:**

The marketing mode is one MCP tool (`crux_marketing_generate`) plus a mode definition in `.crux/modes/marketing.md` plus event hooks that increment counters and check trigger thresholds. The mode tells the LLM how to read sources, generate posts in the right voice (all lowercase except proper nouns, technical, direct), and present the inline review. The MCP tool handles Typefully API calls (create draft, schedule, list) and state management (cooldown tracking, history dedup).

The event hooks are lightweight: PostToolUse increments `interactions_since_last_post`, commit detection increments `commits_since_last_post`, and each checks against thresholds. When a threshold is met and cooldown has elapsed, the hook triggers draft generation.

This means marketing mode works from any tool that speaks MCP — Claude Code, OpenCode, etc. And because the marketing infrastructure lives in `.crux/`, if you switch coding tools, your marketing state, drafts, history, and config travel with you.

## 15. Budget (Nearly Zero)

**What you pay:**
- Claude Code Pro Max: $200/month (already paying, not marginal)
- Typefully Creator: $12.50/month (unlimited posts, full API access — required for automated pipeline)
- runcrux.io domain: ~$30/year
- cruxvibe.io domain: ~$30/year
- Server: already have (not marginal)
- **New marginal cost: ~$17.50/month** ($12.50 Typefully + ~$5 domains amortized)

**What you don't pay for:**
- 11ty (free, open source)
- OBS Studio (free, open source)
- Dev.to (free)
- Discord (free)
- GitHub (free for open source)
- All social accounts (free)
- Email (use Gmail)
- Plausible/GoatCounter (free self-hosted, or ~$9/month hosted)

**Why Typefully Creator is worth it:** The free tier caps at 3 scheduled posts and blocks API publishing. Creator unlocks unlimited scheduling and full API access, which is what powers the `crux marketing` → Typefully pipeline. Without it, you'd have to manually copy-paste every post into X. With it, approved posts queue automatically from your terminal. $12.50/month to automate your entire posting infrastructure is the best ROI in this whole plan.

**Reality:** You can run this entire operation for ~$218/month (Claude + Typefully + domains), and Claude is a cost you already pay for building. The website hosting is free since you have a server.

## 16. Risk Mitigation

**Burnout Risk**
- *Problem:* Even with AI handling 80% of content creation, you could burn out doing marketing + building.
- *Solution:* Marketing is not optional, it's part of your job now. But it's woven into your build flow — one-keystroke approvals between commits, not a separate time block. The overhead is ~5 seconds per post.
- *Reality check:* Because the pipeline is event-driven and inline, the actual time cost is near zero. The AI drafts. You approve or skip. That's it.

**Consistency Risk**
- *Problem:* Some weeks you'll ship nothing. Some weeks you'll build infrastructure nobody sees. Posts will be irregular.
- *Solution:* The automated pipeline means posts still happen even if it's boring infrastructure work. Boring infrastructure is the best content anyway. It shows you're serious.
- *Reality:* Your inconsistency becomes your brand. Some weeks are explosive shipping, some weeks are deep refactoring. That's real.

**Quality Risk**
- *Problem:* AI-generated posts could sound robotic or miss the mark.
- *Solution:* You review everything. No auto-publish. Your voice is the filter.
- *Implementation:* Review inline as drafts appear — one keystroke to approve, edit, or skip. No batched review session needed.

**Platform Risk**
- *Problem:* If X dies, or Reddit kills your account, you lose leverage.
- *Solution:* Multi-platform strategy. YouTube, Dev.to, Hashnode, Discord, GitHub. Never be dependent on one platform.
- *Reality:* Even if X collapses, you'll have 2K followers on Hashnode, 5 YouTube videos, 50 blog posts across platforms. That compounds.

**Spam Perception Risk**
- *Problem:* Posting ~1/hour while working could feel spammy.
- *Solution:* Mix content types. Mix platforms. Mix authentic engagement. Never auto-engage (replies, RTs, follows). Always human review.
- *Implementation:* 40% shipping updates, 30% technical deep-dives, 20% community engagement, 10% fun stuff (memes, contrarian takes). The cooldown gate (15 min floor) prevents bursts.

**Audience Burnout Risk**
- *Problem:* Even good content feels annoying if it's the same person, every day.
- *Solution:* Don't just market. Build community. Celebrate others. Spotlight contributors. Make Discord a place people want to be.
- *Reality:* If you're the only voice in the room, it feels like marketing. If you're hosting a conversation, it feels like community.

---

## Execution (Already Started)

**Day 1 (March 5, 2026) — DONE:**
1. ~~Create Typefully account~~ — Done. @splntrb connected, Creator plan active.
2. ~~Create Typefully API key~~ — Done. "Crux Marketing" key, stored for API access.
3. ~~Post first content~~ — Done. 3 posts published/scheduled:
   - 7:15 PM: Day 1 hook tweet (published)
   - 7:35 PM: 6-tweet architecture deep-dive thread (scheduled)
   - 8:00 PM: Shipping update with Day 1 metrics (scheduled)
4. ~~Validate Typefully API integration~~ — Done. POST, PATCH, GET all tested and working.

**This week (remaining):**
1. Register runcrux.io and cruxvibe.io domains
2. Create `.crux/marketing/` directory structure in the Crux repo
3. Store Typefully API key in `.crux/marketing/typefully.key` (gitignored)
4. Create `.crux/marketing/config.json` with social set ID, website config, and defaults
5. Scaffold 11ty project in `site/` directory
6. Build runcrux.io landing page (hero + architecture diagram + tool logos)
7. Write first 3 blog posts from Day 1 work
8. Deploy to server, verify SSL, update Typefully bio to link runcrux.io
9. Implement `crux_marketing_generate` MCP tool (reads sources, generates tweet + blog post)
10. Wire Typefully API calls + blog post generation + deploy into the MCP tool
11. Don't aim for perfect. Aim for shipped.

**Next week:**
1. Wire the full pipeline: one keystroke = tweet queued + blog post published + site deployed
2. Add RSS feed to runcrux.io
3. Add changelog page (auto-populated from git tags)
4. Submit to Google Search Console
5. Add Reddit + Dev.to to the rotation
6. Engage on Reddit for 30 min (comment on others' posts, build goodwill)

**Month 2:**
1. Add docs section to runcrux.io (migrate from GitHub README)
2. Add per-tool pages (/docs/claude-code, /docs/cursor, etc.)
3. Set up Plausible or GoatCounter for privacy-respecting analytics
4. Plan your Product Hunt launch
5. Start YouTube (periodic 5-min videos)
6. Solidify the continuous cadence

**Month 3:**
1. Product Hunt launch
2. Second HN "Show HN" post
3. cruxvibe.io landing page (when commercial product is ready)
4. First conference talk application
5. Monthly metrics review

---

## 17. The Website: runcrux.io (11ty Static Site + Build-in-Public Blog)

**Domains:**
- **runcrux.io** — open-source Crux project site, blog, docs, build-in-public log
- **cruxvibe.io** — commercial Crux Vibe product (later, when ready)

**Why 11ty:** Fast, zero-JS by default, markdown-native, Git-friendly. Every blog post is a markdown file committed to the repo. Deploys are a `git push`. No database. No CMS. No moving parts to break. Perfect for a solo developer who writes in a terminal.

### Site Architecture

```
runcrux.io/
├── /                        # Landing page: hero, one-liner, architecture diagram, CTA
├── /blog/                   # Build-in-public blog index (reverse chronological)
│   ├── /blog/day-1-crux/    # Auto-generated from first day's work
│   ├── /blog/mcp-architecture/
│   └── ...
├── /docs/                   # Technical docs (can start as links to GitHub wiki/README)
├── /changelog/              # Auto-generated from git tags/releases
├── /about/                  # Solo founder story, philosophy, .crux/ explained
└── /feed.xml                # RSS feed (11ty plugin)
```

### 11ty Project Structure

```
site/
├── .eleventy.js             # Config: markdown, collections, filters
├── package.json
├── src/
│   ├── _data/               # Global data (site metadata, navigation)
│   ├── _includes/
│   │   ├── base.njk         # Base HTML layout
│   │   ├── post.njk         # Blog post layout
│   │   └── components/      # Header, footer, nav, post-card
│   ├── index.njk            # Landing page
│   ├── about.md
│   ├── blog/
│   │   └── *.md             # Each post is a markdown file with frontmatter
│   ├── changelog/
│   │   └── index.njk        # Pulls from _data/releases.json or git tags
│   ├── docs/
│   │   └── index.md
│   └── css/
│       └── style.css        # Minimal, hand-written CSS. No Tailwind. No framework.
├── _site/                   # Build output (gitignored)
└── deploy.sh                # rsync to your server or git push to trigger deploy
```

### The Pipeline: Code → Post → Tweet → Blog

This is the key integration. When the marketing trigger fires and you approve a post, **two things happen simultaneously:**

```
You're building. Trigger fires. Draft appears.

     [a]pprove

     → Typefully API: queue the tweet/thread (existing flow)
     → ALSO: generate expanded blog post from the same source material
     → Blog post is a markdown file written to site/src/blog/
     → git add + git commit + git push
     → Server pulls, 11ty rebuilds (< 1 second)
     → runcrux.io/blog/new-post/ is live
     → Tweet includes link to blog post for deeper context

One keystroke. Tweet queued. Blog post published. Site rebuilt.
```

**The blog post is NOT the tweet.** The tweet is 1-3 sentences. The blog post is the expanded version — 200-800 words with code snippets, architecture diagrams, the "why" behind the decision. The tweet drives traffic to the blog. The blog drives traffic to GitHub.

### Blog Post Auto-Generation

When the marketing trigger fires, the MCP tool generates two outputs from the same source material:

1. **Tweet/thread** (short, punchy, your voice) → Typefully
2. **Blog post** (expanded, technical, includes code) → markdown file

Blog post frontmatter format:
```yaml
---
title: "wiring crux adopt for mid-session onboarding"
date: 2026-03-05
tags: [shipping, architecture, mcp]
tweet_id: 8281849
summary: "two-phase onboarding so you can start using Crux on an existing project without losing context"
---
```

The `tweet_id` field cross-references the Typefully post, so the site can show "originally posted on X" with a link, and the tweet can include a "read more →" link to the blog post.

### Blog Post Types

Not every tweet gets a blog post. The MCP tool decides based on signal strength:

- **High-signal events** (new MCP tool, architecture decision, tests pass after failure) → always generate blog post
- **Milestone tweets** (git tag, PR merge, major feature) → always generate blog post
- **Routine shipping updates** (fixed a bug, small refactor) → tweet only, no blog post
- **Digest threads** (every ~50-100 commits) → always generate companion blog post (this becomes your "weekly update" equivalent)

Target: ~3-5 blog posts per week. Not forced — they come from the natural rhythm of high-signal work.

### Deployment

You said you have a server. The deployment flow:

```bash
# In site/ directory
npm run build          # 11ty builds to _site/
rsync -avz _site/ user@server:/var/www/runcrux.io/

# Or if server has git:
git push origin main   # Server has post-receive hook that runs 11ty build
```

For the MCP tool integration, the `crux_marketing_generate` tool:
1. Writes the blog post markdown to `site/src/blog/YYYY-MM-DD-slug.md`
2. Runs `cd site && npm run build`
3. Deploys (rsync or git push)
4. Returns the live URL for inclusion in the tweet

All of this happens in the same flow as the Typefully API call — one keystroke, both outputs.

### The Landing Page

runcrux.io homepage should be minimal and direct:

```
crux
rails for AI coding tools

your AI tools are disposable. your intelligence shouldn't be.

.crux/ is a directory that stores everything your AI learns —
corrections, patterns, session state, safety rules.
it travels with you. no matter what tool you use.

[view on GitHub]  [read the blog]  [get started]

───────────────────────────────────

works with:
Claude Code · OpenCode · Cursor · Aider · Roo Code · Qwen-Agent

───────────────────────────────────

latest from the build log:
[auto-populated from 3 most recent blog posts]
```

No JavaScript. No animations. No cookie banners. Sub-100KB page load. The site itself embodies the philosophy: infrastructure over decoration.

### Design Principles

- **All lowercase** in copy (matching your voice), proper nouns capitalized
- **Monospace headings**, system font for body text
- **Dark mode default** (developers), light mode toggle
- **No tracking.** No Google Analytics. No cookies. If you want metrics, use server-side access logs or a privacy-respecting tool like Plausible or GoatCounter.
- **Fast.** Target < 50ms TTFB, < 100KB total page weight. 11ty makes this trivial.
- **RSS feed.** Developers subscribe to RSS. The 11ty RSS plugin makes this one line of config.

### Integration with Marketing Config

Add to `.crux/marketing/config.json`:
```json
{
  "website": {
    "domain": "runcrux.io",
    "site_path": "site/",
    "blog_path": "site/src/blog/",
    "deploy_command": "cd site && npm run build && rsync -avz _site/ user@server:/var/www/runcrux.io/",
    "generate_blog_post": true,
    "blog_post_threshold": "high_signal",
    "cross_link_tweets": true
  }
}
```

### State Tracking

Add to `.crux/marketing/state.json`:
```json
{
  "last_blog_post_at": "2026-03-06T00:35:00Z",
  "last_blog_post_slug": "day-1-building-crux",
  "blog_posts_today": 2,
  "site_last_deployed_at": "2026-03-06T00:35:15Z"
}
```

### Execution Timeline

**This week:**
1. Register runcrux.io and cruxvibe.io
2. Scaffold 11ty project in repo (`site/` directory)
3. Build landing page (hero + architecture diagram + tool logos)
4. Write first 3 blog posts from today's work (Day 1 recap, MCP architecture decision, .crux/ directory design)
5. Deploy to server, verify SSL
6. Update Typefully bio/links to point to runcrux.io

**Next week:**
1. Wire blog post generation into `crux_marketing_generate` MCP tool
2. Add deploy step to the marketing pipeline (one keystroke = tweet + blog + deploy)
3. Add RSS feed
4. Add changelog page (auto-populated from git tags)
5. Submit to Google Search Console

**Month 2:**
1. Add docs section (start migrating from GitHub README)
2. Add "works with" pages (one per tool: /docs/claude-code, /docs/cursor, etc.)
3. Set up Plausible or GoatCounter for privacy-respecting analytics
4. cruxvibe.io landing page (when commercial product is ready)

---

## 18. Competitive Analysis: Crux + OpenClaw vs Shipper 2.0

Shipper 2.0 (by @nicholasdevhub) markets itself as "the first AI that can truly build and run a business for you." It wraps Claude's API in a hosted chat UI with an "Advisor" chatbot and a deploy pipeline, charging ~$25/100 credits (Pro plan ~$100/month). Their X launch made seven specific claims. Here's how Crux + OpenClaw stacks up against every single one — with real mechanisms, not marketing.

### Claim 1: "Build web apps, mobile apps, and Chrome extensions"

**Shipper reality:** Claude writes code in a hosted sandbox. Deploy is to their own infrastructure. Mobile and Chrome extension support is unsubstantiated — no demo, no docs, no user reports.

**Crux + OpenClaw reality:**
- **Web apps:** OpenClaw's `web-hosting` skill provides zero-friction deploy to Vercel or Netlify. It auto-detects your framework (Next.js, Vite, plain HTML), wires CI/CD, handles custom domains, and manages environment variables. This is a real, documented, community-tested skill with thousands of users.
- **Mobile apps:** React Native / Expo support exists through community projects and ClawHost's RN mobile app component. Not as seamless as web deploy, but it's real and it works.
- **Chrome extensions:** OpenClaw's code execution + browser automation (`chrome-relay` extension + headless Playwright) makes building and testing Chrome extensions feasible. The manifest.json / popup / background script pattern is well within Claude Code's capabilities, and Crux's correction memory means the agent learns your extension's architecture across sessions.
- **What Crux adds:** Every architectural decision, every bug fix pattern, every framework quirk gets stored in `.crux/`. The next app builds faster because the intelligence compounds. Shipper starts from zero every session.

**Verdict: Crux + OpenClaw delivers. Web apps are stronger than Shipper. Mobile and Chrome extensions are feasible with real tooling, not vaporware.**

### Claim 2: "Code, design, monetize, launch"

**Shipper reality:** "Code" = Claude writes code (any wrapper does this). "Design" = unsubstantiated, no Figma integration or design system. "Monetize" = no evidence of payment integration. "Launch" = deploy to their hosting.

**Crux + OpenClaw reality:**
- **Code:** Claude Code / OpenCode / Cursor / Aider — take your pick. Crux makes your intelligence portable across all of them.
- **Design:** OpenClaw's browser automation can interact with design tools. More practically, Claude Code generates Tailwind/CSS with increasingly good design sense, and Crux's corrections file means you teach it your design preferences once and they persist.
- **Monetize:** OpenClaw's `stripe` skill handles the full payment lifecycle — PaymentIntents, subscriptions, invoicing, refunds, webhook handling, test/live mode switching. This isn't a marketing claim; it's a real MCP skill that interacts with Stripe's API. You can go from "add payments" to working checkout in one session.
- **Launch:** OpenClaw `web-hosting` skill deploys to Vercel/Netlify. DNS, SSL, CI/CD — all handled. Plus Crux's marketing pipeline can auto-generate the launch tweet and blog post from the same session.

**Verdict: Crux + OpenClaw delivers on all four, with real mechanisms. Shipper's "monetize" claim has zero supporting evidence. OpenClaw's Stripe skill actually exists.**

### Claim 3: "Do email marketing for you"

**Shipper reality:** This is the most unsubstantiated claim. No documentation, no screenshots, no user reports of Shipper sending emails or managing subscriber lists. Zero evidence this feature exists.

**Crux + OpenClaw reality:**
- **Gmail integration:** OpenClaw's email skills use Gmail Pub/Sub for real-time email monitoring. Read, compose, reply, label, search — all through MCP tools.
- **Transactional email:** Resend and SMTP skills for sending from your own domain. HTML templates, attachments, the works.
- **Newsletter management:** Subscriber tracking, open/click analytics, list management. This is built into the email skill ecosystem.
- **Automated sequences:** Combine OpenClaw's cron jobs with email skills. Schedule drip campaigns, follow-ups, digest emails — all running autonomously on your machine.
- **What Crux adds:** Your email voice, your formatting preferences, your "don't email these people" rules — all stored in `.crux/corrections.md`. The agent learns what works and what doesn't from your feedback.

**Verdict: Crux + OpenClaw actually delivers what Shipper only claims. Real Gmail integration, real sending infrastructure, real subscriber management.**

### Claim 4: "Continue to build out new features"

**Shipper reality:** The claim implies autonomous feature development. In practice, this means "you can ask Claude to add features in subsequent chat sessions." Every Claude wrapper does this. There's no evidence of proactive feature development.

**Crux + OpenClaw reality:**
- **Cron-based autonomous work:** OpenClaw's cron jobs can schedule tasks that run without human intervention. The documented "overnight app builder" pattern has users literally waking up to new features their agent built while they slept.
- **Self-healing as feature iteration:** The 4-tier recovery system (KeepAlive → Watchdog → AI Emergency → Human Alert) means the agent doesn't just fix crashes — it can identify patterns of failure and proactively refactor to prevent them.
- **What Crux adds:** This is where Crux's intelligence layer becomes the difference-maker. `.crux/sessions/` tracks what was built and why. `.crux/corrections.md` accumulates architectural preferences. `.crux/knowledge/` stores domain context. So when the agent builds new features autonomously, it does so with full knowledge of your codebase's patterns, your style preferences, and your past decisions. It's not just "Claude writing code" — it's Claude writing code informed by your project's entire history.

**Verdict: Crux + OpenClaw delivers this for real with cron jobs and overnight autonomous building. Shipper's version is just "you can keep chatting with Claude."**

### Claim 5: "Self-maintain in the long run"

**Shipper reality:** No evidence. No documentation of monitoring, health checks, error recovery, or autonomous maintenance. This appears to be pure marketing.

**Crux + OpenClaw reality:**
- **4-tier self-healing architecture:**
  - Tier 1 — KeepAlive (0-30s): Automatic restart on crash, state preservation
  - Tier 2 — Watchdog (3-5min): Process monitoring, resource management, dependency checks
  - Tier 3 — AI Emergency (5-30min): Claude Code analyzes the failure, writes a fix, tests it, deploys it
  - Tier 4 — Human Alert: Escalation when autonomous recovery fails
- **Cron-based maintenance:** Scheduled health checks, log rotation, dependency updates, database optimization — all running on your schedule.
- **What Crux adds:** `.crux/corrections.md` accumulates maintenance patterns. "When this error occurs, do this." "This dependency breaks on update, pin it." "This endpoint needs rate limiting after 1000 req/min." The maintenance intelligence compounds over time, making each recovery faster and more accurate.

**Verdict: Crux + OpenClaw has a real, documented, multi-tier self-healing system. Shipper has a marketing bullet point.**

### Claim 6: "From a <10 word prompt"

**Shipper reality:** Cherry-picked demo. "Build me a todo app" → working todo app. Sure. But "build me an e-commerce platform with subscription billing, email marketing, and mobile support" in <10 words? That's not how software works, regardless of the tool.

**Crux + OpenClaw reality:**
- A 10-word prompt works just as well (or poorly) with any Claude-powered tool. The quality of the output depends on the model, not the wrapper.
- **Where Crux is actually better:** With `.crux/` context loaded, a 10-word prompt carries far more information than 10 words. "Add payments like the last project" is 6 words, but Crux knows what "like the last project" means because it has your Stripe integration patterns, your preferred checkout flow, and your error handling style all stored in the intelligence layer.
- The honest framing: Simple apps from short prompts? Yes, any Claude tool does this. Complex apps? You'll need iterative sessions regardless — and Crux makes each iteration smarter because nothing is lost between sessions.

**Verdict: Tie on simple prompts (any Claude wrapper does this). Crux wins on complex projects because context accumulates instead of resetting.**

### Claim 7: "For as low as $0.12/app"

**Shipper reality:** Extreme cherry-pick. At $25/100 credits, $0.12 means ~0.5 credits. That's maybe one short API call. A real app with iteration, debugging, and deployment would cost $5-50+ in Shipper credits. Their Pro plan is ~$100/month.

**Crux + OpenClaw reality:**
- **You pay the API provider directly.** Claude Code Pro is $100/month (unlimited within usage policy). OpenCode uses your own API key — you pay Anthropic/OpenAI directly at their rates.
- **No middleman markup.** Shipper charges $25/100 credits on top of Claude's API costs. With Crux + OpenClaw, there's no wrapper tax.
- **Real cost comparison:** A Claude Code Pro subscription gives you unlimited app building, maintenance, email automation, payment integration, deploys — everything. Same $100/month as Shipper's Pro plan, but with no credit limits, no per-app charges, and your intelligence compounds across everything you build.

**Verdict: Crux + OpenClaw is cheaper for any real workload. No per-app pricing games, no credit system, no middleman markup.**

### The Unfair Advantage: What Shipper Can Never Do

Beyond matching every claim, Crux + OpenClaw has structural advantages Shipper can't replicate:

1. **Portable intelligence.** Switch from Claude Code to Cursor to OpenCode mid-project. Your corrections, patterns, and knowledge travel with you. Shipper locks you into their chat UI.

2. **Compounding knowledge.** Every app you build makes the next one faster. Shipper resets to zero every session.

3. **Open source transparency.** You can audit every line of Crux. Shipper is a black box.

4. **Tool-agnostic community.** Every AI coding tool community is your community. Shipper is one more walled garden competing with every other wrapper.

5. **No vendor lock-in.** If Crux disappears tomorrow, your `.crux/` directory still works as context files for any AI tool. If Shipper disappears, you lose everything.

6. **Self-improving safety.** Crux's corrections pipeline means "don't delete the production database" gets learned once and enforced forever. Shipper has no equivalent.

### Bottom Line

Shipper is a $100/month Claude API wrapper with marketing claims that range from real-but-unremarkable (Claude writes code) to unsubstantiated (email marketing, self-maintenance). Its value proposition is convenience — you don't need to set anything up.

Crux + OpenClaw is an open-source intelligence framework running on top of battle-tested tools with 200K+ stars, 13,729+ community skills, real self-healing architecture, real payment integration, real email automation, and real autonomous operation. Its value proposition is compounding intelligence — every project makes the next one smarter.

The marketing angle: **"Shipper promises it. We actually built it."**

---

## Final Thoughts

You have three unfair advantages now, not one.

First: you're a solo founder who builds real products, uses your own tools, and has zero marketing budget to hide behind. That's not a constraint. That's your whole strength.

Second: the `.crux/` architecture means you're not competing with any AI tool — you're enhancing all of them. Every tool community is your community. Every "which tool?" debate is your distribution channel. Every frustrated developer who's lost context switching tools is your customer. You don't have competitors in the traditional sense. You have a blue ocean.

Third: you're dogfooding the exact workflow you're selling. Every time you `crux switch` between Claude Code and OpenCode on Crux itself, that's a demo. Every time `.crux/` carries your corrections and knowledge between tools, that's proof. Your daily workflow IS your marketing content.

Most founders would kill to have what you have: authentic narrative, consistent shipping, technical depth, a product that solves a universal pain point, and positioning that makes you welcome in every competing community simultaneously.

This plan is designed to make consistency automatic (infrastructure handles 80%) so you can stay focused on building. The content writes itself from your work. You just refine it.

Start tomorrow. Don't aim for perfect. Aim for shipped. Post your first thread about switching tools mid-project without losing context. That single story is more compelling than any feature list.

The compounding will shock you.
