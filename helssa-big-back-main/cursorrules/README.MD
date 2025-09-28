# 🚀 Agent Governance

### Purpose & Scope

This directive applies to all contributors—humans and agents—working in this repository (and related modules). It governs changes on all branches when work results in a pull request; the default base for comparison is `develop` (override via `BASE_BRANCH` if your project uses a different base).

## 📌 Canonical Rule

**⚠️ Hard rule.** ⏩ Before any action ▶️, the 🤖 must 📖 read the **entire** `agent/` 📁 and 📌 follow it **verbatim**. If any ad‑hoc 🗒️ ⛔️ conflicts with `agent/` prescriptions: ① 🧾 record the conflict (provenance: 🗂️ path + #️⃣ line) ② 🛑 stop execution.

## 🚫🌀 Non‑Contradiction Doctrine

### 🔍 Decision Tree (Short)

- **Conflict in canonical rules?** If two prescriptions (same scope/time) in `agent/` or between `agent/` and an ad‑hoc request **cannot both be true**, treat as a **contradiction** → 🛑 stop → file a Paradox Report.
- **Extension without violation?** If an ad‑hoc request *adds* behavior **without violating** any `agent/` rule *and* `agent/` permits extensions, it is a **permissible deviation** → proceed.
- **Ambiguous or underspecified?** If requirements are unclear or incomplete, treat as **insufficient information** → do **not** proceed; document questions in the report and ping reviewers.

### 🧩 Examples

- **Contradiction:** `agent/` mandates **presigned, time‑bounded URLs** for downloads; an ad‑hoc request instructs to **expose public URLs**. → Stop, report.
- **Permissible deviation:** tests exceed the minimum coverage target without altering security policy. → Proceed.

### ⏱️ SLA for Filing

- Submit the **Paradox Report** within **1 business hour** of detection (absolute max: **24h**). Name it using UTC: `agent/reports/YYYY‑MM‑DDTHHMMZ-paradox.md`.

### 🚨 Escalation Path

- Tag **CODEOWNERS** (auto) and notify `@maintainers`. If security/privacy is implicated, also notify `@security`.
- If blocked, open a **Draft PR** containing the report to provide visibility while awaiting guidance.

The 🤖 must **not proceed** when specs ⚙️🔀 contradict or yield a 🌀 paradox.

### 🧾 Paradox Report — Required Contents

**Naming convention (UTC):** `agent/reports/YYYY‑MM‑DDTHHMMZ-paradox.md` (e.g., `2025-08-28T1432Z-paradox.md`). Use UTC ("Z"). If UTC is unavailable, fallback to `YYYYMMDD-HHMM-paradox.md`.

**Mini‑template:**

```md
# Paradox Report
- Report ID: 2025-08-28T1432Z-paradox
- Author: <name or bot id>
- Branch: <feature/...>
- Task/Issue: <link or ID>
- Timestamp (UTC): 2025-08-28T14:32:00Z

## Conflict Excerpts
- File: path/to/file.py:123–128
  > "…verbatim…"
- File: agent/README.md:45–51
  > "…verbatim…"

## Analysis
<brief synthesis explaining locus and nature of the contradiction>

## Proposed Resolution / Questions
<clear next steps or questions for maintainers>

## Notifications
- Notified: @owner1 @owner2
```

Upon detection:

1. 🛑 **Stop** immediately.
2. ✍️ Create a **Paradox Report** with: ⏱️ UTC timestamp · 🔗 task/issue reference · 📎 verbatim conflicting snippets with 🗂️ file paths and #️⃣ line numbers · 🧠 concise analysis · 🧭 proposed resolution or ❓ questions.
3. 💾 Save at: `agent/reports/YYYYMMDD-HHMM-paradox.md` (📁 auto‑create if missing).
4. 💾 **Commit** and ⤴️ **push** the report to **your branch**.

## 🧵 Terminal Workflow — Always (Base: `develop` by default; set `BASE_BRANCH` if different • Required CI: lint, tests, coverage ≥ 85% (≥ 90% core) • CODEOWNERS review required • Use Draft PR when paradox‑blocked)

1. 💾 **Commit** all changes (or the 🧾 Paradox Report if work halted).
2. ⤴️ **Push** to **your branch**.
3. 🔀 **Open a PR**: `your-branch` → `` (base: `develop`).
4. 🏷️ **Label the PR (required)** — select ≥ 1 from **each** set:
   - **Change Type:** ✨ `feature` · 🛠️ `fix` · 📝 `docs` · ♻️ `refactor` · 🧪 `test` · 🚀 `perf` · 🔒 `security` · 🧹 `chore` · 🏗️ `build` · 🤖 `ci`.
   - **Subsystem/Scope:** 🤖 `agent` · 🐍 `backend/django` · 🧮 `db/pgvector` · ☁️ `storage/minio` · 📱 `frontend/flutter` · ⚙️ `infra/devops`.
   - **Impact/Status (if applicable):** 💥 `breaking-change` · 🔁 `migration` · 🚑 `hotfix` · 👀 `needs-review` · ⛔️ `blocked/paradox`.
5. 🧾 **PR body** must include: 🎯 objective · 🧾 changeset synopsis · ⚠️ risk/impact · 🔬 verification notes · 🔗 links to issues/tasks.
6. 🚫 **Do not merge.** ⏳ Wait for ✅ CI and 👤 human review/approval.

## 🌿 Branching & 🧾 Commit Semantics

- 🌿 Naming: `feature/<short-desc>` or `fix/<short-desc>`.
- 🧾 Use **Conventional Commits** (e.g., `feat: …`, `fix: …`, `docs: …`).

## 🔎 TL;DR

`agent/` = 🔝📖 single source of truth. If 🌀 arises: **report → 💾 save → 💾 commit & ⤴️ push → 🔀 PR → 🏷️ label → ⏳ review**.

**TL;DR (emoji‑light):** `agent/` is the single source of truth. On contradiction: report → save → commit & push → open PR to `develop` → label → await review.

