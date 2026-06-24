=== access-troubleshooter/ ===
---
name: access-troubleshooter
description: >-
  Debug authorization and permission issues in Snowflake.
  Use when: access denied, insufficient privileges, permission errors, 
  role issues, missing grants, privilege analysis,
  least-privilege role creation, find authorizing roles.
  Triggers: access denied, insufficient privileges, permission error,
  authorization failed, can't access, missing permission, grant needed,
  role recommendation, SQL access control error, does not exist or not authorized,
  EXPLAIN_PRIVILEGES, SYSTEM$ANALYZE_ROLE_ACCESS, SYSTEM$SUGGEST_ROLE_GRANTS.
---

# Access Troubleshooter

Debug authorization failures, analyze required privileges, and manage role-based access in Snowflake.

## When to Use

- User gets "Insufficient privileges" or "Access denied" errors
- User wants to know what privileges are needed for a query
- User wants to find which role can run a specific query
- User needs to create a least-privilege role for a task
- User asks "Why can't [person/role] access [object]?"
- User wants to grant missing privileges to an existing role

## Auto-Trigger Error Patterns

When you detect these error message patterns, AUTOMATICALLY offer to help:

**Pattern 1:** `SQL access control error:\nInsufficient privileges to operate on`

**Pattern 2:** `SQL compilation error:.*does not exist or not authorized`

**When detected, respond with:**

```
Would you like me to debug this using the access-troubleshooter skill? I can:

1. Find what privileges are missing for this query
2. Find which roles can run this query
3. Generate GRANT statements to fix the access
```

If user agrees, proceed to the Main Workflow below.

## Workflows

| Workflow | Description |
|----------|-------------|
| `workflows/debug-error.md` | Full diagnostic flow for authorization errors (Steps A1–A6) |
| `workflows/analyze-privileges.md` | List all required or missing privileges for a query |
| `workflows/find-authorizing-roles.md` | Find which roles can authorize a query |
| `workflows/create-role.md` | Create a new least-privilege role for a query |
| `workflows/grant-permissions.md` | Grant missing privileges to an existing role |

## References

Load [references/function-reference.md](references/function-reference.md) on-demand for detailed syntax, parameters, and output format for `EXPLAIN_PRIVILEGES`, `SYSTEM$ANALYZE_ROLE_ACCESS`, and `SYSTEM$SUGGEST_ROLE_GRANTS`.

---

## Agent Behavior Rules (Apply to ALL Workflows)

1. **Safety protocols** — Never run GRANT or CREATE ROLE without explicit user approval. Present all SQL statements for review before execution. Provide revert instructions after changes.

2. **Fresh data only** — Do NOT use cached results from previous authorization analyses. Roles, grants, and privileges can change at any time. Always re-query the current state.

3. **Follow step order** — Execute steps sequentially as defined. Do not skip steps, pre-select options, or jump ahead based on the user's opening message. Route based on AskUserQuestion selections, not inferred intent.

4. **Hard stops are mandatory** — Steps marked with a checkpoint are gates. Do not proceed until the required user input is received. Once approved, proceed directly without re-asking.

5. **Choices vs. free text** — When the user must choose between options (routing, resolution strategy, role selection), use AskUserQuestion with a selectable list. Only collect as plain free text when creating new names (role name).

6. **EXPLAIN_PRIVILEGES first for diagnostics** — In the initial diagnostic phase, always use `EXPLAIN_PRIVILEGES` first to understand requirements and check session authorization. Subsequent steps (e.g., finding which roles can authorize, suggesting grants) may use `SYSTEM$ANALYZE_ROLE_ACCESS` or `SYSTEM$SUGGEST_ROLE_GRANTS` directly.

7. **`<ANY>` translation** — When generating GRANT statements from `EXPLAIN_PRIVILEGES` output, translate `"<ANY>"` to `USAGE` for DATABASE and SCHEMA objects.

8. **On-behalf-of analysis** — If the user is analyzing for a different user (e.g., "check what USER_X is missing," "debug this for BOB," "what roles can run this for ALICE"), collect the target username (store as `<TARGET_USER>`) and use it throughout:
   - `SYSTEM$ANALYZE_ROLE_ACCESS(sql, false, '<TARGET_USER>')` so `isGranted` reflects the target user's grants
   - `SYSTEM$SUGGEST_ROLE_GRANTS(sql, '', '<TARGET_USER>')` for user-scoped grant suggestions
   - `EXPLAIN_PRIVILEGES(..., for_role => '<role>')` when checking a specific role of the target user
   - `GRANT ROLE ... TO USER <TARGET_USER>` when granting roles

   **If on-behalf-of queries fail with insufficient privileges** (e.g., `SHOW GRANTS TO USER <TARGET_USER>` or `SYSTEM$ANALYZE_ROLE_ACCESS` with `forUser` returns a permission error): **Stop analysis.** Tell the user: *"You don't have sufficient privileges to analyze this statement on behalf of another user. Please contact your system administrator. ACCOUNTADMIN role may be required to manage the privileges on the object."* Proceed to **Step 3** in the Main Workflow.

---

## Main Workflow

### Step 1: Determine Intent

Ask what the user wants to do. **Do NOT load any workflow file yet** — just record the selection for Step 2.

```python
AskUserQuestion(
    questions=[{
        "question": "What would you like to do?",
        "header": "Privilege Analysis",
        "multiSelect": false,
        "options": [
            {"label": "Debug an authorization error", "description": "I got a permission error and need to diagnose and fix it"},
            {"label": "Analyze what privileges a query needs", "description": "Show all required or missing privileges for a SQL statement"},
            {"label": "Find which roles can run a query", "description": "Search for existing roles that can authorize a SQL statement"},
            {"label": "Create a least-privilege role", "description": "Create a new role with minimum privileges for a SQL statement"},
            {"label": "Grant missing privileges to a role", "description": "Add missing privileges to an existing role"}
        ]
    }]
)
```

Record the selection, then proceed to **Step 2**.

---

### Step 2: Load and Execute Workflow

**YOU MUST read the relevant workflow file below and then follow it step by step.** The workflow files contain the full procedure.

| Step 1 Selection | File to read (use Read tool) |
|-----------|--------|
| **Debug an authorization error** | `workflows/debug-error.md` |
| **Analyze what privileges a query needs** | `workflows/analyze-privileges.md` |
| **Find which roles can run a query** | `workflows/find-authorizing-roles.md` |
| **Create a least-privilege role** | `workflows/create-role.md` |
| **Grant missing privileges to a role** | `workflows/grant-permissions.md` |

**If you proceed without reading the file, the workflow will be wrong.**

Once the workflow completes its final step, proceed to **Step 3**.

---

### Step 3: Repeat or Done

```python
AskUserQuestion(
    questions=[{
        "question": "What would you like to do next?",
        "header": "Next Step",
        "multiSelect": false,
        "options": [
            {"label": "Start another operation", "description": "Return to the privilege analysis main menu"},
            {"label": "Done", "description": "Exit"}
        ]
    }]
)
```

| Selection | Action |
|-----------|--------|
| **Start another operation** | Go back to **Step 1** and present its exact AskUserQuestion again. Do NOT infer the next operation. |
| **Done** | Workflow complete — stop. Do not suggest further actions. |

---

## Quick Reference

### Function Quick Reference

| Question | Function | Notes |
|----------|----------|-------|
| What privileges needed? | `EXPLAIN_PRIVILEGES(sql)` | Use first |
| What am I missing? | `EXPLAIN_PRIVILEGES(sql, missing_only => true)` | Session check |
| What is role missing? | `EXPLAIN_PRIVILEGES(sql, missing_only => true, for_role => 'ROLE')` | Per-role check |
| Which roles can authorize? | `SYSTEM$ANALYZE_ROLE_ACCESS(sql)` | Sorted role hierarchy |
| What grants to add for a role? | `SYSTEM$SUGGEST_ROLE_GRANTS(sql, 'ROLE')` | Per-role coverage of missing grants |

### Recommended Order

1. `EXPLAIN_PRIVILEGES(sql)` — understand requirements
2. `EXPLAIN_PRIVILEGES(sql, missing_only => true)` — can session authorize?
3. `EXPLAIN_PRIVILEGES(sql, missing_only => true, for_role => 'ROLE')` — check each user role
4. `SYSTEM$ANALYZE_ROLE_ACCESS(sql)` — which roles can authorize?
5. `SYSTEM$SUGGEST_ROLE_GRANTS(sql, 'ROLE')` — what grants to add? (if needed)

---

## Common Error Messages

- "SQL access control error: Insufficient privileges to operate on schema"
- "SQL access control error: Insufficient privileges to operate on table"
- "SQL compilation error: Object 'X' does not exist or not authorized"
- "SQL compilation error: Database 'X' does not exist or not authorized"
- "SQL compilation error: Schema 'X' does not exist or not authorized"

---

## Troubleshooting

| Issue | Possible Cause | Action |
|-------|---------------|--------|
| `supported: false` from ANALYZE_ROLE_ACCESS | Runtime authorization (row access, masking policies) | Use EXPLAIN_PRIVILEGES or test with execution |
| "requires access on all objects in the statement" | Role cannot resolve one or more objects in the query | **Stop analysis.** Do NOT attempt manual lookups (SHOW GRANTS, SHOW TABLES, etc.) — this would leak object existence. Tell user: *"Please contact your system administrator. ACCOUNTADMIN role may be required to manage the privileges on the object."* |
| User has role but still can't access | Wrong active role, row-level security, masking policy | Check `CURRENT_ROLE()`, `SHOW ROW ACCESS POLICIES`, `SHOW MASKING POLICIES` |
| Privilege exists but query fails | Object doesn't exist, wrong DB/schema context, future grant needed | Verify object exists and context is correct |
| EXPLAIN_PRIVILEGES "Unsupported feature" | Function not available in this account | Fall back to `SYSTEM$ANALYZE_ROLE_ACCESS` |

---

## Stopping Points

- Step 1: always wait for user selection before routing
- Step 2: must load the workflow file — do not skip
- `workflows/debug-error.md`: checkpoint before executing GRANT or CREATE ROLE statements
- `workflows/create-role.md`: checkpoint before creating role and executing grants
- `workflows/grant-permissions.md`: checkpoint before executing grant statements
- Any time resolution SQL is generated: present for approval before executing

**Resume rule:** Upon user approval, proceed directly to the next step without re-asking.

---

## Output

- Identified missing privileges with specific details
- Generated appropriate GRANT statements
- Created least-privilege role if requested
- Verified access restored

=== ai-data-share/ ===
---
name: ai-data-share
description: "Make a listing or data share AI-Ready. Use when: creating semantic views for listings, creating cortex agents for data shares, making data AI-ready. Triggers: AI-ready listing, share agent, data share semantic view, marketplace AI."
---

# AI Ready Data Share

## Purpose

Automatically create a complete data agent by:
1. Resolving your data source (listing or share)
2. Creating a semantic view from the source tables
3. Creating a Cortex Agent connected to the semantic view

## Workflow

### Step 0: Resolve the listing or the share

 **Load** `resolve_source.md` first. This will ask the user whether they're starting from a listing or an existing share:
- **Listing path:** Resolves the listing to extract the share, then inspects share objects.
- **Share path:** Validates the share directly, optionally reverse-looks up an associated listing for metadata enrichment, then inspects share objects.

Both paths converge on share object inspection, exclusion rules, and existing semantic view checks before proceeding to Phase 1.

---

### Phase 1: Create Semantic View

**Load:** [create_semantic_view.md](create_semantic_view.md)

This phase will:
- Collect your source tables (from listing or share)
- Ask for documentation/context about the data
- Discover table schemas and relationships
- Generate table/column comments from context (only for empty fields)
- Generate and deploy a semantic view using FastGen

---

### Phase 2: Create Agent

**Load:** [create_agent.md](create_agent.md)

This phase will:
- Check for existing agents on the same tables
- Offer choice: use existing, create new, or optimize existing
- Connect to the semantic view from Phase 1
- Generate orchestration and response prompts
- Configure tools with appropriate descriptions
- Deploy the agent to Snowflake via REST API

---

## Attaching Objects to Shares

After creating semantic views or agents, use the **attach-ai-products-to-share** skill to properly attach them to the share, if they haven't been added already:

```
<invoke name="skill">
<parameter name="command">attach-ai-products-to-share</parameter>
</invoke>
```

The skill handles:
- Correct grant ordering (database → schema → object)
- Semantic view dependencies (underlying tables)
- Agent tool dependencies
- Cortex Search Service grants

### Quick Reference (Manual Grants)

| Object Type | Syntax |
|-------------|--------|
| Show Agents | `SHOW AGENTS IN DATABASE db;` (NOT `SHOW CORTEX AGENTS`) |
| Semantic View | `GRANT SELECT, REFERENCES ON SEMANTIC VIEW db.schema.view TO SHARE share_name;` |
| Agent | `GRANT USAGE ON AGENT db.schema.agent TO SHARE share_name;` |
| Cortex Search Service | `GRANT USAGE ON CORTEX SEARCH SERVICE db.schema.css TO SHARE share_name;` |
| Table | `GRANT SELECT ON TABLE db.schema.table TO SHARE share_name;` |
| Schema | `GRANT USAGE ON SCHEMA db.schema TO SHARE share_name;` |
| Database | `GRANT USAGE ON DATABASE db TO SHARE share_name;` |

---

## Output

Upon completion, this skill produces:

| Deliverable | Description |
|-------------|-------------|
| Semantic View | Fully qualified semantic view connected to source tables |
| Cortex Agent | Agent with orchestration/response prompts, linked to semantic view |
| Share Grants | All objects properly granted to share |

**Files generated:**
- Semantic model YAML (via semantic-view skill)
- Agent specification (via cortex-agent skill)

---

## Stopping Points

- ✋ **resolve_source:** Choose entry point (listing or share)
- ✋ **resolve_source:** Select listing identification method (listing path only)
- ✋ **resolve_source:** Confirm included/excluded objects before proceeding
- ✋ **resolve_source:** If existing semantic view found, choose reuse or create new
- ✋ **create_semantic_view:** Confirm inputs and documentation sources
- ✋ **create_semantic_view:** Review semantic model before deployment
- ✋ **create_agent:** Provide agent persona, domain focus, target audience
- ✋ **create_agent:** Select agent location from eligible schemas
- ✋ **create_agent:** Review agent configuration before deployment

**Resume rule:** Upon user approval, proceed directly to next step without re-asking.

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid identifier" on FastGen upload | Passed 3-part name instead of 2-part | Use `DATABASE.SCHEMA` not `DATABASE.SCHEMA.VIEW` |
| "CORTEX AGENT not found" on grant | Wrong grant syntax | Use `GRANT USAGE ON AGENT` (no CORTEX keyword) |
| pyarrow build fails | Python 3.13+ incompatible | Run `uv python install 3.11` - uv will use the correct Python version automatically |
| FastGen many-to-many warning | Missing unique keys on FK target | Informational only - relationships still work via other paths |
| "Cannot grant to share" | Object not in eligible schema | Ensure object is in a schema with USAGE grant to share |
| Agent spec empty after creation | Wrong DDL syntax | Use `FROM SPECIFICATION $$...$$` not `SPEC = '...'` |

=== ai-readiness-score/ ===
---
name: ai-readiness-score
description: >
  Measure AI readiness for this Snowflake account. Scores Consumption-Ready (CR)
  tables, Semantic View (SV) coverage and quality, and demand coverage. Generates
  an HTML scorecard report with recommendations. Runs in Snowsight (notebook) or
  CLI mode (direct SQL), auto-detected by environment. Caches results for fast reruns.
  Use when: AI readiness, readiness score, how AI-ready am I, measure my ai readiness,
  semantic view coverage, Semantic View (SV) quality, Consumption-Ready (CR) tables,
  demand coverage, CR tables, AI readiness report, score my account.
---

# AI Readiness Score — Dispatcher

This skill measures your account's AI readiness. It has two execution modes
depending on how it was invoked:

| Mode | Environment | What happens |
|------|-------------|--------------|
| **Snowsight** | Snowsight Workspaces CoCo UI | Builds and runs a notebook, generates an HTML report |
| **CLI** | CoCo CLI (terminal) | Runs SQL directly, outputs scores and generates an HTML report |

---

## Environment Detection

Determine which mode to use based on the following signals:

- **Snowsight Workspace** — System reminders mention "Current workspace:" or the
  skill was loaded from a path containing `/snowflake/stages/`.
- **Snowsight non-workspace** — The `get_page_context` tool is in the tool list,
  but there is no "Current workspace:" reminder and no `/snowflake/stages/` path.
  The user is on a Snowsight page (home, catalog, etc.) but not in a Workspace.
- **CoCo CLI** — The `get_page_context` tool is not in the tool list.

**Decision rule (check in this order):**

1. If there is a "Current workspace:" system reminder or the skill was loaded from
   a path containing `/snowflake/stages/` → **Snowsight Workspace mode**
2. If the `get_page_context` tool is available in the tool list → **Snowsight non-workspace**
   - Use the `snowsight_navigate` tool with `route: "workspaces"` to prompt the user
     to switch to a Workspace.
   - Print: "This skill creates a notebook to run the analysis. Navigating to Workspaces..."
   - Once the user is in a Workspace, proceed with **Snowsight Workspace mode**.
   - If the user skips/declines navigation, print:
     > "The AI Readiness Score skill requires a Workspace to create and run the
     > analysis notebook. Please navigate to a Workspace and re-trigger the skill
     > when you're ready."
   - Stop execution.
3. If `get_page_context` is not in the tool list → **CLI mode**

---

## Routing

Once you have determined the mode, read the corresponding sub-skill file from the
skill directory (the same directory this file lives in) and follow its instructions.

### If Snowsight Workspace mode:

Read the file `skill-snowsight.md` from the skill directory and follow all its phases.

### If CLI mode:

Read the file `skill-cli.md` from the skill directory and follow all its phases.

---

## Shared Components

Both modes share the same `scripts/` directory:

| File | Purpose |
|------|---------|
| `scripts/build_notebook.py` | Builds the .ipynb notebook (Snowsight only) |
| `scripts/notebook_cells.py` | Cell content definitions (Snowsight only) |
| `scripts/cr_tables.sql` | CR table scoring query |
| `scripts/sv_quality.sql` | SV quality scoring query |
| `scripts/recommendations.py` | Builds recommendation text from scores |
| `scripts/report.py` | Renders the HTML report |

=== alert/ ===
---
name: alert
description: "Snowflake alert management - create, alter, suspend, resume, and troubleshoot alerts. Use when: user wants to create a new alert, modify an existing alert, set up monitoring, suspend or resume alerts, or investigate why an alert is firing/failing/not delivering. Triggers: create alert, new alert, add alert, alter alert, modify alert, change alert, suspend alert, resume alert, monitor with alert, set up alert, alert condition, troubleshoot alert, debug alert, investigate alert, alert firing, alert failed, alert not firing, why did my alert trigger, CONDITION_FAILED, ACTION_FAILED, notification not delivered."
---

# Alert

**MANDATORY DELEGATION:** This skill does NOT contain alert logic. You MUST load the appropriate sub-skill from the table below. Do NOT attempt to handle any alert-related request on your own — always delegate to a sub-skill first.

Do NOT:
- Generate any alert SQL without first loading the matching sub-skill
- Guess at syntax, condition queries, or notification content
- Skip loading the sub-skill because you think you already know the answer
- Partially follow the sub-skill — follow its complete workflow end-to-end

## Route to Sub-Skill

| Intent | Triggers | Action |
|--------|----------|--------|
| Create, alter, or delete alerts | "create alert", "new alert", "alter alert", "modify alert", "drop alert", "suspend alert", "resume alert", "set up alert", "monitor with alert" | **Load** `alert-create-alter/SKILL.md` |
| Troubleshoot an alert that is firing, failing, or not delivering | "alert firing", "alert failed", "why did my alert trigger", "alert not firing", "CONDITION_FAILED", "ACTION_FAILED", "ACTION_SKIPPED", "notification not delivered", "debug alert", "investigate alert", "alert misfiring", "alert noisy", "alert silent" | **Load** `alert-troubleshoot/SKILL.md` |

For the broader troubleshooting landscape (which products have dedicated troubleshoot skills, where the gaps are, how the uber skill routes between them), see [`TROUBLESHOOTING_LANDSCAPE.md`](TROUBLESHOOTING_LANDSCAPE.md).

=== attach-ai-products-to-share/ ===
---
name: attach-ai-products-to-share
description: "Attach AI products to Snowflake shares. Use when: adding semantic views, cortex agents, or cortex search services to a share. Triggers: share semantic view, share agent, share cortex search. Invoke this skill to add AI products to a share as a step of sharing AI products or creating a listing to share an AI product."
---

# Attach AI Products to Share

Attach AI products (semantic views, cortex agents, cortex search services) to Snowflake shares for marketplace listings.

## Supported AI Products

| Product Type | Privileges | Grant Command |
|-------------|------------|---------------|
| Semantic View | SELECT, REFERENCES | `GRANT SELECT ON SEMANTIC VIEW` + `GRANT REFERENCES ON SEMANTIC VIEW` |
| Cortex Agent | USAGE | `GRANT USAGE ON AGENT` |
| Cortex Search Service | USAGE | `GRANT USAGE ON CORTEX SEARCH SERVICE` |

## General Rules

**Grant privileges in this order (required for all AI products):**

> **⚠️ CRITICAL: This order is MANDATORY. Granting schema before database will fail with an error.**

1. **Database** → `GRANT USAGE ON DATABASE` (MUST be first)
2. **Schema** → `GRANT USAGE ON SCHEMA` (MUST be after database)
3. **Product** → Grant product-specific privileges (MUST be last)


```sql
   -- FIRST: Database
   GRANT USAGE ON DATABASE <database_name> TO SHARE <share_name>;
   
   -- SECOND: Schema
   GRANT USAGE ON SCHEMA <database_name>.<schema_name> TO SHARE <share_name>;

   -- LAST: Tables/Views/Semantic Views
   -- For tables:
   GRANT SELECT ON TABLE <database_name>.<schema_name>.<table> TO SHARE <share_name>;
   -- Or for all tables:
   GRANT SELECT ON ALL TABLES IN SCHEMA <database_name>.<schema_name> TO SHARE <share_name>;
   
   -- ⚠️ VIEWS: Must grant individually (bulk grant on views is restricted)
   GRANT SELECT ON VIEW <database_name>.<schema_name>.<view> TO SHARE <share_name>;
   -- NOTE: "GRANT SELECT ON ALL VIEWS" is NOT supported for shares
   
   -- ⚠️ SEMANTIC VIEWS: Use SELECT, REFERENCES (not USAGE)
   GRANT SELECT, REFERENCES ON SEMANTIC VIEW <database_name>.<schema_name>.<semantic_view> TO SHARE <share_name>;
   ```
   
   **⚠️ Finding Semantic Views**: Use `SHOW SEMANTIC VIEWS` (not `SHOW VIEWS`):
```sql
   SHOW SEMANTIC VIEWS IN SCHEMA <database_name>.<schema_name>;
   ```

**Why this order matters:**
- **Granting schema before database will fail** with error: "Share does not currently have a database"
- Consumers cannot access schema without database access
- Consumers cannot access products without schema access

**Important constraints:**
- Only **one database** can be granted USAGE to a share
- Within that database, multiple schemas and objects can be granted
- All objects in a share must belong to the same database

**⚠️ CRITICAL**: Only add objects the user explicitly specifies to the share. 
- Do NOT add INFORMATION_SCHEMA
- Do NOT add system schemas
- Do NOT add objects the user didn't request
- Ask user to confirm the exact list of objects before creating the share

## Product-Specific Rules

### Cortex Search Service (Cortex Knowledge Extension)

When a Cortex Search Service is shared on the Snowflake Marketplace, it becomes a **Cortex Knowledge Extension (CKE)**. CKEs can be used in RAG architectures to integrate licensed/proprietary content into Cortex AI applications.

Cortex Search Service is **self-contained**. Granting privilege to the service itself is sufficient.

```sql
GRANT USAGE ON CORTEX SEARCH SERVICE <database>.<schema>.<css> TO SHARE <share_name>;
```

No additional grants required.

### Semantic View

Semantic views **reference underlying tables**. For consumers to use the semantic view, you must also grant privileges on those tables.

```sql
-- 1. Grant privileges on the semantic view
GRANT SELECT ON SEMANTIC VIEW <database>.<schema>.<semantic_view> TO SHARE <share_name>;
GRANT REFERENCES ON SEMANTIC VIEW <database>.<schema>.<semantic_view> TO SHARE <share_name>;

-- 2. Grant privileges on underlying tables (REQUIRED)
GRANT SELECT ON TABLE <database>.<schema>.<table1> TO SHARE <share_name>;
GRANT SELECT ON TABLE <database>.<schema>.<table2> TO SHARE <share_name>;
-- ... repeat for all tables referenced by the semantic view
```

**To find referenced tables:** Check the semantic view definition for table references.

### Cortex Agent

Cortex Agents **use different tools** (semantic views, cortex search services, custom functions). For consumers to use the agent smoothly, appropriate privileges for **every tool** must be granted to the same share.

```sql
-- 1. Grant privileges on the agent
GRANT USAGE ON AGENT <database>.<schema>.<agent> TO SHARE <share_name>;

-- 2. Grant privileges on ALL tools used by the agent:

-- If agent uses a Semantic View:
GRANT SELECT ON SEMANTIC VIEW <database>.<schema>.<semantic_view> TO SHARE <share_name>;
GRANT REFERENCES ON SEMANTIC VIEW <database>.<schema>.<semantic_view> TO SHARE <share_name>;
GRANT SELECT ON TABLE <database>.<schema>.<underlying_table> TO SHARE <share_name>;

-- If agent uses a Cortex Search Service:
GRANT USAGE ON CORTEX SEARCH SERVICE <database>.<schema>.<css> TO SHARE <share_name>;

-- If agent uses custom functions/procedures:
GRANT USAGE ON FUNCTION <database>.<schema>.<function> TO SHARE <share_name>;
```

**To find agent tools:** Run `DESC AGENT <database>.<schema>.<agent>` to see the agent specification and identify all tools.

#### Cortex Agent Limitations

| Limitation | Description |
|------------|-------------|
| **Same database requirement** | All tools used by the agent must be in the **same database** as the agent itself. Agents with cross-database tool references cannot be granted to a share. |
| **Valid agent spec** | Agents with invalid specifications cannot be granted to a share. |

**If grant fails with "Agent cannot be granted" error:**
1. Check if any tools reference objects in different databases
2. Validate the agent specification with `DESC AGENT`

**Workaround for cross-database tools:** Recreate the agent and all its tools in the same database before granting to the share.

## Workflow

### Step 1: Identify AI Products to Attach

**Ask user:**
```
What AI product(s) would you like to attach to a share?

1. Provide object name(s) - e.g., "MYDB.SCHEMA.MY_SEMANTIC_VIEW"
2. List AI products in a schema first
```

**If listing needed:**
```sql
-- List semantic views
SHOW SEMANTIC VIEWS IN SCHEMA <database>.<schema>;

-- List agents
SHOW AGENTS IN SCHEMA <database>.<schema>;

-- List cortex search services
SHOW CORTEX SEARCH SERVICES IN SCHEMA <database>.<schema>;
```

### Step 2: Identify Share

**Ask user:**
```
Which existing share should receive these AI products?

Provide the share name.
```

**Validate the share exists:**
```sql
SHOW SHARES LIKE '<share_name>';
```

Confirm the share exists and the current role owns it (check `kind = 'OUTBOUND'`).

**Verify database/schema usage is already granted:**
```sql
SHOW GRANTS TO SHARE <share_name>;
```

If database/schema USAGE grants are missing, add them:
```sql
GRANT USAGE ON DATABASE <database> TO SHARE <share_name>;
GRANT USAGE ON SCHEMA <database>.<schema> TO SHARE <share_name>;
```

### Step 3: Attach AI Products

**Execute the appropriate grants for each product:**

```sql
-- Semantic View (requires both SELECT and REFERENCES)
GRANT SELECT ON SEMANTIC VIEW <database>.<schema>.<semantic_view> 
  TO SHARE <share_name>;
GRANT REFERENCES ON SEMANTIC VIEW <database>.<schema>.<semantic_view> 
  TO SHARE <share_name>;

-- Cortex Agent
GRANT USAGE ON AGENT <database>.<schema>.<agent> 
  TO SHARE <share_name>;

-- Cortex Search Service
GRANT USAGE ON CORTEX SEARCH SERVICE <database>.<schema>.<css> 
  TO SHARE <share_name>;
```

### Step 4: Add Consumer Accounts (Optional)

After attaching objects, add consumer accounts to the share:

```sql
-- Add accounts to the share
ALTER SHARE <share_name> ADD ACCOUNTS = <orgname.accountname1>, <orgname.accountname2>;

-- Remove accounts from the share
ALTER SHARE <share_name> REMOVE ACCOUNTS = <orgname.accountname>;

-- View current accounts
SHOW GRANTS OF SHARE <share_name>;
```

**Note:** Removing an account immediately revokes access. If re-added later, the consumer must re-create the database.

### Step 5: Verify Attachments

```sql
SHOW GRANTS TO SHARE <share_name>;
```

**Present summary:**
```
AI products attached to share <share_name>:
- [List of products with types]
```

## Known Limitations

### Cortex Agent Restrictions

Agents **cannot** be granted to a share if:
- Agent contains tools in different databases
- Agent has an invalid spec

**Workaround:** Create agent in same database as share objects.

### Semantic View Dependencies

If a semantic view references tables, those tables must also be granted to the share for the semantic view to function properly for consumers.

## Stopping Points

- **Step 1:** After listing products (user selects which to attach)
- **Step 2:** After identifying share (user confirms)
- **Step 4:** After adding consumer accounts (optional)
- **Step 5:** After verification (present summary)

## Quick Reference

### Attach Semantic View
```sql
-- Only if schema USAGE not already granted to the share:
GRANT USAGE ON SCHEMA mydb.myschema TO SHARE my_ai_share;

GRANT SELECT ON SEMANTIC VIEW mydb.myschema.my_semantic_view TO SHARE my_ai_share;
GRANT REFERENCES ON SEMANTIC VIEW mydb.myschema.my_semantic_view TO SHARE my_ai_share;
```

### Attach Full AI Stack
```sql
-- Semantic View (for Cortex Analyst) - requires SELECT and REFERENCES
GRANT SELECT ON SEMANTIC VIEW mydb.schema.analytics_view TO SHARE my_share;
GRANT REFERENCES ON SEMANTIC VIEW mydb.schema.analytics_view TO SHARE my_share;

-- Cortex Search Service (for RAG)
GRANT USAGE ON CORTEX SEARCH SERVICE mydb.schema.docs_search TO SHARE my_share;

-- Cortex Agent (orchestrates both)
GRANT USAGE ON AGENT mydb.schema.assistant_agent TO SHARE my_share;
```

## Output

- Share with attached AI products
- Verification of grants
- Summary of attachments

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Object does not exist` | Wrong name or missing permissions | Verify with SHOW command |
| `Insufficient privileges` | Not owner of share or object | Use ACCOUNTADMIN or object owner role |
| `Agent cannot be granted` | Cross-database tools or invalid spec | Recreate agent in same database, validate spec |
| `Database not granted` | Missing USAGE on database | Grant USAGE ON DATABASE first |
| `Cannot grant to share` | Object from different database | All objects must be in the same database as the share |
| `Share already has a database` | Attempting to add second database | Only one database per share is allowed |

## Access Control

| Action | Required Privilege |
|--------|-------------------|
| Grant objects to share | `OWNERSHIP` on share or object owner |
| Add/remove accounts | `OWNERSHIP` on share or `MANAGE SHARE TARGET` |
| View share grants | `OWNERSHIP` on share or ACCOUNTADMIN |

```sql
-- Grant MANAGE SHARE TARGET to manage consumer accounts
GRANT MANAGE SHARE TARGET ON ACCOUNT TO ROLE <role_name>;
```

=== billing/ ===
---
name: billing
description: "Org-level Snowflake billing in dollars/currency. Use for: dollar spend by service type, monthly spend trends, which services cost the most money, remaining balance, contract termination date, contract expiration date, contract start date, contract details, rate comparison, reconciliation. Consumption invoices: ODSS_INVOICE_DOCUMENTS, outstanding invoice, overdue invoice, unpaid invoice. Not for credit-based analytics (cost-intelligence) or warehouse DDL (warehouse). Key distinction: dollars/currency → billing, credits only → cost-intelligence."
---

# Billing Skill

Router skill for all Snowflake billing questions.

## Intent Detection

Identify the user's intent and **immediately load the matching sub-skill**:

| User Intent | Load |
|-------------|------|
| Spending, charges, monthly spend, **service costs in dollars**, **which services cost the most money**, balance, contract details, rates, reconciliation | `billing-queries/SKILL.md` |
| Consumption invoices: `ODSS_INVOICE_DOCUMENTS`, outstanding invoice, overdue invoice, unpaid invoice, what do I owe | `billing/odss-invoices/SKILL.md` |

> **Dollar vs credits routing**: If the question involves money/dollars/currency (even if it mentions "services" or "cost"), this is the correct skill. `cost-intelligence` handles credit-based analysis only.

## ⚠️ DO NOT PROCEED WITHOUT LOADING A SUB-SKILL

This router provides NO implementation details. All queries, workflows, and column guidance are in the sub-skills above.

> **Never use `SNOWFLAKE.ACCOUNT_USAGE.METERING_HISTORY` for any spending or cost question.** That view contains credits only — no dollar amounts. All dollar spend questions (including breakdowns by service type) use `SNOWFLAKE.ORGANIZATION_USAGE.USAGE_IN_CURRENCY_DAILY`. Load the sub-skill before writing any query.

=== cortex-agent/ ===
---
name: cortex-agent
description: "**[REQUIRED]** Use for ALL requests that mention agents: list, show, create, build, set up, edit, modify, update, delete, drop, remove, download, export, debug, fix, troubleshoot, optimize, improve, evaluate, analyze, commit, version, or alias a (Cortex) agent. Also use when user wants to: chat with, talk to, converse with, send messages to, have a conversation with an agent, or run a lite/objectless agent. Also use when request mentions: VERSION$, SHOW VERSIONS, commit LIVE version, set alias, set default version, versioned run, ALTER AGENT. Also use when debugging Snowflake Intelligence with a request ID (SI is powered by Cortex Agents). This is the REQUIRED entry point - even if the request seems simple. DO NOT attempt to manage (Cortex) agents manually - always invoke this skill first."
---

# Main

## When to Use

When a user wants to list, create, edit, delete, download, debug, evaluate, optimize, or chat with a (Cortex) agent. This is the entry point for all (Cortex) agent workflows.

## Setup

1. **Load** `agent-system-of-record/SKILL.md`: Required first step for all sessions.
2. **Load** `best-practices/SKILL.md`: Required to help maintain best practices for agent development.

⚠️ CRITICAL SAFETY INSTRUCTION: Before modifying an agent check with a user if it is a production agent and offer to create a clone. Ask user for the **fully qualified clone name** (`DATABASE.SCHEMA.CLONE_AGENT_NAME`) where they want the clone created. Follow `agent-system-of-record/SKILL.md` for clone creation. 

## Intent Detection

When user makes a request, detect their intent and load the appropriate sub-skill:

**CREATE Intent** - User wants to create/build a new agent:

- Trigger phrases: "create agent", "build agent", "set up agent", "new agent", "make an agent"
- **→ Load** `create-cortex-agent/SKILL.md`

**EDIT Intent** - User wants to edit/modify an existing agent (including modifying the LIVE version's spec):

- Trigger phrases: "edit agent", "modify agent", "update agent", "change agent instructions", "change agent", "update instructions", "modify live version", "modify specification", "MODIFY LIVE VERSION SET SPECIFICATION"
- **→ Load** `edit-cortex-agent/SKILL.md`

**ADHOC_TESTING Intent** - User wants to test questions interactively:

- Trigger phrases: "test questions", "try queries", "test agent", "run some questions"
- **→ Load** `adhoc-testing-for-cortex-agent/SKILL.md`

**EVALUATE Intent** - User wants to run formal evaluation or benchmark agent:

- Trigger phrases: "evaluate agent", "run evaluation", "benchmark", "measure accuracy", "check metrics", "evaluation results"
- **→ Load** `evaluate-cortex-agent/SKILL.md`

**DATASET Intent** - User wants to create or manage evaluation datasets:

- Trigger phrases: "create dataset", "build dataset", "evaluation dataset", "add questions to dataset", "curate dataset"
- **→ Load** `dataset-curation/SKILL.md`

**DEBUG_SINGLE_QUERY Intent** - User wants to debug specific query or agent request:

- Trigger phrases: "debug query", "why did this fail", "analyze response", "investigate issue", "debug request ID", "Snowflake Intelligence error with request ID", "SI request ID"
- **→ Load** `debug-single-query-for-cortex-agent/SKILL.md`

**DEBUG_EVAL Intent** - User wants to debug/investigate evaluation runs or results:

- Trigger phrases: "debug evaluation", "investigate agent evaluations", "eval timed out", "evaluation error", "missing eval metrics", "analyze low scores", "evaluation traces"
- **→ Load** `investigate-cortex-agent-evals/SKILL.md`

**OPTIMIZE Intent** - User wants to improve agent performance:

- Trigger phrases: "optimize", "improve accuracy", "production ready", "make it better"
- **→ Load** `optimize-cortex-agent/SKILL.md`

**DELETE Intent** - User wants to delete/drop/remove an agent:

- Trigger phrases: "delete agent", "drop agent", "remove agent", "destroy agent", "clean up agent"
- **→ Load** `delete-cortex-agent/SKILL.md`

**ACCESS Intent** - User wants to grant, revoke, or check access on an agent:

- Trigger phrases: "grant access", "revoke access", "share agent", "who has access", "show grants", "agent permissions"
- **→ Load** `create-cortex-agent/ACCESS_MANAGEMENT.md`

**LIST Intent** - User wants to list/show existing agents:

- Trigger phrases: "list agents", "show agents", "what agents exist", "find agents", "which agents"
- **→ Load** `list-cortex-agents/SKILL.md`

**DOWNLOAD Intent** - User wants to download/export an agent's configuration:

- Trigger phrases: "download agent", "export agent", "save agent config", "get agent spec", "dump agent", "back up agent"
- **→ Run** `get_agent_config.py` directly (no sub-skill needed):

```bash
uv run python scripts/get_agent_config.py --agent-name <AGENT_NAME> \
  --database <DATABASE> --schema <SCHEMA> --connection <CONNECTION> \
  --output <OUTPUT_PATH>
```

Ask the user for agent coordinates (database, schema, agent name) and where to save the file. Defaults to `./<AGENT_NAME>_spec.json` in the current directory.

**CHAT Intent** - User wants to chat with or talk to an agent:

- Trigger phrases: "chat with agent", "talk to agent", "converse with agent", "send message", "ask agent", "have a conversation", "multi-turn", "follow-up question", "lite agent", "objectless agent", "run lite agent"
- **→ Load** `chat-with-agent/SKILL.md`

**THREADS Intent** - User wants to manage conversation threads:

- Trigger phrases: "create thread", "list threads", "show threads", "describe thread", "view thread", "rename thread", "delete thread", "manage threads", "thread messages", "conversation history"
- **→ Load** `manage-agent-threads/SKILL.md`

**CHART_CUSTOMIZATION Intent** - User wants to customize chart appearance for an agent or semantic model:

- Trigger phrases: "set up chart customization", "brand colors for charts", "always use bar chart", "format y-axis as dollars", "set font", "chart theme", "dark background charts", "enforce chart style", "viz policy", "vega template for charts", "customize charts", "chart colors"
- **→ Load** `cortex-chart-customization/SKILL.md`

**VERSIONING Intent** - User wants to manage agent versions (commit, alias, default, run, list, drop):

- Trigger phrases: "version agent", "commit agent", "agent version", "show versions", "set alias", "set default version", "versioned run", "run specific version", "drop version", "ALTER AGENT COMMIT"
- Note: "modify live version" / "modify specification" → route to **EDIT Intent** instead
- **→ Load** `agent-versioning/SKILL.md`

## Core Capabilities

### Primary Workflows

#### 1. Create Cortex Agent Flow

**Load** `create-cortex-agent/SKILL.md` when user chooses CREATE mode.

#### 2. Edit Cortex Agent Flow

**Load** `edit-cortex-agent/SKILL.md` when user chooses EDIT mode.

Edit existing agent configuration - update instructions, add/remove tools, modify settings.

#### 3. Adhoc Testing Flow

**Load** `adhoc-testing-for-cortex-agent/SKILL.md` when user chooses ADHOC_TESTING mode.

Interactive testing of agent responses - explore behavior, debug issues, validate fixes.

#### 4. Evaluate Cortex Agent Flow

**Load** `evaluate-cortex-agent/SKILL.md` when user chooses EVALUATE mode.

Run formal evaluations using Snowflake's native Agent Evaluations with metrics:
- `answer_correctness` - Is the answer correct?
- `tool_selection_accuracy` - Did agent select the right tool?
- `logical_consistency` - Is response logically consistent?

#### 5. Dataset Curation Flow

**Load** `dataset-curation/SKILL.md` when user chooses DATASET mode.

Create and manage evaluation datasets - from scratch, from production data, or add to existing.

#### 6. Debug Single Query Flow

**Load** `debug-single-query-for-cortex-agent/SKILL.md` when user chooses DEBUG_SINGLE_QUERY mode.

#### 7. Optimize Cortex Agent Flow

**Load** `optimize-cortex-agent/SKILL.md` when user chooses OPTIMIZE mode.

Full optimization workflow: benchmark → identify issues → improve → validate.

#### 8. Delete Cortex Agent Flow

**Load** `delete-cortex-agent/SKILL.md` when user chooses DELETE mode.

Safely delete an agent: backup spec → production safety check → drop → verify.

#### 9. Agent Access Management Flow

**Load** `create-cortex-agent/ACCESS_MANAGEMENT.md` when user chooses ACCESS mode.

Grant, revoke, or inspect access grants on an agent.

#### 10. List Cortex Agents Flow

**Load** `list-cortex-agents/SKILL.md` when user chooses LIST mode.

List agents by scope: account, database, or schema.

#### 11. Download Agent Config Flow

Run `get_agent_config.py` directly when user chooses DOWNLOAD mode.

Download/export an agent's full specification JSON to a local file.

#### 12. Debug Evaluation Flow

**Load** `investigate-cortex-agent-evals/SKILL.md` when user chooses DEBUG_EVAL mode.

Debug evaluation failures, investigate task timeouts, analyze low scores, and troubleshoot AI Observability issues. Provides SQL queries using `GET_AI_EVALUATION_DATA` and `GET_AI_RECORD_TRACE` functions.

#### 13. Chat with Agent Flow

**Load** `chat-with-agent/SKILL.md` when user chooses CHAT mode.

Interactive conversation with an agent — supports object-based and lite (objectless) runs, single-turn and multi-turn conversations via server-managed threads.

#### 14. Manage Agent Threads Flow

**Load** `manage-agent-threads/SKILL.md` when user chooses THREADS mode.

Create, list, describe, update, and delete conversation threads for multi-turn agent interactions.

#### 15. Chart Customization Flow

**Load** `cortex-chart-customization/SKILL.md` when user chooses CHART_CUSTOMIZATION mode.

Generate a `<chart_customization>` block for an agent's orchestration instructions or a semantic model's custom instructions — covers brand colors, fonts, axis ranges, sort order, number formatting, chart types, and Vega templates.

#### 16. Agent Versioning Flow

**Load** `agent-versioning/SKILL.md` when user chooses VERSIONING mode.

Manage agent versions: create versioned agents, commit versions, set aliases, modify live specs, run specific versions via REST API, and troubleshoot versioning issues.

## Workflow Decision Tree

```
Start Session
    ↓
Run setup (Load `agent-system-of-record/SKILL.md` and `best-practices/SKILL.md`)
    ↓
Detect User Intent
    ↓
    ├─→ CREATE/BUILD → Load `create-cortex-agent/SKILL.md`
    │   (Triggers: "create agent", "build agent", "set up agent", "new agent")
    │
    ├─→ EDIT/MODIFY → Load `edit-cortex-agent/SKILL.md`
    │   (Triggers: "edit agent", "modify agent", "update agent", "change agent")
    │
    ├─→ ADHOC_TESTING → Load `adhoc-testing-for-cortex-agent/SKILL.md`
    │   (Triggers: "test questions", "try queries", "test agent")
    │
    ├─→ EVALUATE → Load `evaluate-cortex-agent/SKILL.md`
    │   (Triggers: "evaluate agent", "run evaluation", "benchmark", "metrics")
    │
    ├─→ DATASET → Load `dataset-curation/SKILL.md`
    │   (Triggers: "create dataset", "build dataset", "evaluation dataset")
    │
    ├─→ DEBUG_SINGLE_QUERY → Load `debug-single-query-for-cortex-agent/SKILL.md`
    │   (Triggers: "debug query", "why did this fail", "analyze response")
    │
    ├─→ OPTIMIZE → Load `optimize-cortex-agent/SKILL.md`
    │   (Triggers: "optimize", "improve accuracy", "production ready")
    │
    ├─→ DELETE → Load `delete-cortex-agent/SKILL.md`
    │   (Triggers: "delete agent", "drop agent", "remove agent")
    │   ⚠️ Backs up spec, requires explicit confirmation
    │
    ├─→ ACCESS → Load `create-cortex-agent/ACCESS_MANAGEMENT.md`
    │   (Triggers: "grant access", "revoke access", "share agent", "agent permissions")
    │
    ├─→ LIST → Load `list-cortex-agents/SKILL.md`
    │   (Triggers: "list agents", "show agents", "what agents exist")
    │
    ├─→ DOWNLOAD → Run `get_agent_config.py`
    │   (Triggers: "download agent", "export agent", "save agent config")
    │
    ├─→ CHAT → Load `chat-with-agent/SKILL.md`
    │   (Triggers: "chat with agent", "talk to agent", "lite agent", "multi-turn")
    │
    ├─→ THREADS → Load `manage-agent-threads/SKILL.md`
    │   (Triggers: "create thread", "list threads", "manage threads", "delete thread")
    │
    ├─→ CHART_CUSTOMIZATION → Load `cortex-chart-customization/SKILL.md`
    │   (Triggers: "chart customization", "brand colors for charts", "chart theme", "viz policy", "vega template")
    │
    ├─→ VERSIONING → Load `agent-versioning/SKILL.md`
    │   (Triggers: "version agent", "commit agent", "show versions", "set alias", "versioned run")
    │
    └─→ DEBUG_EVAL → Load `investigate-cortex-agent-evals/SKILL.md`
        (Triggers: "debug evaluation", "eval failure", "eval timed out", "low scores")
```

## Typical User Journeys

### Journey 1: New Agent Development
```
CREATE → ADHOC_TESTING → DATASET → EVALUATE → OPTIMIZE
```

### Journey 2: Production Agent Improvement
```
EVALUATE (baseline) → OPTIMIZE → EVALUATE (validate)
```

### Journey 3: Quick Edit
```
EDIT → ADHOC_TESTING (verify changes)
```

### Journey 4: Quick Testing
```
ADHOC_TESTING → DEBUG_SINGLE_QUERY (if issues found)
```

### Journey 5: Formal Benchmarking
```
DATASET → EVALUATE → compare results
```

### Journey 6: Agent Cleanup
```
DELETE (with production safety check + backup if prod)
```

### Journey 7: Discovery
```
LIST (show all agents in account/database/schema)
```

### Journey 8: Export
```
DOWNLOAD (save agent spec to local file)
```

### Journey 9: Interactive Chat
```
CHAT (single-turn or multi-turn conversation with deployed or lite agent)
```

### Journey 10: Post-Creation Chat
```
CREATE → CHAT (verify agent works by chatting with it)
```

### Journey 11: Version Management
```
EDIT → VERSIONING (commit version, set alias, set default) → ADHOC_TESTING (verify via versioned run)
```

## Rules

### Running Scripts

When running any scripts in any of the above skills, make sure to do all of the following:

1. **Check if `uv` is installed** by running `uv --version`. If it's not installed, prompt the user to install it using one of these methods:
   - `curl -LsSf https://astral.sh/uv/install.sh | sh` (recommended)
   - `brew install uv` (macOS)
   - `pip install uv`
2. When running python scripts, use `uv run --project <DIRECTORY THIS SKILL.md file is in> python <DIRECTORY THIS SKILL.md file is in>/scripts/script_name.py` to run them.
3. Do not `cd` into another directory to run them, but run them from whatever directory you're already in.
   WHY: This maintains your current working context and prevents path confusion. When using `uv run --project`, you must provide absolute paths for BOTH the --project flag AND the script itself.
4. Just run the script the way the skill says. Do not question it by running `--help` or reading the script unless the script fails when run as intended.

#### Common Mistakes When Running Scripts

1. ❌ WRONG: `uv run --project <DIRECTORY THIS SKILL.md file is in> python scripts/test_agent.py ...`
   (Relative path to script will fail)
2. ❌ WRONG: `cd <DIRECTORY THIS SKILL.md file is in> && uv run python scripts/test_agent.py ...`
   (Violates the "don't cd" rule)
3. ✅ CORRECT: `uv run --project <DIRECTORY THIS SKILL.md file is in> python <DIRECTORY THIS SKILL.md file is in>/scripts/test_agent.py ...`
   (Use the same base directory for both --project and the script path)

### System of Record

**Load** `agent-system-of-record/SKILL.md`.

=== cortex-ai-function-studio/ ===
---
name: cortex-ai-function-studio
description: "Create, evaluate, and optimize custom AI functions using Snowflake Cortex AI Complete. Also helps users apply built-in Cortex AI functions (AI_CLASSIFY, AI_EXTRACT, AI_FILTER, AI_COMPLETE, AI_SENTIMENT, AI_SUMMARIZE_AGG, AI_AGG, AI_TRANSLATE, AI_EMBED, AI_PARSE_DOCUMENT, AI_REDACT, AI_TRANSCRIBE, AI_SIMILARITY) and onboard research-preview bring-your-own-model SPCS services. Use when: building LLM-powered functions, evaluating AI function performance, tuning prompts, selecting models, checking async job status, onboarding BYOM/SPCS model inference, classifying content, extracting from text, filtering rows by condition, summarizing, sentiment analysis, analyzing unstructured data with AI, exploring AI function options, using cortex AI functions. Triggers: ai function builder, custom ai function, user defined ai function, build my own llm function, evaluate ai function, tune ai function, optimize ai function, BYOM, bring your own model, model service, SPCS inference, Hugging Face model, demo ai function, resume ai function job, image classification, document analysis, multimodal ai function, AI_CLASSIFY, AI_EXTRACT, AI_FILTER, AI_COMPLETE, AI_SENTIMENT, AI_SUMMARIZE_AGG, AI_TRANSLATE, AI_EMBED, AI_PARSE_DOCUMENT, AI_REDACT, AI_SIMILARITY, classify text, extract from text, filter rows, summarize text, analyze data with AI, explore AI functions, unstructured data, what AI functions, analyze my data, cortex function, which AI function, built-in AI function."
---
<!-- Copyright (c) 2026 Snowflake Inc. All rights reserved.
     Licensed under the Snowflake Skills License. See LICENSE file. -->

# Cortex AI Function Studio

**Skill Version:** 1.0.0

Build, evaluate, and optimize AI functions powered by Snowflake Cortex AI Complete.

## When to Load

Load when user wants to work with AI functions — either built-in Cortex AI functions or custom AI function workflows: "custom ai function", "build llm function", "evaluate ai function", "optimize prompt", "tune ai function", "AI_CLASSIFY", "AI_EXTRACT", "classify", "extract from text", "which AI function", "analyze data with AI", "explore AI functions", "unstructured data analysis".

**If the user's message already contains a clear intent** (e.g., "create a custom function", "evaluate my function", "check status", or names a specific function like AI_CLASSIFY), skip this welcome and go directly to Step 1.

**If the user enters with no specific request** (bare `/cortex-ai-function-studio`, or generic prompt without a clear workflow), render the following message **VERBATIM** — do NOT paraphrase, shorten, or omit sections. Then WAIT for the user to choose. Do NOT skip ahead to prerequisites or assume CREATE:
```
Welcome to the Cortex AI Function Studio — your one-stop shop for AI-powered analytics on unstructured data in Snowflake.

I can help you work with Snowflake's AI functions — whether you want to use a **built-in** function (AI_CLASSIFY, AI_EXTRACT, AI_FILTER, AI_TRANSLATE, etc.) for immediate results, build a **custom** AI function tailored to your domain, or onboard a research-preview BYOM/SPCS model service.

For custom functions, the intended workflow is create → evaluate → optimize. During creation, you choose how to build: Direct (simple AI_COMPLETE call) or [research preview] Agent Research (I research and propose approaches with SQL pre/post-processing — you can also specify your own strategy). After building, evaluate against labeled data, then optimize with automated function body optimization and model selection.
If you're new to custom functions, start with a demo to see a worked example end-to-end.

What would you like to do?

1. Create — Build a new Custom AI Function (start here if you haven’t created one before)
2. Evaluate — Evaluate an existing Custom AI Function's performance
3. Optimize — Tune prompts and compare models for an existing Custom AI Function for better cost-quality tradeoff
4. Demo — Interactive walkthrough with example use cases of custom AI Function
5. Check Status — Check on an async evaluation or optimization job on a Custom AI Function
6. Built-in AI Functions — Use a native Snowflake built-in AI Function (no setup, immediate SQL)
**Note:** Evaluate and Optimize only work with Custom AI Functions today. They do not apply to built-in AI Functions yet.

Pick a number or describe what you're working on.
```

## Agent Execution Rules

**After a `⚠️ STOP` point is cleared by the user, execute all subsequent tool calls (stored procedure calls, SQL, uv scripts) WITHOUT re-asking for confirmation until the next `⚠️ STOP` point.** The skill-level confirmation IS the authorization to proceed.

Do NOT:
- Ask "shall I proceed?" immediately before running a command the user just approved
- Ask "OK to run this SQL?" after the user confirmed the evaluation/optimization settings
- Re-confirm tool calls that are direct consequences of an already-approved action
- Ask the user to choose between sync and async execution — default to sync
- Use the `SNOWFLAKE.CORTEX.*` namespace for built-in AI functions — it is **deprecated**. Always use `AI_CLASSIFY`, `AI_EXTRACT`, `AI_SENTIMENT`, `AI_TRANSLATE`, `AI_COMPLETE`, etc. directly (no prefix). If a user references `SNOWFLAKE.CORTEX.CLASSIFY(...)` or similar, correct them to the `AI_*` equivalent.

These rules apply to all sub-skills (create, evaluate, optimize, BYOM, demos).

### Snowsight Environment Rules

**If `environment == snowsight`** (detected in Step 0 prerequisites), these rules apply to ALL sub-skills:

1. **Use stored procedures or documented SQL, not Python scripts.** Execute `CALL SNOWFLAKE.CORTEX.<procedure>(...)` or BYOM SQL DDL/session statements via the `execute_sql` tool. Do NOT run `uv run`, `!python`, or any Python scripts, except for the BYOM notebook-based Model Registry import fallback explicitly documented in `byom/SKILL.md` Step 4 after `SYSTEM$IMPORT_MODEL` fails. Each sub-skill's `**If environment == snowsight:**` branch provides the exact CALL syntax.

2. **Execute stored procedure CALLs via `execute_sql`, not in notebook cells.** The `execute_sql` tool runs SQL in the agent's own execution context. Notebooks are for display only (results, charts, Try It examples), except for the BYOM notebook-based Model Registry import fallback explicitly documented in `byom/SKILL.md` Step 4 after `SYSTEM$IMPORT_MODEL` fails.

3. **Always set database/schema context before CALL statements.** The `execute_sql` session may not have a current database/schema. Prepend `USE {database}.{schema};` before every `CALL SNOWFLAKE.CORTEX.<procedure>(...)` to avoid `Cannot perform CREATE ... This session does not have a current database` errors.

4. **Create and use a notebook for visual output.** Load `references/snowsight/core.md` when entering any sub-skill workflow (loaded once at prerequisites time). Per-workflow notebook recipes are in `references/snowsight/{create,evaluate,optimize,synthetic_data,custom_metrics}.md`. The notebook is required for example calls (Create), evaluation results (Evaluate), optimization charts (Optimize), and data previews (Synthetic Data). Do NOT complete workflows with chat-only output.

5. **Do NOT write to existing `.sql` files or Snowsight SQL worksheets.** Always create a `.ipynb` notebook file for the function.

6. **Do NOT query internal experiment stage files.** Never access `candidates.json.gz`, `gepa_state.bin.gz`, `run_dir/`, or other internal artifacts via `snow://experiment/...` paths for retrieving function bodies or optimization state. Use ONLY `SHOW RUN METRICS` and `SHOW RUN PARAMETERS` to retrieve optimization/evaluation results. SnowURL paths are only valid for per-row eval detail files (`seed_eval_detail.json`, `best_eval_detail.json`).

7. **Procedure names are EXACT — do NOT hallucinate alternatives.** The only valid CAIFS stored procedures are:
   - `SNOWFLAKE.CORTEX.CREATE_AI_FUNCTION` (9 positional params) — do NOT use `CREATE FUNCTION ... LANGUAGE CORTEX_AI` DDL
   - `SNOWFLAKE.CORTEX.EVALUATE_AI_FUNCTION` (12 positional params) — do NOT use `AI_FUNC_EVALUATE` or named `=>` params
   - `SNOWFLAKE.CORTEX.OPTIMIZE_AI_FUNCTION` (18 positional params; inside a Task for async, direct CALL for sync/demo) — do NOT use `OBJECT_CONSTRUCT(...)` single-param syntax

	   All parameters are **positional**. Never use named parameters (`param_name => value`). You MUST read the sub-skill file to get the exact parameter order — do NOT guess from training data. BYOM uses documented SQL object/service operations and `AI_COMPLETE('<service_name>', ...)`; do not invent BYOM-specific `SNOWFLAKE.CORTEX.*` procedures.

**Handling "Object already exists" errors:** All `CREATE` statements (FUNCTION, TABLE, VIEW, STAGE) use plain `CREATE` (not `CREATE OR REPLACE`). If any `CREATE` fails with `SQL compilation error: Object '{name}' already exists`, prompt the user:
```
That object name already exists. Would you like to:
1. **Choose a different name** — e.g., {OBJECT_NAME}_{YYYYMMDD_HHMMSS} to avoid clashes
2. **Drop and recreate** — Drop the existing object first, then create the new one
```
If option 1, suggest a timestamped variant and re-run. If option 2, run the appropriate `DROP ... IF EXISTS` then retry.

## Workflow

### Step 0: Check Prerequisites

**⚠️ STOP**: Before proceeding, verify all prerequisites by loading `references/prerequisites.md`. This checks the Snowflake connection, tool installation, collects the target database/schema, and verifies the user's role has the necessary privileges.

**Snowsight environments**: `prerequisites.md` will mandate loading `references/snowsight/core.md` next — read it before any `write`/`notebook_action` call to avoid silent kernel timeouts and invalid cell payloads.

If any prerequisites or privileges are missing, follow the instructions in the prerequisites file. Do not proceed until all checks pass.

### Step 1: Detect Intent

| Intent | Triggers | Route |
|--------|----------|-------|
| CREATE | "create", "build", "new" + custom/ai/llm function | `create/SKILL.md` |
| EVALUATE | "evaluate", "test", "measure", "score" | `evaluate/SKILL.md` |
| OPTIMIZE | "optimize", "tune", "improve" | `optimize/SKILL.md` |
| BYOM | "BYOM", "bring your own model", "model service", "SPCS inference", "Hugging Face model" | `byom/SKILL.md` |
| DEMO | "demo", "example", "walkthrough", "show me", "how does this work" | `demos/SKILL.md` |
| CHECK_STATUS | "check status", "run_id", "ai_func_eval_", "ai_func_opt_", "is my job done", "resume", "pick up" | `references/async_status.md` |
| BUILTIN_FUNCTION | explicit function name (AI_CLASSIFY, AI_EXTRACT, etc.), "use built-in", "which AI function" | `built-in-ai-functions/SKILL.md` |
| EXPLORE | task-oriented request (classify, extract, filter, summarize, sentiment), "analyze data with AI", "explore AI functions", "unstructured data", generic data analysis — without explicit function name or studio keyword | See Explore below |

**Routing priority (highest to lowest):**
1. **CREATE / EVALUATE / OPTIMIZE / DEMO / CHECK_STATUS** — If the user explicitly mentions these workflows (e.g., "create a custom function", "evaluate my function", "optimize", "demo"), route there. These always win.
2. **BUILTIN_FUNCTION** — If the user names a specific built-in function (AI_CLASSIFY, AI_EXTRACT, etc.) or says "use built-in" / "which AI function", route there. Only override with CREATE if the user also explicitly says "custom function", "my own", or expresses accuracy dissatisfaction.
3. **EXPLORE** — Fallback for task-oriented requests ("classify my tickets", "summarize feedback") or generic discovery ("analyze data with AI") that don't match the above.

EXPLORE never takes priority over an explicit workflow or function request. When no clear intent at all, show the options menu from "When to Load" and WAIT.

### Step 2: Route

**⚠️ MANDATORY**: You MUST read the sub-skill file before responding. The sub-skill contains the actual command syntax, parameter formats, and execution details. Do NOT generate commands, SQL, or CLI invocations from memory — always read the sub-skill first. **If you skip this read, you WILL produce hallucinated procedure names and incorrect parameter signatures that do not exist in Snowflake.**

**If CREATE:** Read `create/SKILL.md`. (In Snowsight, deployment uses `CALL SNOWFLAKE.CORTEX.CREATE_AI_FUNCTION(...)` with **9 positional params**. Do NOT use raw `CREATE FUNCTION` DDL or `LANGUAGE CORTEX_AI` — these are wrong. `create/SKILL.md` Step 9 will direct you to read `references/snowsight/create.md` for the exact template.)

**If EVALUATE:** Read `evaluate/SKILL.md` before responding. (In Snowsight, runs via `CALL SNOWFLAKE.CORTEX.EVALUATE_AI_FUNCTION(...)` with **12 positional params**. Do NOT use `AI_FUNC_EVALUATE`, `AI_FUNCTION_EVALUATE`, or named `=>` parameters — these do not exist.)

**If OPTIMIZE:** Read `optimize/SKILL.md` before responding. (In Snowsight, runs via `CALL SNOWFLAKE.CORTEX.OPTIMIZE_AI_FUNCTION(...)` with **18 positional params**. For `budget == demo`, call directly (sync); otherwise wrap in a `CREATE TASK` (async). Do NOT use `OBJECT_CONSTRUCT(...)` single-param syntax or named parameters — these do not exist.)

**If BYOM:** Read `byom/SKILL.md` before responding. BYOM is a research-preview onboarding path layered into model selection and optimization: inspect GPU compute pools, shortlist verified Hugging Face models, import/deploy the selected model to Snowflake Model Registry/SPCS if needed, then expose it through `AI_COMPLETE('<db>.<schema>.<service>', ...)`. Do NOT fabricate unavailable system functions, model registries, image names, or service specs; use verified references and ask for missing account-specific values.

**If DEMO:** Read `demos/SKILL.md` before responding.

**If CHECK_STATUS:** Read `references/async_status.md` with the run_id from the user's message (if provided).

**If BUILTIN_FUNCTION:** Read `built-in-ai-functions/SKILL.md` before responding. The user wants to use a specific built-in function — help them directly.

**If EXPLORE:** Follow the explore logic below to present options.

**If unclear**, display the options menu from "When to Load" and wait for user choice.

### Explore Logic

When the user describes a task (e.g., "classify support tickets"), wants to explore AI function options (e.g., "analyze my data with AI"), or arrives from the UI landing page:

1. **Understand the use case.** If unclear, ask what data they have and what they want to accomplish.
2. **Check if custom is even applicable.** Custom AI functions are built on AI_COMPLETE and do NOT support embeddings (AI_EMBED), vector similarity (AI_SIMILARITY), aggregation (AI_SUMMARIZE_AGG, AI_AGG), transcription (AI_TRANSCRIBE), or document parsing (AI_PARSE_DOCUMENT). If the task maps to one of these, tell the user a built-in function handles it and route to BUILTIN_FUNCTION — custom is not an alternative.
3. **Present two paths and stop.** Your response MUST be short (3-5 sentences max). Do NOT exhaustively list function names, produce tables of functions, or generate SQL. Do NOT editorialize about which path is "best" or "recommended" — present both neutrally and let the user decide. Just say:
   - Built-in AI functions: no setup, immediate SQL, handles common patterns
   - Custom AI functions: higher accuracy on domain-specific tasks, control over cost/quality (model selection, prompt optimization)
   - Ask which path they'd like to explore
4. **Wait for the user to choose.** Do NOT continue until they respond. Do NOT load sub-skills, generate SQL, or elaborate further.

After the user picks, route to BUILTIN_FUNCTION or CREATE as appropriate.

## Capabilities

- **Create**: Two modes — Direct (simple AI_COMPLETE) or [research preview] Agent Research (research + propose SQL UDF structures, with option to specify your own)
- **Evaluate**: Measure with pre-built or custom metrics via SQL
- **Optimize**: Improve functions using function body optimization (modifies prompts, model references, and SQL pre/post-processing) and perform cost/quality model comparison. Pass ALL models in a single call — the optimizer runs them concurrently. Do NOT make separate calls per model.
- **BYOM**: Research-preview onboarding for task-specific open-source/Hugging Face models served through Snowpark Container Services and compared on the CAIFS cost/quality Pareto frontier.
- **Demo**: Interactive walkthroughs with example use cases
- **Data Preparation**: Prepare train/test data (`references/data_preparation.md`)
- **Synthetic Data**: Generate data for evaluation and optimization (`synthetic-data/SKILL.md`)
- **Pseudo Labels**: Label input-only tables using strong-model inference and reuse for evaluate/optimize (`synthetic-data/SKILL.md`)

## Data Suggestions

| Workflow | Recommended Rows |
|----------|------------------|
| Evaluate | 20–50 rows       |
| Optimize | 20–50 rows       |

> These sizes are enough for fast iteration. Larger datasets (200+ rows) improve statistical signal but are not required to get started.

## Stopping Points

- ✋ Step 0: After prerequisite check fails
- ✋ Step 1-2: If intent unclear, ask user to select workflow

Each sub-skill has its own stopping points documented within.

## Output

Depends on workflow selected:
- **Create**: AI function created in Snowflake via stored procedure
- **Evaluate**: Performance score and detailed results table
- **Optimize**: Optimized function with improved performance
- **Demo**: Completed walkthrough with demo objects (cleanable)

=== cortex-code-guide/ ===
---
name: cortex-code-guide
description: >
  Load this skill when users ask about Cortex Code capabilities, CoCo features, available commands, tools, settings,
  shortcuts, CLI subcommands, how to use Cortex Code, what CoCo can do, CoCo help, CoCo reference, Cortex Code CLI
  guide, available slash commands, keybindings, keyboard shortcuts, configuration options, environment variables,
  agent modes, special syntax triggers, bundled agents, MCP setup, skills management, hooks, scheduling, dbt tools,
  Snowflake connections, SQL execution, semantic views, Cortex Agents, notebook support, background agents, team mode,
  plan mode, memory tool, cron scheduling, data diff, tgrep, or any question about Cortex Code functionality.
---

# Cortex Code (CoCo) — Comprehensive Reference Guide

## Quick Start

| Action | How |
|--------|-----|
| Get help | `/help` or `/h` or `/?` |
| Open settings | `/settings` |
| Manage connections | `/connections` or `/conn` |
| Run a SQL query | `/sql <query>` or just ask in natural language |
| Start a new session | `/new` |
| Resume a session | `/resume` or `/r` |
| Update CoCo | `/update` |
| View current config | `/status` |
| Open docs in browser | `/docs` |

---

## Special Input Syntax

These trigger characters have special meaning in the input bar:

| Trigger | Name | Description |
|---------|------|-------------|
| `/` | Slash Command | Invoke a slash command |
| `!` | Bash Terminal | Enter terminal mode (run a bash command) |
| `@` | File Reference | Reference a file in the prompt |
| `@{` | File Injection | Inject file contents into the prompt |
| `#` | Table Trigger | Reference a table |
| `$` | Skill Trigger | Reference a skill |
| `%` | Agent Trigger | Mention a Cortex Agent |

---

## Slash Commands

### Navigation & Session Management

| Command | Aliases | Description |
|---------|---------|-------------|
| `/new` | | Start a new session (optionally with a name) |
| `/resume` | `/r`, `/sessions` | Resume a previous session |
| `/fork` | | Fork into a new session (optionally `/fork <session-id \| artifact-id \| share-url>`) |
| `/rename` | `/name` | Rename the current session |
| `/clear` | `/cls` | Clear screen (optionally keep last N exchanges) |
| `/compact` | | Clear conversation history but keep a summary in context. Optional: `/compact [instructions]` |
| `/rewind` | | Rewind the conversation by N user messages, or open interactive selector |
| `/quit` | `/q`, `/exit`, `quit`, `exit` | Exit the CLI with session summary |
| `/wipe-session` | | Purge session transcript and exit |
| `/recap` | | Generate a session recap now |
| `/qq` | `/quick`, `/btw` | Quick question — side conversation |

### SQL & Data

| Command | Aliases | Description |
|---------|---------|-------------|
| `/sql` | | Execute SQL query directly (use `--limit N` to show more rows) |
| `/sql-readonly` | | Toggle the built-in SQL tool between read-only and write modes |
| `/table` | `/csv` | Open interactive table viewer for SQL results or CSV files |
| `/copy-table` | `/cpt` | Copy a table to clipboard (Enter to copy, ↑↓ to cycle tables) |
| `/connections` | `/conn` | Manage Snowflake connections in fullscreen |
| `/workspace` | | Browse and switch the mounted Snowflake workspace |
| `/doctor` | `/diag` | Diagnose Snowflake connection issues |

### dbt & Lineage

| Command | Aliases | Description |
|---------|---------|-------------|
| `/fdbt` | | Execute fdbt command for fast DBT project analysis |
| `/lineage` | | Show dbt model lineage in fullscreen DAG view |

### Agents & Teams

| Command | Aliases | Description |
|---------|---------|-------------|
| `/agents` | | View and manage sub-agents |
| `/background-agent` | `/bg` | Launch a background agent to work on a task while you continue chatting |
| `/swarm` | `/mission-control` | Open swarm mission control with this session |
| `/team` | | Enable teams mode (use parallel teammates) |
| `/team-off` | | Disable teams mode |
| `/share` | | Share the current conversation via a Snowsight link |

### Skills & Plugins

| Command | Aliases | Description |
|---------|---------|-------------|
| `/skill` | `/skills` | Manage skills — view, add, remove, sync, browse catalog |
| `/plugin` | `/plugins` | Manage plugins |
| `/reload-plugins` | | Reload plugins, plugin skills, agents, hooks, and MCP servers |
| `/mcp` | | Manage MCP servers |
| `/rules` | | View, edit, or create instruction files |

### Scheduling

| Command | Aliases | Description |
|---------|---------|-------------|
| `/loop` | `/cron` | Schedule recurring tasks (cron-style scheduling) |
| `/automation` | `/automations` | Schedule a Cortex Code automation (recurring agent task run) |

### Modes & Permissions

| Command | Aliases | Description |
|---------|---------|-------------|
| `/plan` | | Enable plan mode (present plan before execution) |
| `/plan-off` | | Disable plan mode |
| `/auto-accept-plan` | | Enable auto-accept plans (auto-approve plan requests) |
| `/auto-accept-plan-off` | | Disable auto-accept plans |
| `/bypass` | | Enable bypass safeguards mode (auto-approve all tool calls) |
| `/bypass-off` | | Disable bypass safeguards mode |
| `/permissions` | | Manage workspace trust and tool permission rules |

### UI & Display

| Command | Aliases | Description |
|---------|---------|-------------|
| `/theme` | `/themes` | Select color theme (dark/light/pro) |
| `/model` | | Show and select available models |
| `/context` | | View current context window breakdown |
| `/copy` | `/cp` | Copy last response to clipboard as rich text (`--md` for markdown, `--text` for plain text) |
| `/diff` | `/changes`, `/review` | Review git changes in fullscreen (use `--staged` or `--cached` for staged changes) |
| `/tts` | `/speak` | Toggle text-to-speech output |
| `/voice-setup` | | Set up voice input (STT) and text-to-speech (TTS) |

### Configuration & Maintenance

| Command | Aliases | Description |
|---------|---------|-------------|
| `/settings` | `/preferences`, `/prefs` | Open settings page or modify specific settings |
| `/status` | | Show current configuration |
| `/update` | | Update Cortex Code to the latest version |
| `/feedback` | | Create a feedback bundle for debugging and support |
| `/clear-cache` | | Clear application caches (debug logging, table cache, etc.) |
| `/hooks` | | View and test configured hooks |
| `/profile` | | Manage profiles — reusable configurations with custom system prompts and settings |
| `/secrets` | `/secret` | Manage secrets |
| `/add-dir` | | Add an additional working directory |
| `/goal` | | Set or view the goal for a long-running task |
| `/index` | | Build or refresh search indexes (tgrep semantic search and/or instant-grep regex search). Use `--rebuild` to force a refresh. |
| `/tgrep` | | Enable, disable, or show status of tgrep (semantic code search). Subcommands: `on \| off \| status` |
| `/commands` | `/cmds` | Manage custom commands — view, copy, move between locations |
| `/sh` | | Execute shell command directly or enter terminal mode |
| `/shop` | `/store` | Open the Snowflake store in browser |
| `/docs` | | Open Cortex Code CLI documentation in browser |
| `/setup-jupyter` | | Set up Jupyter notebook environment with required packages |
| `/ssh` | `/remote` | SSH into a remote server and continue this session there |
| `/airflow` | | Configure Airflow instances |
| `/port-forward` | `/pf` | Forward a host port to the sandbox VM (requires running sandbox) |
| `/worktree` | | Manage git worktrees (create, list, switch, delete) |
| `/developer` | `/dev` | Developer menu for system prompt override |

### Plugin Subcommands (`/plugin`)

| Subcommand | Description |
|------------|-------------|
| `list` | List discovered and installed plugins |
| `info` | Show details for a plugin |

---

## Tools

### File & Code Operations

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `read` | Reads file content with line numbers. Supports text, images (PNG/JPG/JPEG/GIF/WebP), PDFs, and Jupyter notebooks. For PDFs, offset/limit are page numbers (0-based). | `file_path` (string, required), `offset` (number), `limit` (number) |
| `write` | Writes content to a file. Creates the file and parent directories if needed, or overwrites if it exists. | `file_path` (string, required), `content` (string, required) |
| `edit` | Performs a search-and-replace on a file. `old_string` must appear exactly once (or once within the `after` scope). | `file_path` (string, required), `old_string` (string, required), `new_string` (string, required), `after` (string) |
| `apply_patch` | Edit files using a structured diff format. Supports Add File, Delete File, and Update File (with optional rename) operations. | `input` (string, required) |
| `glob` | Finds files matching a glob pattern. Returns matching file paths. | `pattern` (string, required), `path` (string) |
| `grep` | Searches for a regex pattern in files. Returns matching lines with file paths and line numbers. | `pattern` (string, required), `path` (string), `include` (string), `head_limit` (number) |
| `tgrep` | Semantic and keyword code search over the project. Modes: `semantic` (default), `keyword`, `hybrid`. Index is built in the background on first use. | `query` (string, required), `mode` (string), `max_results` (integer), `compact` (boolean), `reindex` (boolean), `directory` (string) |

### Shell & Process

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `bash` | Executes a bash command and returns output. | `command` (string, required), `description` (string), `timeout_ms` (number), `run_in_background` (boolean) |
| `bash_output` | Retrieve output from a running or completed background bash shell started with `run_in_background=true`. | `bash_id` (string, required), `filter` (string), `wait` (boolean), `timeout_ms` (number) |
| `kill_shell` | Kill a running background bash shell by its ID. | `shell_id` (string, required) |
| `find_custom_python_environment` | Find custom Python environments (UV/Poetry/venv) in a directory and subdirectories. Returns the appropriate command to run Python for each environment found. | `working_dir` (string, required) |

### Planning & Task Management

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `enter_plan_mode` | Request to enter plan mode for careful task planning. Use when a task is complex, risky, involves multiple files, or has architectural implications. Do not use for simple or single-file tasks. | `reason` (string, required) |
| `exit_plan_mode` | Present a plan to the user and exit plan mode. Call when research is complete and ready for user confirmation. | `plan` (string, required), `question_to_clarify_with_user` (string), `team_mode` (boolean) |
| `system_todo_write` | Updates the local todo store for UI rendering. | `todos` (array, required) |
| `task_create` | Create a new task to track work. Tasks have a subject, description, and optional active_form. | `subject` (string, required), `description` (string, required), `active_form` (string) |
| `task_get` | Get full details of a specific task by ID. | `task_id` (string, required) |
| `task_list` | List all tasks with status, owner, and dependencies. | _(no parameters)_ |
| `task_update` | Update a task's fields: status, subject, description, owner, active_form, or dependency relationships. Use status `deleted` to remove a task. | `task_id` (string, required), `status` (string), `subject` (string), `description` (string), `active_form` (string), `owner` (string), `add_blocks` (array), `add_blocked_by` (array) |
| `task_stats` | Summarize queue status for the active scope, including counts by status and stale leases. | `team_name` (string), `all_sessions` (boolean), `stale_after_minutes` (integer) |
| `task_next` | Scheduler-facing claim call for shared-pool workers. Claims the next ready task and returns full details. | `owner` (string), `task_id` (string), `team_name` (string), `allow_unsafe_claim` (boolean) |
| `task_complete` | Mark a leased task as completed through the scheduler. Preferred completion path for shared-pool workers. | `task_id` (string, required), `result` (string) |
| `task_fail` | Report task failure. By default requeues as pending; set `requeue=false` to pause instead. | `task_id` (string, required), `error` (string, required), `requeue` (boolean) |
| `task_heartbeat` | Renew the current lease on an in-progress task to prevent the scheduler from requeuing active work. | `task_id` (string, required), `owner` (string) |
| `task_claim` | Atomically claim the next ready unowned task, or a specific ready task, for a named worker. | `task_id` (string), `owner` (string), `team_name` (string), `allow_unsafe_claim` (boolean) |

### Multi-Agent & Teams

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `task` | Launch a new agent to handle complex, multi-step tasks autonomously. Supports background execution, worktree isolation, and agent resumption. | `subagent_type` (string, required), `description` (string, required), `prompt` (string, required), `name` (string), `team_name` (string), `resume` (string), `model` (string), `run_in_background` (boolean), `worktree_isolation` (boolean) |
| `kill_agent` | Terminates a running background agent by its ID. | `agent_id` (string, required) |
| `send_message` | Send a message to another agent or to the main conversation for inter-agent communication in multi-agent workflows. | `recipient` (string, required), `content` (string, required), `summary` (string) |
| `team_create` | Create a new team to coordinate multiple agents working on a project. Teams have a 1:1 correspondence with task lists. | `team_name` (string, required), `description` (string) |
| `team_delete` | Remove the current team and its task directories when team work is complete. | _(no parameters)_ |
| `programmatic_tool_calling` | Execute Python that can call tools internally via `call_tool(name, input)` for serial work, or `call_tools([...])` to run independent tool calls concurrently. | `script` (string, required), `timeout_ms` (number) |

### Scheduling (Cron)

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `cron_create` | Schedule a prompt to be enqueued at a future time. Supports both recurring schedules and one-shot reminders using standard 5-field cron in local timezone. Jobs live only in the current session. The scheduler adds small jitter (up to 10% of period, max 15 min) to avoid API congestion. Tasks auto-expire after 3 days. Max 50 tasks per session. | `cron` (string, required), `prompt` (string, required), `recurring` (boolean) |
| `cron_delete` | Cancel a scheduled task by its 8-character alphanumeric ID. Use `cron_list` to find task IDs. | `task_id` (string, required) |
| `cron_list` | List all active scheduled tasks in the current session. Shows task ID, schedule, prompt, next fire time, fire count, and expiry time. | _(no parameters)_ |

### Snowflake & Data

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `sql_execute` | Execute SQL queries against the active SQL connection (Snowflake or Postgres). For complex analytical queries, first check `semantic_view_search` for curated semantic views. | `sql` (string, required), `description` (string, required), `connection` (string), `timeout_seconds` (number), `only_compile` (boolean) |
| `snowflake_connections_list` | Returns metadata about all available Snowflake connections including the active connection. | _(no parameters)_ |
| `snowflake_connections_set_active` | Switches the active Snowflake connection. The tool handles the persistence prompt automatically — do not ask the user about persistence before calling. | `name` (string, required), `persist_to_config` (boolean) |
| `snowflake_object_search` | Search for Snowflake database objects (tables, views, schemas, databases, functions, agents) using semantic search. | `search_query` (string, required), `object_types` (array), `connection` (string), `max_results` (number) |
| `snowflake_table_lookup` | Look up detailed metadata for specific Snowflake tables including full column lists, join relationships, and column usage patterns. Use after `snowflake_object_search`. | `schema` (string, required), `table` (string, required), `tables` (array), `connection` (string) |
| `snowflake_product_docs` | Search Snowflake product documentation using semantic search. Use `web_fetch` on result URLs to read full page content. | `search_query` (string, required), `connection` (string), `max_results` (number) |
| `snowflake_create_artifact` | Upload files to a Snowflake Workspace. Supports notebooks (`.ipynb`) and generic files. | `artifact_type` (string, required), `artifact_name` (string, required), `local_file_path` (string, required), `remote_location` (string), `overwrite` (boolean), `connection` (string) |
| `snowflake_multi_cortex_analyst` | Execute Cortex Analyst queries over a semantic model to generate SQL from natural language questions. Returns generated SQL, explanations, and suggested follow-up questions. | `query` (string, required), `original_query` (string, required), `previous_related_tool_result_id` (string, required), `check_metric_distribution` (string, required), `check_missing_data` (string, required), `has_time_column` (boolean, required), `queried_time_period` (string, required), `semantic_model_file` (string), `semantic_view` (string), `connection` (string), `skip_vqr_retrieval` (boolean) |
| `data_diff` | Compare two Snowflake tables and identify row-level differences (rows added or removed). Supports same-database and cross-account diffs. Connection names must be wrapped in angle brackets: `snowflake://<connection_name>/DB/SCHEMA`. | `command` (string, required) |

### Semantic Views & Agents

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `semantic_view_search` | Search and discover Snowflake Semantic Views. Use before generating complex SQL queries. Modes: `search_query`, `discover`, `describe_view`. | `search_query` (string), `discover` (boolean), `describe_view` (string), `database` (string), `schema` (string), `account` (boolean), `max_results` (number), `connection` (string) |
| `reflect_semantic_model` | Validate a semantic model YAML file. Performs file existence check, YAML syntax validation, schema validation, and Snowflake server-side validation. | `semantic_model_file` (string, required), `target_schema` (string) |
| `cortex_agent_search` | Search and discover Cortex Agents. Use before writing complex queries. Modes: `search_query`, `discover`, `describe_agent`. | `search_query` (string), `discover` (boolean), `describe_agent` (string), `database` (string), `schema` (string), `account` (boolean), `max_results` (number), `shallow` (boolean), `connection` (string) |

### dbt

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `fdbt` | A fast dbt project explorer — 10-50x faster than Python. Use this first for ANY dbt project questions: models, lineage, sources, tests, columns, and project overview. | `command` (string, required), `project_path` (string) |

**fdbt commands:**

| Category | Command | Description |
|----------|---------|-------------|
| Overview | `info` | Show project statistics |
| Overview | `list [-l layer] [-s] [-f pattern]` | List models, optionally filtered by layer or pattern |
| Lineage | `lineage <model> [-u\|-d] [-c] [--columns]` | Show dependency tree |
| Lineage | `impact <model> [-c] [-s severity]` | Analyze blast radius |
| Tests | `tests coverage [-l layer] [-d] [-f pattern]` | Test coverage stats |
| Tests | `tests list [-m model] [-l layer] [-t type] [-s]` | List tests |
| Tests | `tests missing [-l layer] [-m model]` | Find gaps in coverage |
| Tests | `tests dependencies <test_name>` | Show what a test depends on |
| Tests | `tests stats` | Show overall test statistics |
| Sources | `sources list [-t] [-c] [-u]` | List sources |
| Sources | `sources usage <source>` | Find models using a source |
| Sources | `sources locate <source>` | Find YAML file defining source |
| Columns | `columns trace <column> [-m model]` | Trace column lineage to source |
| Columns | `columns impact <column> [-m model]` | Column impact analysis |
| Schema | `schema check [model]` | Check documentation coverage |
| Schema | `schema locate <model>` | Find where schema is defined |
| Compilation | `compile <model>` | Compile model SQL |
| Macros | `macros list` | List all macros |
| Macros | `macros usage <macro>` | Find macro usage |
| Macros | `macros locate <macro>` | Find file defining macro |

### Notebooks

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `notebook_actions` | Primary tool for all Jupyter notebook operations. Actions: `setup`, `execute_cell`, `insert_cell`, `edit_cell`, `delete_cell`, `read_cell`, `read_notebook`, `execute_all`, `restart_kernel`. Kernel state persists across `execute_cell` calls. Always call `setup` first, then `read_notebook` before modifying an existing notebook. Never call multiple `insert_cell` or `delete_cell` in the same response. | `action` (string, required), `notebook_path` (string, required), `cell_index` (number), `cell_content` (string), `cell_type` (string), `timeout_seconds` (number), `kernel_name` (string) |
| `notebook_execute` | Execute a Jupyter notebook (all cells). | `notebook_path` (string, required), `output_path` (string), `timeout_seconds` (number), `allow_errors` (boolean), `kernel_name` (string), `parameters` (object), `working_directory` (string), `additional_packages` (array), `python_version` (string) |

### Skills

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `skills_list` | List available skills with compact metadata. | `query` (string), `state` (string), `includeArchived` (boolean), `limit` (integer) |
| `skill_view` | View full SKILL.md instructions or a support file for a single skill. | `name` (string, required), `filePath` (string) |
| `skill_manage` | Create, patch, edit, archive, restore, or add support files for agent-created skills. Content must start with YAML frontmatter. | `action` (string, required), `name` (string, required), `content` (string), `category` (string), `filePath` (string), `fileContent` (string), `oldString` (string), `newString` (string), `replaceAll` (boolean), `absorbedInto` (string) |
| `curator` | Run and inspect the skill Curator lifecycle manager. | `action` (string, required), `skill` (string), `dryRun` (boolean), `mutate` (boolean), `llmReview` (boolean), `sync` (boolean) |

### Memory

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `memory` | Client-side memory tool for storing and retrieving information across sessions. Supports `view`, `create`, `str_replace`, `insert`, `delete`, `rename` commands. All paths must start with `/memories`. | `command` (string, required), `path` (string), `view_range` (array), `file_text` (string), `old_str` (string), `new_str` (string), `insert_line` (number), `insert_text` (string), `old_path` (string), `new_path` (string) |

### Web & Search

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `web_search` | Search the web using Brave Search. Requires `ENABLE_CORTEX_WEBSEARCH` to be enabled. | `query` (string, required), `num_results` (number) |
| `web_fetch` | Fetch content from a web URL and optionally extract text. | `url` (string, required), `extract_text` (boolean) |
| `tool_search` | Search deferred tools by keyword. Returns matching tool schemas. | `query` (string, required), `max_results` (number), `search_type` (string) |

### UI & Secrets

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `render_ui` | Render a rich interactive UI in the browser. Only available in web UI mode. Components: Card, MetricCard, BarChart, LineChart, PieChart, DataTable, SqlBlock, Grid, Stack, Heading, Text, Badge. | `spec` (object, required) |
| `request_secret` | Request credentials for a third-party service. Checks the secret store and host environment. Real secrets never enter the sandbox. If no credentials found, guides the user to store one via `/secret`. | `service` (string, required), `reason` (string, required) |

---

## Bundled Agent Types

Use with the `task` tool via `subagent_type`:

| Agent | Description | Tools |
|-------|-------------|-------|
| `general-purpose` | General-purpose agent for researching complex questions, searching for code, and executing multi-step tasks. | All (`*`) |
| `Explore` | Fast agent for exploring codebases. Specify thoroughness: `quick`, `medium`, or `very thorough`. | All (`*`) |
| `Plan` | Read-only software architect agent for codebase exploration and implementation planning. Cannot modify files. | All (`*`) |
| `feedback` | Collects structured feedback about the coding session. Triggered when the user expresses dissatisfaction or when responses relied on unconfirmed assumptions. | `ask_user_question` |
| `curator` | Reviews agent-created skills and recommends or applies lifecycle maintenance. | `skills_list`, `skill_view`, `skill_manage`, `curator` |
| `dbt-verify` | dbt project verification agent. Use after implementing or fixing a dbt project to validate correctness. Catches bugs that `dbt build` alone misses. | All (`*`) |
| `sql-verify` | SQL correctness verification agent. Reviews SQL for common pitfalls: cartesian joins, NULL errors, division by zero, fanout, etc. Performs static analysis, does not run the query. | All (`*`) |
| `semantic-view-transform` | Transforms semantic view YAML into SQL-ready markdown documentation. Prevents "Object does not exist" errors in SQL generation. | All (`*`) |

Users can also define custom agents by creating `.md` files in the cortex agents directory or `.cortex/agents/` in the project directory.

---

## Settings

### Connection

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `cortexAgentConnectionName` | Inference Connection | connection | | Snowflake connection used for AI/LLM inference calls |
| `sqlConnectionName` | SQL Connection | connection | | Default SQL connection for database queries (Snowflake or Postgres; falls back to active Snowflake connection if not set) |

### Behavior

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `agentMode` | Agent Mode | enum | `standard` | Behavior profile for the CLI. Options: `standard`, `code` |
| `agentMentionMode` | Agent Mention Mode (%) | enum | `cortex_code` | `cortex_code`: inject agent spec into prompt. `snowflake_intelligence`: call Agent API directly (supports MCP servers) |
| `autoAcceptPlans` | Auto Accept Plans | boolean | `false` | Automatically accept plan mode requests without confirmation prompts |
| `sessionRecap` | Session Recap | boolean | `true` | Automatically generate a brief recap after periods of inactivity. Use `/recap` to trigger manually |
| `mcpWait` | Wait for MCP Servers | boolean | `false` | Wait for all MCP servers to connect before starting task execution |
| `cortexAgentEagerMode` | Agent Eager Mode | boolean | `false` | Encourage the agent to search for relevant Cortex Agents before analytical queries. Requires `cortexAgentIndexService` to be set |
| `cortexAgentIndexService` | Agent Index Service | string | | Fully qualified name of the Cortex Search service for the agent index (e.g., `MY_DB.MY_SCHEMA.CORTEX_AGENT_SEARCH`) |

### Display

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `diffDisplayMode` | Diff Display Mode | enum | `unified` | How file edits are displayed. Options: `unified` (git-style), `side_by_side` |
| `defaultViewMode` | Default View Mode | enum | `compact` | View mode when starting CoCo (cycle with Ctrl+O). Options: `compact`, `expanded`, `transcript` |
| `transcriptTruncationLimit` | Exchanges to Display | number | `50` | Maximum number of exchanges shown on resume or view mode change |
| `alwaysShowContextUsage` | Show Context Usage | boolean | `false` | Always show the context usage indicator (by default only appears when ≤30% of context remains) |
| `showModelInFooter` | Show Model in Footer | boolean | `false` | Display the active model name in the status footer |
| `titleLocation` | Title Location | enum | `inputBar` | Where to display the session title. Options: `hidden`, `footer`, `inputBar` |
| `funThinkingWords` | Thinking Word Theme | enum | `penguins` | Themed word pack for the animated thinking indicator. Options: penguins, cooking, fitness, music, science, gardening, space, coffee, woodworking, cats, pirate, mountaineering, dogs, off |
| `theme` | Theme | link | | Select color theme (dark/light/pro) |
| `penguinColors` | CoCo Color | link | | Customize CoCo the penguin |

### Timeouts

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `bashDefaultTimeoutMs` | Bash Default Timeout | number | `180000` | Default timeout for bash commands (ms) |
| `bashMaxTimeoutMs` | Bash Max Timeout | number | | Maximum timeout for bash commands; caps both default and agent-specified values |
| `jupyterExecuteTimeoutMs` | Jupyter Execution Timeout | number | `600000` | Timeout for Jupyter notebook cell execution (ms) |
| `sqlDefaultTimeoutSeconds` | SQL Max Timeout | number | `180` | Default timeout for Snowflake SQL execution when `timeout_seconds` is not specified |

### Memory & Search

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `enableMemory` | Enable Memory | boolean | `false` | Enable the memory tool for persistent storage across sessions |
| `tgrepEnabled` | Semantic Search (tgrep) | boolean | `true` | Semantic code search via Snowflake Cortex embeddings. Requires account access to Snowflake Arctic embeddings model |

### Scheduling

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `disableCron` | Disable Scheduled Tasks | boolean | `false` | Disable `/loop` command and cron scheduling tools. Also configurable via `COCO_DISABLE_CRON=1` env var |

### Task Management

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `confirmTaskDelete` | Confirm Task Delete | boolean | `true` | Ask for confirmation before deleting a single task (`d`) in the task viewer |
| `confirmTaskDeleteAll` | Confirm Delete All Tasks | boolean | `true` | Ask for confirmation before deleting all tasks (`D`) in the task viewer |

### Updates

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `autoUpdate` | Auto Update | boolean | `true` | Automatically update on launch (if disabled, shows notification only) |

### Cache & Cleanup

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `tableCache.maxCacheSizeBytes` | Max Cache Size | number | `1073741824` | Maximum total cache size in bytes |
| `tableCache.ttlDays` | TTL Days | number | `7` | Time-to-live for cached results in days |
| `tableCache.inlineMaxBytes` | Inline Max Bytes | number | `50000` | Maximum bytes to send inline to agent |
| `sessionCleanup.enabled` | Enabled | boolean | | Enable automatic cleanup of old session files |
| `sessionCleanup.maxAgeDays` | Max Age | number | | Delete conversation and debug files older than this many days |

### Plugins & Instructions

| Key | Label | Type | Description |
|-----|-------|------|-------------|
| `plugins` | Plugin Directories | array | Paths to plugin directories to load |
| `disabledPlugins` | Disabled Plugins | array | Plugin names that have been disabled |
| `disableBundledSkills` | Disabled Bundled Skills | array | List of bundled skills to disable |
| `enabledInstructionPatterns` | Instruction Files | array | Glob patterns for instruction files to load (case-insensitive) |

### Platform

| Key | Label | Type | Default | Description |
|-----|-------|------|---------|-------------|
| `windowsShell` | Windows Shell Executor | enum | `powershell` | Shell used to execute commands on Windows. Options: `powershell`, `cmd`, `bash` (Git Bash/WSL). Ignored on macOS/Linux |
| `browserHeadless` | Browser Headless Mode | boolean | `false` | Run browser automation without a visible window. Also toggleable via `CORTEX_BROWSER_HEADLESS=1` env var |
| `browserProfilePath` | Browser Profile Path | string | | Custom browser profile directory for Playwright. Leave empty for default |
| `enableDesktopNotifications` | Desktop Notifications | boolean | `false` | Send OS notifications when agent needs your attention |

---

## Keyboard Shortcuts

### Global

| Key | Action |
|-----|--------|
| `Ctrl+P` | Toggle Plan Mode |
| `Ctrl+G` | Toggle Team Mode |
| `Ctrl+O` | Cycle view mode (compact / expanded / transcript) |
| `Ctrl+S` | Open subagent picker |
| `Ctrl+B` | (App-level action) |
| `Ctrl+L` | (App-level action) |
| `Ctrl+C` | Interrupt / cancel |
| `Ctrl+Z` | Undo |
| `Shift+Tab` | Cycle Permission Level |
| `Escape` | Show help / close overlay |
| `Alt+T` | Exit fullscreen todo viewer |

### Text Input & Editing

| Key | Action |
|-----|--------|
| `Ctrl+J` | Insert newline |
| `Alt+A` | (Input action) |
| `Alt+R` | (Input action) |
| `Up` / `Down` | Navigate history |
| `Ctrl+A` | Move to line start |
| `Ctrl+E` | Move to line end |
| `Ctrl+B` | Move cursor left |
| `Ctrl+F` | Move cursor right |
| `Alt+B` | Move word left |
| `Alt+F` | Move word right |
| `Home` / `End` | Move to start/end of line |
| `Shift+Left/Right/Up/Down` | Select text |
| `Shift+Home` / `Shift+End` | Select to start/end of line |
| `Ctrl+W` | Delete word left |
| `Ctrl+K` | Delete to end of line |
| `Alt+D` | Delete word right |
| `Ctrl+Y` | Yank (paste killed text) |
| `Ctrl+Delete` | Delete word right / Undo |
| `Alt+U` | Undo |
| `Shift+Alt+U` | Redo |
| `Ctrl+R` | History search |

### Navigation (Fullscreen / Lists)

| Key | Action |
|-----|--------|
| `Up` / `Down` | Navigate up/down |
| `Left` / `Right` | Navigate left/right (agents/tabs) |
| `Pageup` / `Pagedown` | Page up/down in viewer |
| `Ctrl+Pageup` / `Ctrl+Pagedown` | Page up/down in list |
| `Return` | Confirm / submit |
| `Escape` | Cancel / exit mode |
| `Tab` | Tab (session manager) |
| `Backspace` | Back (session manager) |
| `Ctrl+Escape` | Cancel (selectors/sandbox) |
| `Ctrl+Alt+Return` | Action in lineage viewer |

---

## Hook Events

Hooks are shell commands that execute in response to lifecycle events. Configure via settings or the `/hooks` command.

| Event | Description |
|-------|-------------|
| `PreToolUse` | Fires before any tool is called |
| `PostToolUse` | Fires after any tool completes |
| `PermissionRequest` | Fires when a permission prompt is raised |
| `UserPromptSubmit` | Fires when the user submits a prompt |
| `Stop` | Fires when the main agent stops |
| `SubagentStop` | Fires when a subagent stops |
| `Notification` | Fires on notifications |
| `SessionStart` | Fires at the start of a session |
| `SessionEnd` | Fires at the end of a session |
| `PreCompact` | Fires before conversation compaction |
| `Setup` | Fires during initial setup |

---

## MCP (Model Context Protocol) Servers

| Item | Detail |
|------|--------|
| Supported transports | `http`, `sse`, `stdio` |
| Tool name pattern | `mcp__<server>__<tool>` |
| Config file | `~/.snowflake/cortex/mcp.json` |
| CLI management | `cortex mcp` |
| In-session management | `/mcp` |

### `cortex mcp` Subcommands

| Subcommand | Description |
|------------|-------------|
| `add` | Add an MCP server |
| `get` | Get MCP server details |
| `list` | List configured MCP servers |
| `remove` | Remove an MCP server |
| `start` | Start an MCP server |

---

## Permission / Agent Modes

| Mode | Value | Description |
|------|-------|-------------|
| Confirm Actions | `confirm_actions` | Prompt for confirmation before tool calls |
| Bypass | `bypass_safeguards` | Auto-approve all tool calls |

### Permission Modes

| Mode | Value |
|------|-------|
| Default | `default` |
| Plan | `plan` |
| Confirm Actions | `confirmActions` |
| Don't Ask | `dontAsk` |
| Bypass Permissions | `bypassPermissions` |

---

## Environment Variables & Feature Flags

| Feature | Env Var / Config Key |
|---------|---------------------|
| Code streaming | `CORTEX_CODE_STREAMING` |
| Snowutils | `USE_SNOWUTILS` |
| Disable todo tool | `CORTEX_DISABLE_TODO_TOOL` |
| Enable memory tool | `CORTEX_ENABLE_MEMORY` |
| Developer mode | `CORTEX_AGENT_USE_LOCAL_ORCHESTRATOR` |
| Context step enforcement | `CTX_STEP_ENFORCEMENT` |
| Disable cron/scheduling | `COCO_DISABLE_CRON` |
| Disable routines | `COCO_DISABLE_ROUTINES` |
| Disable browser reminder | `COCO_DISABLE_BROWSER_REMINDER` |
| Enable Snowflake-managed MCP servers | `CORTEX_CODE_ENABLE_SNOWFLAKE_MANAGED_MCP_SERVERS` |
| Browser headless mode | `CORTEX_BROWSER_HEADLESS` |
| SSH support | `config: ssh` |
| Airflow plugins | `config: airflow_plugins` |
| Tool search | `config: toolSearch` |
| Apply patch | `config: applyPatch` |
| Programmatic tool calling | `config: programmaticToolCalling` |
| PTC batch mode | `config: ptcBatchEnabled` |
| Tgrep semantic search | `config: tgrep` |
| Python REPL | `config: pythonRepl` |
| Skill catalog | `config: enableSkillCatalog` |
| Catalog search | `config: skillCatalogSearch` |
| Cocobox sandbox | `config: cocoboxSandbox` |
| Hook workdir reinit | `config: hookWorkdirReinit` |
| Sandbox secret store push | `config: sandboxSecretStorePush` |

---

## CLI Subcommands (`cortex <command>`)

### `cortex acp`
| Subcommand | |
|------------|--|
| `serve` | |

### `cortex conversations`
| Subcommand | |
|------------|--|
| `list` | |
| `search` | |
| `transcript` | |

### `cortex ctx`
| Subcommand | |
|------------|--|
| `ctxRunner` | |
| `init` | |
| `push` | |
| `remember` | |
| `repo` | |
| `rule` | |
| `search` | |
| `show` | |
| `step` | |
| `task` | |

### `cortex developer`
| Subcommand | |
|------------|--|
| `system-prompt` | |

### `cortex logs`
| Subcommand | |
|------------|--|
| `errors` | |
| `path` | |
| `query` | |
| `reader` | |
| `shared` | |
| `show` | |
| `tail` | |

### `cortex mcp`
| Subcommand | |
|------------|--|
| `add` | |
| `get` | |
| `list` | |
| `remove` | |
| `start` | |

### `cortex memory`
| Subcommand | |
|------------|--|
| `drop` | |
| `edit` | |
| `extract` | |
| `init` | |
| `list` | |
| `recall` | |
| `remember` | |
| `runners` | |

### `cortex plugin`
| Subcommand | |
|------------|--|
| `activate` | |
| `add` | |
| `check` | |
| `deactivate` | |
| `find` | |
| `list` | |
| `publish` | |
| `remove` | |
| `unpublish` | |
| `update` | |
| `validate` | |

### `cortex postgres`
| Subcommand | |
|------------|--|
| `add` | |
| `list` | |
| `remove` | |

### `cortex profile`
| Subcommand | |
|------------|--|
| `add` | |
| `delete` | |
| `list-remote` | |
| `list` | |
| `publish` | |
| `set-default` | |
| `show` | |
| `sync` | |

### `cortex skill`
| Subcommand | |
|------------|--|
| `add` | |
| `check` | |
| `connection` | |
| `find` | |
| `list` | |
| `publish` | |
| `remove` | |
| `update` | |

### `cortex skill-catalog`
| Subcommand | |
|------------|--|
| `install` | |
| `publish` | |
| `remove` | |
| `search` | |

### `cortex update`
| Subcommand | |
|------------|--|
| `download` | |
| `releaseChannel` | |

### `cortex worktree`
| Subcommand | |
|------------|--|
| `cleanup` | |
| `create` | |
| `delete` | |
| `list` | |
| `switch` | |

### `cortex shared`
| Subcommand | |
|------------|--|
| `connection` | |

### Other top-level commands (no subcommands listed)
`cortex airflow`, `cortex curator`, `cortex dispatch`, `cortex routines`, `cortex utils`, `cortex versions`

### Additional top-level commands
`acp`, `analyst`, `artifact`, `automation`, `automations`, `completion`, `connections`, `conversations`, `create-ui-launcher`, `ctx`, `curator`, `env`, `logs`, `mcp`, `memory`, `plugin`, `postgres`, `profile`, `reflect`, `search`, `semantic-views`, `skill`, `update`, `versions`, `worktree`

---

## Tips

- **Use `/plan` or `Ctrl+P`** before complex, multi-file operations so CoCo presents a plan for approval before making changes. Enable `autoAcceptPlans` to skip confirmation for routine work.
- **Use `#` to reference tables** and `@` to reference files directly in your prompt without extra commands.
- **Use `$` to invoke a skill** — for example, `$commit` to trigger the commit skill by name.
- **Use `%` to mention a Cortex Agent** — CoCo will inject the agent spec or call the Agent API depending on your `agentMentionMode` setting.
- **Use `/compact`** when the context window fills up. It preserves a summary so CoCo retains context without starting fresh.
- **Use `/qq` (quick question)** for side questions that shouldn't pollute the main conversation history.
- **Use `/bg` (`/background-agent`)** to launch a long-running agent task while you continue chatting in the main session. Check on it with `Ctrl+S` to open the subagent picker.
- **Use `/loop` or `/cron`** to schedule recurring prompts. Cron expressions use local time in standard 5-field format. Tasks auto-expire after 3 days and are session-only.
- **Use `semantic_view_search` before complex SQL** — if a semantic view exists for your domain, use it for more reliable, verified business definitions.
- **Use `cortex_agent_search` before analytical queries** — agents contain curated routing instructions that map question types to the right data sources.
- **Use `fdbt`** (or `/fdbt`) for any dbt project question. It is 10-50x faster than shell-based exploration and understands lineage, tests, sources, and columns natively.
- **Use `/sql-readonly`** to lock the SQL tool to read-only mode when you want to prevent accidental writes.
- **Use `/rewind`** to step back through conversation history if CoCo went in the wrong direction, without starting a completely new session.
- **Use `/worktree`** or set `worktree_isolation: true` when launching background agents on tasks that touch the same files, to avoid conflicts.
- **Use `tgrep`** for semantic code search across your project — it searches by meaning, not just exact text. Enable/disable with `/tgrep on|off`.
- **Use `/index --rebuild`** to force a fresh search index after significant code changes.
- **Enable `enableMemory`** (or set `CORTEX_ENABLE_MEMORY=1`) to persist notes and context across sessions via the `memory` tool.
- **Use `/settings`** to adjust timeouts (`bashDefaultTimeoutMs`, `sqlDefaultTimeoutSeconds`) for long-running queries or scripts.
- **Use `Ctrl+G`** to toggle team mode for multi-agent parallel work, or `/team` and `/team-off` as slash command equivalents.

=== cortex-secrets/ ===
---
name: cortex-secrets
description: "MUST consult whenever any command needs a credential, secret, API key, token, or password — whether discovered from an error, source code, --help output, or any other signal. MUST also consult when the user shares, pastes, or includes a secret value directly in their message. Also use when: the user asks about /secrets, storing credentials, secret scopes, or consent modes. Triggers: secret, secrets, /secrets, API key, credential, token, password, authentication, unauthorized, 401, 403, forbidden, EACCES, permission denied, access denied, missing key, invalid token, auth error, connection refused, login failed, .env, environment variable, env var, keychain, export SECRET, cortex secret list, inline secret injection, pasted secret, shared secret, my key is, my password is, my token is, here is my, use it to."
---

# Secrets Management

This skill extends the bash tool's `# Secrets` section with the full credential workflow, security protocols, and user-facing guidance.

The bash tool teaches the injection mechanics: `VAR="<key>"` prefix syntax, `cortex secret list`, and `/secrets`. This skill covers **when and how to apply them**, plus what to do when things go wrong (auth errors, missing secrets, pasted credentials).

---

## When to Use

- A command, script, or tool needs a credential, API key, token, or password
- A tool fails with an authentication or permission error (401, 403, EACCES, etc.)
- A tool's `--help` output reveals required environment variables
- The user asks how to store or manage credentials
- The user pastes a secret value in chat

---

## Workflow

**Whenever a command needs a credential** -- whether discovered from an error, from reading source code, from `--help` output, or from any other signal:

1. Run `cortex secret list` silently to check existing secrets (agent-internal -- do NOT show or mention this command to the user)
2. If a match exists, re-run the command using the inline injection syntax from the bash tool: `VAR="<key>" my-command`
3. If no match, direct the user to add it via `/secrets`, then ask them to retry

**NEVER skip step 1.** Always check for existing secrets before suggesting the user add one.

### Tool Discovery

When running an unfamiliar CLI tool for the first time, run `tool --help` to discover which env vars or credentials it expects, then follow the workflow above.

**Sandbox environments**: If the system prompt indicates you are running in a Cortex Code sandbox / Linux VM, consult the `cortex-code-sandbox` skill for the proxy-managed credential workflow.

---

## Security Rules

These rules extend the bash tool's `NEVER` directives:

- NEVER ask the user to paste or share a secret in chat -- direct them to `/secrets`
- NEVER suggest `export VAR=value`, manual env var setup, or writing to `.env` files
- NEVER write secrets into config files or any file on disk
- Never use `echo`, `env`, `printenv`, or any command that would print a secret value
- Never show the `VAR="<key>"` injection syntax or `cortex secret` commands to the user -- these are agent-internal mechanics
- The user-facing interface is ONLY `/secrets`

---

## If the User Pastes a Secret in Chat

1. **Stop** -- do NOT use the value
2. **Warn**: the secret is now recorded in the conversation transcript and has been sent to the server -- it cannot be unsent
3. **Tell them to run `/wipe-session`** to delete local session files and exit
4. **Recommend** rotating the compromised secret immediately
5. **Direct them to `/secrets`** as the correct way to provide credentials going forward
6. Do not repeat or reference the pasted value

---

## /secrets Slash Command

```
/secrets
```

Opens the interactive secret manager where the user can:

- **Add** a new secret (user or session scope)
- **Delete** an existing secret
- **View** stored secret names (values are never displayed)

Values are entered through a masked input field that prevents them from appearing in the conversation.

---

## Secret Scopes

| Scope | Storage | Lifetime | Default consent |
|-------|---------|----------|-----------------|
| **User** | OS keychain | Persistent across sessions | `once` -- prompt once per session |
| **Session** | In-memory | Current session only | `never` -- inject silently |

---

## Consent Modes

| Mode | Behavior |
|------|----------|
| `once` | Prompt the first time per session, then allow silently |
| `always` | Prompt every time the secret is used |
| `never` | Inject silently without prompting |

The user chooses the consent mode when adding a secret via `/secrets`.

---

## Stopping Points

- After step 1 (checking `cortex secret list`): if no matching secret exists, stop and direct the user to `/secrets` before retrying
- If the user pastes a secret in chat: stop immediately, warn, and do NOT proceed with the value

---

## Output

This skill does not produce artifacts. It guides the agent's behavior when credentials are involved, ensuring secrets are managed through `/secrets` and injected securely via the bash tool's inline `"<key>"` syntax.

=== cost-intelligence/ ===
---
name: cost-intelligence
description: "Account-level cost analytics via SNOWFLAKE.ACCOUNT_USAGE. Credit usage by warehouse, user, service. Budgets, spending limits, custom budgets. Resource monitors, credit quotas, suspend triggers. Anomaly detection, costs, chargeback, storage, serverless, containers, data transfer, top user spend, query cost grouping. Cortex AI cost or usage including Cortex Agents, Snowflake Intelligence, AI function, Cortex Code, Cortex Search, Cortex Analyst, Cortex REST API, model training/fine-tuning, and provisioned throughput. Cost insights, waste reduction, savings. Not for org-wide currency spend or multi-account billing (billing/organization-management) or warehouse DDL (warehouse)."
---

# Cost Intelligence Skill

> **⚠️ Native App costs**: If the user is asking about the cost of an **installed native app**, **do NOT continue with this skill**. Instead, load the `native-app-consumer` skill immediately — it has app-specific cost views (`APPLICATION_DAILY_USAGE_HISTORY`) and cost management instructions that this skill does not cover.

> **Do NOT search for semantic views for cost questions.**  
> Cost data lives in `SNOWFLAKE.ACCOUNT_USAGE` views, not user-created semantic views.  
> Skip `cortex semantic-views search/discover` and `SHOW DATABASES` — go directly to the routing table below.

> **⚠️ Budget Syntax Warning**  
> Budgets are **class instances**, NOT standard objects. Never use `SHOW BUDGETS` — it will fail.  
> ✅ Correct: `SHOW SNOWFLAKE.CORE.BUDGET LIKE '...'` or `SHOW SNOWFLAKE.CORE.BUDGET INSTANCES IN ACCOUNT`  
> ❌ Wrong: `SHOW BUDGETS LIKE '...'`

> **⚠️ Account Budget Limitations**  
> The **account budget** (`SNOWFLAKE.LOCAL.ACCOUNT_ROOT_BUDGET`) monitors ALL account spending automatically.  
> It does **NOT** support tag or resource management methods:  
> - ❌ `ADD_RESOURCE`, `REMOVE_RESOURCE`, `GET_LINKED_RESOURCES`  
> - ❌ `ADD_RESOURCE_TAG`, `REMOVE_RESOURCE_TAG`, `GET_RESOURCE_TAGS`, `GET_BUDGET_SCOPE`  
> If the user asks about tags/resources on the **account budget**, tell them immediately this isn't supported.  
> They need a **custom budget** to track specific objects or tags.

---

## Routing

Match the user's question to keywords and read the corresponding file **before writing any queries**.

| Keywords | Route |
|----------|-------|
| "top spenders", "who is spending", "user costs", "top users", "user spending" | `references/queries/users-queries.md` |
| "expensive queries", "query costs", "costly queries", "parameterized hash", "query patterns", "grouped by hash" | `references/queries/users-queries.md` |
| "where is my money going", "cost breakdown", "credits by service", "overall spending" | `references/queries/overview.md` |
| "warehouse", "compute", "virtual warehouse", "warehouse costs" | `references/queries/warehouse.md` |
| "week over week", "month over month", "cost increase", "spike", "why did costs go up", "compared to last" | `references/queries/trends.md` |
| "anomalies", "unusual spending", "cost spikes", "anomaly detection", "anomaly notification", "anomaly email", "cost spike alert" | `skills/anomaly-insights/SKILL.md` |
| "serverless", "tasks", "snowpipe", "serverless task credits" | `references/queries/serverless.md` |
| "storage", "database size", "storage costs", "data storage" | `references/queries/storage.md` |
| "cortex cost", "cortex credits", "cortex spend", "AI costs", "cortex AI cost", "analyst cost", "analyst credits", "LLM cost", "cortex search cost", "cortex search credits", "cortex agents cost", "cortex agents credits", "agent spend", "agent usage", "cortex code cost", "cortex code cli cost", "cortex code snowsight cost", "cortex code credits", "snowflake intelligence cost", "snowflake intelligence credits", "fine-tuning cost", "model training cost", "provisioned throughput cost", "PTU cost", "no data", "did we have usage", "why is it zero", "request drill-down", "request breakdown", "per request", "by request", "per user", "by user", "by instance", "report in credits" | `skills/cortex-ai/SKILL.md` |
| "team costs", "department spending", "cost center", "chargeback", "showback", "tags", "attribution", "tag value", "cost by tag" | `skills/tag-attribution/SKILL.md` |
| "containers", "SPCS", "compute pools", "container services" | `references/queries/containers.md` |
| "data transfer", "cross-region", "cross-cloud", "egress" | `references/queries/data-transfer.md` |
| "over budget", "at risk budget", "list all budgets", "compare budgets", "which budgets" | `references/queries/budgets.md` |
| "create budget", "set budget", "activate budget", "spending limit", "budget notifications", "add to budget", "budget actions", "deactivate budget", "drop budget", "delete budget", "remove budget", "budget alerts", "custom budget", "account budget", "budget status", "budget spend", "budget usage" | `skills/budget/SKILL.md` |
| "cost insights", "optimization insights", "waste reduction", "what can I save", "unused resources", "idle warehouses", "savings recommendations", "never queried tables", "query gaps", "auto-clustering waste", "unused materialized views" | `skills/cost-insights/SKILL.md` |

**Never write ad-hoc queries when a verified query exists in the routed file.**

=== data-cleanrooms/ ===
---
name: data-cleanrooms
description: "Use for ALL requests related to Snowflake Data Clean Rooms (DCR): clean room, cleanroom, DCR, collaboration(s), view/list collaborations, join/review collaboration, invitation, data offering(s), template(s), register, share table, run analysis, run activation, audience overlap, activation, export segment, create collaboration, create cleanroom, measure overlap, manage templates, add template, remove template, approve template, reject template, auto-approval, link data offering, unlink data offering, share data with runner, revoke data access, link local data offering, unlink local data offering, tear down, leave, drop collaboration, delete collaboration, RBAC, DCR roles, DCR privileges, create roles for clean rooms, assign DCR privileges, grant collaboration privileges, revoke DCR privileges, set up DCR roles, privileges for data engineers, privileges for campaign manager. Covers browsing, joining, registering, running analysis/activation, creating collaborations, managing templates, managing data offerings, RBAC/role setup, and leaving/tearing down collaborations via the DCR Collaboration API."
allowed-tools:
  - snowflake_sql_execute
  - bash
---

# Snowflake Data Clean Room (DCR) Collaboration API

This skill helps you work with the Snowflake DCR Collaboration API (`snowflake_product_docs`: `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/about`; if that tool is unavailable, `cortex search docs "<query>"` via bash) — a fully symmetric, multi-party collaboration environment for secure data analysis without sharing raw data.

## When to Use

- View collaborations, data offerings, or templates
- Review and join collaborations
- Register data offerings (datasets) for collaborations
- Register templates (analysis queries) for collaborations
- Run analysis templates (standard audience overlap, standard audience overlap activation, custom)
- Create a new collaboration with other parties
- Manage templates in collaborations (add, remove, approve/reject requests, auto-approval)
- Link or unlink data offerings in collaborations (share with runners, revoke access, local linking)
- Leave or tear down collaborations
- Create roles and assign DCR privileges (account-level, collaboration-level, registry-level, persona-based)
- Understand DCR concepts (data mapping, collaboration roles)

## Prerequisites

### 1. DCR Must Be Installed

Verify DCR is available in your account:

```sql
SHOW DATABASES LIKE 'SAMOOHA_BY_SNOWFLAKE_LOCAL_DB%';
```
If no results, DCR is not installed. Contact your administrator.


## Collaboration Roles

The DCR Collaboration API supports flexible multi-party roles:

| Role | Description |
|------|-------------|
| **Owner** | Creates and owns the collaboration, defines invited parties and their roles |
| **Data Provider** | Provides data offerings (datasets) |
| **Analysis Runner** | Runs permitted templates on allowed data offerings |

One account can have multiple roles (e.g., owner + data provider + analysis runner) within the same collaboration.

## Workflow

```
Start
  |
Database Discovery (MANDATORY)
  |
  +-- ONE DB --> use as {DB}
  +-- MULTIPLE --> STOP, ask user
  +-- NONE --> STOP, not installed
  |
Intent Detection
  +---> VIEW --> Load browse/SKILL.md
  +---> JOIN/REVIEW --> Load review-join/SKILL.md
  +---> REGISTER --> Load register/SKILL.md
  +---> RUN --> Load run/SKILL.md
  +---> CREATE --> Load create/SKILL.md
  +---> MANAGE TEMPLATES --> Load manage-templates/SKILL.md
  +---> LINK/UNLINK DATA OFFERINGS --> Load manage-data-offerings/SKILL.md
  +---> RBAC --> Load rbac/SKILL.md
  +---> LEAVE/TEARDOWN --> Load teardown-leave/SKILL.md
```

1. **Database Discovery (MANDATORY)** - See [Database Discovery](#database-discovery-first-step---mandatory) below.

2. **Route to Sub-Skill** — Detect intent from user request and **use the `read` tool** to load the matching sub-skill:

   **VIEW** — "view collaborations", "show collaborations", "list collaborations", "view offerings", "view templates"
   → Load `browse/SKILL.md`

   **JOIN/REVIEW** — "join collaboration", "review collaboration", "accept invitation", "review invitation"
   → Load `review-join/SKILL.md`

   **REGISTER** — "register data offering", "register template", "register table", "share table", "create template"
   → Load `register/SKILL.md`

   **RUN** — "run analysis", "run template", "audience overlap", "standard audience overlap", "measure overlap", "activation", "run activation", "compare audiences", "activate", "export segment"
   → Load `run/SKILL.md`

   **CREATE** — "create collaboration", "create cleanroom", "create dcr", "new collaboration", "set up clean room", "initiate collaboration"
   → Load `create/SKILL.md`

   **MANAGE TEMPLATES** — "add template", "remove template", "manage templates", "approve template", "reject template", "template request", "auto-approval", "view update requests"
   → Load `manage-templates/SKILL.md`

   **LINK/UNLINK DATA OFFERINGS** — "link data offering", "unlink data offering", "share data with runner", "revoke data access", "link offering", "unlink offering", "make offering available", "remove offering access", "link local data offering", "unlink local data offering", "add my data locally"
   → Load `manage-data-offerings/SKILL.md`

   **RBAC** — "create roles for data clean rooms", "assign DCR privileges", "grant collaboration privileges", "revoke DCR privileges", "set up DCR roles", "RBAC for clean rooms", "privileges for data engineers", "privileges for campaign manager"
   → Load `rbac/SKILL.md`

   **LEAVE/TEARDOWN** — "leave collaboration", "tear down", "teardown", "drop collaboration", "delete collaboration", "leave cleanroom", "exit collaboration"
   → Load `teardown-leave/SKILL.md`

3. **Execute Sub-Skill Workflow & Present Results**

## Database Discovery (FIRST STEP - MANDATORY)

Before any DCR operation, discover the DCR database:

```sql
SHOW DATABASES LIKE 'SAMOOHA_BY_SNOWFLAKE_LOCAL_DB%';
```

| Result | Action |
|--------|--------|
| ONE database | Use that database name as `{DB}` |
| MULTIPLE databases | **STOP** - Ask user which one to use |
| NO database | **STOP** - DCR is not installed. Ask user to install DCR first. |

**If user provides a database name directly**, skip discovery and use that database.

**DO NOT PROCEED until database is confirmed.**

### Using the Database

Once discovered, **replace `{DB}` with the actual database name** in ALL procedure calls:

```sql
-- Example: If discovered database is SAMOOHA_BY_SNOWFLAKE_LOCAL_DB
CALL SAMOOHA_BY_SNOWFLAKE_LOCAL_DB.COLLABORATION.VIEW_COLLABORATIONS();
```

**IMPORTANT:** Sub-skills use `{DB}` as a placeholder. You MUST substitute it with the discovered database name when executing procedures.

## Important: Only Use Documented Procedures

**ALWAYS use CALL procedures to interact with DCR. NEVER query or modify DCR internal tables directly.**

**Rules:**
1. **Only use procedures documented in this skill or its sub-skills.** If a procedure is not listed in any SKILL.md file, do NOT invent or guess it. Refer the user to Snowflake documentation instead.
2. **NEVER modify DCR internal tables.** No `INSERT`, `UPDATE`, or `DELETE` on any DCR table. All interaction must go through `CALL` procedures.
3. **NEVER fabricate API names.** If you are unsure whether a procedure exists (e.g., `UNREGISTER_TEMPLATE`, `DELETE_DATA_OFFERING`, `MODIFY_COLLABORATION`), assume it does NOT exist. Do not propose it.

**Why:** DCR internal table structures are not part of the public API and may change. Only the documented procedures are stable and supported.

**Examples:**
- ❌ `SELECT * FROM {DB}.COLLABORATION.DATA_OFFERINGS`
- ❌ `SELECT * FROM {DB}.COLLABORATION.TEMPLATE_SPECS`
- ❌ `SELECT * FROM {DB}.COLLABORATION.COLLABORATION_STATE`
- ❌ `DELETE FROM {DB}.REGISTRY.REGISTERED_TEMPLATES WHERE ...`
- ❌ `INSERT INTO {DB}.COLLABORATION.DATA_OFFERINGS ...`
- ❌ `CALL {DB}.REGISTRY.UNREGISTER_TEMPLATE(...)` (does not exist)
- ✓ `CALL {DB}.COLLABORATION.VIEW_DATA_OFFERINGS('<collaboration_name>')`
- ✓ `CALL {DB}.REGISTRY.VIEW_REGISTERED_TEMPLATES()`

## Sub-Skills

| Task | Load | Stopping Point? |
|------|------|-----------------|
| View collaborations, offerings, templates | `browse/SKILL.md` | No |
| Review and join collaborations | `review-join/SKILL.md` | Yes (confirm before join) |
| Register data offerings and templates | `register/SKILL.md` | Yes |
| Run analysis templates | `run/SKILL.md` | Yes |
| Create a new collaboration (single or multi-party) | `create/SKILL.md` | Yes (confirm spec before initialize) |
| Manage templates (add, remove, approve/reject) | `manage-templates/SKILL.md` | Yes (confirm before add/remove) |
| Link or unlink data offerings | `manage-data-offerings/SKILL.md` | Yes (confirm before link/unlink) |
| Create roles and assign DCR privileges | `rbac/SKILL.md` | Yes (confirm before grant/revoke) |
| Leave or tear down collaborations | `teardown-leave/SKILL.md` | Yes (confirm before teardown/leave) |

## Stopping Points

- **Database Discovery**: If multiple DBs found, ask user to choose
- **Review-Join**: Confirm before joining a collaboration
- **Register**: Confirm specification before registration
- **Run**: Collaboration selection, template selection, parameter confirmation before execution
- **Create**: Confirm collaboration spec before initializing
- **Manage Templates**: Confirm before adding/removing templates, confirm before approving/rejecting requests
- **RBAC**: Confirm before granting or revoking account-level, collaboration-level, or registry-level privileges; confirm persona-based setup before executing
- **Leave/Teardown**: Confirm before leaving or tearing down a collaboration

**Resume rule:** Upon user approval, proceed directly without re-asking.

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Object does not exist" | Wrong database name | Re-run database discovery |
| "Insufficient privileges" | Missing DCR privilege | See "Required Privileges" below |
| "Unknown user-defined function" | Missing DCR privilege | See "Required Privileges" below |
| "Collaboration not found" | Wrong name or not joined | Check `VIEW_COLLABORATIONS()` |
| `ActivationDestinationsNotFoundException` | Missing `activation_destinations` on the runner with the activation template | See `create/SKILL.md` Step 6 |
| "Secondary roles must be disabled" | Procedure requires Secondary roles to be disabled | Run `USE SECONDARY ROLES NONE` before executing procedure and `USE SECONDARY ROLES ALL` to restore after |

## Required Privileges

DCR operations require specific privileges. If you get "Insufficient privileges" or "Unknown user-defined function" errors, an ACCOUNTADMIN must grant the appropriate privilege using the DCR Admin APIs.

### Granting Account-Level Privileges

```sql
-- Use ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Grant an account-level privilege
CALL {DB}.ADMIN.GRANT_PRIVILEGE_ON_ACCOUNT_TO_ROLE(
    '<privilege_name>',
    '<user_role>'
);

-- Example: Grant ability to view collaborations
CALL SAMOOHA_BY_SNOWFLAKE_LOCAL_DB.ADMIN.GRANT_PRIVILEGE_ON_ACCOUNT_TO_ROLE(
    'VIEW COLLABORATIONS',
    'ANALYST_ROLE'
);
```

### Granting Collaboration-Level Privileges

```sql
-- Use ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Grant privilege on a specific collaboration
CALL {DB}.ADMIN.GRANT_PRIVILEGE_ON_OBJECT_TO_ROLE(
    '<privilege_name>',
    'COLLABORATION',
    '<collaboration_name>',
    '<user_role>'
);

-- Example: Grant ability to view data offerings on a collaboration
CALL SAMOOHA_BY_SNOWFLAKE_LOCAL_DB.ADMIN.GRANT_PRIVILEGE_ON_OBJECT_TO_ROLE(
    'VIEW DATA OFFERINGS',
    'COLLABORATION',
    'my_collaboration',
    'ANALYST_ROLE'
);
```

For full privilege management details, look up Snowflake docs for `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/roles` (`snowflake_product_docs`, else `cortex search docs "<query>"` via bash).

**Note:** Each sub-skill documents its specific required privileges.

## Output

This skill routes to sub-skills, each of which produces its own output:

| Sub-Skill | Output |
|-----------|--------|
| browse | Tables of collaborations, data offerings, or templates |
| review-join | Confirmation of join action |
| register | Confirmation of registration |
| run | Analysis result rows or activation segment export status |
| create | Confirmation of collaboration creation |
| rbac | Role creation and privilege grant/revoke confirmation |

## Tools

### `snowflake_sql_execute`

Used to execute SQL `CALL` procedures against the DCR Collaboration API. All DCR operations go through stored procedures (not direct table queries). This tool is required because every sub-skill relies on procedure calls like `{DB}.COLLABORATION.VIEW_COLLABORATIONS()`.

### Documentation lookups

**`snowflake_product_docs`**, else **`cortex search docs "<query>"`** via **`bash`**. Use `bash` only for that fallback (not for shell file operations).

## Out of Scope / Unknown Requests

If a user asks about DCR functionality not covered in this skill:

1. **First**, search Snowflake product documentation for the relevant DCR topic (e.g., `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/using`) — `snowflake_product_docs`, else `cortex search docs "<query>"` via bash.

2. **If not found**, respond:
   > "This functionality will be added in future updates to this skill. You may want to check with Snowflake support or the latest documentation for updates."

## References

For additional details, search Snowflake product documentation for these topics (`snowflake_product_docs`, else `cortex search docs "<query>"` via bash):
- `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/about`
- `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/roles`
- `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/using`
- `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/v2-api-reference`
- `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/spec-reference`
- `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/registries`
- `https://docs.snowflake.com/en/user-guide/cleanrooms/v2/troubleshooting`

## Sub-Skill Files

- `browse/SKILL.md` - View operations
- `review-join/SKILL.md` - Review and join operations
- `register/SKILL.md` - Register operations
- `run/SKILL.md` - Run analysis templates
- `create/SKILL.md` - Create collaboration operations
- `manage-templates/SKILL.md` - Manage templates (add, remove, approve/reject, auto-approval)
- `manage-data-offerings/SKILL.md` - Link or unlink data offerings in collaborations
- `rbac/SKILL.md` - Create roles and assign DCR privileges
- `teardown-leave/SKILL.md` - Leave or tear down collaborations

=== data-governance/ ===
---
name: data-governance
description: "**[REQUIRED]** for all Snowflake data governance tasks. Routes to six sub-skills: (1) horizon-catalog — access history, users, roles, grants, permissions, query history, compliance, catalog; (2) data-policy — [REQUIRED] masking, row access, projection, aggregation, join, and tokenization policies, tag-based masking, protect sensitive data, column/TIMESTAMP masking, the 2-stage UI create flow triggered by `/data-governance Create a new <policy type> policy for me`; (3) sensitive-data-classification — [REQUIRED for ALL classification] PII, classify, data classification, manual/automatic classification, Classification Profile, auto_tag, custom classifiers, regex, semantic/privacy category, IDENTIFIER, QUASI_IDENTIFIER, SENSITIVE, SYSTEM$CLASSIFY, DATA_CLASSIFICATION_LATEST, GDPR/CCPA/PCI; (4) governance-maturity-score — governance posture, maturity score, assessment, recommendations; (5) observability-maturity-score — data observability, DMF coverage, quality monitoring maturity, lineage usage, observability assessment; (6) object-contacts — [REQUIRED] assign data steward, create contact, object contact, contact report, who owns this table, SET CONTACT, data stewardship. MUST be used for classification or masking tasks — do not answer from general knowledge. horizon-catalog is the fallback. Triggers: governance, access history, permissions, grants, roles, audit, compliance, catalog, masking policy, row access policy, projection policy, aggregation policy, join policy, JOIN_REQUIRED, tokenization policy, tokenize at write time, external tokenization, FPE, PII, sensitive data, classification, run classification, SYSTEM$CLASSIFY, classifier, classification profile, DATA_CLASSIFICATION_LATEST, detect PII, GDPR, CCPA, PCI, tag sensitive columns, governance maturity score, governance posture, how well governed, data observability, observability maturity, DMF coverage, lineage usage, observability assessment, data steward, object contact, assign contact, who owns this table, contact report, SET CONTACT, /data-governance Create a new policy."
---

# Data Governance

Route general data-governance, catalog & audit queries, data policy work, sensitive data classification, governance maturity assessment, and object contact management to the right sub-skill.

> **Fast-path: UI policy slash-commands.** If the user's first message starts with one of the data-governance UI slash-commands below, load `workflows/data-policy.md` AND the matching workflow file together, and follow the 2-stage UI workflow exclusively. Do not load other layers. Do not ask the universal intake questions.
>
> - `/data-governance Create a new <policy type> policy for me` (any of: masking, row access, projection, aggregation, join, tokenization) → also load `workflows/data-policy/L4_workflow_create_2stage_ui.md`
> - `/data-governance Edit the <POLICY_KIND> POLICY named <POLICY_NAME> located at <DB>.<SCHEMA>.` → also load `workflows/data-policy/L4_workflow_edit_2stage_ui.md`

## When to Use

Activate this skill when the user asks about any of:

- **Policy keywords**: "masking policy", "row access policy", "projection policy", "aggregation policy", "join policy", "tokenization policy", "data policy", "audit policies", "create policy", "policy best practices", "tag-based masking", "tag-based tokenization", "role-based access control for columns", "protect sensitive data", "column masking", "TIMESTAMP masking", "JOIN_REQUIRED", "JOIN_CONSTRAINT", "tokenize at write time", "external tokenization", "FPE", "format-preserving encryption", "/data-governance Create a new policy"
- **Classification keywords** *(always use this skill if the keywords matches— do not answer with general knowledge or the catalog workflow)*: "PII", "sensitive data", "classify", "classification", "data classification", "manual data classification", "run data classification", "run classification", "run manual classification", "automatic data classification", "set up automatic classification", "enable automatic classification", "SYSTEM$CLASSIFY", "auto-classification", "find sensitive data", "classify my table", "classification profile", "Data Privacy Classification Profile", "privacy profile", "custom classifier", "create classifier", "regex pattern", "value regex", "semantic category", "privacy category", "IDENTIFIER", "QUASI_IDENTIFIER", "SENSITIVE", "DATA_CLASSIFICATION_LATEST", "detect PII", "find PII", "scan for PII", "GDPR compliance", "CCPA compliance", "PCI data detection", "auto-tag columns", "tag sensitive columns", "tag PII columns", "minimum_object_age_for_classification_days", "maximum_classification_validity_days", "auto_tag", "unset classification profile", "internal ID classifier", "internal code detection"
- **Catalog & audit keywords**: "access history", "who has access", "who accessed", "permissions", "role hierarchy", "grants", "audit trail", "query history", "object dependencies", "compliance", "catalog", "users", "roles", "schema change", "column changed", "column definition", "DDL history", "has column changed", "when was this column changed", "what is the data type of", "column metadata"
- **Governance maturity keywords**: "governance maturity score", "governance posture", "governance assessment", "governance health", "governance recommendations", "governance checklist", "how well governed is my account"
- **Observability maturity keywords**: "data observability score", "observability maturity", "observability assessment", "DMF coverage", "quality monitoring maturity", "pipeline monitoring maturity", "dashboard data quality", "BI tool monitoring", "external lineage", "lineage for RCA", "impact analysis readiness"
- **Object contact keywords**: "data steward", "object contact", "assign contact", "create contact", "contact report", "who owns this table", "who is responsible for", "SET CONTACT", "STEWARD contact", "ACCESS_APPROVAL contact", "SUPPORT contact", "data stewardship", "contact inheritance", "GET_CONTACTS"

## Workflow Decision Tree

```
User request
  |
  v
Step 1: Identify intent
  |
  ├── Masking policy / row access policy / projection policy / aggregation policy /
  |   join policy / tokenization policy / audit policies / tag-based masking or
  |   tokenization / role-based column access / protect sensitive data /
  |   column masking / TIMESTAMP masking / clean room joins / tokenize at write time
  |         └──> Load workflows/data-policy.md
  |             (data-policy.md will further detect the UI slash-command
  |              `/data-governance Create a new <policy type> policy for me`
  |              and route to its 2-stage UI workflow if matched.)
  |
  ├── PII / sensitive data / classification / data classification / run classification /
  |   manual data classification / automatic data classification / SYSTEM$CLASSIFY /
  |   classifier / custom classifier / create classifier / regex pattern / value regex /
  |   semantic category / privacy category / IDENTIFIER / QUASI_IDENTIFIER / SENSITIVE /
  |   classification profile / Data Privacy Classification Profile / DATA_CLASSIFICATION_LATEST /
  |   detect PII / find PII / scan for PII / auto-classification / GDPR / CCPA / PCI /
  |   auto-tag columns / tag sensitive columns / unset classification profile /
  |   minimum_object_age_for_classification_days / maximum_classification_validity_days / auto_tag
  |         └──> Load workflows/sensitive-data-classification.md
  |
  ├── Governance maturity score / governance posture / governance assessment /
  |   governance health / governance recommendations / governance checklist /
  |   how well governed
  |         └──> Load workflows/governance-maturity-score.md
  |
  ├── Data observability score / observability maturity / DMF coverage /
  |   quality monitoring maturity / lineage usage / observability assessment
  |         └──> Load workflows/observability-maturity-score.md
  |
  ├── Data steward / object contact / assign contact / create contact /
  |   contact report / who owns this table / SET CONTACT / GET_CONTACTS /
  |   contact inheritance / stewardship
  |         └──> Load workflows/object-contacts.md
  |
  └── Everything else (catalog, access, users, grants, roles, object deps,
      query history, compliance, or any governance question not matched above)
            └──> Load workflows/horizon-catalog.md  ← also the fallback
```

## Workflow

### Step 1: Route to Sub-skill

Identify the user's intent and load the matching sub-skill:

| User Intent | Sub-skill to Load |
|---|---|
| Masking policy, row access policy, projection policy, aggregation policy, join policy, tokenization policy, create policy, audit policies, policy best practices, tag-based masking, tag-based tokenization, role-based column access, protect sensitive data, column masking, TIMESTAMP masking, JOIN_REQUIRED, JOIN_CONSTRAINT, tokenize at write time, external tokenization, FPE, `/data-governance Create a new <policy type> policy for me` | **Load** `workflows/data-policy.md` (which will then route to the 2-stage UI workflow if the slash-command pattern matches, otherwise to the standard create / audit workflows) |
| PII, sensitive data, classify, classification, data classification, run classification, manual data classification, automatic data classification, set up automatic classification, enable automatic classification, SYSTEM$CLASSIFY, auto-classification, custom classifier, create classifier, regex pattern, value regex, semantic category, privacy category, IDENTIFIER, QUASI_IDENTIFIER, SENSITIVE, classification profile, Data Privacy Classification Profile, minimum_object_age_for_classification_days, maximum_classification_validity_days, auto_tag, unset classification profile, DATA_CLASSIFICATION_LATEST, detect PII, find PII, scan for PII, GDPR/CCPA/PCI compliance detection, auto-tag columns, tag PII columns | **Load** `workflows/sensitive-data-classification.md` |
| Governance maturity score, governance posture, governance assessment, governance health, governance recommendations, governance checklist, how well governed | **Load** `workflows/governance-maturity-score.md` |
| Data observability score, observability maturity, DMF coverage, quality monitoring maturity, lineage usage, observability assessment, BI tool monitoring, external lineage | **Load** `workflows/observability-maturity-score.md` |
| Data steward, object contact, assign contact, create contact, contact report, who owns this table, who is responsible for, SET CONTACT, GET_CONTACTS, STEWARD/SUPPORT/ACCESS_APPROVAL contact, contact inheritance, data stewardship | **Load** `workflows/object-contacts.md` |
| Catalog, access history, who has access, permissions, grants, roles, users, query history, object dependencies, compliance, or any other governance or catalog related questions | **Load** `workflows/horizon-catalog.md` |

If the intent spans multiple areas (e.g., "classify my data and set up a masking policy"), load both sub-skills sequentially, starting with classification.

If intent is ambiguous, ask:

```
Which area can I help you with?

1. Horizon Catalog — Access history, who has access, role/grant analysis, object dependencies, compliance queries, catalog exploration
2. Data Policies — Masking policies, row access policies, projection policies
3. Sensitive Data Classification — Detect PII, set up auto-classification, create classifiers
4. Governance Maturity Score — Assess governance posture, score (0–5), recommendations
5. Observability Maturity Score — Assess data observability (DMFs, BI coverage, lineage), score (0–5), recommendations
6. Object Contacts — Assign data stewards, create contacts, generate contact reports, manage stewardship
```

### Step 2: Execute Sub-skill

Follow the loaded sub-skill's workflow completely. Each sub-skill is self-contained with its own templates, references, and stopping points.

**Fallback rule:** If any sub-skill cannot fully answer the question, load `workflows/horizon-catalog.md` for supplemental catalog context.

## Sub-skills

| Sub-skill | File | Purpose |
|---|---|---|
| Horizon Catalog | `workflows/horizon-catalog.md` | Full ACCOUNT_USAGE catalog: access, users, roles, grants, permissions, object dependencies, query history. Default fallback. |
| Data Policy | `workflows/data-policy.md` | **[REQUIRED]** Masking, row access, projection, aggregation, join, and tokenization policy creation and auditing; protect sensitive data; column and TIMESTAMP masking; UI 2-stage create flow via `/data-governance Create a new <policy type> policy for me` |
| Sensitive Data Classification | `workflows/sensitive-data-classification.md` | **[REQUIRED]** PII detection, run/manual/automatic data classification, Data Privacy Classification Profiles, auto-classification setup, GDPR/CCPA/PCI, custom classifiers |
| Governance Maturity Score | `workflows/governance-maturity-score.md` | Assess governance posture across Know/Protect/Monitor pillars; produce maturity score (0–5) and actionable recommendations |
| Observability Maturity Score | `workflows/observability-maturity-score.md` | Assess data observability (Quality Monitoring, BI Coverage, External Lineage, Lineage Usage); score (0–5) and recommendations |
| Object Contacts | `workflows/object-contacts.md` | **[REQUIRED]** Assign data stewards, create contacts, manage contact inheritance, generate contact reports, find objects by contact |

## Stopping Points

- ✋ **On ambiguous intent**: Present the 6-option menu and wait for user selection before loading any sub-skill
- ✋ **Sub-skill stopping points**: Each sub-skill has its own mandatory stopping points — honour them

=== data-products/ ===
---
name: internal-marketplace-org-listing
description: >
  Create organizational listings to share data products via Internal Marketplace.
  Triggers: create data product, share to internal marketplace, publish to internal marketplace,
  share to other accounts, share with other accounts, organization listing, org listing,
  share across accounts, internal marketplace, cross-account sharing, share my agent to other accounts.
  
  WHEN TO USE THIS SKILL:
  - User wants to share with OTHER ACCOUNTS → Use this skill
  - User mentions "internal marketplace" or "data product" (even for same account) → Use this skill
  
  WHEN TO USE RBAC INSTEAD (not this skill):
  - User wants to share with roles in SAME account only
  - User does NOT mention "internal marketplace" or "data product" or "listing"
  - Example: "share this table with ANALYST role" → Use GRANT, not this skill

  WHEN NOT TO USE THIS SKILL:
  - User wants to migrate an EXISTING direct share to an org listing → Use the direct-share-to-org-listing-migration skill instead
  - User wants to migrate an EXISTING personalized listing to an org listing → Use the personalized-listing-to-org-listing-migration skill instead
  - User wants to migrate an EXISTING private data exchange (PDX) listing to an org listing → Use the pdx-listing-to-org-listing-migration skill instead
  
  KEY: If user says "share via internal marketplace" or "as a data product" even for
  same-account roles, use this skill. Otherwise, same-account = regular RBAC grants.
---

# Organizational Listing Provider Skill

Create and publish organizational listings to share data products across accounts within your Snowflake organization via Internal Marketplace.

## When to Use

**USE THIS SKILL when:**
- Sharing objects with **OTHER ACCOUNTS** in the organization
- User mentions **"internal marketplace"** or **"data product"** (even for same account)
- Creating internal marketplace listings as a data provider
- Publishing data products to internal consumers
- Cross-region auto-fulfillment setup

**USE RBAC (not this skill) when:**
- User wants to share with roles in the **SAME account only**
- User does NOT mention "internal marketplace" or "data product"
- Example: "grant access to ANALYST role" → Use `GRANT` command, not this skill

**DO NOT USE THIS SKILL when:**
- User wants to migrate an **existing direct share** to an org listing → Use the `direct-share-to-org-listing-migration` skill instead
- User wants to migrate an **existing personalized listing** to an org listing → Use the `personalized-listing-to-org-listing-migration` skill instead
- User wants to migrate an **existing private data exchange (PDX) listing** to an org listing → Use the `pdx-listing-to-org-listing-migration` skill instead

**Common triggers**: "share to internal marketplace", "create a data product", "share with other accounts", "publish to internal marketplace"

**Documentation**: [Organization Listing Docs](https://docs.snowflake.com/en/user-guide/collaboration/listings/organizational/org-listing-create)

## Quick Flow (Minimal Input)

When user says something like **"share my agent to internal marketplace"** or **"share this object internally"**:

1. **Identify the object(s)** the user wants to share
2. **Ask for required info**:
   ```
   To create the listing, I need:
   1. Who should have access? (all accounts / specific accounts / access must be requested)
   2. What email should I use for support and approver contacts?
   ```
3. **Check for required custom attributes** — run `SHOW AVAILABLE INTERNAL MARKETPLACE CONFIGS` and filter for `props = custom_attribute_type`. If any have `is_required: true`, collect their values using `ask_user_question` before proceeding.
4. **Auto-generate** listing with minimal fields:
   - Title: create a meaningful title that describes the data product and all objects included
   - Description: auto-generated a helpful description on what this data product can do, what objects it includes, and what use cases it can help address
   - Discovery/Access: based on user's input
   - Contacts: use the email provided by the user for both support and approver if only one email is provided, otherwise use the email to the specific contact field specified by the user.
   - Request approval flow: Include `request_approval_type: "REQUEST_AND_APPROVE_IN_SNOWFLAKE"` automatically when access must be requested (access field omitted), or when user explicitly specifies how approvals should be handled
   - Data Dictionary: Add data dictionary for all tables and views added in the data product
5. **Skip data dictionary** for non-table objects (agents, semantic views, functions)
6. **Create and publish** immediately after confirmation

**⚠️ Note**: Data dictionary and usage examples are **only applicable for tables/views**. Skip these for agents, semantic views, functions, and other non-queryable objects.

**⚠️ Cortex Agent Sharing Limitations**: Cortex Agents CANNOT be shared if they:
- Use a custom warehouse in agent spec or tools
- Have tools in different databases
- Have custom `query_timeout` settings
- Have an invalid agent spec

If agent sharing fails, suggest sharing the underlying tables instead.

## Prerequisites

1. **Organization Setup**:
   - Account must be part of a Snowflake organization with `ORGADMIN` role
   - Know your organization's account names (`SHOW ORGANIZATION ACCOUNTS`)

2. **Required Privileges**:
   - `CREATE SHARE` on ACCOUNT
   - `CREATE ORGANIZATION LISTING` on ACCOUNT
   - `USAGE WITH GRANT OPTION` on database/schema to share
   - `MANAGE LISTING AUTO FULFILLMENT` on ACCOUNT (if cross-region)

**Verify with:**
```sql
SELECT CURRENT_ROLE();
SHOW GRANTS TO ROLE <your_role>;
```

## Workflow

```
Start → Step 1: Gather → Step 2: Create Share → Step 3: Create Listing → Step 4: Verify → Done
            ↑                                         ↑
      ⚠️ STOP                                   ⚠️ STOP
```

### Step 1: Gather Requirements

**Goal:** Collect all information needed to create the share and listing.

**Actions:**

1. **Ask** the user:
   ```
   To create your organizational listing, please provide:
   
   1. **Objects to share**: Which database/schema/tables/views/semantic views?
      (Please list the EXACT objects - only these will be added to the share)
   2. **Access**: Who should have access?
      - All internal accounts (or user already said "share with all accounts")
      - Specific accounts only (please list them)
   3. **Contact email**: What email should be used for support and approver contacts?
   4. **Organization profile** Which organization profile should be used for this listing? 
      - The system-generated default INTERNAL profile
      - An available custom profile in your organization (please specify the name)
   ```

2. **Auto-generate** (do not ask user for these):
   - **Title**: Create a meaningful title that describes the data product and all objects included
   - **Description**: Generate a helpful description explaining what this data product offers, what objects it includes, and what use cases it can address
   - **Data Dictionary**: Add data dictionary for all tables and views in the data product
   - **Support & Approver contacts**: 
      - If the user provides TWO distinct emails with labels (e.g., "Support Contact: email1" and "Approver Contact: email2"), map each email to its corresponding field (support_contact = email1, approver_contact = email2)
      - If the user provides only ONE email, use it for BOTH support_contact and approver_contact fields

   **⚠️ CRITICAL**: Only share objects the user explicitly lists. Never add:
   - INFORMATION_SCHEMA
   - System schemas or tables
   - Objects not explicitly requested by the user

3. **If user asks to share "all objects in a schema"**, discover them:
   ```sql
   -- Get all tables
   SHOW TABLES IN SCHEMA <database>.<schema>;
   
   -- Get all views
   SHOW VIEWS IN SCHEMA <database>.<schema>;
   
   -- Get all semantic views (NOT included in SHOW VIEWS)
   SHOW SEMANTIC VIEWS IN SCHEMA <database>.<schema>;
   ```
   Compile the list from all three commands, then confirm with user before proceeding.

4. **If user mentions sharing to accounts or targeting accounts, or if user mentions targeting/sharing to regions**

   **Step A**: Verify whether a specified account is a valid account in the organization:
   Fetch all the accounts in the organization by running:
   ```sql
   SHOW ACCOUNTS;
   -- record query id
   ```
   **⚠️ CRITICAL**: DO NOT run `SHOW ORGANIZATION ACCOUNTS` to fetch the accounts.
   **⚠️ CRITICAL**: `SHOW ACCOUNTS` output may be truncated in large organizations. If the result indicates truncation (e.g., "N row(s) shown but more may have been returned"), always use `RESULT_SCAN` with a WHERE filter to search for specific accounts in the response of `SHOW ACCOUNTS` rather than scanning the raw output visually:
    ```sql
   -- use the returned `account_name` and `snowflake_region` for the following steps.
   SELECT "account_name", "account_locator", "snowflake_region"
   FROM TABLE(RESULT_SCAN(<query id of show accounts>))
   WHERE UPPER("account_name") = '<ACCOUNT>' OR UPPER("account_locator") = '<ACCOUNT>';
    ```

   If the user specified the account name in the format of "<organization name>.<account alias>", use the account alias as the account name for account name verification and following steps if the organization name is the same as the current account. ALWAYS use `account_name` instead of `account_locator` in the following steps even when the user specified the account locator.
   
   **Step B**: Use the exact account name in `organization_targets`:
   
   **⚠️ CRITICAL - Account Name Format:**
   - Use ONLY the `account_name` from `SHOW ACCOUNTS`
   - **NEVER** append region names
   - **NEVER** use account locators
   
   ```yaml
   organization_targets:
     discovery:
       - account: "HR"  # Use exact account_name from SHOW ACCOUNTS
     access:
       - account: "HR"  
   ```
   
   **⚠️ OPTIMIZATION - For "current account" or "same account":**
   
   When instruction mentions "**current account**", "**same account**", or "roles in this account", you can use `CURRENT_ACCOUNT_NAME()` directly without needing to query `SHOW ACCOUNTS`:
   
   ```sql
   SELECT CURRENT_ACCOUNT_NAME() as account_name;
   ```
   
   Use the returned value directly in `organization_targets`:
   
   ```yaml
   organization_targets:
     access:
       - account: "PM_AWS_US_WEST_2"  # From CURRENT_ACCOUNT_NAME()
         roles: ['ACCOUNTADMIN', 'SYSADMIN']
   ```

5. **Verify the specified organization profile**:
   
   Find all the organization profiles available in this organization:
   ```sql
   SHOW AVAILABLE ORGANIZATION PROFILES;
   -- Convert the user-specified organization profile name to all uppercase if needed and look for the exact organization profile name from the 'name' column.
   ```
   **⚠️ CRITICAL**: An organization profile is only available for publishing listings when the exact name matches with the uppercase format of the user-specified name, and the 'can_publish_listings_with_profile' column for this organization profile is true.

   If the specified organization profile is not found, list the names of the available organization profiles with the 'can_publish_listings_with_profile' column as true and ask the user to choose from one of these options.
   

6. **Check for required custom attributes**:

   Run:
   ```sql
   SHOW AVAILABLE INTERNAL MARKETPLACE CONFIGS;
   ```
   
   - Filter to only rows where `props` = `custom_attribute_type` — ignore rows with other types (e.g., `notification_integration_name`)
   - If no filtered rows have `is_required: true` → **skip silently**, do not mention custom attributes to the user
   - If any rows have `is_required: true` → use the `ask_user_question` tool to collect values. Present each required attribute as its own individual question (up to 4 per call):
     - **Single/multi-select attributes** (predefined options exist): use `options` with each option's `display_name` as the label. Use `multiSelect: true` if the attribute allows multiple values.
     - **Free-text attributes** (no predefined options): use a text input with a sensible `defaultValue` if one can be inferred
     - If there are more than 4 required attributes, batch them in groups of up to 4 per `ask_user_question` call
   - **List ALL valid options** from the result for constrained attributes — do not summarize or truncate
   - When writing values to the manifest, use the `display_name` field (not `value`) for each selected option
   - **Do not ask about optional attributes** (`is_required: false`) unless the user explicitly requests them
   - **⚠️ MANDATORY STOPPING POINT**: Do NOT proceed to generate the manifest until all required custom attribute values have been successfully collected from the user

7. **Get current region** (needed for locations):
   ```sql
   SELECT CURRENT_REGION();
   ```

**⚠️ MANDATORY STOPPING POINT**: Do NOT proceed until user provides all required information.

---

### Step 2: Create the Share

**Goal:** Create the underlying share with correct privilege grants.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚠️ CRITICAL: GRANT ORDER MATTERS - FOLLOW EXACTLY OR SHARE WILL FAIL       ║
║                                                                              ║
║  1. FIRST:  GRANT USAGE ON DATABASE  ← Must be first!                        ║
║  2. SECOND: GRANT USAGE ON SCHEMA                                            ║
║  3. LAST:   GRANT SELECT ON TABLE/VIEW/SEMANTIC VIEW                         ║
║                                                                              ║
║  Error "Share does not currently have a database" = Wrong order!             ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**⚠️ CRITICAL**: Only add objects the user explicitly specifies to the share. 
- Do NOT add INFORMATION_SCHEMA
- Do NOT add system schemas
- Do NOT add objects the user didn't request
- Ask user to confirm the exact list of objects before creating the share

**Actions:**

1. **Create share**:
   ```sql
   CREATE SHARE IF NOT EXISTS <share_name>
     COMMENT = '<description of what is being shared>';
   ```

2. **Grant privileges** (in order!):
   ```sql
   -- FIRST: Database
   GRANT USAGE ON DATABASE <database_name> TO SHARE <share_name>;
   
   -- SECOND: Schema
   GRANT USAGE ON SCHEMA <database_name>.<schema_name> TO SHARE <share_name>;

   -- LAST: Tables/Views/Semantic Views
   -- For tables:
   GRANT SELECT ON TABLE <database_name>.<schema_name>.<table> TO SHARE <share_name>;
   -- Or for all tables:
   GRANT SELECT ON ALL TABLES IN SCHEMA <database_name>.<schema_name> TO SHARE <share_name>;
   
   -- ⚠️ VIEWS: Must grant individually (bulk grant on views is restricted)
   GRANT SELECT ON VIEW <database_name>.<schema_name>.<view> TO SHARE <share_name>;
   -- NOTE: "GRANT SELECT ON ALL VIEWS" is NOT supported for shares
   
   -- ⚠️ SEMANTIC VIEWS: Use SELECT (not USAGE)
   GRANT SELECT ON SEMANTIC VIEW <database_name>.<schema_name>.<semantic_view> TO SHARE <share_name>;
   ```
   
   **⚠️ Finding Semantic Views**: Use `SHOW SEMANTIC VIEWS` (not `SHOW VIEWS`):
   ```sql
   SHOW SEMANTIC VIEWS IN SCHEMA <database_name>.<schema_name>;
   ```

   **If error "Non-secure object can only be granted to shares with "secure_objects_only" property set to false." happens when granting any of the tables, views, or functions to the share** → List all the options and ask the user to confirm how they want to proceed with the share creation:
   - Option 1: Alter the share to allow sharing non-secure objects. Show a bold warning with this option that a share cannot set secure_objects_only to true once it's set to false, execute
   ```sql
   ALTER SHARE <share_name> SET SECURE_OBJECTS_ONLY = FALSE;
   ```
   - Option 2: Convert this object to a secure object. Show a bold warning with this option that users should weigh the trade-off between data privacy/security and query performance before proceeding. If the user chooses option 2, execute: 
   ```sql
   ALTER VIEW <database_name>.<schema_name>.<view> SET SECURE;
   ```
   - Option 3: Skip granting this non-secure object to the share. 

3. **Verify share contents**:
   ```sql
   DESCRIBE SHARE <share_name>;
   ```

**Output:** Share created with all requested objects granted.

**If error "Share does not currently have a database"** → Check grant order (database must be first).

**⚠️ Metadata Visibility Note**: Granting `USAGE ON DATABASE` makes all schema names visible to consumers in metadata, even if they can't query objects in those schemas.

---

### Step 3: Create the Listing

**Goal:** Create organizational listing with YAML manifest including data dictionary.

**Actions:**

0. **Organization Targets - Discovery & Access**:
   
   **⚠️ CRITICAL - How to handle discovery and access targets:**
   
   - If instruction says "**Do not** allow anyone to discover" or "**No discovery**" → **OMIT the `discovery` field entirely** from `organization_targets`:
     ```yaml
     organization_targets:
       access:
         - account: "ACCOUNT_NAME"
       # NO discovery field when discovery is disabled
     ```
   
   - If instruction says "**access must be requested**" or "**no automatic access**" or "**accessible to no one**" or "**discovery-only**" → **OMIT the `access` field entirely** from `organization_targets`. **Discovery targets must still be specified** based on the user's instruction. Also include `request_approval_type: "REQUEST_AND_APPROVE_IN_SNOWFLAKE"` so consumers have a mechanism to request access:
     ```yaml
     organization_targets:
       discovery:
         - all_internal_accounts: true  # or specific accounts — based on user instruction
       # NO access field when access must be requested
     
     request_approval_type: "REQUEST_AND_APPROVE_IN_SNOWFLAKE"  # top-level field, not nested
     ```
   
   - If instruction says "**all accounts** in the organization" for discovery or access → use `all_internal_accounts: true`:
     ```yaml
     organization_targets:
       discovery:
         - all_internal_accounts: true
       access:
         - all_internal_accounts: true
     ```
   
   - If instruction specifies specific accounts for discovery or access → list them:
     ```yaml
     organization_targets:
       discovery:
         - account: "ACCOUNT_1"
       access:
         - account: "ACCOUNT_1"
     ```
   
   **⚠️ CRITICAL - Role-based access:**
   - If instruction mentions roles (e.g., "ACCOUNTADMIN role in PM_SHARING" or "ACCOUNTADMIN and SYSADMIN roles") → include `roles` field in the following format:
     ```yaml
     organization_targets:
       access:
         - account: "PM_SHARING"
           roles: ['ACCOUNTADMIN', 'SYSADMIN']
     ```

1. **Access Regions**:
   
   **⚠️ The listing owner can specify any access regions they want. This is independent of auto-fulfillment.**
   
   **How to choose access regions:**
   
   - **If instruction explicitly says "all regions" or "target all regions":**
     - Use the literal value `ALL`:

   
   - **If instruction specifies specific regions:**
     - Use those specific regions (e.g., `PUBLIC.AWS_US_WEST_2`, `PUBLIC.AWS_US_EAST_1`)
   
   - **If instruction doesn't specify regions:**
     - Default to the current account's region (e.g., `PUBLIC.AWS_US_WEST_2`)
   
   **Note:** Access region choice does NOT determine auto-fulfillment. See section 5 below for auto-fulfillment logic.

   When using specific access regions:
   - If user requests targeting specific regions, or mentions targeting only the target accounts' regions or locations, or mentions targeting the minimal set of regions possible, add the access region names to the manifest.

      Each access region name should be in the format of "<region_group>.<snowflake_region>", e.g., "PUBLIC.AWS_US_WEST_2". If the user specified a set of regions, use the specified region list; otherwise add the regions of all targeted accounts without duplication. If the region group is not specified for any snowflake regions, run:
      ```sql
      SHOW REGIONS IN DATA EXCHANGE SNOWFLAKE_DATA_MARKETPLACE;
      ```
      and use the values in the `region_group` field in the response for the corresponding `snowflake_regions` of the accounts. 

      If any of the target accounts are outside the access regions, list the following options and ask user for supplemental information:
         - Skip this target account that is not in any of the specified access regions.
         - Add the access region "<region_group>.<snowflake_region>" to the access regions

   Add the access regions to the manifest in the following format:
   ```yaml
      locations:
      access_regions:
         - name: "<REGION_NAME>"
         - name: "<REGION_NAME_2>"
   ```

2. **Auto-select tables for data dictionary** (up to 5):
   
   **⚠️ SKIP this step if sharing non-table objects** (agents, semantic views, functions). Data dictionary is only supported for tables and views.
   
   - Query the share to identify objects:
     ```sql
     DESCRIBE SHARE <share_name>;
     ```
   - **Prioritize** (select up to 5 most relevant):
     - Main fact tables (transactions, events, orders)
     - Key dimension tables (customers, products)
     - Commonly queried views
     - Aggregated/summary tables
   - **Exclude**: staging tables, internal/system tables, rarely used lookups
   
   - **Auto-detect PII fields** in selected objects (tables only):
     ```sql
     -- Check column names for PII patterns
     DESCRIBE TABLE <database>.<schema>.<table>;
     
     -- If available, check Snowflake classification tags
     SELECT * FROM TABLE(
       INFORMATION_SCHEMA.TAG_REFERENCES('<database>.<schema>.<table>', 'TABLE')
     );
     ```
   - **Common PII patterns to detect**:
     - Names: `first_name`, `last_name`, `full_name`, `customer_name`
     - Contact: `email`, `phone`, `mobile`, `address`, `zip`, `postal`
     - IDs: `ssn`, `social_security`, `tax_id`, `passport`, `driver_license`
     - Financial: `credit_card`, `account_number`, `bank_account`
     - Health: `dob`, `date_of_birth`, `medical_id`, `patient_id`
   - **Note PII fields in description** for consumer awareness

3. **Auto-generate SQL usage examples** (tables/views only):
   
   **⚠️ SKIP if no tables/views in the data product** (e.g., only agents or functions).
   
   ```
   ╔══════════════════════════════════════════════════════════════════════════╗
   ║  ⚠️ MANDATORY: Run DESCRIBE TABLE for EACH table BEFORE writing queries ║
   ║                                                                          ║
   ║  NEVER assume column names! Get the ACTUAL column names first.           ║
   ╚══════════════════════════════════════════════════════════════════════════╝
   ```
   
   **Step 0: Get ACTUAL column names (MANDATORY)**
   ```sql
   -- Run this for EACH table before writing any usage examples
   DESCRIBE TABLE <database>.<schema>.<table>;
   ```
   Use ONLY the column names returned by DESCRIBE. Never guess or assume.
   
   **Step 2: Think about what questions users would ask this data**
   
   Based on the table/column names, deduce what the data represents and what insights users would want:
   
   | Data Type | Example Tables | Questions Users Would Ask | Query Pattern |
   |-----------|----------------|---------------------------|---------------|
   | **Sales/Orders** | orders, transactions, sales | "What's the revenue by region?" "Top customers?" | GROUP BY with SUM, ranking |
   | **Customer/User** | customers, users, accounts | "How many active users?" "Customer segments?" | COUNT, segmentation, cohorts |
   | **Events/Logs** | events, logs, activity | "What happened last 7 days?" "Error rate?" | Time filters, COUNT by type |
   | **Product/Inventory** | products, inventory, catalog | "What's in stock?" "Top products?" | JOINs, availability checks |
   | **Financial** | invoices, payments, budgets | "Monthly spend?" "Outstanding balance?" | SUM, date aggregations |
   
   **Step 3: Generate 2-3 meaningful queries**
   
   **Rules:**
   - **ALWAYS use fully qualified table names**: `DATABASE.SCHEMA.TABLE`
   - **NEVER use `SELECT *`** - select specific, useful columns
   - **Include aggregations** (SUM, COUNT, AVG) with GROUP BY
   - **Include JOINs** if multiple related tables exist
   - **Include date filters** for time-series data
   - Validate SQL compiles before adding to manifest
   
   **Example - For a CALLS table with columns (call_id, agent_id, duration_seconds, created_at, status):**
   ```sql
   -- Example 1: Call volume and average duration by day
   SELECT 
     DATE_TRUNC('day', created_at) as call_date,
     COUNT(*) as total_calls,
     AVG(duration_seconds) as avg_duration_sec,
     SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_calls
   FROM MYDB.MYSCHEMA.CALLS
   WHERE created_at >= DATEADD('day', -30, CURRENT_DATE)
   GROUP BY 1
   ORDER BY 1 DESC;
   
   -- Example 2: Top agents by call volume
   SELECT 
     agent_id,
     COUNT(*) as total_calls,
     SUM(duration_seconds) as total_duration,
     AVG(duration_seconds) as avg_call_duration
   FROM MYDB.MYSCHEMA.CALLS
   GROUP BY agent_id
   ORDER BY total_calls DESC
   LIMIT 10;
   ```

4. **Request approval flow**
   
   **How to interpret user instructions:**
   - If instruction says "Request approvals are handled inside Snowflake" → **include** `request_approval_type: "REQUEST_AND_APPROVE_IN_SNOWFLAKE"`
   - If instruction says "Request approvals are handled outside Snowflake" → **include** `request_approval_type: "REQUEST_AND_APPROVE_OUTSIDE_SNOWFLAKE"`
   - If user does not specify how approvals are handled → **omit** the field (defaults to `REQUEST_AND_APPROVE_OUTSIDE_SNOWFLAKE`)

   Example when approvals are handled inside Snowflake:
   ```yaml
   request_approval_type: "REQUEST_AND_APPROVE_IN_SNOWFLAKE"
   ```

5. **Auto-fulfillment**:
   
   **⚠️ When auto-fulfillment is REQUIRED (include it when ANY of these apply):**
   - Targeting an account in a different region than the current account, OR
   - Targeting all accounts in the organization (which may include accounts in different regions), OR
   - Using a remote access region (an access region different from the current account's region)
   
   **⚠️ When auto-fulfillment is NOT required (omit it):**
   - Targeting only the current account (same region)
   - Targeting only accounts in the same region as the current account AND using only that region as access region
   
   Add auto-fulfillment setting to the manifest in this format **ONLY when required**:
   ```yaml
   auto_fulfillment:
      refresh_type: "SUB_DATABASE"
      refresh_schedule: "10 MINUTE"  # Check existing listings on same DB for schedule
   ```

6. **Generate the manifest** and present to user:

```sql
CREATE ORGANIZATION LISTING <listing_name>
  SHARE <share_name> AS
$$
title: "<Listing Title - max 110 chars>"
description: |
     <Detailed description - supports Markdown>

organization_profile: "<Organization Profile Name>"

organization_targets:
  discovery:
    # Targeting all accounts in the organization
    - all_internal_accounts: true
    # OR for specific accounts (use singular "account:" NOT "accounts:"):
    # - account: "ACCOUNT_1"
    # - account: "ACCOUNT_2"
    # OR omit discovery field entirely if user says "Do not allow discovery"
  access:
    # Targeting all accounts in the organization
    - all_internal_accounts: true
    # OR for specific accounts:
    # - account: "ACCOUNT_1"
    # - account: "ACCOUNT_2"
    # ⚠️ Use ONLY account_name from SHOW ACCOUNTS
    # ⚠️ Omit this entire access block if user says "access must be requested"

support_contact: "<support_email>"  # Use user's support contact email
approver_contact: "<approver_email>"  # Use user's approver contact email, always include

# Include request_approval_type if user specifies approval handling method
# Examples:
# request_approval_type: "REQUEST_AND_APPROVE_IN_SNOWFLAKE"  # When "handled inside Snowflake"
# request_approval_type: "REQUEST_AND_APPROVE_OUTSIDE_SNOWFLAKE"  # When "handled outside Snowflake"
# Omit if not specified (defaults to REQUEST_AND_APPROVE_OUTSIDE_SNOWFLAKE)

# Always include data_dictionary for discoverability (up to 5 objects)
# ⚠️ Use UNQUOTED identifiers for database, schema, and object names
data_dictionary:
  featured:
    database: DATABASE_NAME  # No quotes!
    objects:
      - schema: SCHEMA_NAME  # No quotes!
        name: TABLE_1  # No quotes!
        domain: TABLE
      - schema: SCHEMA_NAME
        name: TABLE_2
        domain: TABLE
      # Auto-select up to 5 most relevant tables/views

   # Always include usage_examples to help consumers (2-3 examples)
   # ⚠️ ALWAYS use fully qualified table names: DATABASE.SCHEMA.TABLE
usage_examples:
  - title: "<Example Title - max 110 chars>"
    description: "<What this query demonstrates - max 300 chars>"
    query: |
      SELECT col1, col2 FROM DATABASE.SCHEMA.TABLE WHERE condition
  - title: "<Second Example>"
    description: "<Description>"
    query: |
      SELECT * FROM DATABASE.SCHEMA.TABLE LIMIT 10

   # Access regions: Can be ALL, specific regions, or current region based on instruction
   # Examples:
   #   - "all regions" instruction → ALL
   #   - "specific regions" → PUBLIC.AWS_US_WEST_2, PUBLIC.AWS_US_EAST_1
   #   - No mention → current region (e.g., PUBLIC.AWS_US_WEST_2)
locations:
  access_regions:
    - name: "PUBLIC.AWS_US_WEST_2"  # Default: current region if not specified
    
# Include auto_fulfillment ONLY when:
# - Targeting accounts in different region, OR
# - Targeting all accounts, OR  
# - Using remote access region (different from current region)
# auto_fulfillment:
#   refresh_type: "SUB_DATABASE"
#   refresh_schedule: "10 MINUTE"  # Check existing listings on same DB for schedule

# Include custom_attributes ONLY when required attributes were found in SHOW AVAILABLE INTERNAL MARKETPLACE CONFIGS
# Omit this block entirely if no required custom attributes exist
# custom_attributes:
# - name: <attribute_name>
#   values:
#     - <value_1>
#     - <value_2>  # include multiple values if the attribute accepts them
$$ PUBLISH = <FALSE if user explicitly specified to create a draft listing or not to publish the listing, otherwise TRUE>;
```

   **⚠️ CRITICAL - PUBLISH flag:**
   - If instruction says "Create a **draft** listing" → use `PUBLISH = FALSE`
   - If instruction says "Create and **publish**" or just "Create" → use `PUBLISH = TRUE`
   - Default to `TRUE` unless explicitly told to create a draft

   **⚠️ CRITICAL - Auto-fulfillment:**
   Include `auto_fulfillment` when ANY of these apply:
   - Targeting accounts in different region than current account
   - Targeting all accounts in the organization
   - Using remote access region (different from current account's region)
   
   **⚠️ Refresh Schedule**: If other listings exist on the same database, the refresh_schedule MUST match. Query existing listings to check.

   **⚠️ CRITICAL**: Do NOT use CREATE LISTING syntax to create organizational listing

**⚠️ MANDATORY STOPPING POINT**: Present complete manifest to user for confirmation before executing.

Show summary:
```
Summary:
- Share name: <share_name>
- Objects included: <list of tables/views>
- Featured in data dictionary: <up to 5 key tables/views>
- PII detected: <Yes/No - list fields if Yes>
- Usage examples: <number of examples generated>
- Discovery: <all accounts / specific accounts>
- Access: <all accounts / specific accounts with roles>
- Regions: ALL (default)

Does this look correct? (Yes/No)
```

**Only execute after user confirms.**

---

### Step 4: Verify and Notify

**Goal:** Confirm listing created and provide user with access information.

**Actions:**

1. **Verify listing**:
   ```sql
   SHOW LISTINGS;
   DESCRIBE LISTING <listing_name>;
   ```

2. **Notify user** (always show listing TITLE, not internal name):
   - To get the listing global name, run:
   ```sql
   DESCRIBE LISTING <listing_name>
   ```
   and use the exact name from the 'global_name' column. 

   ```
   ✅ Your data product "<LISTING_TITLE>" has been created successfully!
   
   **Listing Title:** <listing_title>  ← Always show title to user
   **Share Name:** <share_name>
   **State:** PUBLISHED (automatic for org listings)
   **Listing URL:** https://app.snowflake.com/marketplace/internal/listing/<listing_global_name>
   
   **To view your listing:**
   1. Go to Snowsight: https://app.snowflake.com
   2. Navigate: Data Sharing → Internal Sharing → Listings tab
   3. Find your listing: "<listing_title>"
   ```
   
   **⚠️ Always display the listing TITLE** (e.g., "Customer Analytics Data"), not the internal listing name (e.g., CUSTOMER_ANALYTICS_LISTING)

**Output:** Published organizational listing accessible to target accounts.

---

### Step 5: Manage Listing (Optional)

**If user wants to update the listing:**

**Add objects to share:**
```sql
GRANT SELECT ON TABLE <db>.<schema>.<new_table> TO SHARE <share_name>;
DESCRIBE SHARE <share_name>;
```

**Update manifest:**
```sql
-- ⚠️ NOTE: Use "AS" without "SET" when updating manifest content
-- ⚠️ NOTE: "CREATE OR REPLACE" is NOT supported for org listings - use ALTER
ALTER LISTING <listing_name> AS $$
title: "Updated Title"
-- ... updated manifest fields
$$;
```

**Publish listing** (if not auto-published):
```sql
-- ⚠️ Use ALTER LISTING ... PUBLISH (not SET STATE = PUBLISHED)
ALTER LISTING <listing_name> PUBLISH;
```

**Unpublish listing:**
```sql
ALTER LISTING <listing_name> UNPUBLISH;
```

**Delete listing:**
```sql
DROP LISTING <listing_name>;
DROP SHARE <share_name>;  -- Optional
```

**Handle access requests** (if using `REQUEST_AND_APPROVE_IN_SNOWFLAKE`):
```sql
-- View pending requests
SELECT * FROM SNOWFLAKE.DATA_SHARING_USAGE.LISTING_ACCESS_REQUESTS
WHERE LISTING_NAME = '<listing_name>' AND REQUEST_STATUS = 'PENDING';

-- Approve/deny
CALL SYSTEM$APPROVE_LISTING_REQUEST('<request_id>');
CALL SYSTEM$DENY_LISTING_REQUEST('<request_id>', 'Reason');
```

---

## Organization Targets Quick Reference

**⚠️ SYNTAX WARNING**: Use singular `account:` NOT plural `accounts:`

**All accounts discover & access:**
```yaml
organization_targets:
  discovery:
    - all_internal_accounts: true
  access:
    - all_internal_accounts: true
```

**Specific accounts for discovery AND access:**
```yaml
# ⚠️ Use singular "account:" - NOT "accounts:"
organization_targets:
  discovery:
    - account: "ACCOUNT_1"  # ← singular "account:"
    - account: "ACCOUNT_2"
  access:
    - account: "ACCOUNT_1"
    - account: "ACCOUNT_2"
```

**Specific accounts with roles:**
```yaml
organization_targets:
  discovery:
    - all_internal_accounts: true
  access:
    - account: 'finance_account'  # ← singular "account:"
      roles: ['analyst', 'manager']
    - account: 'analytics_account'
```

---

## Stopping Points

- ✋ **Step 1**: After gathering requirements (confirm all inputs before proceeding)
- ✋ **Step 3**: After generating manifest (confirm YAML before execution)

**Resume rule:** Upon user approval, proceed directly to next step without re-asking.

## Output

- Published organizational listing in Internal Marketplace
- Share containing specified database objects
- Snowsight URL for listing management
- ULL (Uniform Listing Locator) for referencing the listing

## Common Errors Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| "Share does not currently have a database" | Wrong grant order | Grant DATABASE first, then SCHEMA, then TABLES |
| "invalid identifier 'column_name'" | Wrong column name in usage_examples | Run `DESCRIBE TABLE` first, use actual column names |
| YAML syntax error with `accounts:` | Used plural | Use singular `account:` not `accounts:` |
| "Semantic view not found" | Used `SHOW VIEWS` | Use `SHOW SEMANTIC VIEWS` instead |
| "USAGE not supported for semantic view" | Wrong privilege | Use `GRANT SELECT ON SEMANTIC VIEW` |
| "Missing approver contact" | Field required | Always include `approver_contact` |

## References

For detailed information, **load** these files:

- `references/manifest-reference.md`: All manifest fields, data attributes, data dictionary config, access control setup
- `references/templates.md`: Quick copy-paste templates for common scenarios
- `references/errors.md`: Common errors and troubleshooting guide

## Known Limitations

- Each share can be attached to **one listing only**
- Reader accounts not supported with organizational listings
- Native App listings don't support target roles
- Multiple regions require auto-fulfillment configuration
- Provider studio analytics not supported for org listings

=== data-quality/ ===
---
name: data-quality
description: "Monitor, analyze, and enforce data quality using Snowflake DMFs. Schema-level and per-table DMF attachment, health scoring, incident investigation, circuit breakers, table comparison, dataset popularity, ad-hoc assessment, prompt quality scoring, and per-group monitoring via WITHIN GROUP clause."
---

# Data Quality

Monitor, analyze, and enforce data quality across Snowflake schemas using Data Metric Functions (DMFs). Compare tables for migration validation, regression testing, and data reconciliation. Analyze dataset popularity and usage patterns to prioritize governance.

## When to Use

Activate this skill when the user mentions any of:

- **Health/trust keywords**: "schema health", "data quality score", "can I trust my data", "quality check"
- **DMF keywords**: "data metric function", "DMF", "DMF results", "metrics failing"
- **Issue investigation**: "why is this table failing", "what's wrong with my data", "root cause", "quality issues"
- **Change detection**: "quality regression", "what changed", "what broke", "did quality get worse"
- **Trend keywords**: "quality trends", "is quality improving", "quality over time"
- **Alerting keywords**: "quality alerts", "SLA monitoring", "alert me on quality drops", "enforce DQ SLAs"
- **Table comparison keywords**: "compare tables", "data diff", "table diff", "validate migration", "dev vs prod data", "find differences", "data reconciliation"
- **Popularity/usage keywords**: "popular tables", "most used tables", "least used", "unused tables", "stale data", "dataset usage", "table popularity", "who uses this table", "is this table used"
- **Ad-hoc / no-DMF keywords**: "check data quality without DMFs", "one-time quality check", "quick quality scan", "assess columns", "check for nulls", "check freshness", "check completeness"
- **Listing quality keywords**: "listing quality", "listing health", "listing freshness", "provider data quality", "consumer data quality", "data product quality", "check my listing"
- **Accepted values / categorical keywords**: "accepted values", "ACCEPTED_VALUES", "value in set", "allowed values", "validate column values", "categorical validation", "column must be in list"
- **Referential integrity keywords**: "referential integrity", "REFERENTIAL_INTEGRITY_COUNT", "orphaned rows", "foreign key check", "FK validation", "cross-table integrity check", "orphan rows"
- **Schema-level DMF keywords**: "add DMF to schema", "monitor whole schema", "schema-level DMF", "ALTER SCHEMA ADD DATA METRIC FUNCTION", "bulk attach DMF", "schema anomaly detection", "monitor all tables", "schema monitoring", "schema data quality"
- **Prompt quality keywords**: "score my prompt", "prompt quality", "prompt linter", "improve my prompt", "rewrite prompt", "prompt engineering", "prompt score"
- **Prompt comparison keywords**: "compare prompts", "prompt regression", "before and after prompt", "prompt iteration"
- **Prompt execution keywords**: "execute prompt", "run both prompts", "test my prompt"
- **Within group / grouped DMF keywords**: "within group", "group by DMF", "per-group metrics", "grouped monitoring", "GROUP LIMIT", "broken down by", "separately for each", "metrics per group"

**Do NOT use** for: non-quality-related schema operations or data access control.

**Cross-skill:** After identifying quality issues (e.g. NULLs, failing DMFs, wrong values), proactively use the **lineage** skill to trace upstream and find where the bad data originated—do not wait for the user to ask. This gives a complete root-cause answer (what is wrong + where it came from).

## Workflow Decision Tree

```
User request
  |
  v
Step 0: Check intent BEFORE preflight
  |
  ├── "recommend monitors" / "what should I monitor" / "set up DMFs" /
  |   "attach DMFs for the first time" / "which DMFs should I add"
  |         └──> Load workflows/monitor-recommendations.md
  |              (DMF-first: profiles columns, ranks by criticality, generates DDL)
  |
  ├── "coverage gaps" / "unmonitored tables" / "monitoring health" /
  |   "what % of tables are monitored" / "noisy monitors" / "silent monitors" /
  |   "DMF cost" / "monitoring coverage report"
  |         └──> Load workflows/coverage-gaps.md
  |
  ├── "investigate DQ incident" / "why did freshness drop" / "why did row count drop" /
  |   "correlate violation" / "DQ incident root cause" / "why did my pipeline fail quality"
  |         └──> Load workflows/dq-incident-investigation.md
  |              (orchestrates: DMF violations → lineage skill → data-governance skill)
  |
  ├── "circuit breaker" / "pause pipeline on violation" / "halt bad data" /
  |   "stop downstream when quality fails"
  |         └──> Load workflows/circuit-breaker.md
  |
  ├── "accepted values" / "ACCEPTED_VALUES" / "value in set" / "allowed values" /
  |   "categorical validation" / "validate column values"
  |         └──> Load workflows/custom-dmf-patterns.md
  |              (Step 1: Prefer ACCEPTED_VALUES; escalate to custom DMF only when needed)
  |
  ├── "add DMF to schema" / "schema-level DMF" / "monitor whole schema" /
  |   "ALTER SCHEMA ADD DATA METRIC FUNCTION" / "bulk attach DMF" /
  |   "schema anomaly detection" / "monitor all tables in schema"
  |         └──> Load workflows/monitor-recommendations.md
  |              (Step 1b: Schema-level fast path for ROW_COUNT + FRESHNESS)
  |
  ├── "referential integrity" / "REFERENTIAL_INTEGRITY_COUNT" / "orphaned rows" /
  |   "FK check" / "foreign key validation" / "cross-table integrity"
  |         └──> Load workflows/monitor-recommendations.md
  |              (Prefer system DMF REFERENTIAL_INTEGRITY_COUNT over custom DMF)
  |
  ├── "within group" / "group by" / "per-group metrics" / "grouped monitoring" /
  |   "monitor by region" / "monitor by category" / "null count per" /
  |   "duplicates by" / "GROUP LIMIT" / "quality by segment" /
  |   "broken down by" / "separately for each" / "per region" / "per category" /
  |   "for each <column> separately" / "which <groups> have the worst" /
  |   "metrics per" / "quality per" / "track <metric> for each <group>"
  |         └──> Load workflows/within-group-dmf.md
  |              (Per-group DMF metrics via WITHIN GROUP clause.
  |               IMPORTANT: If the user wants a DMF metric computed separately
  |               for each value of a column — e.g. "nulls per region",
  |               "quality broken down by category", "which departments have
  |               the worst data" — this is a WITHIN GROUP use case.
  |               Do NOT create dynamic tables, manual GROUP BY queries,
  |               or separate DMF associations per group value.)
  |
  ├── "custom DMF" / "format validation" / "email format check" / "value range check" /
  |   "cross-column validation DMF"
  |         └──> Load workflows/custom-dmf-patterns.md
  |
  ├── "DMF expectations" / "set threshold" / "tune DMF threshold" /
  |   "review expectations" / "expectation management"
  |         └──> Load workflows/expectations-management.md
  |
  ├── Listing quality / ad-hoc check / "without DMFs" / "one-time check"
  |         └──> Load workflows/adhoc-assessment.md
  |              (no DMFs required; works for listings too)
  |
  ├── "score my prompt" / "prompt quality" / "prompt linter" / "prompt score"
  |         └──> Load workflows/prompt-quality.md
  |              (Score via Cortex Complete — no DMFs, no schema needed)
  |
  ├── "improve prompt" / "rewrite prompt" / "prompt engineering" /
  |   "make my prompt better"
  |         └──> Load workflows/prompt-improve.md
  |              (Score + rewrite via Cortex + re-score + before/after)
  |
  ├── "compare prompts" / "prompt regression" / "execute both prompts" /
  |   "test my prompt" / "run both prompts"
  |         └──> Load workflows/prompt-execute-compare.md
  |              (Execute original + improved via Cortex Complete, compare outputs)
  |
  └── None of the above — proceed to Step 1 preflight check
        |
        v
    Step 1 preflight: total_dmfs_attached = 0?
        |
        ├── YES — offer 3 options to user:
        |     1. Set up DMFs (continuous monitoring) ──> Load workflows/monitor-recommendations.md
        |     2. Run ad-hoc one-time assessment ──────> Load workflows/adhoc-assessment.md
        |     3. None / skip
        |
        └── NO (DMFs present) — Step 2: Identify intent
              |
              ├── Health/trust/score ----------> Load workflows/health-scoring.md
              |
              ├── Failures/root cause ---------> Load workflows/root-cause-analysis.md
              |
              ├── Regression/what changed -----> Load workflows/regression-detection.md
              |
              ├── Trends/over time ------------> Load workflows/trend-analysis.md
              |
              ├── Alerts/SLA/notify -----------> Load workflows/sla-alerting.md
              |
              ├── Compare tables/diff/migrate -> Load workflows/compare-tables.md
              |                                    (has its own sub-workflows)
              |
              └── Popularity/usage/unused -----> Load workflows/popularity.md
```

## Critical: Correct Snowflake View/Function Locations

Before executing any query, be aware of the correct data sources:

| Data | Correct Location | Notes |
|---|---|---|
| DMF metric results (values) | `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS()` | **Table function**, not a view. Takes `REF_ENTITY_NAME` and `REF_ENTITY_DOMAIN` params. |
| **Expectation pass/fail status** | `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS` | **View or table function.** Use this for "which expectations are passing/failing" and for violation counts. Has `expectation_violated`, `value`, `expectation_expression`, `measurement_time`. Do not derive pass/fail by joining RESULTS + DATA_METRIC_FUNCTION_EXPECTATIONS. |
| DMF references (config) | `INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES()` | **Table function** per-table or per-schema. Use `REF_ENTITY_DOMAIN => 'table'` for table-level; use `REF_ENTITY_DOMAIN => 'schema'` to see schema-level associations (lowercase enum values). Includes new columns: `LEVEL` (`'TABLE'` or `'SCHEMA'`, uppercase) and `EXCLUDE_TABLE_TYPES`. Also available as `SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES` view (same new columns). |
| DMF expectations (config only) | `SNOWFLAKE.ACCOUNT_USAGE.DATA_METRIC_FUNCTION_EXPECTATIONS` | View with expectation definitions (name, expression). For **status** (pass/fail) use DATA_QUALITY_MONITORING_EXPECTATION_STATUS instead. |
| DMF credit/usage | `SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_USAGE_HISTORY` | View for cost tracking, NOT metric values |

**`SNOWFLAKE.ACCOUNT_USAGE.DATA_QUALITY_MONITORING_RESULTS` does NOT exist.** Never query it. Always use `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS()`.

**Schema-level DMF associations:** When ROW_COUNT or FRESHNESS is added at the schema level via `ALTER SCHEMA ... ADD DATA METRIC FUNCTION`, Snowflake automatically creates object-level associations for all supported table-like objects in the schema (unless excluded). To check which DMFs were added at the schema level, call `INFORMATION_SCHEMA.DATA_METRIC_FUNCTION_REFERENCES()` with `REF_ENTITY_DOMAIN => 'schema'`. Individual object-level references created via schema-level association show `LEVEL = 'SCHEMA'` in the `DATA_METRIC_FUNCTION_REFERENCES` view/function. Use `EXCLUDE_TABLE_TYPES` to see which object types were excluded.

**Correct column names for `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS()`:**
`MEASUREMENT_TIME`, `TABLE_NAME`, `TABLE_SCHEMA`, `TABLE_DATABASE`, `METRIC_NAME`, `METRIC_SCHEMA`, `METRIC_DATABASE`, `VALUE`, `REFERENCE_ID`, `ARGUMENT_NAMES`, `ARGUMENT_TYPES`, `ARGUMENT_IDS`

**Grouped DMF (WITHIN GROUP) results:** When a DMF is attached with `WITHIN GROUP`, `DATA_QUALITY_MONITORING_RESULTS()` includes a `GROUP_BY_INFO` column (VARIANT) containing per-group column IDs and values. `SYSTEM$EVALUATE_DATA_QUALITY_EXPECTATIONS` returns one row per (expectation, group_value) combination with a `GROUP_BY_VALUES` column. Use `SYSTEM$DATA_METRIC_SCAN` with `WITHIN_GROUP_VALUES` parameter to filter results by specific group value.

**Correct column names for `ACCOUNT_USAGE.DATA_METRIC_FUNCTION_REFERENCES`:**
`REF_DATABASE_NAME`, `REF_SCHEMA_NAME`, `REF_ENTITY_NAME`, `REF_ENTITY_DOMAIN`, `METRIC_NAME`, `SCHEDULE`, `SCHEDULE_STATUS`, `LEVEL` (new: `TABLE` or `SCHEMA`), `EXCLUDE_TABLE_TYPES` (new: list of excluded object types for schema-level associations)

## Workflow

### Step 0: Preflight Check (REQUIRED for DMF workflows)

**Goal:** Validate the environment before running any DMF-based workflow. Skip for: compare-tables, popularity, adhoc-assessment, monitor-recommendations, coverage-gaps, circuit-breaker, custom-dmf-patterns, and expectations-management workflows (each of those handles its own setup validation internally).

**Actions:**

1. Extract `DATABASE.SCHEMA` from the user's message. If only a schema name is provided, ask which database it belongs to.
2. Read and execute `templates/preflight-check.sql` with placeholders replaced.
3. Evaluate results:
   - **table_count = 0** → Stop. "Schema is empty or doesn't exist."
   - **total_dmfs_attached = 0** → DMFs are not configured. **Do not stop.** Instead, ask the user:

     > "I didn't find any Data Metric Functions (DMFs) attached to the tables in `<DATABASE>.<SCHEMA>`.
     > DMFs enable continuous, scheduled quality monitoring. How would you like to proceed?
     >
     > **1. Set up DMFs for continuous monitoring** — I'll analyze your tables and recommend the right DMFs to attach. You'll get trend history, regression detection, and SLA alerts.
     >
     > **2. Run a one-time ad-hoc assessment** — I'll check your data quality right now using inline Snowflake system functions, with no setup required. Works for any table, schema, or Marketplace listing.
     >
     > **3. Skip for now** — Continue without a quality check."

     - If user chooses **1**: Load `workflows/monitor-recommendations.md` and proceed.
     - If user chooses **2**: Load `workflows/adhoc-assessment.md` and proceed with the ad-hoc flow.
     - If user chooses **3**: Stop gracefully.

   - **readiness_status = 'NO_RESULTS'** → Stop. "DMFs haven't run yet. Wait 1-2 minutes and retry."
   - **readiness_status = 'LIMITED'** → Proceed, but warn that regression/trend queries may not work.
   - **readiness_status = 'READY'** → Proceed to Step 1.

### Step 1: Route to Workflow

**Goal:** Determine which workflow matches the user's intent and load it.

| User Intent | Workflow to Load |
|---|---|
| Health check, trust, quality score | **Load** `workflows/health-scoring.md` |
| Why failing, what's wrong, root cause (DMF-based) | **Load** `workflows/root-cause-analysis.md` |
| DQ incident investigation, correlate violation, why did freshness/volume drop | **Load** `workflows/dq-incident-investigation.md` |
| What changed, regression, what broke | **Load** `workflows/regression-detection.md` |
| Quality trends, improving, over time | **Load** `workflows/trend-analysis.md` |
| Set up alerts, SLA, notify on drops | **Load** `workflows/sla-alerting.md` |
| Compare tables, data diff, validate migration, dev vs prod | **Load** `workflows/compare-tables.md` |
| Popular tables, most/least used, unused data, who uses this | **Load** `workflows/popularity.md` |
| Ad-hoc check, no DMFs, one-time, listing quality | **Load** `workflows/adhoc-assessment.md` |
| Recommend monitors, set up DMFs, which DMFs to attach | **Load** `workflows/monitor-recommendations.md` |
| Coverage gaps, unmonitored tables, noisy/silent monitors, DMF cost | **Load** `workflows/coverage-gaps.md` |
| Circuit breaker, pause pipeline on violation | **Load** `workflows/circuit-breaker.md` |
| Referential integrity, orphaned rows, FK validation, cross-table integrity | **Load** `workflows/monitor-recommendations.md` (use REFERENTIAL_INTEGRITY_COUNT system DMF) |
| Schema-level DMF: add/modify/suspend ROW_COUNT or FRESHNESS on a schema, check schema-level associations | **Load** `workflows/monitor-recommendations.md` (Step 1b: schema-level fast path) |
| Within group / grouped DMF: per-group metrics, broken down by, monitor by region/category, GROUP LIMIT | **Load** `workflows/within-group-dmf.md` |
| Custom DMF, format validation, value range, cross-column validation | **Load** `workflows/custom-dmf-patterns.md` |
| Accepted values, value in set, categorical validation, allowed values | **Load** `workflows/custom-dmf-patterns.md` (Step 1: ACCEPTED_VALUES first) |
| DMF expectations, set threshold, tune threshold | **Load** `workflows/expectations-management.md` |
| Score prompt, prompt quality, prompt linter | **Load** `workflows/prompt-quality.md` |
| Improve prompt, rewrite prompt, prompt engineering | **Load** `workflows/prompt-improve.md` |
| Execute prompts, compare outputs, test prompt, prompt regression | **Load** `workflows/prompt-execute-compare.md` |

If the intent is ambiguous, ask the user which workflow they want.

### Step 2: Execute Template from Workflow

**Goal:** Run the SQL template specified by the loaded workflow.

**Actions:**

1. Read the SQL template specified in the workflow file (from `templates/` directory)
2. Replace all placeholders:
   - `<database>` with the actual database name
   - `<schema>` with the actual schema name
3. Execute using `snowflake_sql_execute`
4. If the primary template fails, try the fallback template specified in the workflow

**Note:** The compare-tables and popularity workflows have their own step-by-step execution flows — follow the loaded workflow directly when those routes are selected.

**Error handling:**
- If template fails and fallback also fails: run `templates/preflight-check.sql` to diagnose
- If no DMFs found: inform user that DMFs need to be attached first
- If no data yet: inform user that DMFs haven't run — wait 1-2 minutes
- Maximum 2 fallback attempts before reporting the error to the user

### Step 3: Present Results

**Goal:** Format and present results per the workflow's output guidelines.

Follow the output format specified in the loaded workflow file. Suggest logical next steps (e.g., root cause analysis after health check).

## Tools

### snowflake_sql_execute

**Description:** Executes SQL queries against the user's Snowflake account.

**When to use:** All template executions — health checks, root cause analysis, regression detection, trend analysis, and alert creation.

**Usage pattern:**
1. Read the appropriate SQL template from `templates/`
2. Replace `<database>` and `<schema>` placeholders with actual values
3. Execute the resulting SQL via `snowflake_sql_execute`

**Templates available (DMF workflows):**

| Template | Purpose | Type |
|---|---|---|
| `preflight-check.sql` | Validate environment before any workflow | Read |
| `check-dmf-status.sql` | Verify DMF setup per table | Read |
| `check-dq-monitoring-enabled.sql` | Check DMF result availability | Read |
| `schema-health-snapshot-realtime.sql` | Current health (primary) | Read |
| `schema-health-snapshot.sql` | Current health (fallback) | Read |
| `schema-root-cause-realtime.sql` | Current failures (primary) | Read |
| `schema-root-cause.sql` | Current failures (fallback) | Read |
| `schema-regression-detection.sql` | Compare runs over time | Read |
| `schema-quality-trends.sql` | Time-series analysis | Read |
| `schema-sla-alert.sql` | Create automated alert | **Write** |
| `adhoc-column-quality.sql` | SNOWFLAKE.CORE.* inline DMF patterns for ad-hoc assessment | Read |
| `monitor-recommendations.sql` | Profile columns + rank DMF recommendations by criticality | Read |
| `coverage-gaps-summary.sql` | Coverage % + critical unmonitored tables | Read |
| `monitor-effectiveness.sql` | Noisy/silent monitor analysis (uses DATA_QUALITY_MONITORING_EXPECTATION_STATUS) | Read |
| `circuit-breaker-setup.sql` | Create ALERT + TASK suspension; trigger uses DATA_QUALITY_MONITORING_EXPECTATION_STATUS + expectation_violated | **Write** |
| `custom-dmf-create.sql` | Custom DMF templates for format/range/FK validation | **Write** |
| `expectations-review.sql` | Review DMF expectations and pass/fail status (uses DATA_QUALITY_MONITORING_EXPECTATION_STATUS) | Read |
| `prompt-cortex-complete.sql` | Score, rewrite, or execute a prompt via Cortex Complete | Read + LLM credits |

All DMF monitoring templates use `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS()` for raw metric values — never `SNOWFLAKE.ACCOUNT_USAGE`. For **expectation pass/fail** and **violation counts**, use `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_EXPECTATION_STATUS` (view or table function); the templates `expectations-review.sql`, `monitor-effectiveness.sql`, and `circuit-breaker-setup.sql` use it.
The `adhoc-column-quality.sql` template uses `SNOWFLAKE.CORE.*` functions called inline and requires no pre-attached DMFs.

For compare-tables tools (`data_diff` CLI, SQL templates), see `workflows/compare-tables.md`.

## Stopping Points

- ✋ **Before SLA alert creation**: The `sla-alerting` workflow creates Snowflake ALERT objects and a log table — present the full configuration and get explicit user approval before executing any CREATE statements
- ✋ **Before materializing diff results**: The compare-tables workflow can write diff results to a new table — confirm table name and location with user first
- ✋ **After health check with failures**: Present results and ask if user wants root cause analysis (do not auto-chain workflows)
- ✋ **When DMFs are absent (Step 0)**: Present the three-option menu (DMF recommendations / ad-hoc assessment / skip) — do not auto-select on behalf of the user
- ✋ **Before executing DMF recommendations DDL**: `monitor-recommendations` must show the ranked DDL plan and await explicit approval
- ✋ **Before creating custom DMFs**: `custom-dmf-patterns` must show generated DDL and await approval
- ✋ **Before activating circuit breaker**: `circuit-breaker` must present the ALERT + task modification plan and get explicit approval
- ✋ **Before rewriting a prompt**: Present detected quality gaps and confirm user wants Cortex to rewrite (costs LLM credits, may alter intent)
- ✋ **Before executing both prompts**: Confirm user wants to run original + improved prompts through Cortex Complete (costs LLM credits)

**Resume rule:** Upon user approval, proceed directly to the next step without re-asking.

## Cross-Skill Delegation Rules

Data quality investigation often requires capabilities owned by other skills. **Never re-implement what other skills already do.** Delegate explicitly:

| Capability Needed | Delegate To | How |
|---|---|---|
| Upstream lineage tracing | `lineage` skill | Say "Loading lineage skill for upstream root cause" → load `lineage/workflows/root-cause-analysis.md` |
| DDL change detection on upstream tables | `lineage` skill | Say "Checking upstream change history" → load `lineage` and use `change-detection.sql` |
| QUERY_HISTORY analysis for failed queries | `data-governance` skill | Say "Loading data-governance skill for query history" → load `data-governance/workflows/horizon-catalog.md` |
| TASK_HISTORY for failed task runs | `data-governance` skill | Same delegation as above |
| Data masking policy after quality finding | `data-governance` skill | Load `data-governance/workflows/data-policy.md` |
| PII detection after quality profiling | `data-governance` skill | Load `data-governance/workflows/sensitive-data-classification.md` |

## Output

Each workflow produces structured output:

- **Health Scoring**: Overall health percentage, passing/failing metric counts, tables monitored
- **Root Cause Analysis**: Failing metrics by table/column, issue descriptions, fix recommendations
- **DQ Incident Investigation**: Multi-dimensional root-cause report with timeline, primary cause, contributing factors, remediation steps
- **Regression Detection**: Health delta (previous vs current), new failures, resolved issues
- **Trend Analysis**: Time-series health scores, persistent vs transient issues, trend direction
- **SLA Alerting**: Alert configuration summary, activation status, monitoring instructions
- **Compare Tables**: Row counts, added/removed/modified rows, schema differences, validation report (see `workflows/compare-tables.md` for details)
- **Dataset Popularity**: Popularity-ranked tables, unused/stale object list, storage cost estimates, usage trends, top consumers
- **Monitor Recommendations**: Ranked DMF recommendations by criticality, column-type mappings, deployment DDL
- **Coverage Gaps**: Coverage % by schema, critical unmonitored tables, noisy/silent monitor list, cost optimization suggestions
- **Circuit Breaker**: Circuit breaker configuration, ALERT DDL, resume workflow
- **Custom DMF Patterns**: Generated `CREATE DATA METRIC FUNCTION` DDL for format/range/FK checks
- **Expectations Management**: Current expectation inventory with pass/fail status, threshold tuning suggestions
- **Prompt Quality**: Overall 1-10 score, 9 dimension scores with detail, strengths vs gaps, improvement suggestions
- **Prompt Improve**: Before vs after scores, per-dimension delta table, improved prompt text
- **Prompt Execute Compare**: Side-by-side LLM outputs for original vs improved prompt

## Error Handling

| Error | Action |
|---|---|
| Primary template fails | Try fallback template from the same workflow |
| Fallback also fails | Run `preflight-check.sql` to diagnose environment |
| No DMFs found | Present 3-option menu: continuous monitoring setup / ad-hoc one-time assessment / skip |
| No data available | Inform user: "DMFs haven't run yet. Wait 1-2 minutes and retry." |
| Insufficient history | Inform user: "Need at least 2 measurements for comparison." |
| SQL compilation error | Report the error clearly — do not hide failures or fabricate results |
| `ACCOUNT_USAGE.DATA_QUALITY_MONITORING_RESULTS` referenced | This view does NOT exist. Use `SNOWFLAKE.LOCAL.DATA_QUALITY_MONITORING_RESULTS()` instead |

## Reference

For detailed DMF concepts, **Load** `reference/dmf-concepts.md` when the user asks about DMF setup, concepts, or best practices.

For detailed prompt scoring dimensions (sub-criteria, scoring rules), **Load** `reference/prompt-scoring-dimensions.md` when the user asks about how prompt dimensions are scored.

=== data-sharing/ ===
---
name: data-sharing
description: >
  Snowflake secure data sharing: create direct shares, external marketplace listings, debug grant failures.
  Triggers: create share, share data, share table, share database, outbound share, data sharing,
  share with account, direct share, external listing, marketplace listing,
  debug share, share not working, grant failed, consumer can't access,
  share troubleshooting, why can't they see my data, share error, permission denied on share,
  share external data, share iceberg table, iceberg data sharing, share S3 data, share Azure data,
  share GCS data, share without moving data, data outside snowflake, iceberg listing,
  move data to snowflake and share, replicate and share, openflow and share, load data then share.
  
  WHEN TO USE THIS SKILL:
  - User wants to share data (generic intent — will ask who they want to share with)
  - User wants to create direct shares with specific accounts
  - User wants to create external listings (Snowflake Marketplace)
  - User needs to debug why a share isn't working
  
  WHEN TO USE org-listing workflow INSTEAD:
  - User mentions "internal marketplace", "organization listing", or "data product"
  - User wants to share within their Snowflake organization
---

# Data Sharing

Snowflake secure data sharing: help users share data by first understanding who they want to share with, then routing to the right mechanism.

**Documentation**: [Snowflake Secure Data Sharing](https://docs.snowflake.com/en/user-guide/data-sharing-intro)

## Critical Rules (apply to all sub-skills)

1. **Role preflight is mandatory.** Before running any `CREATE SHARE`, `CREATE EXTERNAL LISTING`, `CREATE ORGANIZATION LISTING`, or `ALTER LISTING` that changes auto-fulfillment, the loaded workflow MUST run its Step 0 Role Preflight and stop if the current role is missing a required privilege. Do not attempt the `CREATE` / `ALTER` speculatively. (Note: `CREATE EXTERNAL LISTING` the SQL command requires the **`CREATE LISTING`** account-level privilege — there is no `CREATE EXTERNAL LISTING` privilege.)

2. **Do not retry on privilege errors — ask the user which role to use.** If any statement returns `Insufficient privileges`, `not authorized`, `does not have privilege`, or error codes 3001 / 3003:
   - **Stop.** Do not try syntax variations, alternate commands, or guesses from public docs.
   - Surface the error verbatim.
   - Query `SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES` for the **specific** privilege that failed (not a broad list) to build a candidate-role list. This view can lag by up to ~2h — if the returned list is empty or looks stale, fall back to `SHOW GRANTS ON ACCOUNT` + `RESULT_SCAN` as shown in the Prerequisites section below. Cap the list at 3 (prefer `ACCOUNTADMIN` / `SYSADMIN` / `ORGADMIN` when present).
   - **If BOTH the ACCOUNT_USAGE query AND the SHOW GRANTS fallback fail with privilege errors** (common when the current role is genuinely low-privilege — it often can't read account metadata either), skip candidate discovery and ask the user directly for a role name they know has the privilege, or tell them to escalate to an admin. Do not loop.
   - Present the candidates as a pick list (or, if discovery failed, an open prompt) with these options: each candidate role as a "Switch to <ROLE>" choice, plus "Enter a different role name" and "Ask an admin to grant the privilege instead." Do NOT print a `USE ROLE <role_with_privilege>` template for the user to run manually.
   - When the user picks a role: **treat the role change as statement-scoped**. Do NOT rely on a standalone `USE ROLE <picked>;` to persist across subsequent tool calls — in cortex CLI each SQL_EXECUTE can run in a fresh connection that resets the role back to the profile default. Instead, **prepend `USE ROLE <picked>;` to every subsequent SQL statement for the rest of this workflow** (preflight re-run, CREATE, GRANT, DESCRIBE, etc.). Example: `USE ROLE <picked>; CREATE SHARE <share_name> ...;` in a single SQL_EXECUTE call.

3. **`GRANT SELECT ON VIEW` requires `GET_OBJECT_REFERENCES` first — no exceptions.** Before executing `GRANT SELECT ON VIEW` in any share, you MUST run `GET_OBJECT_REFERENCES` on that view to discover cross-database dependencies. For every external database returned, run `GRANT REFERENCE_USAGE ON DATABASE <ext_db> TO SHARE <share_name>` before attempting `GRANT SELECT ON VIEW`. Skipping this step produces a share that fails silently for consumers. See `workflows/create.md` Step 3 item 3 for the full A–E sequence.

4. **Use the full-manifest `ALTER LISTING ... AS $$...$$` form** when updating any listing. `ALTER LISTING <name> SET refresh_schedule = ...` and `ALTER DATABASE <name> SET ...` are **not valid syntax** for refresh schedules — they will fail. See `references/sql-syntax.md`.

5. **Secure views and UDFs: optional, not mandatory.** New shares default to `SECURE_OBJECTS_ONLY = TRUE`, so `GRANT SELECT ON VIEW` and `GRANT USAGE ON FUNCTION` apply to secure views and secure SQL/JavaScript UDFs until the share is relaxed. Snowflake documents **secure** views and UDFs as a pattern that can limit how much definition and query-plan detail consumers see ([Use secure objects to control data access](https://docs.snowflake.com/en/user-guide/data-sharing-secure-views)); **regular views and non-secure UDFs remain valid share targets** after `SECURE_OBJECTS_ONLY = FALSE` ([Share data in non-secured views](https://docs.snowflake.com/en/user-guide/data-sharing-views), [GRANT … TO SHARE](https://docs.snowflake.com/en/sql-reference/sql/grant-privilege-share)). Do not choose for the user: explain default behavior, irreversibility of `SECURE_OBJECTS_ONLY = FALSE`, and trade-offs, then follow their choice. Do **not** run `ALTER VIEW ... SET SECURE` or `ALTER FUNCTION ... SET SECURE` unless they explicitly approve changing the object.

---

## Intent Detection

When a user makes a request, detect their intent and route to the appropriate sub-skill.

### Explicit Intent (user already knows what they want)

If the user uses specific mechanism keywords, route directly without asking:

| Trigger phrases | Route |
|----------------|-------|
| "create share", "direct share", "new share" | **Load** [workflows/create.md](workflows/create.md) |
| "external listing", "marketplace listing", "snowflake marketplace", "publish to marketplace" | **Load** [workflows/external-listing.md](workflows/external-listing.md) |
| "internal marketplace", "organization listing", "org listing", "data product" | **Load** [workflows/org-listing.md](workflows/org-listing.md) |
| "share external data", "share iceberg table", "iceberg data sharing", "share S3 data", "share Azure data", "share GCS data", "share without moving data", "data outside snowflake", "share glue tables", "share unity catalog data", "iceberg listing", "snowflake catalog iceberg", "snowflake managed iceberg", "share iceberg snowflake catalog", "move data to snowflake and share", "replicate and share", "openflow and share", "load data then share" | **Load** [workflows/external-data.md](workflows/external-data.md) |
| "share not working", "can't see shared data", "grant failed", "consumer can't access", "debug share", "troubleshoot share", "share error", "why isn't my share working", "permission denied", "share does not have database" | **Load** [workflows/debug.md](workflows/debug.md) |

### Generic Share Intent (target unclear)

When the user says something generic like "share this table", "share data with", "share my database", "I want to share", "set up share", "outbound share", "share to account", or "share data" **without specifying a listing type**, ask:

> "Who do you want to share this data with?"
>
> 1. **Accounts in my Snowflake organization** (all internal accounts or specific org accounts)
> 2. **Specific Snowflake accounts outside my organization**
> 3. **Specific regions**
> 4. **Anyone — publish publicly on Snowflake Marketplace**

Then route based on the answer:

| User's answer | Route |
|---------------|-------|
| Option 1 — Org accounts | **Load** [workflows/org-listing.md](workflows/org-listing.md) (creates org listing) |
| Options 2, 3, or 4 — Outside org / regions / public | **Load** [workflows/external-listing.md](workflows/external-listing.md) (creates external listing) |

---

## Workflow Decision Tree

```
Start
  |
  Detect User Intent
  |
  |-- Explicit "create share" / "direct share"
  |     --> Load workflows/create.md
  |         --> Step 0: Role Preflight (MANDATORY STOP if missing CREATE SHARE)
  |
  |-- Explicit "internal marketplace" / "org listing" / "data product"
  |     --> Load workflows/org-listing.md
  |         --> Step 0: Role Preflight (MANDATORY STOP if missing CREATE ORGANIZATION LISTING / CREATE SHARE)
  |
  |-- Explicit "external listing" / "marketplace listing"
  |     --> Load workflows/external-listing.md
  |         --> Step 0: Role Preflight (MANDATORY STOP if missing CREATE LISTING / CREATE SHARE)
  |
  |-- EXTERNAL DATA triggers (iceberg, S3, openflow...)
  |     --> Load workflows/external-data.md
  |
  |-- DEBUG triggers
  |     --> Load workflows/debug.md
  |
  |-- Generic "share" (no clear target or listing type)
        --> Ask: "Who do you want to share with?"
        |-- Org accounts --> Load workflows/org-listing.md (preflight required)
        |-- Outside org / regions / public --> Load workflows/external-listing.md (preflight required)
```

---

## Sub-Skills

| Sub-Skill | Purpose | When to Load |
|-----------|---------|--------------|
| [workflows/create.md](workflows/create.md) | Create shares (with optional direct targets) | Explicit "create share" / "direct share" only |
| [workflows/external-listing.md](workflows/external-listing.md) | Create Snowflake Marketplace listings | Outside org / regions / public targets, or explicit "external listing" |
| [workflows/org-listing.md](workflows/org-listing.md) | Create internal marketplace / org listings | Org account targets, or explicit "internal marketplace" / "org listing" / "data product" |
| [workflows/external-data.md](workflows/external-data.md) | Share external data — keep in place (Iceberg) or move into Snowflake (Openflow) | EXTERNAL DATA intent |
| [workflows/debug.md](workflows/debug.md) | Troubleshoot share issues | DEBUG intent |

---

## Quick Diagnostic Queries

For immediate assessment before routing:

```sql
-- List all shares you've created
SHOW SHARES;

-- Check specific share contents
DESCRIBE SHARE <share_name>;

-- Check grants to a share
SHOW GRANTS TO SHARE <share_name>;

-- Check consumer access
SHOW GRANTS OF SHARE <share_name>;
```

---

## Prerequisites (All Operations)

Every create workflow has a mandatory **Step 0: Role Preflight** that checks the operation-specific privileges below. Do not skip it — see Critical Rule 1.

| Operation | Required privileges on ACCOUNT |
|-----------|-------------------------------|
| Create share | `CREATE SHARE` |
| Create external listing | `CREATE LISTING` + `CREATE SHARE` (if share doesn't exist) |
| Create organization listing | `CREATE ORGANIZATION LISTING` + `CREATE SHARE` (if share doesn't exist) |
| Configure auto-fulfillment (cross-region / ALL / remote access region) | `MANAGE LISTING AUTO FULFILLMENT` (in addition to the listing privilege) |
| Modify existing share | `OWNERSHIP` or `MODIFY` on the share |

All operations also require `USAGE` on the database/schema and `SELECT` (or appropriate privilege) on the objects being shared.

**Verify current role:**
```sql
-- Step 1: get the current role
SELECT CURRENT_ROLE();
-- Step 2: substitute the returned role name LITERALLY into SHOW GRANTS.
-- (SHOW GRANTS TO ROLE IDENTIFIER(CURRENT_ROLE()) is NOT valid Snowflake syntax.)
SHOW GRANTS TO ROLE <current_role>;
```

**Find roles that already hold a privilege** (use this when preflight fails). `ACCOUNT_USAGE.GRANTS_TO_ROLES` is the primary path; it may have up to ~2 hours of latency but is authoritative for account-level grants:

```sql
-- Primary: ACCOUNT_USAGE (authoritative, but may lag up to ~2h — use SHOW GRANTS ON ACCOUNT below as a freshness fallback)
SELECT GRANTEE_NAME
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE PRIVILEGE = 'CREATE LISTING'  -- or CREATE SHARE / CREATE ORGANIZATION LISTING / MANAGE LISTING AUTO FULFILLMENT
  AND GRANTED_ON = 'ACCOUNT'
  AND GRANTED_TO = 'ROLE'
  AND DELETED_ON IS NULL;

-- No-latency alternative: dump all account-level grants and filter in RESULT_SCAN
SHOW GRANTS ON ACCOUNT;
SELECT "grantee_name"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "privilege" = 'CREATE LISTING'
  AND "granted_on" = 'ACCOUNT'
  AND "granted_to" = 'ROLE';
```

---

## References

For detailed information, **load** these files:

- `references/sql-syntax.md`: Complete SQL command reference for shares
- `references/errors.md`: Common errors and troubleshooting for org listings
- `references/manifest-reference.md`: Detailed manifest field documentation and configuration examples
- `references/templates.md`: Copy-paste templates for common org listing scenarios

=== dbt-projects-on-snowflake/ ===
---
name: dbt-projects-on-snowflake
description: "ONLY for dbt projects deployed INTO Snowflake as native objects via the `snow dbt` CLI, OR for authoring dbt models using Snowflake-native features (e.g., semantic_view materialization via dbt_semantic_view package). NOT for normal dbt development. Invoke ONLY when the user explicitly mentions: `snow dbt` commands (deploy, execute, list), `EXECUTE DBT PROJECT` SQL, a deployed dbt project object (e.g., DB.SCHEMA.MY_PROJECT), `ALTER/DROP/DESCRIBE/SHOW DBT PROJECT` SQL, scheduling a deployed dbt project with CREATE TASK, generating documentation/catalog/lineage for a deployed project, OR authoring Snowflake-specific dbt materializations (semantic_view, dbt_semantic_view), OR adding a semantic view to an existing dbt project. Do NOT invoke for standard dbt workflows: dbt run, dbt build, dbt test, dbt seed, dbt init, dbt compile, dbt debug, dbt snapshot, dbt deps, dbt clean, dbt retry, dbt ls, profiles.yml, dbt_project.yml, model editing, source freshness, Jinja/macro development, CI/CD pipelines, or any dbt command run from a terminal. The key distinction: this skill is about dbt-as-a-Snowflake-object (snow dbt deploy), not dbt-as-a-CLI-tool (dbt run). Triggers: snow dbt, snow dbt deploy, snow dbt execute, snow dbt list, EXECUTE DBT PROJECT, deployed dbt project, ALTER DBT PROJECT, DROP DBT PROJECT, DESCRIBE DBT PROJECT, SHOW DBT PROJECTS, VERSION$, external-access-integration, dbt project object, migrate, prepare for snowflake, docs generate deployed, documentation deployed project, data catalog deployed, lineage deployed project, generate documentation for deployed, semantic_view materialization, dbt_semantic_view, semantic view in dbt project, add semantic view to dbt, dbt project semantic view, analytical access dbt project."
---

# Snowflake-Native dbt Projects

Deploy and run dbt Core projects directly **inside Snowflake** using the `snow` CLI and `EXECUTE DBT PROJECT` SQL. Also covers authoring dbt models with Snowflake-specific materializations like `semantic_view`.

**SCOPE:** This skill covers dbt projects deployed as Snowflake objects — created via `snow dbt deploy`, executed via `snow dbt execute` or `EXECUTE DBT PROJECT` SQL, and managed via `ALTER/DESCRIBE/DROP/SHOW DBT PROJECT` SQL. It also covers authoring dbt models that use Snowflake-specific materializations (e.g., `semantic_view` via the `dbt_semantic_view` package).

**DO NOT use this skill when:**
- The user is running dbt locally against Snowflake (standard `dbt run`, `dbt build`, `dbt test`, `dbt seed`)
- The user is editing dbt models, fixing SQL bugs, writing macros, or doing dbt development work
- The user has a local `profiles.yml` with password/authenticator fields (this is normal for local dbt)
- The user is configuring `dbt_project.yml`, `packages.yml`, or project structure
- The user mentions `dbt init`, `dbt debug`, `dbt deps`, `dbt clean`, `dbt compile`, `dbt snapshot`, `dbt retry`, `dbt ls`
- The user asks about CI/CD, GitHub Actions, source freshness, or dbt documentation
- There is NO mention of `snow dbt`, a deployed project, a project in a Snowflake schema, `EXECUTE DBT PROJECT`, or Snowflake-specific materializations (`semantic_view`)

If the user's request matches the above, do NOT load any sub-skills — just answer using standard dbt knowledge.

**WHY THIS SKILL EXISTS:** Snowflake's native dbt integration uses unique syntax (`snow dbt`, `EXECUTE DBT PROJECT`) that differs from standard dbt CLI. This skill provides the correct syntax for that specific workflow, plus guidance on Snowflake-specific dbt materializations like `semantic_view`.

> **Semantic views:** For creating semantic views as part of a dbt project, this skill provides the `dbt_semantic_view` package workflow (see SEMANTIC VIEW intent below). For ongoing optimization of existing semantic views (auditing, VQR mining, Cortex Analyst tuning), use the `semantic-view` skill instead.

---

## Intent Detection

**Only match these intents when the user is explicitly working with Snowflake-native dbt (deployed projects, `snow dbt`, `EXECUTE DBT PROJECT`).** Do NOT match for standard local dbt CLI work.

| Intent | Triggers | Action |
|--------|----------|--------|
| **DEPLOY** | "snow dbt deploy", "deploy dbt project to snowflake", "create dbt project in snowflake", "upload dbt", "external access integration" | Load `deploy/SKILL.md` |
| **EXECUTE** | "snow dbt execute", "EXECUTE DBT PROJECT", "run deployed project", "execute deployed project", "snow dbt show", "run the deployed", "run in deployed", "execute in deployed", "docs generate", "generate documentation", "documentation", "data catalog", "catalog", "lineage" | **⚠️ You MUST read `execute/SKILL.md`** - it has CRITICAL syntax for docs generate |
| **MANAGE** | "snow dbt list", "list dbt projects", "show dbt projects", "describe dbt project", "drop dbt project", "rename dbt project", "SHOW DBT PROJECTS", "ALTER DBT PROJECT", "add version", "VERSION$", "set comment", "set default target", "download project files", "get model SQL from deployed", "inspect deployed project", "access project files", "list files in project" | Load `manage/SKILL.md` |
| **SCHEDULE** | "schedule dbt project", "CREATE TASK for dbt", "EXECUTE DBT PROJECT in task", "automate dbt runs", "Snowflake task for dbt" | Load `schedule/SKILL.md` |
| **MONITOR** | "dbt execution logs", "dbt artifacts", "dbt archive", "dbt execution history", "download artifacts" | Load `monitoring/SKILL.md` |
| **MIGRATE** | "migrate", "env_var", "environment variable", "convert to var", "migration", "prepare for snowflake" | ⚠️ **You MUST `Read` `migrate/SKILL.md` before taking any action.** Migration has complex, non-obvious requirements that will cause failures if skipped. Do NOT attempt migration from general knowledge. |
| **SEMANTIC VIEW** | "semantic view", "create semantic view", "dbt_semantic_view", "cortex analyst semantic", "semantic_view materialization" | Load `references/semantic-views.md` |

## ⚠️ Critical: Incremental Model Fixes Require `--full-refresh`

After fixing an incremental model's logic (e.g., restoring a missing `is_incremental()` guard, changing the unique key, or altering the incremental strategy), you **MUST** execute with `--full-refresh`. Without it, the existing table still contains data built by the broken logic — a normal incremental run only processes new rows and won't fix the bad data.

## Quick Reference

```bash
# Deploy (add --external-access-integration if project needs external network access)
snow dbt deploy my_project --source /path/to/dbt --database my_db --schema my_schema --external-access-integration MY_EAI

# PREVIEW model output (does NOT create objects)
snow dbt execute -c default --database my_db --schema my_schema my_project show --select model_name

# Execute/RUN models (creates tables/views)
snow dbt execute -c default --database my_db --schema my_schema my_project run

# Full refresh (REQUIRED after fixing incremental model logic)
snow dbt execute -c default --database my_db --schema my_schema my_project run --full-refresh

# Execute specific models with dependencies
# Upstream deps of target:
snow dbt execute -c default --database my_db --schema my_schema my_project run --select +target_model
# Downstream deps of target:
snow dbt execute -c default --database my_db --schema my_schema my_project run --select target_model+
# Both sides:
snow dbt execute -c default --database my_db --schema my_schema my_project run --select +target_model+

# List (omit --database to use connection default)
snow dbt list --in schema my_schema --database my_db

# Schedule (via SQL - always use EXECUTE DBT PROJECT)
CREATE TASK my_db.my_schema.run_dbt_daily
  WAREHOUSE = my_wh
  SCHEDULE = 'USING CRON 0 6 * * * UTC'
AS
EXECUTE DBT PROJECT my_db.my_schema.my_project ARGS = 'run';
```

## Workflow

```
User Request
     ↓
Intent Detection
     ↓
├─→ DEPLOY   → Load deploy/SKILL.md
├─→ EXECUTE  → Load execute/SKILL.md
├─→ MANAGE   → Load manage/SKILL.md
├─→ SCHEDULE → Load schedule/SKILL.md
├─→ MONITOR  → Load monitoring/SKILL.md
├─→ MIGRATE  → ⚠️ MUST Read migrate/SKILL.md first (complex requirements) → Then follow its steps exactly
└─→ SEMANTIC VIEW → Load references/semantic-views.md
```

## Stopping Points

- ⚠️ Before any destructive operation (DROP, RENAME)

## Output

- Deployed dbt projects in Snowflake
- Materialized tables/views/semantic views from dbt models
- Test results from dbt test
- Scheduled TASK objects for automated execution
- Execution logs and artifacts for debugging

=== dcm/ ===
---
name: dcm
description: "Use for **ALL** requests that mention: create, build, set up, debug, fix, troubleshoot, optimize, improve, evaluate, or analyze a DCM project. This is the **REQUIRED** entry point - even if the request seems simple. DO NOT attempt to create DCM projects manually or search for DCM documentation - always invoke this skill first. This skill guides users through creating, auditing, evaluating, and debugging workflows for DCM (Database Change Management) projects. Triggers: DCM, DCM project, Database Change Management, snow dcm, manifest.yml with DEFINE, infrastructure-as-code, three-tier role pattern, database roles, DEFINE TABLE, DEFINE SCHEMA."
---

# DCM (Database Change Management) Skill

## When to Use

Use this skill when a user wants to:

- Create a new DCM project from scratch
- Modify an existing DCM project (with or without local source code)
- Define or modify Snowflake infrastructure (databases, schemas, tables, views, dynamic tables, tasks, warehouses, roles, grants, sequences, procedures, alerts)
- Set up data quality expectations and data metric functions
- Understand dependencies or lineage between objects in a DCM project
- Deploy changes to Snowflake infrastructure

## Prerequisites

- Active Snowflake connection (`-c <connection>` required for all DCM commands)
- Appropriate Snowflake privileges for the operations being performed
- For new projects: `CREATE DATABASE` or `CREATE SCHEMA` privileges as needed
- For deployments: privileges to create/alter/drop the objects defined in the project
- Snowflake CLI (`snow`) version 3.17 or later (recommended)

## ⚠️ MANDATORY INITIALIZATION

Before any DCM workflow, you MUST complete Steps 0, 1, and 2 as **sequential gates**. Each step MUST complete (including any required user response) before the next step begins. DO NOT batch these steps with other tool calls. Each gate requires its own turn in the conversation.

### Step 0: Check Snowflake CLI Version ✋ BLOCKING

Run `snow --version`.

**If version >= 3.17** → Proceed to Step 1.

**If version >= 3.16 but < 3.17** → Output the warning below, then proceed to Step 1. Note the version for later — `purge` will not be available in this session.

> "⚠️ Your Snowflake CLI version is X.Y.Z. DCM works best with version 3.17 or later. Most features will work, but `snow dcm purge` requires 3.17+.
>
> To upgrade, run:
> ```
> pip install snowflake-cli --upgrade
> ```
>
> You can continue with your current version, upgrade manually, or I can run the upgrade for you."

**If version < 3.16** → Output the warning below, then STOP. Do not proceed to Step 1. Do not load any files. Do not call any tools. Your entire response for this turn must be ONLY the warning message. Wait for the user to respond.

> "⚠️ Your Snowflake CLI version is X.Y.Z. DCM works best with version 3.17 or later — some features may not work as expected on older versions.
> 
> To upgrade, run:
> ```
> pip install snowflake-cli --upgrade
> ```
> 
> You can continue with your current version, upgrade manually, or I can run the upgrade for you."

Do not run the upgrade unless the user explicitly asks you to. If they choose to continue, proceed to Step 1.

**🛑 END OF TURN. Output ONLY the warning above. Do not call any other tools. Do not read any files. Wait for user response.**

**If `snow` is not found** → Inform the user they need to install the Snowflake CLI before using DCM, then STOP.

### Step 1: Load Syntax Overview ✋ BLOCKING

**⚠️ Gate check: Only proceed here if Step 0 completed with version >= 3.16, or the user explicitly chose to continue with an older version.**

**Load** the syntax overview to understand DCM core principles:

1. **Load**: [reference/syntax_overview.md](reference/syntax_overview.md) - DCM syntax principles, supported entities, and primitive loading guide

**Additional references — load as needed per sub-skill guidance:**
- [reference/project_structure.md](reference/project_structure.md) - Manifest and project structure (load when creating/modifying manifests)
- [reference/cli_reference.md](reference/cli_reference.md) - CLI command details (load when running DCM commands)
- `reference/primitives/*.md` - Per-object-type syntax and examples (load only the primitives needed for the task — see the loading guide in syntax_overview.md)

**DO NOT PROCEED until you have loaded the syntax overview.**

### Step 2: Gather Required Information ✋ BLOCKING

For ALL DCM operations, you MUST collect:

1. **Target DCM Project Identifier** (fully qualified: `DATABASE.SCHEMA.PROJECT_NAME`)

   - This is the Snowflake object where the project is registered
   - Required for all `snow dcm` commands (except `list` that should be used to aid the user in selecting a project)
   - **⚠️ CRITICAL**: A DCM project CANNOT define its parent database or schema. If the project identifier is `MY_DB.MY_SCHEMA.MY_PROJECT`, you cannot use `DEFINE DATABASE MY_DB` or `DEFINE SCHEMA MY_DB.MY_SCHEMA` - these containers must already exist. You can only define objects *inside* the project's schema.

2. **Snowflake Connection** (`--connection` or `-c`)

   - The named connection to use for all operations
   - Ask user if not provided (or use default connection if not specified)

3. **Target Name** (if the project uses targets)
   - Check `manifest.yml` for available targets (DEV, PROD, etc.)
   - The `--target` flag selects a target from the manifest, which bundles the project identifier with a templating configuration
   - If omitted, the `default_target` from the manifest is used

**DO NOT PROCEED until you have confirmed these details with the user.**

## Intent Detection

When a user makes a request, detect their intent and follow the appropriate workflow.

**⚠️ MANDATORY SUB-SKILL LOADING**: When an intent below maps to a sub-skill file (marked with ✋ MUST Load), you **MUST** load that sub-skill file before doing any work. The inline workflow summaries later in this document are overviews only — they are **NOT sufficient** to complete the task correctly. The sub-skills contain critical details, examples, and guardrails that prevent common errors. **DO NOT** skip loading the sub-skill and attempt to follow only the inline workflow.

### CREATE Intent - User wants to create a new DCM project

**Trigger phrases**: "create project", "new project", "set up DCM", "start from scratch", "build infrastructure"

**→ ✋ MUST Load**: [create-project/SKILL.md](create-project/SKILL.md) — DO NOT write any files or run commands until this sub-skill is loaded.

### MODIFY_LOCAL Intent - User wants to modify an existing project with local source code

**Trigger phrases**: "modify", "update", "change", "add table", "edit definitions" (when source files are available locally)

**→ ✋ MUST Load**: [modify-project/SKILL.md](modify-project/SKILL.md) — DO NOT modify definitions until this sub-skill is loaded.

### DOWNLOAD_AND_MODIFY Intent - User wants to work with an existing deployed project (no local code)

**Trigger phrases**: "download project", "get sources", "work with existing project", "modify deployed project"

**→ ✋ MUST Load**: [modify-project/SKILL.md](modify-project/SKILL.md) (includes download workflow) — DO NOT download or modify until this sub-skill is loaded.

### ANALYZE Intent - User wants to understand dependencies or check for errors

**Trigger phrases**: "analyze", "check dependencies", "lineage", "what depends on", "validate"

**→ Follow**: [Analyze Project Workflow](#workflow-4-analyze-project)

### IMPORT_EXISTING Intent - User wants to import/adopt existing Snowflake objects into DCM

**Trigger phrases**: "import existing", "adopt objects", "bring into DCM", "convert to DCM", "add existing table"

**→ Follow**: [Adopting Existing Objects Workflow](#workflow-5-adopting-existing-objects)

### ROLE_GRANT_GUIDELINES Intent - User needs guidance on roles/grants in DCM

**Trigger phrases**: "dcm role", "dcm grant", "roles in dcm", "grants in dcm project", "dcm permission model", "dcm warehouse grant error", "define roles in dcm"

**→ ✋ MUST Load**: [roles-and-grants/SKILL.md](roles-and-grants/SKILL.md) — DO NOT give grant advice until this sub-skill is loaded.

### DEPLOY Intent - User wants to deploy changes

**Trigger phrases**: "deploy", "apply changes", "push to Snowflake"

**→ ✋ MUST Load**: [deploy-project/SKILL.md](deploy-project/SKILL.md) — DO NOT run plan or deploy commands until this sub-skill is loaded.

### DROP_PROJECT Intent - User wants to drop / delete the DCM project

**Trigger phrases**: "drop project", "delete project", "remove project", "snow dcm drop"

**⚠️ IMPORTANT**: `snow dcm drop` removes **only the DCM project metadata**. It does NOT drop the Snowflake objects the project manages (tables, views, dynamic tables, etc.). Those objects will remain in Snowflake as orphans.

When this intent is detected:
1. Inform the user: "This will remove the DCM project registration but leave all managed objects (tables, views, dynamic tables, etc.) in Snowflake as orphans. If you also want to permanently drop all of those objects and their data, I can run a purge first."
2. Ask: "Would you also like to purge all managed objects first? **Warning: purge is irreversible and will permanently delete data.**"
3. If yes → treat as PURGE intent (load purge sub-skill, then run `snow dcm drop` after purge completes)
4. If no → proceed with `snow dcm drop <identifier> -c <connection>`

### PURGE Intent - User wants to drop all objects managed by the project

**Trigger phrases**: "purge", "purge project", "drop all objects", "drop all objects inside this project", "drop everything in the project", "start over", "decommission project"

**🚨 THIS IS EXTREMELY DANGEROUS.** Purge permanently drops every Snowflake object managed by the project — including all table data — and cannot be automatically undone.

**⚠️ Requires CLI version 3.17+.** You already know the user's CLI version from Step 0. If their version is < 3.17, do NOT proceed with purge — instead inform them:

> "The `snow dcm purge` command requires Snowflake CLI 3.17 or later. You are running X.Y.Z. To use purge, upgrade first:
> ```
> pip install snowflake-cli --upgrade
> ```
> Would you like me to run the upgrade?"

**→ ✋ MUST Load**: [purge-project/SKILL.md](purge-project/SKILL.md) — DO NOT run purge or any destructive commands until this sub-skill is loaded.

## Core Workflows

### Workflow 1: Create New Project

This workflow is fully documented in [create-project/SKILL.md](create-project/SKILL.md).
You **MUST** load that sub-skill before writing any files or running commands.

### Workflow 2: Modify Existing Project

This workflow is fully documented in [modify-project/SKILL.md](modify-project/SKILL.md).
You **MUST** load that sub-skill before modifying any definitions.

### Workflow 3: Download and Modify Existing Project

This workflow is fully documented in [modify-project/SKILL.md](modify-project/SKILL.md) (includes the download workflow).
You **MUST** load that sub-skill before downloading or modifying any project.

### Workflow 4: Analyze Project

```
User wants to understand dependencies or validate
    ↓
1. Run analyze:
   snow dcm raw-analyze <identifier> -c <connection> \
     --target <config> 
    ↓
2. ⚠️ CRITICAL: Read and parse command output
   - This step is MANDATORY, not optional
   - Check for errors at file and definition levels
   - Extract dependency information
   - Extract column-level lineage
    ↓
3. If errors exist:
   - Report them to the user
   - Fix issues in definition files
   - Rerun analyze
    ↓
4. Present findings to user:
   - List of objects defined
   - Dependencies between objects
   - Any errors or warnings
   - Column lineage (if requested)
```

### Workflow 5: Adopting Existing Objects

```
User wants to import existing Snowflake objects into DCM
    ↓
1. Identify the objects to adopt:
   - Ask user which objects to import
   - Get fully qualified names
    ↓
2. Get current DDL for each object:
   SELECT GET_DDL('TABLE', 'DB.SCHEMA.TABLE');
   SELECT GET_DDL('VIEW', 'DB.SCHEMA.VIEW');
   SELECT GET_DDL('STAGE', 'DB.SCHEMA.STAGE');
    ↓
2.5. ⚠️ MANDATORY: Categorize Objects by DCM Support
   - **Stages**: Check for URL parameter
     ✅ No URL (internal) → Use DEFINE STAGE
     ⚠️ Has URL (external) → Place in post_deploy.sql
   - **Grants**: Load roles-and-grants/SKILL.md
     ✅ Supported → include in definitions
     ⚠️ Workaround needed → warehouse grants need account role
     ❌ Unsupported → document in post_deployment_grants.sql
   - **Other Objects**: Tables, Views, Warehouses, Sequences, Procedures, Alerts → DEFINE
   - **Unsupported Objects**: Streams → post_deploy.sql; Integrations → pre_deploy.sql
   - Present categorized analysis to user
   - ⚠️ CHECKPOINT: Get explicit approval before proceeding
    ↓
3. Convert supported objects (CREATE to DEFINE):
   - Replace CREATE keyword with DEFINE for supported objects
   - Internal stages: CREATE STAGE → DEFINE STAGE
   - Preserve all properties exactly
   - Keep grants separate (handle per step 2.5 analysis)
   - External stages/streams go to companion scripts (not DEFINE)
    ↓
4. Add definitions to project files:
   - DEFINE statements → appropriate .sql files
   - Unsupported objects → pre_deploy.sql or post_deploy.sql (see unsupported_objects.md)
   - Unsupported grants → post_deployment_grants.sql
    ↓
5. Run analyze and READ command output:
   - Verify objects appear in definitions
    ↓
6. Run plan and READ out/plan/plan_result.json:
   - ⚠️ VERIFY: Plan should show ZERO changes for adopted objects
   - If plan shows CREATE/ALTER, the definition doesn't match
   - Adjust definition to match existing object exactly
    ↓
7. Repeat until plan shows no changes for adopted objects
```

**Key Point:** Successful adoption = plan shows NO operations for the adopted objects. They should appear in analyze but result in zero changes in plan.

### Workflow 6: Deploy Changes

This workflow is fully documented in [deploy-project/SKILL.md](deploy-project/SKILL.md).
You **MUST** load that sub-skill before running plan or deploy commands.

⚠️ **CRITICAL: NEVER deploy without running plan first and getting explicit user confirmation.**

## Workflow Decision Tree

```
Start Session
    ↓
MANDATORY: Load syntax_overview.md (primitives loaded on-demand by sub-skills)
    ↓
Gather: Project identifier, Connection, Configuration
    ↓
Detect User Intent
    ↓
    ├─→ CREATE → ✋ MUST Load create-project/SKILL.md BEFORE writing any files
    │   (Triggers: "create project", "new project", "set up DCM")
    │   ⚠️ If roles/grants/permissions mentioned:
    │      → ALSO MUST load roles-and-grants/SKILL.md
    │
    ├─→ MODIFY_LOCAL → ✋ MUST Load modify-project/SKILL.md BEFORE modifying
    │   (Triggers: "modify", "update", "add table" with local files)
    │
    ├─→ DOWNLOAD_AND_MODIFY → ✋ MUST Load modify-project/SKILL.md BEFORE downloading
    │   (Triggers: "download project", "get sources", "work with existing")
    │
    ├─→ IMPORT_EXISTING → Follow Adopting Existing Objects workflow
    │   (Triggers: "import existing", "adopt", "bring into DCM", "convert DDL")
    │   → Get DDL → ⚠️ Analyze grants first → Convert to DEFINE
    │   → ALWAYS load roles-and-grants/SKILL.md for grant analysis
    │   → Verify plan shows zero changes for adopted objects
    │
    ├─→ ROLE_GRANT_GUIDELINES → ✋ MUST Load roles-and-grants/SKILL.md
    │   (Triggers: "dcm role", "dcm grant", "roles in dcm", "dcm permission model")
    │   → Recommended patterns for roles and grants in DCM
    │
    ├─→ ANALYZE → Run analyze workflow
    │   (Triggers: "analyze", "check dependencies", "lineage")
    │   ⚠️ MUST read command output after running
    │
    ├─→ DEPLOY → ✋ MUST Load deploy-project/SKILL.md BEFORE running plan/deploy
    │   (Triggers: "deploy", "apply changes")
    │       ↓
    │   ALWAYS: analyze → plan → READ OUTPUT FILES → user confirmation → deploy
    │       ↓
    │   If tests exist: offer to run tests
    │
    ├─→ DROP_PROJECT → Clarify metadata-only drop, offer purge
    │   (Triggers: "drop project", "delete project", "remove project")
    │   → Explain drop only removes project metadata, NOT managed objects
    │   → Ask if user also wants to purge managed objects
    │   → If yes: treat as PURGE intent below
    │   → If no: snow dcm drop <identifier> -c <connection>
    │
    └─→ PURGE → 🚨 ✋ MUST Load purge-project/SKILL.md BEFORE any destructive action
        (Triggers: "purge", "drop all objects", "drop everything in the project")
        🚨 EXTREMELY DANGEROUS — permanently deletes all managed objects and data
            ↓
        ALWAYS: analyze to enumerate objects → danger warning with object list → user confirmation → purge
```

## Sub-Skills

| Sub-Skill                                          | Purpose                                     | When to Load                  |
| -------------------------------------------------- | ------------------------------------------- | ----------------------------- |
| [create-project/SKILL.md](create-project/SKILL.md) | Create new DCM project from scratch         | CREATE intent                 |
| [modify-project/SKILL.md](modify-project/SKILL.md) | Modify existing project (local or download) | MODIFY/DOWNLOAD/IMPORT intent |
| [deploy-project/SKILL.md](deploy-project/SKILL.md) | Safe deployment with confirmation           | DEPLOY intent                 |
| [roles-and-grants/SKILL.md](roles-and-grants/SKILL.md) | Best practices for roles/grants in DCM | Role patterns, grant errors, permission models |
| [purge-project/SKILL.md](purge-project/SKILL.md) | 🚨 Drop ALL managed objects and their data — irreversible | PURGE intent, or after DROP_PROJECT if user wants purge |

**Note:** The IMPORT_EXISTING workflow (adopting existing objects) is documented in [modify-project/SKILL.md](modify-project/SKILL.md) and in [Workflow 5: Adopting Existing Objects](#workflow-5-adopting-existing-objects).

**Note:** For role and grant guidance (recommended patterns, handling warehouse constraints, unsupported grant types), load the **roles-and-grants** skill.

## Rules

### Running Scripts

When running scripts from this skill:

1. Use bash to run the download script:

   ```bash
   python <skill-dir>/scripts/download_project.py <project_name> \
     --connection <connection> \
     --target <target_folder>
   ```

2. Do not `cd` into the skill directory - run from the user's working directory.

### DCM Command Patterns

All DCM commands follow this pattern:

```bash
snow dcm <command> <identifier> -c <connection> [options]
```

**Common options:**

- `--target <name>`: Use specific target from manifest.yml (bundles project identifier + templating config)
- `--format json`: Get machine-readable output (for list commands)

### Definition Syntax Rules

1. **Use DEFINE, not CREATE** for named objects:

   ```sql
   DEFINE TABLE MY_DB.MY_SCHEMA.MY_TABLE (
       id NUMBER,
       name VARCHAR
   );
   ```

2. **Always use fully qualified names**:

   ```sql
   DEFINE TABLE database.schema.table_name (...);
   ```

3. **Grants use standard SQL syntax** (imperative, not DEFINE):

   ```sql
   GRANT SELECT ON TABLE MY_DB.MY_SCHEMA.MY_TABLE TO ROLE MY_ROLE;
   ```

4. **Data quality expectations** use ATTACH syntax:
   ```sql
   ATTACH DATA METRIC FUNCTION SNOWFLAKE.CORE.NULL_COUNT
       TO TABLE MY_DB.RAW.MY_TABLE
       ON (column_name)
       EXPECTATION NO_NULLS (value = 0);
   ```

### ⚠️ CRITICAL: Reading Output Files

**After running `plan`, you MUST read and parse the output JSON files:**

- `out/plan/plan_result.json` - after plan

**This is MANDATORY, not optional.** The agent must:

1. Read the JSON file
2. Parse the content
3. Check for errors or issues
4. Report findings to the user
5. Fix any issues before proceeding

**If plan output already exists** and user asks for a summary, **read the existing file** instead of rerunning unless explicitly requested.

### Safety Rules

1. **NEVER deploy without running plan first**
2. **NEVER deploy without explicit user confirmation**
3. **ALWAYS highlight DROP and data-affecting ALTER operations**
4. **ALWAYS suggest using --alias for deployments** to track deployment history
5. **ALWAYS read and parse output JSON files** after analyze/plan commands
6. **If you encounter `ATTACH PRE_HOOK` or `ATTACH POST_HOOK`** in any definition file, inform the user that DDL hooks are not supported in the current version of DCM. Offer to extract the hook contents into `pre_deploy.sql` / `post_deploy.sql` companion scripts at the project root. ⚠️ Warn that companion scripts do NOT support Jinja — any `{{ }}` variables must be replaced with literal values or shell variable substitution.

### When Creating Definitions

1. **Clarify requirements before writing code**:

   - Ask about object names
   - Confirm column names and types
   - Verify relationships between objects
   - Understand configuration needs (multi-environment?)

2. **Propose structure and get confirmation**:

   - Present proposed definitions to user
   - Wait for approval before writing files

3. **Use appropriate file organization** (all files go in `sources/definitions/`):
   - `infrastructure.sql`: Databases, schemas, warehouses, **internal stages**, sequences
   - `tables.sql` or `raw.sql`: Table definitions
   - `analytics.sql`: Dynamic tables, transformations
   - `serve.sql`: Views for consumption
   - `procedures.sql`: Stored procedures
   - `alerts.sql`: Alerts (or combine with `tasks.sql` as `scheduled.sql`)
   - `access.sql`: Roles, grants, permissions
   - `expectations.sql`: Data quality rules

## Common Use Cases

### Creating a Data Pipeline

1. Define source tables with CHANGE_TRACKING = TRUE
2. Define dynamic tables for transformations (or tasks for procedural ETL)
3. Define views for consumption
4. Define tasks for scheduled operations and orchestration
5. Define roles and grants for access control
6. Optionally add data quality expectations

### Adopting Existing Objects into DCM

When a user wants to "import" or "adopt" existing Snowflake objects:

1. **Get current DDL**: `SELECT GET_DDL('TABLE', 'fully.qualified.name')`
2. **Categorize the object**:
   - ✅ **Internal stages** (no URL) → Convert to `DEFINE STAGE`
   - ⚠️ **External stages** (with URL parameter) → Place in `post_deploy.sql`
   - ✅ **Tables, Views, Warehouses, Sequences, Procedures, Alerts** → Convert to `DEFINE`
   - ⚠️ **Streams** → Place in `post_deploy.sql`
   - ⚠️ **Integrations** → Place in `pre_deploy.sql`
3. **Convert CREATE to DEFINE** (for supported objects): Replace the keyword only
4. **Add to DCM project definitions**: Place in appropriate .sql file
5. **Run analyze**: Verify object appears in definitions
6. **Run plan and READ the output**:
   - ⚠️ Plan should show **ZERO changes** for adopted objects
   - If plan shows CREATE/ALTER, definition doesn't match exactly
   - Adjust definition until plan shows no changes

**Success criteria:** Adopted objects appear in analyze but result in zero operations in plan.

### Multi-Environment Setup

1. Define targets in manifest.yml (DEV, PROD) with corresponding `templating` configurations
2. Ensure each target on the same account has a unique `project_name` (e.g., `MY_PROJECT_DEV`, `MY_PROJECT_STG`, `MY_PROJECT_PROD`) -- targets with the same `project_name` on the same account will deploy over each other
3. Use Jinja variables in definitions: `{{env_suffix}}`, `{{wh_size}}`
4. Use `--target` flag to select the target (which resolves both project identifier and templating config)
5. Use `templating.defaults` for shared values and configurations for overrides
6. Use Jinja dictionaries for per-resource configuration (e.g., team-specific warehouse sizes, retention policies)

### Inspecting dbt Pipelines

When user asks to create DCM from dbt models:

1. Read dbt model files to understand transformations
2. Create corresponding dynamic table definitions
3. Preserve the DAG structure in DCM

## Error Handling

When commands fail, check:

1. **Connection issues**: Verify connection name is correct
2. **Permission errors**: Ensure user has required privileges
3. **Analysis errors**: Review errors in analyze output JSON
4. **Plan failures**: Check the `error` field in plan output

For debugging, suggest: `snow dcm <command> --debug`

## Related Documentation

- [DCM Syntax Overview](reference/syntax_overview.md) - Core principles and primitive loading guide
- [Project Structure Guide](reference/project_structure.md) - Manifest and project layout
- [CLI Command Reference](reference/cli_reference.md) - All `snow dcm` commands
- `reference/primitives/` - Per-object-type syntax and examples (loaded on-demand)

=== declarative-sharing/ ===
---
name: declarative-sharing
description: "**[REQUIRED]** Use for **ALL** declarative sharing and application packages with TYPE=DATA, (i.e data apps). Share data products across Snowflake accounts with versioning. Default choice when user wants to share data with another account. Also use when converting an existing data share to declarative sharing, or when a consumer wants to migrate from a data share to a declarative app. Triggers: declarative, data product, native app, data app, data application, share, sharing, another account, cross account, cross region, application package, manifest, marketplace, listing, publish, share a table, share data, manifest from share, share to manifest, generate manifest from share, inspect share, share to yaml, introspect share, convert share, migrate share, existing share, secure share to declarative, upgrade share, future-proof share, multiple shares, combine shares, merge shares, multiple data shares, consumer migration, migrate from share, upgrade share to app, replace share with app, share to app migration, drop-in replacement, switch from share to app"
---

# Declarative Sharing (Data Apps)

Share data products with versioning, bundling, and app roles - without the complexity of full native apps.

**"Data app" = declarative share.** When a user says "data app", "data application", "bundle into an app", or "create an app they can install", they mean a declarative share (`TYPE = DATA` application package) — NOT a full native app. Only use the full native app framework if the user explicitly needs a setup script, consumer-side data access, or Snowpark Container Services.

## Intent Detection

Detect user intent and route to the appropriate workflow:

| User Intent | Route |
|-------------|-------|
| **Create/share data from scratch** — share objects, create a data app, build a package, create a listing (no existing data share) | Default workflow (Steps 1-6 below) |
| **Convert or create declarative share from one or more existing data shares** — provider has one or more traditional data shares (secure shares) and wants to migrate or combine them into declarative sharing, or use them as the starting point for a new declarative share | **Load** `workflows/manifest-from-share.md`, then continue with Steps 4-6 below |
| **Consumer migrating from data share to declarative app** — consumer has a database from a traditional data share and the provider has published a new declarative app (listing or package). Consumer wants to switch with zero downtime and no query changes | **Load** `workflows/consumer-share-migration.md` (standalone workflow, does NOT continue with Steps below) |

**Route to `workflows/manifest-from-share.md`** when the user mentions an existing data share (or multiple data shares) they want to convert or base the declarative share on. Common motivations:
- Migrating from traditional sharing to declarative sharing
- Combining multiple data shares into a single declarative share spanning multiple databases
- Adding new capabilities (notebooks, agents, semantic views) to an existing share
- Future-proofing a data share with versioning and app roles
- Getting versioning support for an existing share

After `workflows/manifest-from-share.md` produces the manifest, return here at **Step 4** to create and release the application package.

**Route to `workflows/consumer-share-migration.md`** when the user is a **consumer** (not provider) who already has a database from a traditional data share and wants to switch to a new declarative app. Key signals:
- User mentions having a shared database they want to replace/upgrade
- User mentions a listing name or app package from their provider
- User asks about migrating grants, renaming databases, or zero-downtime share migration
- User is on the **consumer** side (they received a share, not created one)

## When to Use This Skill

**Choose Declarative Sharing when cross-account sharing:**
- Sharing data with **another account** (recommend declarative sharing by default)
- Sharing **multiple related objects** (tables + views + agents + semantic views)
- Need **versioning** with automatic consumer updates
- Want **app roles** for granular access control within the share
- Sharing **Cortex Agents** or **semantic views**
- Even sharing a **single table** — declarative sharing provides versioning and a better upgrade path

**Use Traditional Data Sharing ONLY when:**
- User **explicitly** asks for a traditional data share (not an application package)
- Sharing a **single table or view** with **no future need** for bundling, versioning, or AI features
- No versioning or bundling needed and user confirms they don't want it

**Use Full Native Apps instead when:**
- Need a **setup script** to create objects in consumer account
- App must **access consumer's data** (with their permission)
- Require **Snowpark Container Services** or custom containers
- Building **Streamlit apps** → Use `apps/deploy-to-spcs` or `apps/build-react-app` skills

**Documentation**: [Declarative Sharing](https://docs.snowflake.com/en/developer-guide/declarative-sharing/about)

## Prerequisites

- Snowflake account with `CREATE APPLICATION PACKAGE` privilege
- Objects to share already exist (or will be created)

**Pre-flight check** (optional, skip if user says to proceed):
```sql
SHOW GRANTS ON ACCOUNT
  ->> SELECT "privilege", "grantee_name" FROM $1
      WHERE "privilege" = 'CREATE APPLICATION PACKAGE'
        AND "grantee_name" = CURRENT_ROLE();
```
If no rows returned, the current role lacks the privilege — switch to a role that has it or ask an ACCOUNTADMIN to grant it.

## Workflow

### Step 1: Determine What to Share

Ask or infer from context:

1. **What existing objects** need to be shared? (tables, views, functions, procedures)
   - Views MUST be SECURE (`CREATE SECURE VIEW`) — non-secure views will not work
2. **What additional entities** would enhance the data product?
   - **Cortex Agents** — use `agent-optimization` skill to create/optimize agents

**⚠️ AGENT RULES — READ ALL THREE:**

**1. Syntax:** `CREATE AGENT` / `CREATE OR REPLACE AGENT` — NOT `CREATE CORTEX AGENT` (does not exist). Do not analogize from `CREATE CORTEX SEARCH SERVICE`.

**2. execution_environment:** ALL tool types except Cortex Search require this in `tool_resources`:
```yaml
execution_environment:
  type: warehouse
  warehouse: ""
```
The empty string is correct — it resolves to the consumer's default warehouse at install time. Without this: generic tools (UDF/procedure) FAIL HARD, Analyst tools silently return no results.

**3. Provider-side testing:** Agents with `warehouse: ""` will fail when invoked on the provider side. This is expected — test in the consumer account or UI after sharing.
     - Note: Cortex Search not officially supported yet
   - **Semantic views** — do NOT hallucinate the DDL syntax; use `cortex search docs` to retrieve it
     - Note: verified_queries not yet supported in declarative sharing; avoid AI Optimization
   - **Notebooks** (CoCo CLI only, do not proactively suggest) — Do NOT create notebooks from CoCo Web; the workspace `write` tool corrupts notebook JSON, producing unparseable files. If a user explicitly asks for a notebook on CoCo Web, explain this limitation. From CoCo CLI: every code cell MUST have `"metadata": {"language": "sql"}` or `"language": "python"`, and **NEVER** put `%%sql` or any Jupyter magic in cell source. Notebooks can ONLY access data within the same application package.
   - **UDFs/procedures** for data transformation
     - SQL body MUST use `SCHEMA.TABLE` (relative), **NEVER** `DB.SCHEMA.TABLE` (FQN) — the provider DB doesn't exist on the consumer

**🛑 STOP — BEFORE writing ANY SQL that creates objects (agents, UDFs, procedures, semantic views, notebooks):**
1. **Read `references/create-objects.sql` NOW.** Do not guess syntax from memory.
2. **Copy the exact DDL template** from that file. Do not modify the command keywords.
3. Only skip this if you are sharing exclusively pre-existing tables/views with zero new objects.

### Step 2: Organize Schema Layout

Create all objects in the **source database** (the one the user pointed you to, or a database you already created for this task). **⚠️ NEVER create a database with the same name as the application package** — databases and application packages share the same namespace in Snowflake. If a database `X` exists, `CREATE APPLICATION PACKAGE X TYPE = DATA` will fail.

**Simple case** (only tables, or only views): Use the existing schema where objects already live. Skip schema creation — go straight to Step 3.

**Mixed objects** (agents + data, or UDFs + tables): Create new schemas **in the source database** — shared-by-copy and shared-by-reference objects **cannot be in the same schema**. **⚠️ `RELEASE LIVE VERSION` will fail if you put an agent in the same schema as tables/views.**

| Category | Objects | Schema |
|----------|---------|--------|
| **Shared-by-copy** | Agents, UDFs, procedures | `SHARED_BY_COPY_SCHEMA` |
| **Shared-by-reference** | Tables, views, semantic views, Cortex Search services | `SHARED_BY_REFERENCE_SCHEMA` |

```
SOURCE_DATABASE/          ← the database containing source data (NOT the package name)
├── SHARED_BY_COPY_SCHEMA /
│   ├── my_agent
│   └── my_udf()
└── SHARED_BY_REFERENCE_SCHEMA/
    ├── my_table
    └── my_semantic_view
```

### Step 3: Create Manifest

**🛑 STOP — Read `references/manifest.yml` NOW before writing any manifest YAML.** The format is non-standard and differs from what you expect. Do not guess.

**Minimal example** (sharing one table from scratch — when coming from `manifest-from-share.md`, use the manifest it generated instead):
```yaml
roles:
  - app_user:
      comment: "Read-only access"

shared_content:
  databases:
    - MY_DATABASE:
        schemas:
          - MY_SCHEMA:
              roles: [app_user]
              tables:
                - MY_TABLE:
                    roles: [app_user]
```

**Critical format rules:**
- Do NOT include `manifest_version` — it is auto-added on release
- Do NOT use `app_roles:` — the correct key is `roles:`
- Do NOT use `artifacts:`, `setup_script:`, `privileges:`, or `references:` — those are for native apps, NOT declarative sharing
- Database and schema names are map keys (with colon), NOT `name:` fields
- Object types are: `tables`, `views`, `semantic_views`, `cortex_agents`, `functions`, `procedures`, `cortex_search_services`
- Per-object `roles` must be a subset of the parent schema's `roles`
- **`required_databases`**: Almost always OMIT this. Only needed when a shared view's expansion references tables in a *different* database that isn't already in `shared_content/databases` — this tells Snowflake to replicate that database in cross-region scenarios. If all your objects live in the same database, do NOT add `required_databases`. It is NOT a place to list the databases you're sharing — that's what `shared_content/databases` is for

### Step 4: Create and Release Package

**🛑 STOP — Read `references/package-release.sql` NOW before running any package commands.** Do not guess syntax.

**⚠️ NEVER do these:**
- `CREATE DATABASE <PACKAGE_NAME>` — databases and app packages share the same namespace; this blocks `CREATE APPLICATION PACKAGE` with that name
- `CREATE CORTEX AGENT` — WRONG; correct is `CREATE AGENT` (no "CORTEX" keyword)
- `CREATE APPLICATION PACKAGE <PKG> DATA = TRUE` — WRONG syntax; correct is `TYPE = DATA`
- `CREATE APPLICATION PACKAGE <PKG> TYPE=SHARE` — WRONG; `TYPE=DATA`, not `TYPE=SHARE`
- `CREATE OR REPLACE APPLICATION PACKAGE ...` — no `OR REPLACE` for APPLICATION PACKAGES
- `CREATE OR REPLACE APPLICATION ...` — no `OR REPLACE` for APPLICATIONS (use DROP + CREATE)
- `ALTER APPLICATION PACKAGE ... ADD LIVE VERSION` — LIVE version is auto-created
- `ALTER APPLICATION PACKAGE ... REGISTER VERSION` — REGISTER is for release channels, not LIVE
- `PUT 'snow://workspace/...'` — PUT only accepts local `file://` URLs; use `COPY FILES` instead
- `SELECT $1 FROM snow://...` — not supported for application packages
- `SET DEFAULT RELEASE DIRECTIVE` — wrong command for LIVE version
- `GRANT REFERENCE_USAGE ON DATABASE ...` — NOT needed; the manifest handles all access automatically
- `GRANT USAGE ON DATABASE/SCHEMA ... TO APPLICATION PACKAGE` — NOT needed for declarative sharing; this is traditional sharing syntax

**Note:** Snowflake uppercases unquoted identifiers. If you create `my_pkg`, it becomes `MY_PKG`. Use the uppercased name in `snow://` URLs: `snow://package/MY_PKG/versions/LIVE/`.

**Environment check** — your system prompt tells you which environment you're in. Use exactly one path below:
- `"You are in a Workspace"` → **CoCo Web (Workspaces)** — has `write`/`read`/`edit` tools
- `"You are NOT in a Workspace"` → **CoCo Web (Non-Workspaces)** — NO file tools, must use stage method
- CLI / terminal → **CoCo CLI** — has `write`/`read`/`edit` tools, local filesystem

**Step 4.1** — Create package (copy this verbatim — do NOT guess variations):
```sql
CREATE APPLICATION PACKAGE <PKG> TYPE = DATA;
```
If unsure about ANY step below, re-read `references/package-release.sql` NOW before proceeding.

**Step 4.2** — Write and upload `manifest.yml`. Follow your environment path:

**CoCo Web (Workspaces):**
1. Write `manifest.yml` via `write` tool. User can review/edit before upload.
2. Upload:
```sql
COPY FILES INTO snow://package/<PKG>/versions/LIVE/
  FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/'
  FILES = ('manifest.yml');
```

**CoCo Web (Non-Workspaces):**
You do NOT have `write`/`read`/`edit` tools. Recommend the user open a Workspace for the best experience: *"For file management and easier editing, open a Workspace in Snowsight (Projects > Workspaces) and start a new CoCo chat there."*

If the user wants to proceed without Workspaces, use the stage method — write YAML directly to a stage using `$$` dollar-quoting and a passthrough file format:
```sql
CREATE OR REPLACE TEMPORARY STAGE manifest_stage;
COPY INTO @manifest_stage/manifest.yml FROM (
  SELECT $$<entire manifest YAML here>$$
)
FILE_FORMAT = (TYPE = CSV COMPRESSION = NONE FIELD_OPTIONALLY_ENCLOSED_BY = NONE ESCAPE = NONE ESCAPE_UNENCLOSED_FIELD = NONE)
SINGLE = TRUE OVERWRITE = TRUE;

COPY FILES INTO snow://package/<PKG>/versions/LIVE/
  FROM @manifest_stage
  FILES = ('manifest.yml');
```
Use `$$` dollar-quoting to avoid escaping issues in YAML. The four FILE_FORMAT params are all required — without them Snowflake adds compression, backslash escaping, or quoting that corrupt the YAML.

**CoCo CLI:**
1. Write `manifest.yml` via `write` tool. User can review/edit before upload.
2. Upload:
```sql
PUT file:///workspace/manifest.yml snow://package/<PKG>/versions/LIVE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

**Step 4.3** (optional, **CoCo CLI only**) — Write notebook `.ipynb` via `write` tool.
**⚠️ Do NOT create notebooks on CoCo Web (any tab).** The workspace `write` tool corrupts notebook JSON, and the stage method cannot produce valid notebook JSON. If the user asks for a notebook on CoCo Web, explain this limitation. Do not proactively suggest notebooks.

**Step 4.3a** — **Notebook sanitization** (CoCo CLI only — REQUIRED before uploading ANY `.ipynb`):
After writing the notebook, **re-read** it and verify:
- **No** `%%sql`, `%%sql -r dataframe_N`, or any `%%` magic prefix in any cell `"source"`
- **No** `"resultVariableName"` in cell `"metadata"`
- Every code cell has `"metadata": {"language": "sql"}` or `"metadata": {"language": "python"}`
If any magic is present, `edit` the file to strip it. Then add a second `PUT` for the `.ipynb` file.

**Step 4.4** — Verify upload before releasing:
```sql
LIST snow://package/<PKG>/versions/LIVE/;
```
**If 0 rows: do NOT release.** Debug the upload — the file path or environment may be wrong. Re-check Step 4.2.

**Step 4.5** — Release (MUST be LAST, ONLY after LIST confirms files are present):
```sql
ALTER APPLICATION PACKAGE <PKG> RELEASE LIVE VERSION;
```

**⚠️ STOP**: Confirm package created and LIVE version released before proceeding.

### Step 4A: Modifying an Existing Package

Use this flow when the user wants to **modify** a package that already exists — e.g., update the manifest or add new files. Skip Steps 1-4 above; jump directly here.

**Step 4A.1** — List current files:
```sql
LIST snow://package/<PKG>/versions/LIVE/
```

**Step 4A.2** — Download files for editing:

**CoCo Web (Workspaces):**
```sql
COPY FILES INTO 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/'
  FROM snow://package/<PKG>/versions/LIVE/
  FILES = ('manifest.yml');
```
Then `read`/`edit` the file in the workspace.

**CoCo Web (Non-Workspaces):**
Recommend the user switch to Workspaces for easier editing. If they decline, download to a stage and read:
```sql
CREATE OR REPLACE STAGE download_stage;
COPY FILES INTO @download_stage/
  FROM snow://package/<PKG>/versions/LIVE/
  FILES = ('manifest.yml');

CREATE OR REPLACE FILE FORMAT raw_text_fmt
  TYPE = CSV FIELD_DELIMITER = NONE RECORD_DELIMITER = NONE
  COMPRESSION = NONE ESCAPE = NONE ESCAPE_UNENCLOSED_FIELD = NONE;

SELECT $1 AS content FROM @download_stage/manifest.yml (FILE_FORMAT => 'raw_text_fmt');
```
Edit the YAML, then re-upload using the stage method from Step 4.2.

**CoCo CLI:**
```sql
GET snow://package/<PKG>/versions/LIVE/manifest.yml file:///tmp/;
```
Ask the user where they want files downloaded — `/tmp/` is a safe default.

**Step 4A.3** — Read and edit files (Workspaces/CLI: via `read`/`edit` tools).

**Step 4A.4** — Upload modified files back to package (same upload commands as Step 4.2 for your environment). Verify with `LIST` before releasing.

**Step 4A.5** — Test or release the updated version:

To **iterate without releasing** (provider-side dev/test cycle):
```sql
-- Build to pick up the updated files:
ALTER APPLICATION PACKAGE <PKG> BUILD;

-- Install test app from LIVE version (first time only):
CREATE APPLICATION <APP> FROM APPLICATION PACKAGE <PKG> USING VERSION LIVE;

-- Upgrade test app to latest built LIVE version (subsequent iterations):
ALTER APPLICATION <APP> UPGRADE USING VERSION LIVE;
```

To **release** (MUST be LAST, after testing):
```sql
ALTER APPLICATION PACKAGE <PKG> RELEASE LIVE VERSION;
```

If a released app already exists (provider or consumer), upgrade it after releasing:
```sql
ALTER APPLICATION <APP> UPGRADE;
```

### Step 5: Create Listing (Distribution)

> **Ready to share?** Would you like to:
> 1. **Create a private listing** (share with specific accounts)
> 2. **Use Provider Studio UI** (more options)
>
> For private listing, I'll need:
> - **Target account(s)**: `MYORG.MYACCOUNT` format
> - **Listing title**

**⚠️ MANDATORY**: Listing syntax is in `references/package-release.sql` (already loaded at Step 4). For advanced listing scenarios, invoke the `internal-marketplace-org-listing` skill.

To find organization name: `SELECT CURRENT_ORGANIZATION_NAME();`

**Cross-region sharing** — Ask the user: "Is the target account in a different region or cloud?" If yes:

**⚠️ NEVER run these for cross-region checks (all are hallucinated/wrong):**
- `SYSTEM$SHOW_ACTIVE_REGION_LIST()` — does NOT exist
- `SYSTEM$SHOW_ACTIVE_REGION_GROUP()` — does NOT exist
- `SYSTEM$GLOBAL_ACCOUNT_SET_PARAMETER(...)` — does NOT exist
- `SHOW ORGANIZATION ACCOUNTS` — wrong tool for this job
- `SHOW SHARES` to find consumer region — wrong tool for this job
- `SNOWFLAKE.ORGANIZATION_USAGE.ACCOUNTS` — wrong tool for this job
- Do NOT try to programmatically discover the consumer's region — just ask the user

**The ONLY command needed** — check if auto-fulfillment is enabled for the provider account:
```sql
SELECT SYSTEM$IS_GLOBAL_DATA_SHARING_ENABLED_FOR_ACCOUNT('<PROVIDER_ACCOUNT_NAME>');
```
- Returns `TRUE` → proceed to create cross-region listing with `auto_fulfillment` in YAML
- Returns `FALSE` → tell user ORGADMIN must enable it first:
  ```sql
  SELECT SYSTEM$ENABLE_GLOBAL_DATA_SHARING_FOR_ACCOUNT('<PROVIDER_ACCOUNT_NAME>');
  ```
- These functions require `ORGADMIN` role. If the current role can't run them, tell the user to ask their ORGADMIN.

Then add `auto_fulfillment` to the listing YAML — see `references/package-release.sql` for the exact cross-region listing template.

### Step 6: Consumer-Side Verification

> **If you're a consumer**, skip directly to this step.

**⚠️ NEVER do these:**
- `CREATE OR REPLACE APPLICATION ...` — does NOT exist. Must `DROP APPLICATION IF EXISTS` first, then `CREATE APPLICATION`

**Install commands** (copy verbatim — do NOT guess):
```sql
-- Same-account install (from package):
CREATE APPLICATION <APP> FROM APPLICATION PACKAGE <PKG>;

-- Cross-account install (from listing):
CREATE APPLICATION <APP> FROM LISTING '<LISTING_ID>';

-- Reinstall (must drop first):
DROP APPLICATION IF EXISTS <APP>;
CREATE APPLICATION <APP> FROM APPLICATION PACKAGE <PKG>;

-- Upgrade existing app to latest released version (no reinstall needed):
ALTER APPLICATION <APP> UPGRADE;
```

**Test in UI first**: Snowflake Intelligence → select the agent.

**Troubleshooting**: See `references/troubleshooting.md`.

---

## Key Concepts

### Constraints & Limits

- **1,000 object limit** in `shared_content` per application package — plan schema layout accordingly
- **No wildcard/regex** for object names in the manifest — every object must be listed explicitly
- **Semantic view verified_queries**: Do NOT use FQN — use table alias only (e.g. `SELECT * FROM COMPANIES`), or you get INTERNAL_ERROR 370001
- **Notebooks can only access data within the same application package** — they cannot query external databases or the provider's source data directly
- **No REFERENCE_USAGE grants** — manifest handles access automatically
- **App name becomes the database** — `SELECT * FROM <app_name>.<schema>.<table>`

---

## Stopping Points

**Skip all stopping points when the user says to proceed end-to-end or skip confirmations.** Execute the full workflow without pausing.

When interactive:
- ✋ After Step 2: Confirm schema layout before creating manifest
- ✋ After Step 4 or 4A: Confirm package created/updated and version released
- ✋ After Step 5: Ask whether user wants a listing
- ✋ After Step 6: Confirm consumer can access data

**Resume rule:** Upon user approval, proceed directly to next step without re-asking.

**Iteration rule:** When user asks to redo or fix a step, skip confirmations for previously approved steps. Go directly to the step that needs fixing without re-asking about earlier decisions.

## Output

- Application package (`TYPE=DATA`) with manifest
- Consumer-installable data app
- Private listing (if requested)

=== deploy-to-spcs/ ===
---
name: deploy-to-spcs
description: "Deploy containerized apps to Snowpark Container Services. Use when: deploying Docker apps, creating SPCS services, pushing images to Snowflake registry, granting role access to SPCS service endpoints. Triggers: SPCS, Snowpark Container Services, deploy to Snowflake, container deployment, grant access to service, grant role access, service role, consumer access, SPCS service, service endpoints."
---

# Deploy to Snowpark Container Services (SPCS)

Deploy any containerized application to Snowflake using Snowpark Container Services. Works with any Docker-based app (Next.js, Python, Go, etc.).

## When to Use
- User has a containerized app (Docker) ready to deploy
- User wants to host an app on Snowflake infrastructure
- User mentions SPCS, Snowpark Container Services, or deploying to Snowflake

## Tools Used
- `bash` - Run docker commands, snow CLI
- `snowflake_sql_execute` - Create compute pools, repos, services
- `cortex browser` - Verify deployed apps

## Stopping Points
- ⚠️ Step 1: Confirm app builds successfully
- ⚠️ Step 2: Confirm SPCS prerequisites exist
- ⚠️ Step 5: Confirm deployment success
- ⚠️ Step 6: Confirm consumer role access

---

## Workflow

### Step 1: Verify App Readiness

**Goal:** Ensure the app is containerized and builds correctly.

**Actions:**

1. Confirm app has a working `Dockerfile`
2. Confirm app builds locally:
   ```bash
   docker build --platform linux/amd64 -t <image-name>:latest .
   ```
3. Confirm app exposes a port (default: 8080)

**Output:** Successful local Docker build.

**⚠️ MANDATORY STOPPING POINT:** Do NOT proceed until app builds successfully.

---

### Step 2: Verify SPCS Prerequisites

**Goal:** Ensure compute pool and image repository exist.

**Actions:**

1. Check current role:
   ```sql
   SELECT CURRENT_ROLE(), CURRENT_USER();
   ```

2. Check/create compute pool:
   ```sql
   SHOW COMPUTE POOLS;
   
   -- If no accessible pool exists:
   CREATE COMPUTE POOL <pool_name>
     MIN_NODES = 1
     MAX_NODES = 1
     INSTANCE_FAMILY = CPU_X64_XS;
   ```

3. Check/create image repository:
   ```sql
   SHOW IMAGE REPOSITORIES;
   
   -- If needed:
   CREATE IMAGE REPOSITORY <db>.<schema>.<repo_name>;
   ```

4. Login to registry:
   ```bash
   snow spcs image-registry login --connection <conn>
   ```

**Output:** Compute pool and image repository ready.

**⚠️ MANDATORY STOPPING POINT:** Do NOT proceed until prerequisites exist.

---

### Step 3: Create Service Specification

**Goal:** Define the service configuration.

**Actions:**

1. Create `service-spec.yaml` with the following template:
   ```yaml
   spec:
     containers:
     - name: <app-name>
       image: /<db>/<schema>/<repo>/<image>:latest
       env:
         HOSTNAME: "0.0.0.0"
         PORT: "8080"
         NODE_ENV: production
       resources:
         requests:
           memory: 1Gi
           cpu: 500m
         limits:
           memory: 2Gi
           cpu: 1000m
       readinessProbe:
         port: 8080
         path: /
     endpoints:
     - name: <endpoint-name>
       port: 8080
       public: true
   ```

2. Adjust `resources`, `port`, and `env` based on app requirements.

**Output:** `service-spec.yaml` file ready for deployment.

**Next:** Proceed to Step 4.

---

### Step 4: Build and Push Image

**Goal:** Push the container image to Snowflake registry.

**Actions:**

1. Build, tag, and push:
   ```bash
   docker build --platform linux/amd64 -t <image-name>:latest .
   docker tag <image-name>:latest <registry-url>/<db>/<schema>/<repo>/<image-name>:latest
   docker push <registry-url>/<db>/<schema>/<repo>/<image-name>:latest
   ```

   Registry URL format: `<account>.registry.snowflakecomputing.com`

**Output:** Image pushed to Snowflake image repository.

**Next:** Proceed to Step 5.

---

### Step 5: Deploy Service

**Goal:** Create the SPCS service and verify it's running.

**Actions:**

1. Create the service:
   ```sql
   CREATE SERVICE <service_name>
     IN COMPUTE POOL <pool_name>
     FROM SPECIFICATION $$
     <contents of service-spec.yaml>
     $$
     MIN_INSTANCES = 1
     MAX_INSTANCES = 1;
   ```

2. Monitor status and get URL:
   ```sql
   SELECT SYSTEM$GET_SERVICE_STATUS('<service_name>');
   SHOW ENDPOINTS IN SERVICE <service_name>;
   ```

3. Extract `ingress_url` from SHOW ENDPOINTS and display to user.

4. Verify deployment:
   ```bash
   cortex browser open "https://<ingress_url>"
   cortex browser snapshot -i
   ```

**Output:** Service running with accessible URL.

**⚠️ MANDATORY STOPPING POINT:** Do NOT proceed until user confirms deployment success.

---

### Step 6: Grant Consumer Access

**Goal:** Configure access for the consuming role.

**Actions:**

1. **Ask user:** "What role will consume this service?"

2. Check the grants to the role 
   ```sql
   SHOW GRANTS TO ROLE <consumer_role>;
   ```

3. Grant ALL THREE of the following (all are required, do not skip any):
   ```sql
   -- 1. Database access (REQUIRED)
   GRANT USAGE ON DATABASE <db> TO ROLE <consumer_role>;
   -- 2. Schema access (REQUIRED)
   GRANT USAGE ON SCHEMA <db>.<schema> TO ROLE <consumer_role>;
   -- 3. Service endpoint access (REQUIRED) — note: GRANT SERVICE ROLE, not GRANT USAGE ON SERVICE
   GRANT SERVICE ROLE <service_name>!ALL_ENDPOINTS_USAGE TO ROLE <consumer_role>;
   ```

4. If the service is using a table in Snowflake, grant what the service needs:
   ```sql
   GRANT USAGE ON DATABASE <table_db> TO ROLE <consumer_role>;
   GRANT USAGE ON SCHEMA <table_db>.<table_schema> TO ROLE <consumer_role>;
   -- Grant privileges the service requires (SELECT, INSERT, UPDATE, DELETE, etc.)
   GRANT <privileges> ON TABLE <table_db>.<table_schema>.<table> TO ROLE <consumer_role>;
   ```


**Output:** Consumer role can access the service.

**⚠️ MANDATORY STOPPING POINT:** Do NOT proceed until user confirms consumer role access works.

---

## Updating a Service

**⚠️ CAUTION:** Always use `ALTER SERVICE` to update. Never drop and recreate—this changes the URL and breaks integrations.

```bash
docker build --platform linux/amd64 -t <image-name>:latest .
docker tag <image-name>:latest <registry-url>/<db>/<schema>/<repo>/<image-name>:latest
docker push <registry-url>/<db>/<schema>/<repo>/<image-name>:latest
```

```sql
ALTER SERVICE <service_name> FROM SPECIFICATION $$
<full yaml spec>
$$;
```

---

## Troubleshooting

**Get service logs:**
```sql
SELECT SYSTEM$GET_SERVICE_LOGS('<service_name>', 0, '<container_name>');
```

**Common issues:**

| Problem | Cause | Fix |
|---------|-------|-----|
| Image not found | Path mismatch | Use exact format: `/<db>/<schema>/<repo>/<image>:latest` (case-sensitive, leading slash required) |
| Service fails readiness | Port mismatch | Align three ports: `readinessProbe.port`, `PORT` env var, `endpoints.port` |
| Auth errors on push | Expired login | Re-run `snow spcs image-registry login --connection <conn>` |
| Permission errors | Missing grants | Grant required privileges to the service owner role |

---

## Output

- Deployed SPCS service URL
- Service status confirmation
- Consumer role access configured

=== developing-with-streamlit-in-snowflake/ ===
---
name: developing-with-streamlit-in-snowflake
description: "Use for Streamlit development tasks with a Snowflake angle: Snowflake-connected dashboards, Streamlit-in-Snowflake (SiS) deployment to warehouse / SPCS / Workspaces, applying Snowflake branding, st.connection('snowflake'), troubleshooting a local `streamlit run` against Snowflake (wrong role/user/database, 'Database not authorized', PAT-bound USE ROLE failure, stale st.connection cache), and operating an already-deployed STREAMLIT object (ALTER STREAMLIT SET QUERY_WAREHOUSE, RENAME, DROP, GRANT, SHOW STREAMLITS). Also use for general Streamlit authoring (widgets, layouts, caching, theming, custom components) — this skill routes general OSS questions to version-matched content from a detected Streamlit ≥1.57 install, or to a bundled OSS snapshot when no install is available. Triggers: streamlit, st., dashboard, app.py, theme, beautify, style, CSS, color, background, button, custom component, st.components, snowflake dashboard, monitor snowflake, streamlit on snowflake, streamlit in snowflake, SiS, scaffold, snowflake theme, st.connection snowflake, snow streamlit deploy, deploy this streamlit, redeploy, alter streamlit, show streamlits, drop streamlit, rename streamlit app, change query warehouse, streamlit app down, streamlit run wrong role, database not authorized, SNOWFLAKE_DEFAULT_CONNECTION_NAME."
---

# Developing with Streamlit in Snowflake

Entry-point skill for Streamlit work in a Snowflake context. Routes to one of two specialized sub-skills based on the user's prompt.

## Sub-skills

| Sub-skill | Read when |
|---|---|
| `sf/SKILL.md` (skill name: `scaffolding-streamlit-in-snowflake`) | User wants a Snowflake-wired starter (dashboard, theme, SiS deploy) or any Snowflake-specific Streamlit task |
| `developing-with-streamlit/SKILL.md` | General Streamlit authoring with no Snowflake-specific angle (used as fallback when no Streamlit ≥1.57 install is detected) |

Execute the steps below in order. Do not answer the user's Streamlit question until a guidance source is loaded.

## Step 1 — Identify routing

If the user's prompt involves any of:
- Snowflake-connected data, `st.connection("snowflake")`
- Deploying to Streamlit-in-Snowflake (SiS warehouse, SPCS, Workspaces), `snow streamlit deploy`, `snowflake.yml`
- Snowflake-branded theming
- A Snowflake-specific scaffold (compute monitor, metrics, stock peers, etc.)
- **Troubleshooting a local `streamlit run` that talks to Snowflake** — wrong role / user / database in the running session, "Database X does not exist or not authorized" while user has Snowsight access, PAT-bound `USE ROLE` failures, stale `st.connection` cache after env-var change, `SNOWFLAKE_DEFAULT_CONNECTION_NAME` questions
- **Operating an already-deployed `STREAMLIT` object** — `ALTER STREAMLIT … SET QUERY_WAREHOUSE`, `RENAME TO`, `DROP STREAMLIT`, `GRANT USAGE`, `SHOW STREAMLITS`, "change the warehouse my deployed app uses", "rename my deployed app", "where are the logs for my SiS app" (there aren't any)

→ Read `<SKILL_DIR>/sf/SKILL.md` and follow its guidance (including `sf/references/snowflake-deployment.md` for manifests, `compute_pool`, and deploy). Continue to Step 2.

Otherwise (general Streamlit authoring with no Snowflake angle) → continue to Step 2.

## Step 2 — OSS path: locate Streamlit content

### 2a. Detect the Python environment

Use the built-in `cortex env detect` command, passing the user's project directory as `--dir` (absolute path):

```bash
cortex env detect --dir <absolute path to user's project>
```

The command returns JSON:

```json
{"directory": "...", "result": "..."}
```

When environments are found, the `result` string embeds a JSON array with an entry per environment:

```json
[{"dir": "/abs/path/to/project", "cmd": "uv run python"}, ...]
```

Each entry gives the env's directory (`dir`) and the exact command to invoke its Python (`cmd`). If `result` reports that no environments were found, skip to **Case B**.

### 2b. Probe each environment for Streamlit

For each entry, invoke the `cmd` against the one-line probe below. For `uv run` style invocations, pin the project with `--project <dir>` so cwd does not matter; for path-based invocations (e.g. `.venv/bin/python`), form an absolute path with the entry's `dir`.

Probe body:

```python
import streamlit, os
print(f"STREAMLIT_PATH={os.path.dirname(streamlit.__file__)}")
print(f"STREAMLIT_VERSION={streamlit.__version__}")
```

Concretely, for a `uv run python` entry:

```bash
uv run --project <dir> python -c "import streamlit, os; print(f'STREAMLIT_PATH={os.path.dirname(streamlit.__file__)}'); print(f'STREAMLIT_VERSION={streamlit.__version__}')"
```

Capture `STREAMLIT_PATH` and `STREAMLIT_VERSION` from the first environment where the probe exits 0. If every environment's probe fails, skip to **Case B**.

## Step 3 — Delegate based on detection outcome

### Case A — Streamlit detected AND version ≥ 1.57.0

The installed package ships version-matched skill content. Read and follow:

```
<STREAMLIT_PATH>/.agents/skills/developing-with-streamlit/SKILL.md
```

Treat that file as your authoritative guidance source for the rest of the task. Reference files, templates, and assets it points to live under `<STREAMLIT_PATH>/.agents/skills/developing-with-streamlit/` — load them from there, not from this skill's directory.

### Case B — No Streamlit found OR version < 1.57.0

Fall back to the bundled OSS snapshot under this skill's `developing-with-streamlit/` sub-skill — content synced from the latest Streamlit PyPI wheel (`.synced-from-version` records the exact version). Read and follow:

```
<SKILL_DIR>/developing-with-streamlit/SKILL.md
```

Reference files and templates it points to live under `<SKILL_DIR>/developing-with-streamlit/references/` and `<SKILL_DIR>/developing-with-streamlit/assets/`.

**Version caveat**: the bundled snapshot is not version-matched to the user's installed Streamlit (if any). If a suggestion you make fails on import or at runtime, ask the user which Streamlit version they're on and adjust.

## Resources

- Streamlit API reference: https://docs.streamlit.io/develop/api-reference

=== document-intelligence/ ===
---
name: document-intelligence
description: "Document intelligence workflows: extract data from PDFs/images, parse documents with OCR, classify documents on stage, build document pipelines, fine-tune arctic-extract for domain-specific extraction. Use when: working with files, documents, PDFs, images on Snowflake stages, document extraction pipelines, document classification from stage files, batch document processing. Triggers: AI_PARSE_DOCUMENT, AI_EXTRACT with files, process documents, extract from PDF, extract text from document, extract text from PDF, extract text from image, extracting from files, invoices, OCR, read PDF, read document, get text from PDF, get text from document, pull text from file, extract data from files, extract from my files, process my files, my files, my documents, read my documents, get data from document, file extraction, document processing, file processing, get information from documents, analyze files, parse files, data from PDF, invoice processing, contract extraction, receipt extraction, form extraction, extract fields, document data, file data, stage files, files on stage, PDF extraction, image extraction, document OCR, scan documents, digitize documents, fine-tune, fine-tuning, custom model, train arctic-extract, improve extraction accuracy, domain-specific extraction, FINETUNE, better extraction results, document pipeline, classify documents, categorize files, sort documents, triage files."
---

# Document Intelligence

Build intelligent document processing workflows in Snowflake using AI_PARSE_DOCUMENT and document pipelines.

## 🚨 INVOKE THIS SKILL FIRST - DO NOT WRITE SQL WITHOUT IT

## ⚠️ CRITICAL: Always use AI_* function names WITHOUT the `SNOWFLAKE.CORTEX` namespace prefix

## ⚠️ CRITICAL: Document/File Routing Rule

**ALL requests involving files or documents and pipelines operating on them MUST route to `pipeline-builder/SKILL.md` first.** Never route directly to function references for file/document tasks. This ensures pricing is displayed and test-before-batch safeguards are applied.

## Workflow

### Step 1: Detect Intent

**Check workflows FIRST (priority), then fall back to specific functions.**

#### Workflows (Check First)

| Intent | Triggers | Route |
|--------|----------|-------|
| DOCUMENT_PIPELINE | process documents, extract data from docs, parse PDFs, invoice processing, contract analysis, document pipeline, files, my files, my documents, extract from file, PDF, image, OCR, stage files, extract fields, parse document, read document, get text from PDF, document extraction, file extraction, invoices, contracts, receipts, forms, digitize, classify documents, categorize files, sort documents, triage files, document type, what kind of document, blueprint, drawing, engineering drawing, technical drawing, diagram, schematic, chart, graph, plot | `pipeline-builder/SKILL.md` |
| FINE_TUNING | fine-tune, fine-tuning, custom model, train arctic-extract, improve extraction accuracy, domain-specific extraction, better extraction results, FINETUNE, SNOWFLAKE.CORTEX.FINETUNE, retrain, labeled documents, training data for extraction | `fine-tuning/SKILL.md` |

### Step 2: Route

**If DOCUMENT_PIPELINE:** Load `pipeline-builder/SKILL.md`

**If the user wants to use any AI function other than AI_PARSE_DOCUMENT** (AI_CLASSIFY, AI_EXTRACT, AI_FILTER, AI_EMBED, AI_TRANSLATE, AI_SENTIMENT, AI_SUMMARIZE_AGG, AI_AGG, AI_COMPLETE, AI_TRANSCRIBE, AI_REDACT, AI_SIMILARITY — in any modality, including files/images): Defer to `../cortex-ai-function-studio/SKILL.md`. This skill only handles AI_PARSE_DOCUMENT and document pipeline workflows.

**If AI_PARSE_DOCUMENT:** Always refer to the latest Snowflake documentation for up-to-date syntax, features first. Don't try to answer from your memory, use reference files of each function in `references/ai-parse-doc.md`.
**If FINE_TUNING:** Load `fine-tuning/SKILL.md`

**If SELECT or unclear**, ask: [WAIT]
```
What would you like to do?

1. Parse Document — OCR and extract content from PDFs/images (AI_PARSE_DOCUMENT)
2. Document Pipeline — Process & extract data from documents at scale
3. Fine-Tuning — Improve arctic-extract accuracy with your own training data

For other AI functions (classify, filter, extract, summarize, translate, etc.),
use cortex-ai-function-studio instead.
```

## Step 3: Validate Generated SQL

**MANDATORY: After generating any SQL, validate it before returning it to the user.**

1. Run `snowflake_sql_execute` with `only_compile: true` on every generated SQL statement.
2. If compilation **succeeds** → return the SQL to the user.
3. If compilation **fails**:
   - Read the full error message carefully.
   - Fix the root cause (do NOT just rewrite the query differently).
   - Re-validate after fixing — do not return SQL that has not passed compilation.
   - Common gotchas to check before re-validating:
     - `VECTOR` type is **not supported inside SQL scripting blocks** — use plain `SELECT` instead.
     - Variables in SQL scripting blocks require **explicit type declarations** (e.g., `LET count INTEGER := 0;`), not type inference from the initializer.
     - `AI_PARSE_DOCUMENT` requires `TO_FILE('@stage', 'file.pdf')` wrapper — never pass a raw string path.

## Stopping Points

- ✋ Step 2: After presenting menu (if SELECT intent) - wait for user selection

## Output

Routes user to appropriate sub-skill or function reference based on detected intent.

## Notes

- All functions run in Snowflake (data never leaves)
- Functions work in SELECT, WHERE, JOIN clauses
- Use batch processing for best throughput
- For interactive/low-latency: consider REST API instead
- **Follow-up handling:** If you have already answered the user's question in a prior turn, do NOT repeat the same response verbatim. Instead, briefly confirm what you already said and ask what additional detail or clarification they need.
- **Explicit go-ahead:** When the user gives a clear directive ("go ahead", "implement all files", "change everything that needs changing"), act on it immediately. Do NOT re-ask for confirmation or defer the decision back to the user. Only ask clarifying questions when the request is genuinely ambiguous, not when the user has already approved the action.
- **Recovery from failure:** When an approach fails or the user signals dissatisfaction ("try again", "that didn't work", "this is wrong"):
  1. Do NOT repeat the same output or retry the identical approach.
  2. Diagnose what specifically failed — read the error, identify the root cause.
  3. If the failure is in your output (wrong SQL, incomplete pipeline), resume from the failing step, not from scratch.
  4. If the failure is an environment/infrastructure blocker (missing stage, encryption error, unsupported feature), clearly tell the user it is not a code error, stop retrying the same fix, and pivot to an alternative approach if the user suggests one.

=== dynamic-tables/ ===
---
name: dynamic-tables
description: "**[REQUIRED]** Use for **ALL** Snowflake Dynamic Table operations: creating, optimizing, monitoring, troubleshooting, and pipeline diagnostics. This is the required entry point for any dynamic table related tasks (DT is an acronym for dynamic table). Triggers: dynamic table, data pipeline, incremental pipeline, DT pipeline, incremental refresh, target lag, UPSTREAM_FAILED, refresh failing, full refresh instead of incremental, DT health, create DT, debug DT, pipeline timeline, Gantt chart, why was DT skipped, trace pipeline, critical path, why was DT skipped, dbt to DT, convert dbt to dynamic table, dbt dynamic table, dbt materialized dynamic_table."
---

# Dynamic Tables

Expert guidance for Snowflake Dynamic Tables: creating pipelines, configuring refreshes, monitoring health, troubleshooting issues, and optimizing performance.

## When to Use

Use this skill when users ask about:
- Creating dynamic tables with appropriate refresh modes
- Setting up dynamic table pipelines with proper target lag configuration
- Monitoring dynamic table health and refresh history
- Troubleshooting refresh failures or performance issues
- Optimizing refresh modes and query patterns
- Breaking large dynamic tables into smaller, more efficient ones

## Dynamic Tables vs Streams+Tasks

**Dynamic Tables are the default choice for Snowflake data pipelines.** For multi-step transformations, chain multiple DTs together—each DT handles one transformation step, and Snowflake manages the dependency graph and refresh order automatically.

```
raw_table → dt_bronze → dt_silver → dt_gold
            (DOWNSTREAM)  (DOWNSTREAM)  (5 min lag)
```

**Only use Streams+Tasks when a specific blocker prevents DT usage:**

| Blocker | Why DTs Can't Handle It |
|---------|------------------------|
| Append-only stream semantics | DTs track all changes (insert/update/delete), can't isolate inserts only. **First check:** can we add IMMUTABLE WHERE on the DT? Consult [optimize/SKILL.md](optimize/SKILL.md). **Or:** use a CI DT with `CHANGES(INFORMATION => APPEND_ONLY)` — see [custom-incrementalization/SKILL.md](custom-incrementalization/SKILL.md). |
| External/directory table sources | Not supported as DT sources |
| Sub-minute latency requirement | DT minimum TARGET_LAG is 1 minute |
| DT → View → DT dependency | Not supported (view cannot sit between two DTs) |
| Stream with static dimension join | ~~DTs recompute full join on any base table change.~~ **Solved by CI DTs**: use `CHANGES()` on the stream side + regular JOIN on static side. See [custom-incrementalization/SKILL.md](custom-incrementalization/SKILL.md). |
| Procedural logic (IF/ELSE, loops) | DTs are declarative SELECT statements only. **Note:** simple conditional MERGE (different actions per INSERT/UPDATE/DELETE) is now supported via CI DTs — see [custom-incrementalization/SKILL.md](custom-incrementalization/SKILL.md). Multi-statement transactions, IF/ELSE blocks, and loops remain blockers. |
| Side effects (API calls, notifications) | DTs cannot call external functions with side effects |
| Write to multiple targets from one source | One DT = one target table |

**Decision tree:**
```
Is there a blocker from the table above?
    │
    ├─ NO  → Use Dynamic Tables (chain multiple for complexity)
    │
    └─ YES → Use Streams+Tasks (or hybrid pattern)
```

For migrating existing Streams+Tasks pipelines to DTs, see [task-to-dt/SKILL.md](task-to-dt/SKILL.md).

## ⚠️ MANDATORY INITIALIZATION

Before any workflow, you MUST:

### Step 1: Load Core References

**Load** the following reference documents:

1. **Load**: [references/sql-syntax.md](references/sql-syntax.md) - SQL command syntax
2. **Load**: [references/monitoring-functions.md](references/monitoring-functions.md) - monitoring function router (database context rules + links to state, refresh analysis, and graph references)

**⚠️ MANDATORY STOPPING POINT**: Do NOT proceed until you have loaded these references.

### Step 2: Establish Session Context

**Goal:** Confirm which Snowflake account, region, user, and role this session is running under so subsequent queries land on the right objects.

Run a single SQL probe before any other DT work:

```sql
SELECT CURRENT_ACCOUNT() AS account,
       CURRENT_REGION()  AS region,
       CURRENT_USER()    AS username,
       CURRENT_ROLE()    AS active_role;
```

If `active_role` cannot see the dynamic tables the user is asking about, ask the user which role they expect to use and re-run with `USE ROLE <role>;`.

**⚠️ MANDATORY STOPPING POINT**: Do NOT proceed until session context is confirmed.

---

## Intent Detection

When a user makes a request, detect their intent and route to the appropriate sub-skill:

### CREATE Intent

**Trigger phrases**: "create dynamic table", "set up DT", "new dynamic table", "define pipeline", "build DT"

**→ Load**: [create/SKILL.md](create/SKILL.md)

### MONITOR Intent

**Trigger phrases**: "check status", "refresh history", "is it healthy", "target lag", "how is my DT", "DT state", "trend", "drift", "week over week", "month over month", "compare before and after", "baseline", "historical refresh performance"

**→ Load**: [monitor/SKILL.md](monitor/SKILL.md)

For **written** health reports (files, runbooks, “every DT in the schema”), use monitor’s **Present Health Report** guidance: cite Snowflake literals such as **`UPSTREAM_FAILED`**, **suspended** / **`SUSPENDED`**, and **`FULL`** refresh mode when those states appear.

### TROUBLESHOOT Intent

**Trigger phrases**: "failing refresh", "not refreshing", "suspended", "full refresh instead of incremental", "refresh_mode_reason", "why is it failing", "DT broken", "errors"

**→ Load**: [troubleshoot/SKILL.md](troubleshoot/SKILL.md)

### OPTIMIZE Intent

**Trigger phrases**: "slow refresh", "make incremental", "improve performance", "immutability", "break into smaller", "decompose", "speed up", "reduce cost"

**→ Load**: [optimize/SKILL.md](optimize/SKILL.md)

### ALERTING Intent

**Trigger phrases**: "set up alerts", "alert on failure", "notify on refresh failure", "DT alerting", "event table alerts", "monitor failures", "email when DT fails"

**→ Load**: [dt-alerting/SKILL.md](dt-alerting/SKILL.md)

### PERMISSIONS Intent

**Trigger phrases**: "insufficient privileges", "permission denied", "privilege error", "DT permissions", "ownership transfer", "can't refresh", "access denied", "masking policy error"

**→ Load**: [permissions/SKILL.md](permissions/SKILL.md)

### TASK-TO-DT Intent

**Trigger phrases**: "convert tasks", "migrate from tasks", "replace stream and task", "task to DT", "streams and tasks to dynamic table", "modernize pipeline"

**Disambiguation:** If the user's pipeline uses MERGE with conditional logic by change type (different handling for inserts vs deletes), or uses a stream-static join pattern, route to CUSTOM-INCREMENTALIZATION instead.

**→ Load**: [task-to-dt/SKILL.md](task-to-dt/SKILL.md)

### CUSTOM-INCREMENTALIZATION Intent

**Trigger phrases**: "custom incrementalization", "CI DT", "REFRESH USING", "MERGE DT", "INSERT INTO SELF", "stream-static join", "append-only log DT", "audit trail DT", "shape of changes", "imperative DT refresh", "different logic for inserts and deletes", "accumulate history in DT", "schema evolution without reinit", "DT only inserts from base table", "DT has only inserts"

**→ Load**: [custom-incrementalization/SKILL.md](custom-incrementalization/SKILL.md)

**Note:** Route here when user needs imperative DML logic in a dynamic table, or when a standard DT can't express their pattern (stream-static joins, conditional INSERT/UPDATE/DELETE handling, append-only accumulation). For general streams+tasks migration where the logic CAN be expressed as a SELECT, route to TASK-TO-DT instead.

### DBT-TO-DT Intent

**Trigger phrases**: "convert dbt to dynamic table", "dbt to DT", "migrate dbt models to DT", "add DT support to dbt", "dbt materialized dynamic_table", "replace dbt table with dynamic table", "dbt dynamic table conversion", "convert dbt pipeline to DT"

**→ Load**: [dbt-to-dt/SKILL.md](dbt-to-dt/SKILL.md)

### PIPELINE-DIAGNOSTICS Intent

**Trigger phrases**: "pipeline timeline", "Gantt chart", "why was DT skipped", "UPSTREAM_FAILED", "trace pipeline", "critical path", "execution timeline", "pipeline execution", "what happened in pipeline", "pipeline visualization", "what was affected by failure", "slowest DT", "pipeline bottleneck", "pipeline trace"

**→ Load**: [pipeline-diagnostics/SKILL.md](pipeline-diagnostics/SKILL.md)

**Note:** This skill handles both pipeline-wide visualization and upstream failure diagnosis using OTel traces. For non-upstream DT issues (e.g., "my DT refresh is failing", "why is it doing full refresh"), route to TROUBLESHOOT instead.

---

## Workflow Decision Tree

```
Start Session
    ↓
MANDATORY: Load reference documents (sql-syntax.md, monitoring-functions.md router)
    ↓
MANDATORY: Confirm session context (CURRENT_ACCOUNT/REGION/USER/ROLE)
    ↓
Detect User Intent
    ↓
    ├─→ CREATE → Load create/SKILL.md
    │   (Triggers: "create dynamic table", "new DT", "set up pipeline")
    │
    ├─→ MONITOR → Load monitor/SKILL.md
    │   (Triggers: "check status", "is it healthy", "refresh history", "trend", "drift", "week over week")
    │
    ├─→ TROUBLESHOOT → Load troubleshoot/SKILL.md
    │   (Triggers: "failing", "not refreshing", "suspended")
    │
    ├─→ OPTIMIZE → Load optimize/SKILL.md
    │   (Triggers: "slow", "improve", "decompose", "make incremental")
    │
    ├─→ ALERTING → Load dt-alerting/SKILL.md
    │   (Triggers: "set up alerts", "notify on failure", "event table alerts")
    │
    ├─→ PERMISSIONS → Load permissions/SKILL.md
    │   (Triggers: "insufficient privileges", "permission denied", "ownership")
    │
    ├─→ TASK-TO-DT → Load task-to-dt/SKILL.md
    │   (Triggers: "convert tasks", "migrate tasks", "replace stream and task")
    │
    ├─→ CUSTOM-INCREMENTALIZATION → Load custom-incrementalization/SKILL.md
    │   (Triggers: "CI DT", "REFRESH USING", "stream-static join",
    │    "shape of changes", "append-only log", "MERGE INTO SELF")
    │
    ├─→ DBT-TO-DT → Load dbt-to-dt/SKILL.md
    │   (Triggers: "convert dbt to DT", "dbt dynamic table", "dbt to DT")
    │
    └─→ PIPELINE-DIAGNOSTICS → Load pipeline-diagnostics/SKILL.md
        (Triggers: "pipeline timeline", "Gantt chart", "UPSTREAM_FAILED",
         "why was DT skipped", "trace pipeline", "critical path")
```

---

## Sub-Skills

| Sub-Skill | Purpose | When to Load |
|-----------|---------|--------------|
| [create/SKILL.md](create/SKILL.md) | Create new dynamic tables | CREATE intent |
| [monitor/SKILL.md](monitor/SKILL.md) | Health checks and status monitoring | MONITOR intent |
| [troubleshoot/SKILL.md](troubleshoot/SKILL.md) | Diagnose and fix issues | TROUBLESHOOT intent |
| [optimize/SKILL.md](optimize/SKILL.md) | Performance improvements | OPTIMIZE intent |
| [dt-alerting/SKILL.md](dt-alerting/SKILL.md) | Set up alerts for refresh failures | ALERTING intent |
| [permissions/SKILL.md](permissions/SKILL.md) | Troubleshoot privilege/permission issues | PERMISSIONS intent |
| [task-to-dt/SKILL.md](task-to-dt/SKILL.md) | Convert streams+tasks pipelines to DTs | TASK-TO-DT intent |
| [custom-incrementalization/SKILL.md](custom-incrementalization/SKILL.md) | CI DTs: stream-static joins, shape-of-changes, append-only logs, stateful MERGE | CUSTOM-INCREMENTALIZATION intent |
| [dbt-to-dt/SKILL.md](dbt-to-dt/SKILL.md) | Convert dbt `table` models to Dynamic Tables | DBT-TO-DT intent |
| [pipeline-diagnostics/SKILL.md](pipeline-diagnostics/SKILL.md) | UPSTREAM_FAILED diagnosis, pipeline timeline, Gantt charts, root cause analysis via OTel traces | PIPELINE-DIAGNOSTICS intent |

---

## Quick Diagnostic Queries

For immediate assessment before routing:

```sql
-- Quick health check for all DTs in schema
SHOW DYNAMIC TABLES IN SCHEMA <database>.<schema>;
-- Check scheduling_state, refresh_mode, refresh_mode_reason columns

-- Check for any errors
SELECT name, state, state_message, refresh_action
FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME_PREFIX => '<database>.<schema>', ERROR_ONLY => TRUE
))
ORDER BY refresh_start_time DESC
LIMIT 5;
```

---

## Important Constraints

### 1. Incremental DTs cannot depend on Full refresh DTs

Dynamic tables in incremental mode cannot depend on full refresh mode dynamic tables.

```sql
-- ❌ BREAKS: dt_final is INCREMENTAL but depends on dt_upstream which is FULL
CREATE DYNAMIC TABLE dt_upstream
  TARGET_LAG = DOWNSTREAM
  REFRESH_MODE = FULL  -- This DT uses FULL refresh
  AS SELECT * FROM source_table;

CREATE DYNAMIC TABLE dt_final
  TARGET_LAG = '5 minutes'
  REFRESH_MODE = INCREMENTAL  -- ERROR: Cannot be INCREMENTAL if upstream is FULL
  AS SELECT * FROM dt_upstream;
```

### 2. Target lag cannot be shorter than upstream's lag

```sql
-- ❌ BREAKS: dt_final has 1 minute lag but dt_upstream has 10 minutes
CREATE DYNAMIC TABLE dt_upstream
  TARGET_LAG = '10 minutes'  -- 10 minute lag
  AS SELECT * FROM source_table;

CREATE DYNAMIC TABLE dt_final
  TARGET_LAG = '1 minute'  -- ERROR: Cannot be fresher than upstream (10 min)
  AS SELECT * FROM dt_upstream;
```

### 3. Change tracking must remain enabled on base objects

```sql
-- ❌ BREAKS: Disabling change tracking after DT creation
CREATE DYNAMIC TABLE my_dt AS SELECT * FROM base_table;

-- Later...
ALTER TABLE base_table SET CHANGE_TRACKING = FALSE;  -- ERROR: DT refreshes will fail
```

### 4. `SELECT *` fails on schema changes

```sql
-- ❌ BREAKS: Using SELECT * then adding a column to source
CREATE DYNAMIC TABLE my_dt AS SELECT * FROM source_table;

-- Later...
ALTER TABLE source_table ADD COLUMN new_col VARCHAR;  -- DT refresh will FAIL

-- ✅ FIX: Use explicit columns
CREATE DYNAMIC TABLE my_dt AS SELECT id, name, amount FROM source_table;
```

### 5. IMMUTABLE WHERE restrictions

```sql
-- ❌ BREAKS: Subquery in IMMUTABLE WHERE
CREATE DYNAMIC TABLE my_dt
  IMMUTABLE WHERE (id IN (SELECT id FROM archived_ids))  -- ERROR: No subqueries
  AS SELECT * FROM source_table;

-- ❌ BREAKS: UDF in IMMUTABLE WHERE
CREATE DYNAMIC TABLE my_dt
  IMMUTABLE WHERE (my_custom_udf(status) = TRUE)  -- ERROR: No UDFs
  AS SELECT * FROM source_table;

-- ❌ BREAKS: Non-deterministic function (except timestamps)
CREATE DYNAMIC TABLE my_dt
  IMMUTABLE WHERE (RANDOM() < 0.5)  -- ERROR: Non-deterministic
  AS SELECT * FROM source_table;

-- ✅ OK: Timestamp functions are allowed
CREATE DYNAMIC TABLE my_dt
  IMMUTABLE WHERE (created_at < CURRENT_TIMESTAMP() - INTERVAL '7 days')
  AS SELECT * FROM source_table;
```

---

## Stopping Points Summary

All sub-skills follow this philosophy: **NO changes without explicit user approval.**

- **READ-ONLY queries**: Can run freely (diagnostics, monitoring)
- **ANY mutation**: Requires stopping point and user approval

See individual sub-skills for specific stopping points.

---

## Refresh and performance context

This skill does not persist local state between sessions. Use the `monitoring-functions.md` router (loaded in Step 1) to select the right reference for your scenario.

=== error-tables-ops/ ===
---
name: error-tables-ops
description: "Assess, enable, monitor, and manage Error Tables (DML Error Logging) across your Snowflake account. Use when: error tables, error logging, ERROR_TABLE, DML errors, which tables should I enable, which tables have error logging, analyze errors, error table storage, error table retention, clean up errors, monitor errors, error table health, error table report, set up alerting, failed DML queries, string truncation, NOT NULL violation, numeric overflow, check constraint violation, constraint failed."
category: operate
tags:
  - error-tables
  - dml-error-logging
  - data-quality
  - data-engineering
---

# Error Tables Operations

Assess, enable, monitor, and manage Error Tables to streamline your Snowflake data pipelines. Instead of failing entire DML statements on bad data, Error Tables let good rows succeed while capturing rejected rows for analysis and repair.

**Docs:** [DML Error Logging](https://docs.snowflake.com/en/user-guide/data-load-overview#dml-error-logging)

## Stopping Points

- Before executing any DDL (`CREATE ALERT`, `CREATE TASK`, `ALTER TABLE`, `TRUNCATE`): present the DDL and get user approval
- Before enabling error logging on production tables: confirm the user understands the behavioral change (partial success instead of full rollback)
- **Before executing any Fix re-insert:** present the error breakdown from Step 1, ask the user how to handle each error type, and only generate/execute the INSERT after they approve
- After the Getting Started demo: ask if the user wants to proceed to Assess or clean up the test table

## Routing

Read the user's request and pick the right sub-skill:

| User intent | Sub-skill |
|------------|-----------|
| "Walk me through it" / "Set up error tables" / "Test error tables" / "Getting started" / "What are error tables" | **Getting Started** |
| "Which tables should I enable this on?" / "Where are my DML failures?" / "Would I benefit?" | **Assess** |
| "Which tables have error logging?" / "Find my error tables" / "List enabled tables" | **Discover** |
| "What errors am I catching?" / "Analyze my error table" / "Error breakdown" | **Analyze** |
| "Set up monitoring" / "Alert me when errors spike" / "Error table alerting" | **Monitor** |
| "Fix the rejected rows" / "Re-insert error data" / "Repair my data" | **Fix** |
| "Clean up old errors" / "Retention" / "Archive errors" / "Truncate" | **Manage** |
| "Temporarily disable" / "Opt out" / "Turn off for my session" / "Debug without error logging" | **Session Opt-Out** |
| "How much storage?" / "Error table size" / "Cost of error tables" | **Storage** |
| "Error tables report" / "Health summary" / "How are my error tables doing?" | **Report** |
| "MERGE/UPDATE with error tables" / "Which DML types are supported?" / "Column changes" | **MERGE & UPDATE** |
| "Transaction behavior" / "What happens in a transaction?" / "Rollback with error tables" | **Transactions** |
| "Iceberg tables" / "DR/replication" / "Failover" | **Iceberg & DR** |
| "Check constraint" / "constraint violation" / "CHECK failed" | **Analyze** (or **Getting Started** if they need a demo) |

If the user asks "what are error tables?" or mentions error tables without a clear operational intent, start with **Getting Started** to show a hands-on demo. If they already have error tables enabled, use **Report**; if exploring which tables to enable, use **Assess**.

---

## Reference: Error Codes

**Load** `references/notes.md` § "Error Codes" for the full table. Key codes used in all queries: 100072 (NOT NULL), 100078 (truncation), 100046 (overflow), 100038 (numeric), 100035 (type mismatch), 100040 (date/time), 100051 (div by zero), 100069 (unsupported conversion), 100320 (CHECK constraint — `error_source` is NULL; use `error_message` for constraint details).

---

## Sub-skill 0: Getting Started

**When to use:** User wants to try error tables, set up a test, or asks "walk me through it" or "what are error tables." Even for informational questions like "what are error tables?" — demonstrate with live SQL instead of explaining conceptually. Showing beats telling.

**What it does:** Executes each SQL step below against the user's Snowflake account, shows the results, and explains what happened. This is a hands-on demo, not a lecture.

> **EXECUTE the SQL** — run each step via the SQL tool, show the result, then explain. The user learns by seeing real output, not reading code blocks.

> **How Error Logging Works:** Error logging is a **TABLE property**, not a per-statement clause. `ERROR_LOGGING = TRUE` on a table automatically diverts bad rows during INSERT/UPDATE/MERGE — good rows succeed, bad rows go to `ERROR_TABLE()`. There is **NO** `ERROR_LOGGING = CONTINUE` clause on DML statements. Never suggest it.

> **What it captures:** Column-level data errors (NOT NULL, truncation, overflow, type mismatch, date/time, division by zero, unsupported conversion, CHECK constraint — see `references/notes.md` for codes). Errors deeper in query execution (subqueries, CTEs, expressions) fail the statement normally and are not diverted.

### Step 1: Create a table with error logging enabled

```sql
CREATE OR REPLACE TABLE {DATABASE}.{SCHEMA}.{TABLE_NAME} (
    ID NUMBER(10,0) NOT NULL,
    NAME VARCHAR(20) NOT NULL,
    EMAIL VARCHAR(30),
    BALANCE NUMBER(8,2),
    SIGNUP_DATE DATE NOT NULL
) ERROR_LOGGING = TRUE;
```

Or enable on an existing table:

```sql
ALTER TABLE {DATABASE}.{SCHEMA}.{TABLE_NAME} SET ERROR_LOGGING = TRUE;
```

### Step 2: Insert data — bad rows are automatically diverted

Use a standard INSERT. No special clause needed — errors are captured automatically:

```sql
INSERT INTO {DATABASE}.{SCHEMA}.{TABLE_NAME} VALUES
    (1, 'Alice Smith', 'alice@example.com', 1500.00, '2025-01-15'),
    (2, 'Bob Jones', 'bob@example.com', 2500.50, '2025-02-20'),
    -- String truncation: NAME > 20 chars
    (3, 'Bartholomew Christopherson III', 'bart@example.com', 500.00, '2025-04-01'),
    -- Numeric overflow: BALANCE > NUMBER(8,2) max
    (4, 'Eve Green', 'eve@example.com', 12345678.99, '2025-06-20'),
    -- NOT NULL violation: NULL NAME
    (5, NULL, 'nobody@example.com', 100.00, '2025-07-01');
```

Result: good rows are inserted, bad rows are diverted to the error table. The statement succeeds.

### Step 3: Query the error table

```sql
SELECT
    ERROR_CODE,
    CASE ERROR_CODE
        WHEN 100072 THEN 'NOT NULL violation'
        WHEN 100078 THEN 'String truncation'
        WHEN 100046 THEN 'Numeric overflow'
    END AS error_type,
    ERROR_METADATA:error_source::STRING AS offending_column,
    ERROR_DATA,
    TIMESTAMP
FROM ERROR_TABLE({DATABASE}.{SCHEMA}.{TABLE_NAME})
ORDER BY TIMESTAMP DESC;
```

### Step 4: Verify the base table has only good rows

```sql
SELECT * FROM {DATABASE}.{SCHEMA}.{TABLE_NAME} ORDER BY ID;
```

### Output guidance

Execute each step sequentially — show result, then explain. Key points: Step 2 → "INSERT succeeded, bad rows diverted"; Step 3 → explain `ERROR_DATA` JSON with `[]` brackets and `error_source`; Step 4 → only good rows landed. If permissions fail, try a different database/schema via `SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()`.

---

## Sub-skill 1: Assess

**When to use:** Customer wants to know which tables would benefit from Error Tables before enabling it.

**What it does:** Scans `QUERY_HISTORY` for failed INSERT/UPDATE/MERGE with runtime error codes, extracts the target table from the error message, and ranks tables by failure volume.

**Parameters:**
- `{DAYS}` — lookback period (default: 30)

### Query: Find tables that would benefit

```sql
SELECT
    REGEXP_SUBSTR(error_message, 'to table ([^\\s]+)', 1, 1, 'e') AS target_table,
    CASE error_code
        WHEN 100072 THEN 'NOT NULL violation'
        WHEN 100078 THEN 'String truncation'
        WHEN 100046 THEN 'Numeric overflow'
        WHEN 100038 THEN 'Numeric not recognized'
        WHEN 100035 THEN 'Type mismatch'
        WHEN 100040 THEN 'Invalid date/time'
        WHEN 100051 THEN 'Division by zero'
        WHEN 100069 THEN 'Unsupported conversion'
        WHEN 100320 THEN 'CHECK constraint violation'
    END AS error_type,
    query_type AS statement_type,
    COUNT(*) AS failed_queries,
    COUNT(DISTINCT query_id) AS distinct_queries,
    MIN(start_time) AS first_failure,
    MAX(start_time) AS last_failure
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE execution_status = 'FAIL'
  AND query_type IN ('INSERT', 'UPDATE', 'MERGE')
  AND error_code IN (100072, 100078, 100046, 100038, 100035, 100040, 100051, 100069, 100320)
  AND start_time >= DATEADD('day', -{DAYS}, CURRENT_TIMESTAMP())
  AND error_message LIKE '%DML operation to table%'
GROUP BY 1, 2, 3
ORDER BY failed_queries DESC
LIMIT 20;
```

### Output guidance

Present a ranked table of tables with failed DML counts. **Always** end with `ALTER TABLE {table} SET ERROR_LOGGING = TRUE;` enable commands for each recommended table. Even when no results are found, still explain that `ALTER TABLE ... SET ERROR_LOGGING = TRUE` is how to enable error logging.

---

## Sub-skill 2: Discover

**When to use:** Customer wants to find which tables already have `ERROR_LOGGING = true` in their account.

**What it does:** Scans tables via `GET_DDL` and reports which have error logging enabled, plus the row count in each error table.

**Parameters:**
- `{DATABASE}` — database to scan (required)
- `{SCHEMA}` — schema to scan (required)

### Queries

**Load** `references/queries.md` § "Discover" for the `_find_error_logging_tables` stored procedure and the error table row count query.

The procedure uses `GET_DDL` + `ILIKE '%ERROR_LOGGING%true%'` to find enabled tables, then for each you query `ERROR_TABLE()` for row counts.

### Output guidance

Present a table showing each enabled table with its error row count, oldest/newest error, and distinct queries. Summarize: "N tables enabled, M actively catching errors." If none found: "No tables with ERROR_LOGGING = true found in {DATABASE}.{SCHEMA}."

**Account-wide discovery:** The stored procedure and `GET_DDL` scan are **per database/schema** — not a single account-wide sweep. If the user asks for "all tables in my account," say that they need to run discovery once per database/schema (or loop `INFORMATION_SCHEMA` / automate across schemas). Do not imply a single query lists every enabled table in the account.

---

## Sub-skill 3: Analyze

**When to use:** Customer wants to understand the error patterns in a specific error table.

**What it does:** Queries `ERROR_TABLE()` and breaks down errors by type, column, time period, and frequency.

**Parameters:**
- `{DATABASE}` — database
- `{SCHEMA}` — schema
- `{TABLE_NAME}` — base table name (not the error table — we use `ERROR_TABLE()`)
- `{DAYS}` — lookback period (default: 7)

### Query: Error breakdown by type and column

```sql
SELECT
    ERROR_CODE,
    CASE ERROR_CODE
        WHEN 100072 THEN 'NOT NULL violation'
        WHEN 100078 THEN 'String truncation'
        WHEN 100046 THEN 'Numeric overflow'
        WHEN 100038 THEN 'Numeric not recognized'
        WHEN 100035 THEN 'Type mismatch'
        WHEN 100040 THEN 'Invalid date/time'
        WHEN 100051 THEN 'Division by zero'
        WHEN 100069 THEN 'Unsupported conversion'
        WHEN 100320 THEN 'CHECK constraint violation'
    END AS error_type,
    COALESCE(ERROR_METADATA:error_source::STRING, ERROR_METADATA:error_message::STRING) AS offending_column,
    COUNT(*) AS error_count,
    MIN(TIMESTAMP) AS first_seen,
    MAX(TIMESTAMP) AS last_seen,
    COUNT(DISTINCT QUERY_ID) AS distinct_queries
FROM ERROR_TABLE({DATABASE}.{SCHEMA}.{TABLE_NAME})
WHERE TIMESTAMP >= DATEADD('day', -{DAYS}, CURRENT_TIMESTAMP())
GROUP BY 1, 2, 3
ORDER BY error_count DESC;
```

### Query: Error trend by day

```sql
SELECT
    TIMESTAMP::DATE AS error_date,
    COUNT(*) AS errors,
    COUNT(DISTINCT QUERY_ID) AS queries_with_errors,
    COUNT(DISTINCT ERROR_CODE) AS error_types
FROM ERROR_TABLE({DATABASE}.{SCHEMA}.{TABLE_NAME})
WHERE TIMESTAMP >= DATEADD('day', -{DAYS}, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 1 DESC;
```

### Output guidance

Present error breakdown table, then daily trend. Suggest fixes: string truncation → widen column, NOT NULL → check upstream NULLs, numeric overflow → increase precision, type mismatch → fix ETL transformation, CHECK constraint → correct values or adjust the constraint. **Note:** For CHECK constraint violations (100320), `error_source` is NULL — the constraint name and expression appear in `error_message` instead. The `COALESCE` in the query handles this automatically.

---

## Sub-skill 3b: Fix

**When to use:** Customer wants to use error table contents to fix rejected rows and re-insert them into the base table.

**What it does:** Shows how to extract rejected rows from `ERROR_TABLE()`, correct the offending values, and re-insert them. Requires `{DATABASE}`, `{SCHEMA}`, `{TABLE_NAME}`, and `{QUERY_ID}` (from the error table's `QUERY_ID` column).

### Step 1: Review what was rejected

```sql
SELECT
    ERROR_CODE,
    CASE ERROR_CODE
        WHEN 100072 THEN 'NOT NULL violation'
        WHEN 100078 THEN 'String truncation'
        WHEN 100046 THEN 'Numeric overflow'
    END AS error_type,
    ERROR_METADATA:error_source::STRING AS offending_column,
    ERROR_DATA
FROM ERROR_TABLE({DATABASE}.{SCHEMA}.{TABLE_NAME})
WHERE QUERY_ID = '{QUERY_ID}'
ORDER BY TIMESTAMP DESC
LIMIT 20;
```

> **⛔ STOP AFTER STEP 1 — DO NOT EXECUTE ANY INSERT UNTIL THE USER APPROVES THE FIX PLAN.**
> After executing Step 1 (review), you MUST present the error breakdown and ask the user how to handle each error type BEFORE generating or executing any INSERT. This is a data modification — the user decides what happens to their data, not the agent.

### Step 2: Ask the user how to fix each error type

Present each distinct error type from Step 1 with options: truncation → truncate to fit / drop; NOT NULL → default value / drop; overflow → cap at max / drop; type mismatch → TRY_CAST / drop; date → TRY_TO_DATE / drop; CHECK (100320) → adjust value / drop.

**Fast path:** If the user said "just fix them" or "auto-fix" — skip the ask and apply sensible defaults (truncate strings, replace NULLs with `'UNKNOWN'`/`0`/`CURRENT_DATE()`, cap overflow, use `TRY_*` for type/date). Otherwise, always ask first.

### Step 3: Generate and execute the re-insert

Only after approval (or fast path). Use `TRY_TO_NUMBER` / `TRY_TO_DATE` in **ALL** numeric/date ELSE branches — Snowflake evaluates all CASE branches, so bare `::NUMBER` casts fail on array-wrapped overflow values. `::STRING` is safe for VARCHAR.

```sql
INSERT INTO {DATABASE}.{SCHEMA}.{TABLE_NAME} (ID, NAME, BALANCE)
SELECT
    CASE WHEN ERROR_CODE = 100072 AND ERROR_METADATA:error_source::STRING = 'ID'
         THEN {replacement_id}
         ELSE TRY_TO_NUMBER(ERROR_DATA:ID::STRING) END AS ID,
    CASE WHEN ERROR_CODE = 100078 AND ERROR_METADATA:error_source::STRING = 'NAME'
         THEN LEFT(ERROR_DATA:NAME[0]::STRING, 20)
         WHEN ERROR_CODE = 100072 AND ERROR_METADATA:error_source::STRING = 'NAME'
         THEN 'UNKNOWN'
         ELSE ERROR_DATA:NAME::STRING END AS NAME,
    CASE WHEN ERROR_CODE = 100046 AND ERROR_METADATA:error_source::STRING = 'BALANCE'
         THEN 999999.99
         ELSE TRY_TO_NUMBER(ERROR_DATA:BALANCE::STRING) END AS BALANCE
FROM ERROR_TABLE({DATABASE}.{SCHEMA}.{TABLE_NAME})
WHERE QUERY_ID = '{QUERY_ID}';
```

Rows the user chose to "Drop" → exclude via `WHERE NOT (ERROR_CODE = ... AND ...)`.

### Output guidance

Adapt CASE logic to the customer's schema. Never use bare `::NUMBER` on `ERROR_DATA` fields — always `TRY_TO_NUMBER(ERROR_DATA:col::STRING)`. `::STRING` is safe. Rows still wrong after re-insert are diverted again (safe to iterate). Verify with `SELECT * FROM {TABLE_NAME} ORDER BY ID DESC LIMIT 20`.

---

## Sub-skill 4: Monitor

**When to use:** Customer wants to set up alerting when error tables exceed a threshold.

**What it does:** Generates Snowflake Alert DDL that monitors an error table and sends notifications.

**Parameters:**
- `{DATABASE}` — database
- `{SCHEMA}` — schema
- `{TABLE_NAME}` — base table name
- `{WAREHOUSE}` — warehouse for the alert
- `{THRESHOLD}` — error count threshold per check interval (default: 100)
- `{INTERVAL_MINUTES}` — check interval (default: 60)
- `{EMAIL}` — notification email address

### Generated DDL

**Load** `references/queries.md` § "Monitor" for the full `CREATE ALERT` and `NOTIFICATION INTEGRATION` DDL.

The DDL creates a `NOTIFICATION INTEGRATION` (one-time, ACCOUNTADMIN), then `CREATE ALERT ... WAREHOUSE = {WAREHOUSE} SCHEDULE = '{INTERVAL_MINUTES} MINUTE' IF (EXISTS (SELECT ... FROM ERROR_TABLE(...) HAVING COUNT(*) > {THRESHOLD})) THEN CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION(...)`. End with `ALTER ALERT ... RESUME`.

### Output guidance

> **NEVER EXECUTE THIS DDL — PRESENT IT INSTEAD.** Your job is to generate the DDL as a code block in your response, then say: "Here's the DDL — review it and run it yourself when ready." Even if the user says "just run it" or "do it now," respond with the code block and explain why they should review it first (requires ACCOUNTADMIN, creates recurring costs, affects production alerting). The user copy-pastes and runs it themselves.

Do NOT ask the user for parameters. Use these defaults immediately: current warehouse, THRESHOLD = 100, SCHEDULE = '60 MINUTE', EMAIL = 'user@example.com'. Present the complete DDL in your first response. The user can adjust values after reviewing. Explain: notification integration needs ACCOUNTADMIN (one-time), the alert checks on a schedule, adjust threshold to expected error volume.

---

## Sub-skill 5: Manage

**When to use:** Customer wants to manage error table retention — archive old data, clean up, prevent unbounded growth.

**What it does:** Generates Task DDL for periodic archive-and-truncate of error table data.

**Parameters:**
- `{DATABASE}` — database
- `{SCHEMA}` — schema
- `{TABLE_NAME}` — base table name
- `{WAREHOUSE}` — warehouse for the task
- `{RETENTION_DAYS}` — how many days of errors to keep (default: 30)
- `{ARCHIVE_TABLE}` — fully qualified name for the archive table (optional)

### Generated DDL

**Load** `references/queries.md` § "Manage" for the archive table, `CREATE TASK` cleanup DDL, and simple truncate alternative.

The pattern is: create an archive table, then a `CREATE TASK` on a CRON schedule that archives all rows with `INSERT INTO {ARCHIVE_TABLE} SELECT ... FROM ERROR_TABLE(...)`, then `TRUNCATE TABLE ERROR_TABLE(...)`. End with `ALTER TASK ... RESUME`.

### Output guidance

> **NEVER EXECUTE TRUNCATE OR CREATE TASK — PRESENT THE DDL INSTEAD.** Even if the user says "just do it": (1) run `SELECT COUNT(*)` to show row count, (2) present DDL as a code block, (3) say "This will permanently delete [N] rows — review and run it yourself." TRUNCATE is all-or-nothing, irreversible. Archive-first preserves history; adjust CRON to error volume.

---

## Sub-skill 5b: Storage

**When to use:** Customer asks about error table storage, cost, or size.

**What it does:** Provides a **best-effort estimate** of how much rejected-row data is currently in the error table (row counts + approximate payload size).

> **Note:** Error tables are **nested objects under the base table** — they are not standalone tables with their own DB/SCHEMA identity. How (or whether) their storage appears in `TABLE_STORAGE_METRICS` or billing views is unconfirmed. Do **not** claim inclusion/exclusion in `TABLE_STORAGE_METRICS`. If the customer asks about billing attribution, call this out as unknown.

### Query: Estimate error table payload size

```sql
SELECT COUNT(*) AS error_rows,
    ROUND(AVG(52 + LENGTH(TO_VARCHAR(ERROR_METADATA)) + LENGTH(TO_VARCHAR(ERROR_DATA))), 0) AS avg_bytes_per_row,
    ROUND(SUM(52 + LENGTH(TO_VARCHAR(ERROR_METADATA)) + LENGTH(TO_VARCHAR(ERROR_DATA))) / (1024*1024), 2) AS estimated_raw_mb
FROM ERROR_TABLE({DATABASE}.{SCHEMA}.{TABLE_NAME});
```

### Output guidance

Lead with: this provides a **best-effort estimate** based on `ERROR_TABLE()` contents. Show row count, estimated raw payload, and average bytes per error row. If empty: "No error rows found." Do **not** reference `TABLE_STORAGE_METRICS` or claim error table storage is included/excluded from base table billing.

---

## Sub-skill 6: Report

**When to use:** Customer wants a health summary across all their error tables.

**What it does:** Combines Discover + Analyze across all enabled tables in a schema to produce a cross-table health summary.

**Parameters:**
- `{DATABASE}` — database
- `{SCHEMA}` — schema
- `{DAYS}` — lookback period (default: 7)

### Workflow

1. Run the **Discover** stored procedure (`_find_error_logging_tables`) to find all tables with error logging enabled
2. For each discovered table, query `ERROR_TABLE()` with the **Analyze** error breakdown query to get error counts, types, and trends
3. Combine into a single health summary showing enabled table count, total error rows, and per-table breakdown

### Output guidance

Present a summary table showing: enabled table count, total error rows, and per-table breakdown with columns for errors, trend (↑/↓/→ flat/NEW), top error type, and top column. End with actionable recommendations per table.

Calculate trend by comparing current period error count to the prior period of the same length (↑ increasing, ↓ decreasing, → flat within 10%, NEW if no prior errors).

---

## Sub-skill 7: Session Opt-Out

**When to use:** User wants to temporarily disable error logging for their session, or asks about opting out.

The **only** session parameter is `OPT_OUT_ERROR_LOGGING`:

```sql
ALTER SESSION SET OPT_OUT_ERROR_LOGGING = TRUE;   -- disable for this session
ALTER SESSION SET OPT_OUT_ERROR_LOGGING = FALSE;  -- re-enable (default)
```

When `TRUE`, DML errors fail normally — table property unchanged, other sessions unaffected, resets at session end. No other session parameter exists for error logging — do not invent names like `ENABLE_ERROR_TABLE`.

---

## Sub-skill 8: MERGE & UPDATE

**When to use:** User asks about MERGE, UPDATE, or INSERT behavior with error tables, or about column/schema changes.

Error Tables support all three DML types: **INSERT, UPDATE, and MERGE**. All three divert bad rows to the error table when `ERROR_LOGGING = TRUE` is set on the target table.

For MERGE specifically:
- Bad rows from WHEN MATCHED (UPDATE) or WHEN NOT MATCHED (INSERT) clauses are captured
- `ERROR_DATA` contains the full rejected row as a JSON VARIANT with the offending column value in `[]` brackets
- `ERROR_METADATA:error_source` identifies the column that caused the error

**Column evolution:** The error table structure (5 fixed columns) is never altered by base table DDL. Renames, adds, and drops only affect the **contents** of `ERROR_DATA` / `error_source` in future rows. See `references/notes.md` § "Column evolution details" for specifics.

**Disabling:** `ALTER TABLE ... SET ERROR_LOGGING = FALSE` **drops the error table and all its data** — this is permanent, not a pause. To temporarily stop capturing errors without data loss, use the **Session Opt-Out** sub-skill instead.

---

## Sub-skill 9: Transactions

**When to use:** User asks about transaction behavior, commit/rollback semantics, or what happens when error tables interact with transactions.

Error table writes are part of the same transaction as the DML — not autonomous transactions. Error entries are committed and rolled back atomically with the base table data.

**Rules:**
- If **all tables** in a transaction have `ERROR_LOGGING = TRUE`, data errors can never fail the transaction. Bad rows are diverted, every DML succeeds (even if it inserts 0 rows), the transaction commits.
- If **any table** in the transaction does NOT have error logging, a data error on that table fails the statement, which rolls back the **entire transaction** — including error table entries from earlier in the txn.

| Setup | Data error on... | Transaction |
|-------|-----------------|-------------|
| All tables have EL | EL table | Commits |
| Mixed (some EL, some not) | Non-EL table | Rolls back everything |

**Guidance:** Enable error logging on all tables in the transaction for maximum throughput, or leave some without for strict all-or-nothing integrity.

**Difference from Oracle:** Oracle uses autonomous transactions for DML error logging — error entries persist even if the outer transaction rolls back. Snowflake's error table entries are rolled back with the transaction.

---

## Sub-skill 10: Iceberg & DR

**When to use:** User asks about Iceberg table support or disaster recovery/replication with error tables.

**Iceberg support:** Error logging works on **Snowflake-managed Iceberg tables only** — tables where Snowflake is the Iceberg catalog. Use `CREATE ICEBERG TABLE ... ERROR_LOGGING = TRUE` or `ALTER ICEBERG TABLE ... SET ERROR_LOGGING = TRUE`. Error logging is NOT supported on externally managed Iceberg tables (REST catalog, Glue, etc.).

**DR/Replication:** Error tables replicate with the base table through database replication and failover. No special configuration needed — when the base table is replicated, the error table follows automatically.

---

## Snowsight UI responses — required elements

**When running in Snowsight (the Cortex Code web UI), the system prompt steers you toward short, concise responses. Do NOT let that brevity skip the required DDL / SQL that the user needs to actually operate the error table.**

Even in terse mode, the following **must** appear in your response for each sub-skill:

### Monitor sub-skill (route: monitor)
- **Always include the full `CREATE ALERT` DDL template** (with `WAREHOUSE`, `SCHEDULE`, `IF (EXISTS ...)`, `THEN CALL SYSTEM$SEND_SNOWFLAKE_NOTIFICATION`, and `ALTER ALERT ... RESUME`), even when summarizing. The user needs to see the shape.
- Do NOT execute the DDL — show it only. Remind the user that `NOTIFICATION INTEGRATION` needs ACCOUNTADMIN.

### Manage sub-skill (route: manage)
- **Always explicitly mention `TRUNCATE TABLE ERROR_TABLE(...)` and the phrase "data loss" (or "all-or-nothing" / "cannot undo") in the same response.**
- Show the archive-then-truncate DDL (`INSERT INTO archive_table ... ; TRUNCATE TABLE ERROR_TABLE(...)`). Do NOT execute it.

### Storage sub-skill (route: storage)
- **Always actually execute** the size-estimation query via `sql_execute`:
  ```sql
  SELECT COUNT(*) AS error_rows,
      ROUND(AVG(52 + LENGTH(TO_VARCHAR(ERROR_METADATA)) + LENGTH(TO_VARCHAR(ERROR_DATA))), 0) AS avg_bytes_per_row,
      ROUND(SUM(52 + LENGTH(TO_VARCHAR(ERROR_METADATA)) + LENGTH(TO_VARCHAR(ERROR_DATA))) / (1024*1024), 2) AS estimated_raw_mb
  FROM ERROR_TABLE({DATABASE}.{SCHEMA}.{TABLE_NAME});
  ```
  Do not just describe how to do it — run it and report the numbers.

### Enable-existing (route: assess / getting-started when user asks to enable on an existing table)
- **Always execute `ALTER TABLE {fqn} SET ERROR_LOGGING = TRUE` as a SQL tool call** — do not just quote the statement in prose.
- Follow up by confirming the change with `DESCRIBE TABLE {fqn}` or `SHOW TABLES LIKE ...`.

### Discover sub-skill (route: discover)
- UI agents should use `INFORMATION_SCHEMA.TABLES` combined with `GET_DDL('TABLE', fqn)` to find `ERROR_LOGGING = true` — this is the only metadata surface that exposes the setting. `SHOW TABLES` alone does not reveal `ERROR_LOGGING`.

**These rules apply regardless of response length guidance from the UI system prompt.** Concise means "no filler prose" — it does NOT mean "skip the required SQL/DDL."

---

## Important Notes

**Load** `references/notes.md` for additional reference on performance overhead and column evolution details.

Key points to always remember:
- `ERROR_TABLE()` requires the base table name, not the error table name
- Only the **owner** of the base table can SELECT from the error table
- Supported operations on error tables: **SELECT and TRUNCATE only**
- The Monitor and Manage sub-skills generate DDL for you to review and run — **DDL is not executed automatically**
- Supported DML types: **INSERT, UPDATE, and MERGE**
=== event-table/ ===
---
name: event-table
description: "Manage Snowflake event tables and telemetry configuration. Use when: viewing/configuring event tables, checking telemetry setup, getting/setting telemetry levels, querying event table data, understanding telemetry formats. Triggers: event table, get event table, show event table, current event table, event table setup, event table configuration, telemetry, telemetry setup, telemetry configuration, telemetry levels, get telemetry, show telemetry, check telemetry, log level, trace level, metric level, logging setup, tracing setup, observability setup, event table format, telemetry format, log format, trace format, metric format."
tools: ["snowflake_sql_execute", "ask_user_question"]
---

# Event Table Router Skill

This skill routes to specialized skills for event table and telemetry tasks.

## Workflow

### Step 1: Detect User Intent

Analyze the user's request and route to the appropriate sub-skill:

| User Intent | Triggers | Action |
|-------------|----------|--------|
| Get/show event table & telemetry config (read-only) | "get event table", "show event table", "current event table", "which event table", "show telemetry levels", "get telemetry", "check telemetry", "telemetry levels", "show log level", "show trace level", "show metric level" | **Load** `event-table-get-setup/SKILL.md` |
| Set up/modify event table & telemetry | "event table setup", "event table configuration", "set log level", "set trace level", "set metric level", "configure telemetry", "create event table", "associate event table", "logging setup", "tracing setup", "observability setup" | **Load** `event-table-modify-setup/SKILL.md` |
| Telemetry format, schema, or product events | "event table format", "telemetry format", "log format", "trace format", "metric format", "telemetry schema", "parse telemetry", "query event table", "event table schema", "telemetry structure", "dynamic table events", "DT events", "DT refresh", "DT telemetry", "DT logs", "DT refresh failures", "task events", "task logs", "task telemetry", "task failures", "task success", "snowpark events", "procedure logs", "UDF logs", "procedure errors", "python procedure", "javascript procedure", "openflow events", "openflow telemetry", "connector events", "replication events" | **Load** `event-table-telemetry-format/SKILL.md` |

### Step 2: Route to Specialized Skill

**Mandatory:** You must load one or more of the below specialized skills, because this router skill does not have enough knowledge.

**If request mentions getting/viewing event tables or telemetry config (read-only):**
- **-> Load**: [event-table-get-setup/SKILL.md](event-table-get-setup/SKILL.md)
- Follow the event table get setup workflow
- The skill will display current configuration without making changes

**If request mentions setting up or modifying event tables or telemetry:**
- **-> Load**: [event-table-modify-setup/SKILL.md](event-table-modify-setup/SKILL.md)
- Follow the event table modify setup workflow
- The skill will guide you through creating, altering, or associating event tables and setting telemetry levels

**If request mentions telemetry format, schema, querying event table data, or product-specific events (dynamic tables, tasks, Snowpark, OpenFlow):**
- **-> Load**: [event-table-telemetry-format/SKILL.md](event-table-telemetry-format/SKILL.md)
- Follow the telemetry format workflow
- The skill identifies the product, finds the correct format, discovers the event table, and generates SQL queries

**If request is to test the skill:**
- Print "hello world"
- Exit

---

## Related Skills (Can Be Loaded Directly)

- [event-table-get-setup/SKILL.md](event-table-get-setup/SKILL.md) - Get/show current event table and telemetry level configuration (read-only)
- [event-table-modify-setup/SKILL.md](event-table-modify-setup/SKILL.md) - Modify event table configuration and telemetry levels
- [event-table-telemetry-format/SKILL.md](event-table-telemetry-format/SKILL.md) - Parse telemetry formats and generate SQL queries for event tables (includes references for dynamic tables, tasks, Snowpark, OpenFlow)

## Stopping Points

- After routing: Sub-skill handles its own stopping points

=== find-skill/ ===
---
name: find-skill
description: >-
  Find, add, check, or update Cortex Code catalog skills before using them.
  Use when the user asks to discover available skills, install a catalog
  skill, make an uninstalled `/skill` or `$skill` usable, search the skill
  marketplace/catalog, check whether installed skills have updates, or update
  skills from the catalog, stage, GitHub, or tarball sources. Do not use this
  for public Snowflake Marketplace datasets or apps; use marketplace-search for
  third-party data/product listings.
---

# Find Skill

Use this skill to discover Cortex Code skills from the skill catalog and make
them available locally before invoking them.

## Workflow

1. Search for candidate skills:

```bash
cortex skill find "<query>"
```

Use a short query based on the capability the user needs. If the user named a
specific saved Snowflake connection, pass `--connection <name>`.

2. Choose by the catalog result's name, description, source, and plugin FQN.
Do not rely on the catalog object's SQL name alone; a Cortex Extension object
name can differ from the actual `name` in `SKILL.md`.

3. Install the selected skill before trying to invoke it. Prefer the exact
command printed by `cortex skill find`; it preserves important options such as
`--connection`. For plugin-backed catalog results, that
usually looks like:

```bash
cortex skill add <catalog-name> --plugin-fqn <DB.SCHEMA.CORTEX_EXTENSION>
```

If the user provided a share URI directly, install it as-is:

```bash
cortex skill add snow://skill_catalog/<DB>.<SCHEMA>.<CORTEX_EXTENSION>
```

4. Confirm the installed skill name:

```bash
cortex skill list
```

Use the installed skill's real `SKILL.md` name for future `$skill` or `/skill`
references. The install output and `cortex skill list` are authoritative.

5. If the user needs the newly installed skill used in the same turn, inspect
the installed skill's `SKILL.md` from the listed path and follow its
instructions directly. A running agent may not auto-load a skill that was
installed after the prompt was parsed, so do not assume `$skill` or `/skill`
will resolve until a later turn.

If the user is testing from a source checkout and provides a CLI prefix such as
`bun run dev --`, use that prefix consistently in place of `cortex`.

## Updates

Check installed remote, stage, tarball, and catalog skills:

```bash
cortex skill check
```

Check one source or skill:

```bash
cortex skill check <skill-or-source>
```

Update an installed skill with the command shown by `check`, or use the
appropriate source form:

```bash
cortex skill update <skill-or-source>
cortex skill update <skill-name> --plugin-fqn <DB.SCHEMA.CORTEX_EXTENSION>
```

## Snowsight Sandbox

If you are running in a Snowsight sandbox session, follow these adjustments
in addition to the workflow above.

### Persist installed skills to the workspace

Set this once per session before any install so the skill registry survives
across sandbox sessions:

```bash
export SKILL_DIR=/workspace/.snowflake/cortex/skills
```

Without this, installed skills go to the process user's home directory and
are lost when the sandbox is recycled.

### Use SQL for `find` instead of `cortex skill find`

`cortex skill find` does not work in the Snowsight sandbox — it hangs with
no output. Use `snowflake_sql_execute` instead:

```sql
SHOW CORTEX EXTENSIONS IN ACCOUNT;
```

Filter the results against the user's query (matching `name` and `comment`
columns). The FQN is `<database_name>.<schema_name>.<name>`.

### Install via `snow stage copy` (preferred in sandbox)

After identifying the FQN from SHOW results, install in **two steps** (not
more). Do NOT use `install_cortex_extension.py` — it fails in the sandbox
because `DESCRIBE CORTEX EXTENSION` returns columnar results that the script
cannot parse as property/value rows, and `GET` leaves `.part` artifacts.

**Step 1 — Resolve the version path.** Run DESCRIBE to find the default
version name from the `default_version_name` column:

```sql
DESCRIBE CORTEX EXTENSION <DB>.<SCHEMA>.<EXTENSION>;
```

The version URI is:
`snow://cortex_extension/<DB>.<SCHEMA>.<EXTENSION>/versions/<DEFAULT_VERSION_NAME>/`

**Step 2 — Copy the bundle to the workspace skill directory:**

```bash
export SKILL_DIR=/workspace/.snowflake/cortex/skills
mkdir -p "$SKILL_DIR/<SKILL_NAME>"
snow stage copy \
  'snow://cortex_extension/<DB>.<SCHEMA>.<EXTENSION>/versions/<VERSION>/' \
  "$SKILL_DIR/<SKILL_NAME>/" --recursive
```

Use `<SKILL_NAME>` matching the extension's SQL object name (usually
uppercase). After copy, read the installed `SKILL.md` to confirm the real
skill `name` in its frontmatter — rename the directory if they differ.

**Step 3 — Clean up `.part` files** (if any appear):

```bash
rm -f "$SKILL_DIR/<SKILL_NAME>"/*.part
```

### Verify installation

```bash
SKILL_DIR=/workspace/.snowflake/cortex/skills cortex skill list
```

The skill should appear under "Discovered skills". Use the `name` from its
`SKILL.md` frontmatter for future `$skill` or `/skill` references.

### Troubleshooting

If `snow stage copy` fails with a permission error:

```sql
SHOW GRANTS ON CORTEX EXTENSION <DB>.<SCHEMA>.<EXTENSION>;
```

If the user lacks USAGE, report to the user — do not retry.

## Guardrails

- Do not tell the user to use an uninstalled catalog skill with `$skill` or
  `/skill`; install it first.
- Do not assume the catalog SQL object name equals the installed skill name.
- Do not edit `SKILL.md` metadata to force a name match during install; preserve
  the publisher's bundle and use the actual installed skill name.
- Do not use this skill for public Snowflake Marketplace datasets, Native Apps,
  or connectors; use `marketplace-search`.
- Minimize tool call turns: combine SHOW + DESCRIBE into awareness of what
  columns to expect, and go straight to `snow stage copy` once the FQN is known.
  The ideal sandbox install is: 1 SQL call (SHOW), 1 SQL call (DESCRIBE), 1 bash
  call (mkdir + snow stage copy + rm .part). Three turns total, not five+.

=== get-marketplace-listing-details/ ===
---
name: get-marketplace-listing-details
description: >-
  Present detailed information about a single Snowflake Marketplace listing
  (data share, native app, private/targeted, or request-only) and explain why
  it is useful given the user's existing Snowflake data and current
  conversation. Use when the user asks about ONE specific listing by title or
  by global name (e.g. "tell me about GZ2FQZ711TU", "what's in the Consumer
  Pricing listing", "describe this marketplace listing", "details on listing
  X"). Do NOT use for marketplace search results spanning multiple listings —
  use `marketplace-listing-formatting` instead.
---

# Skill: get-marketplace-listing-details

Defines how to present detailed information about a single marketplace listing. The goal is to communicate the core details about the listing as well as **why it is useful for the user** in the context of the current conversation and their existing Snowflake data.

## When to use

- The user references **one** listing by title (e.g. "Consumer pricing data") or by global name (e.g. `GZ2FQZ711TU`).
- The user wants details, an overview, or a "should I get this?" recommendation about a listing.

**Do NOT** use this skill when:

- The user is browsing or searching across multiple listings — use `marketplace-listing-formatting` instead.
- It is unclear which specific listing is meant (see Prerequisites — always ask for clarification first).

## Prerequisites

### Identify the listing

This skill must be invoked with the **global name** of the listing.

- The **global name** is an alphanumeric string like `GZ2FQZ711TU`.
- The **title** is a human-readable name like "Consumer pricing data".

**CRITICAL**: If it is unclear which listing is being referred to, **always** ask the user for clarification. If the user provided only a title, search the previous conversation context to find the matching global name. If you cannot find one, ask.

### Fetch the listing

**ALWAYS** run **Query A** below using the available SQL execution tool (for example `snowflake_sql_execute`, or `snow sql` when running locally). Then, **for data-share listings**, also run **Query B** to retrieve the data dictionary URLs.

**Query A and Query B are the ONLY SQL queries this skill executes.** Every field referenced elsewhere in this skill (`metadata.title`, `profile.description`, `metadata.usage`, etc.) is read from the parsed JSON in your own reasoning — *not* fetched with a follow-up query. In particular, **do NOT issue any SQL that wraps Query A in `PARSE_JSON(...)`, `FLATTEN(...)`, `TABLE(...)`, or otherwise re-runs `SYSTEM$BULK_GET_LISTINGS` to "extract", "flatten", or "parse" sub-fields** like `metadata`, `profile`, `usage`, `businessNeeds`, `compliance_badges`, etc. Running such queries is wasted work — the data is already in the Query A result — and it pollutes the response with internal retrieval steps the user does not need.

**Query A — `SYSTEM$BULK_GET_LISTINGS`** (the source of truth for nearly every field — title/description, business needs, **`metadata.usage` SQL examples**, provider info, monetization, type detection, region availability, consumer state, etc.):

```sql
SELECT SYSTEM$BULK_GET_LISTINGS(
  'SNOWFLAKE_DATA_MARKETPLACE',
  '{"listingGlobalEntityIds":["<global_name>"]}'
);
```

**Query B — `SYSTEM$GET_DATA_DICTIONARY_METADATA`** (data-share listings only — returns presigned URLs to JSON files describing the share's tables, columns, and "featured" objects):

```sql
SELECT SYSTEM$GET_DATA_DICTIONARY_METADATA(
  '<global_name>',
  'SNOWFLAKE_DATA_MARKETPLACE'
);
```

#### Parsing the responses

Both queries return a single column whose value is a **JSON string**. **Parse this JSON in your own reasoning — do not issue additional SQL to extract sub-fields.** Each field reference below (e.g. `metadata.title`, `profile.description`, `metadata.usage[*].query`) is a key path on the parsed JSON object, not a column to `SELECT`.

- **Query A** parses to an **array** with one object per requested listing — read element `[0]`. Several inner fields (`metadata`, `profile`, `application_data`, `compliance_badges`, `product_types`, `pricing_plan`) are themselves **JSON-encoded strings** that must be parsed a second time before reading their sub-fields. Do this parsing in your reasoning — not by re-running the query through `PARSE_JSON` / `FLATTEN` in SQL.
- **Query B** parses to an **object** of shape `{presignedUrlMap: {<filename>: <presigned URL>, ...}, updatedOn: <epoch_ms>}`. Filenames typically include `<global_name>dictionary_<n>.json` (column dictionary), `<global_name>objects.json` (table list), and `<global_name>featured.json` (featured objects). **The presigned URLs typically expire within an hour** — if you intend to fetch them via a web-fetch tool, do so promptly.

#### Field reference (Query A — `SYSTEM$BULK_GET_LISTINGS`)

Any field can be `null`, missing, or an empty string for a given listing — defer to what the query actually returned.

| Field path                                          | Type / shape                                                                                       | Use in this skill                                                                                              |
|-----------------------------------------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| `global_name`                                       | string                                                                                             | Verify it matches the requested listing                                                                        |
| `state`                                             | string (`PUBLISHED`, `RETIRED`, `DRAFT`, …)                                                        | If not `PUBLISHED`, surface that status before continuing                                                       |
| `metadata.title`                                    | string                                                                                             | Display as the listing name                                                                                    |
| `metadata.subtitle`, `metadata.description`         | string                                                                                             | Source for the summary section (Step 2)                                                                        |
| `metadata.share`                                    | string (e.g. `EQUILAR PEOPLE BUSINESS INTELLIGENCE TOP 500`)                                       | The Snowflake share name behind the listing — useful technical context                                         |
| `metadata.businessNeeds`                            | array of `{type, name?, key?, description}` — predefined needs use `key` (numeric); custom use `name` | Step 1 enrichment + Step 2 relevance summary; render the `description` text directly when `name`/`key` is opaque |
| `metadata.usage`                                    | array of `{title, description, query, isPaid?, numRows?, isValid?}`                                | **Step 4 SQL examples for data listings** — these are real, runnable queries. Mark `isPaid: true` entries as paid |
| `metadata.link`                                     | string URL                                                                                         | Documentation URL for Step 3 "More details" + Step 1 enrichment                                                |
| `metadata.videoLink`                                | string URL                                                                                         | Demo / video link for Step 3 (render as "Demo")                                                                |
| `metadata.termsOfService`, `metadata.isWithStandardTerms`, `metadata.areTermsProvidedOffline` | URL / boolean / boolean                                  | Surface a one-line note if non-standard or offline-provided terms apply                                         |
| `metadata.attributes.refreshRate`                   | string (e.g. `daily`)                                                                              | Surface in More details when relevant (e.g. "Refresh: daily")                                                  |
| `metadata.attributes.geography`                     | object `{geoOption, granularity[], coverage{states[], continents{}}}`                              | Geographic coverage — summarize concisely (e.g. "United States, city-level")                                   |
| `metadata.attributes.time`                          | object `{range{frame, startDate}, granularity}`                                                    | Time-series coverage / history depth                                                                           |
| `metadata.attributes.features`                      | array of strings                                                                                   | Free-tier capabilities / sample data                                                                           |
| `metadata.paidAttributes`                           | object same shape as `metadata.attributes`                                                         | Paid-tier capabilities — when `is_monetized = true`, contrast `attributes.features` (free) vs `paidAttributes.features` (paid) |
| `metadata.categories`                               | object keyed by numeric category id (e.g. `{"6": true, "27": true}`)                               | Internal numeric ids — **not human-readable**. Skip this row if you have no other category source.             |
| `organization_profile_name`                         | string (may be empty)                                                                              | Provider display name — prefer when non-empty                                                                  |
| `profile`                                           | parsed object `{name, description, image, supportUrl, privacyUrl, contactInfo}`                    | Provider subsection — fall back to `profile.name` when `organization_profile_name` is empty; use `profile.description` for the overview |
| `profile_global_name`                               | string (e.g. `GZ2FQZ711TI`)                                                                        | Opaque internal id — **never print this** (see Step 3)                                                         |
| `product_types`                                     | parsed array of `{type, is_addon}` (e.g. `[{"type":"SHARE",...}]`, `[{"type":"NATIVE_APP",...}]`)  | Type detection (see "Determine the listing type")                                                              |
| `application_data`                                  | parsed object describing the Native App package (`privileges`, `version`, `packageType`, `referenceDefinitions`, `diagnostics`, …) | Native App context — privileges required, current version, etc.                                                |
| `share_type`                                        | string (e.g. `DATA`, `APPLICATION`, `SECURE_VIEW`)                                                 | Secondary type signal alongside `product_types`                                                                |
| `private`                                           | boolean                                                                                            | If `true`, the listing is privately shared / targeted to the consumer's account                                |
| `distribution`                                      | string (`EXTERNAL`, `INTERNAL`, …)                                                                 | Secondary signal for private/internal listings                                                                 |
| `autofulfillment`                                   | boolean                                                                                            | If `false`, the listing typically requires provider approval (request-/contact-driven)                         |
| `is_monetized`, `monetization_version`              | boolean / string                                                                                   | Mention in the More details "Pricing" row when `is_monetized = true`                                           |
| `pricing_plan`                                      | parsed object `{type, currency, base_fee, paid_data_description, free_data_description, billing_duration, payment_type}` (present when `is_monetized = true`) | Render concrete pricing in the Pricing row (e.g. "$500 USD / billing period, paid in arrears")                |
| `compliance_badges`                                 | parsed array of `{type, expiry}` (e.g. `[{"type":"ISO27001","expiry":"06-12-2027"}]`); may be missing entirely | More details "Certifications" — list each `type`, include `expiry` when set                                    |
| `customized_contact_info`                           | string                                                                                             | More details "Contact" — combine with `profile.supportUrl` / `profile.contactInfo`                             |
| `is_available_for_importing`, `is_imported`, `is_share_imported`, `is_purchased` | boolean                                              | The consumer's current relationship to the listing — affects Step 5 wording                                    |
| `regions`                                           | comma-separated string                                                                             | Optional: mention region availability when relevant                                                            |
| `first_published_on`, `last_published_on`, `updated_on` | ISO-8601 timestamp strings                                                                     | Optional: surface freshness when relevant                                                                      |
| `blocked`, `unpublished_by_admin_reason`            | boolean / string                                                                                   | If `blocked = true` or an unpublish reason is set, surface that to the user                                    |
| `provided_by_you`                                   | boolean                                                                                            | If `true`, the listing belongs to the consumer's own account/org — note this                                   |

#### Field reference (Query B — `SYSTEM$GET_DATA_DICTIONARY_METADATA`)

Only fetched for data-share listings.

| Field path                                          | Type / shape                                                                                       | Use in this skill                                                                                              |
|-----------------------------------------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| `presignedUrlMap`                                   | object `{<filename>: <presigned URL>, ...}` — typical filenames: `<global_name>dictionary_<n>.json`, `<global_name>objects.json`, `<global_name>featured.json` | URLs to JSON files describing the share's tables, columns, and featured objects. Use to discover real schema before writing Step 4 SQL — **fetch promptly; URLs expire within ~1 hour**. |
| `updatedOn`                                         | epoch milliseconds                                                                                 | Optional: when the data dictionary was last refreshed                                                          |

**Opaque identifiers — never print:**

- `profile_global_name` and the inner `profile.profileGlobalName` (e.g. `GZ2FQZ711TI`, `GZTYZY3AR0A`).

These are internal IDs. Concretely, **do NOT**:

- Render them as the provider name.
- Put them in a parenthetical or footnote (e.g. "Equilar (`GZ2FQZ711TI`)").
- Put them in a code span anywhere in the response.
- Add a "Profile ID", "Provider ID", "Listing ID", or "Internal ID" row to the More details table or the Provider subsection. **The user does not need any opaque internal id.**

The listing's own `global_name` (e.g. `GZ2FQZ711TU`) is fine to mention — only the **provider/profile** ids are forbidden.

**If a query fails or the listing is not live:**

- *Listing not found / invalid identifier / empty BULK_GET array* — confirm the global name with the user.
- *Insufficient privileges* or *not granted* (common for private and request-only listings) — tell the user the listing is not currently available to their role and suggest requesting access via the provider.
- *`state` is not `PUBLISHED`* (e.g. `RETIRED`, `DRAFT`), or `blocked = true`, or `unpublished_by_admin_reason` is set — surface that status; do not present a retired, blocked, or draft listing as if it were live.
- *Query A succeeds, Query B fails (or is empty)* — proceed with the BULK_GET data and note that the data dictionary was unavailable. Examples in Step 4 must then be derived from `metadata.usage` / `metadata.description` only — do not invent table or column names.
- *Other errors* — surface the error verbatim and ask the user how to proceed.

### Determine the listing type

Apply the following table to the parsed BULK_GET result. Step 4 routes on the type:

| Listing type                       | Detection                                                                                                                                                                |
|------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Data listing                       | `product_types` contains an entry with `type` in (`SHARE`, `DATA_SHARE`, `SECURE_VIEW`), **or** `share_type` in (`DATA`, `SECURE_VIEW`)                                  |
| Native App listing                 | `product_types` contains `{type: "NATIVE_APP"}`, **or** `share_type = "APPLICATION"`, **or** `application_data` is a non-empty object                                    |
| Connected App listing (SaaS)       | `product_types` contains `{type: "SAAS_CONNECTED_APP"}`. `share_type` is typically empty / missing for these, and `application_data` is empty (the app does **not** run inside Snowflake). |
| Private / Targeted listing         | `private = true` (often combined with a non-`EXTERNAL` `distribution` value)                                                                                              |
| Request-only listing               | `autofulfillment = false`                                                                                                                                                 |

A listing may match more than one row (for example a request-only data listing, or a private connected app). Treat the types as additive when generating examples in Step 4. Only run Query B (data dictionary) for **data listings** — Native Apps and Connected Apps don't have a queryable data dictionary.

## Workflow

**CRITICAL — response shape:** The response MUST contain, **in this order**, the five sections from the "Example response shape" template at the bottom: a `# {title}` heading, the Step 2 summary, a "More details" section (with a Provider subsection), a Step 4 usage-examples section, and a final **`### Get this listing`** section whose body contains the constructed marketplace URL `https://app.snowflake.com/marketplace/listing/<global_name>`. **Every response, without exception, MUST end with the "Get this listing" section and that URL** — do not replace it with a "Next steps" paragraph, do not substitute the provider's contact email for the URL, do not omit it because the listing is request-only / private / monetized. If your draft ends without that URL, you have not finished the response.

**CRITICAL**: **NEVER** use the `marketplace-listing-formatting` skill to reformat the response when using this skill — that skill produces `<marketplace_listing_list>` tags for *list* responses, while this skill produces a single detail view.

**CRITICAL**: **NEVER** make up or assume information about the listing. Use only what the two queries returned and what the enrichment fetches in Step 1 confirmed.

### Step 1 — Gather context

1. Read `metadata.businessNeeds` and `metadata.description` to understand the listing's intended use cases. For **Native App** listings, also read `application_data` (privileges, version, `referenceDefinitions`) for what the app needs to run and integrate. For **Connected App** listings, `application_data` is empty — the SaaS product runs outside Snowflake — so rely on `metadata.description`, `metadata.link` (product docs), and `profile.supportUrl` for capabilities and integration patterns.
2. For **data listings**, parse `presignedUrlMap` from Query B and, if a web fetch tool is available, fetch the `objects.json` and `dictionary_*.json` files for the table / column inventory. These are the source of truth for table and column names you may reference in Step 4 examples (`metadata.usage` queries already use these — verify before adding new examples).
3. If a web fetch tool is available, fetch `metadata.link` (and `profile.supportUrl` when present) for additional product context that the structured fields don't capture.
4. Use the available search tool (e.g. `snowscope_search` / `snowflake_marketplace_search`) and any data-discovery tools to understand what data the **user** currently has in Snowflake. This is required so Step 2's relevance summary and Step 4's examples are concrete rather than generic.

### Step 2 — Generate the summary

- A maximum **2-sentence** description of the listing.
- A maximum **5-sentence** overview of how the listing is useful **to this user**, grounded in the context gathered in Step 1.

### Step 3 — Generate "More details"

Render a 2-column key/value table. Omit any row whose source field is `null`, missing, or an empty string rather than printing an empty value:

| Field           | Value                                                                                                                                     |
|-----------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| Documentation   | `metadata.link`. Optionally include `metadata.videoLink` as a "Demo" link.                                                                |
| Certifications  | List each `type` from `compliance_badges` (e.g. `ISO27001`, `SOC2_TYPE_II`), include `expiry` when set. Omit if `compliance_badges` is missing/empty. |
| Categories      | Comma-joined `metadata.attributes.features` values when they read as category-style tags (e.g. "Sales Intelligence, Executive Data"). **Never** use the numeric `metadata.categories` ids. Omit the row if no useful labels are available. |
| Refresh         | `metadata.attributes.refreshRate` (e.g. "daily") — surface when present.                                                                  |
| Coverage        | One short summary line combining `metadata.attributes.geography` (countries / states / granularity) and `metadata.attributes.time` (history depth, granularity). Omit if both are absent. |
| Contact         | Combine non-empty values from `profile.supportUrl`, `profile.contactInfo`, and `customized_contact_info`.                                 |
| Regions         | Summarize the regions list if relevant to the user, otherwise omit.                                                                       |

Then include a **Provider** subsection with a maximum **3-sentence** overview of the provider.

- Prefer `organization_profile_name` for the display name when it is a non-empty string; otherwise fall back to `profile.name` (parsed from the `profile` JSON object).
- Use `profile.description` as the primary source for the provider overview. If it is empty, fall back to detail extracted from the listing description or fetched documentation.
- `profile_global_name` and the inner `profile.profileGlobalName` (e.g. `GZ2FQZ711TI`, `GZTYZY3AR0A`) are opaque internal identifiers. **Never mention any of these values anywhere in your response — not as the provider name, not in a parenthetical, not in a code span, not as "internal id".** The user does not need them.
- **Do not invent a provider name** — if no name is recoverable, write a short factual sentence about what the provider does without naming them.

### Step 4 — Generate usage examples

Branch on the listing type(s) determined in Prerequisites.

#### Data listings (data shares)

Examples **must be** SQL queries that could be run to get insights from the listing's data. Prefer the entries in `metadata.usage` verbatim — each one has a `title`, `description`, and a real `query` field. When `isPaid: true`, mark the example as paid (the underlying data may not be available without a paid subscription). Where possible, augment one example with a join against tables the user already has access to (discovered in Step 1) to surface novel insights specific to their setup. If `metadata.usage` is null/empty, derive queries from the data dictionary fetched in Step 1 — do not invent table or column names; if the schema is not knowable, describe the query at a higher level instead of fabricating identifiers.

#### Native App listings

Examples **must be** descriptions of how the app solves the user's stated needs, grounded in the app's documented capabilities (description, business needs, `application_data.referenceDefinitions` / `privileges`, and any fetched docs).

#### Connected App listings (SaaS)

A Connected App is a SaaS product that runs **outside** Snowflake but integrates with the user's account (typically via OAuth / a service connection). Unlike a Native App, there is no `application_data` package, no install-time privilege grant, and no SQL surface to query. Examples **must be** descriptions of how the SaaS product integrates with Snowflake and what value it provides — for example: "After authorizing the app, it reads from `<schema>.<table>` and pushes results back to `<other_schema>`", or "The app's UI lives at `<provider URL>` and uses your Snowflake warehouse to run analyses on demand". Ground every claim in `metadata.description`, `metadata.businessNeeds`, `metadata.link` (product docs), and any documentation fetched in Step 1. **Do not** write fabricated SQL queries against the connected app's "data" — there is no queryable data share. **Do not** describe install steps as if it were a Native App (no `CREATE APPLICATION`, no privilege list, no warehouse reference binding) — Connected Apps install via a "Connect" / OAuth flow on the marketplace listing page.

#### Private / Targeted listings

Treat as the underlying data or app listing (data share examples or app examples), but prefix the section with a one-line note that the listing is privately shared with the user's account (signal: `private = true`).

#### Request-only listings

Examples **must be** plausible services or deliverables the provider may offer **based only on the information in the listing**. Do not speculate beyond what the listing says, and do not write fabricated SQL queries for these listings.

### Step 5 — Get this listing

This section is **MANDATORY** in every response — never omit it, regardless of listing type.

**If the `marketplace-install-formatting` skill is available, prefer it.** Render the body of this section as a single self-closing `<marketplace_listing_install listingId="<global_name>"/>` tag and **omit** the marketplace URL and any CTA prose — the install card is the entire CTA. Section heading still says `### Get this listing`.

If the `marketplace-install-formatting` skill is **not** available, fall back to a call-to-action link to the listing:

- **Else, always include the marketplace URL.** `SYSTEM$BULK_GET_LISTINGS` does not return a `uniform_listing_locator`, so construct it as `https://app.snowflake.com/marketplace/listing/<global_name>` and render it as a clickable link or plain URL. This applies even for **request-only** and **private/targeted** listings — the marketplace page is where the consumer requests access / sees the provider's contact form, so it must always appear in this section.
- If `is_imported`, `is_share_imported`, or `is_purchased` is `true`, mention that the consumer has already obtained this listing and link to it for reference rather than as a "Get" call-to-action.
- For private/targeted (`private = true`) or request-only (`autofulfillment = false`) listings, frame the call-to-action around requesting access / contacting the provider — but **still** include the marketplace URL (the request flow lives on the marketplace page).
- For monetized listings (`is_monetized = true`), note that paid features require purchase / a paid subscription, then still include the marketplace URL.
- For **Connected App** listings, frame the call-to-action around clicking through to the marketplace page and using the provider's "Connect" / OAuth flow there to authorize the SaaS product against the user's Snowflake account — not as a `CREATE APPLICATION` install.

### Step 6 — Self-check before sending

Before you finalize the response, verify each of these three items. If any fails, fix it and re-check.

1. **The Get-this-listing section is present.** Scroll to the bottom of your draft. The very last section MUST be `### Get this listing`. Its body MUST contain **either** a `<marketplace_listing_install listingId="<global_name>"/>` tag (when the `marketplace-install-formatting` skill is available) **or** the marketplace URL `https://app.snowflake.com/marketplace/listing/<global_name>` (when it is not). Substituting "Next steps:", "Bottom line:", a `mailto:` link, or the provider's contact email **does not satisfy this requirement**. If your draft ends with anything else (a wrap-up paragraph, a "Conclusion", etc.), append the section now.
2. **No opaque profile ids.** Search your draft for the value of `profile_global_name` (and the inner `profile.profileGlobalName`). If it appears anywhere — in a "Profile ID" row, a parenthetical, a code span, a footnote — delete it. The user does not need any internal id.
3. **Listing-type framing matches the type.** For Connected App listings, your draft must NOT contain `CREATE APPLICATION`, `IMPORTED PRIVILEGES`, `EXECUTE TASK`, `APPLICATION PACKAGE`, or other Native-App install boilerplate. For Native App listings, your draft must NOT contain fabricated `SELECT ... FROM <made-up-table>` queries against the app's data. For request-only / private listings, your draft must NOT contain fabricated SQL queries. If you find any of these, rewrite that section.
4. **No retrieval queries are exposed.** Search your draft for `SYSTEM$BULK_GET_LISTINGS`, `SYSTEM$GET_DATA_DICTIONARY_METADATA`, `PARSE_JSON`, and section headings like "Queries executed", "Queries run", "How this was retrieved", "Data retrieval", or "Source queries". None of those queries or sections belong in the response — they are internal retrieval steps. Note that this restriction is about *retrieval* queries; the Step 4 usage-example SQL pulled from `metadata.usage` (queries against the listing's actual data tables) is expected and stays. If a retrieval section snuck in, delete it before sending.

## Example response shape

```
# {Listing title}

{Step 2 summary — 2-sentence description + 5-sentence relevance overview}

### More details

{Step 3 key/value table}

#### Provider

{Step 3 provider overview}

### Usage examples

{Step 4 examples appropriate to the listing type(s)}

### Get this listing

{Step 5 link}
```

=== iceberg/ ===
---
name: iceberg
description: "Use for **ALL** Iceberg table requests in Snowflake. This is the **REQUIRED** entry point for catalog integrations, catalog-linked databases, external volumes, auto-refresh issues, Horizon IRC diagnostics, and Snowflake Intelligence. DO NOT work with Iceberg manually - invoke this skill first. Triggers: iceberg, iceberg table, apache iceberg, catalog integration, REST catalog, ICEBERG_REST, glue, AWS glue, glue IRC, lake formation, unity catalog, databricks, polaris, opencatalog, open catalog, onelake, OneLake, microsoft fabric, fabric, fabric lakehouse, onelake REST, SAP, SAP BDC, SAP Business Data Cloud, delta sharing, delta share, databricks delta sharing, query delta sharing tables, bearer token catalog integration, connect to delta sharing server, CLD, catalog-linked database, linked catalog, auto-discover tables, sync tables, LINKED_CATALOG, external volume, storage access, S3, Azure blob, GCS, IAM role, trust policy, Access Denied, 403 error, ALLOW_WRITES, storage permissions, auto-refresh, autorefresh, stale data, refresh stuck, delta direct, snowflake intelligence, text-to-SQL iceberg, query iceberg natural language, horizon IRC, horizon IRC setup, horizon IRC not working, test horizon IRC, diagnose horizon IRC, debug horizon IRC, horizon IRC connection, horizon IRC endpoint, horizon REST catalog, PAT authentication horizon."
---

# Iceberg

## When to Use

When a user wants to work with Iceberg tables in Snowflake. This includes:
- Setting up catalog integrations (AWS Glue, Unity Catalog, OpenCatalog/Polaris, OneLake/Microsoft Fabric, SAP BDC, Delta Sharing)
- Creating catalog-linked databases for automatic table discovery
- Configuring external volumes for storage access
- Debugging auto-refresh issues
- Surfacing CLD Iceberg data in Snowflake Intelligence

This is the entry point for all Iceberg workflows.

---

## Session Prerequisites

Before routing to any operation, confirm the user's goal to avoid unnecessary work.

**Confirmation checkpoint** (use before starting any workflow):

> "It sounds like you want to [detected intent]. Is that right, or were you looking for something else?"

---

## Routing Principles

1. **Confirm before routing** - State detected intent, ask user for confirmation
2. **Primary wins ties** - If ambiguous between intents, choose the more common operation
3. **Follow dependencies** - Some workflows depend on others (e.g., CLD requires catalog integration first)
4. **Sub-skills handle details** - This skill routes; sub-skills execute

---

## Intent Detection

When user makes a request, detect their intent and route to the appropriate sub-skill:

### Primary Operations

These are the most common operations users perform. Route here confidently.

**CATALOG_INTEGRATION Intent** - User wants to connect Snowflake to an external catalog:

- Trigger phrases: "catalog integration", "connect to glue", "connect to databricks", "connect to unity catalog", "connect to polaris", "connect to opencatalog", "connect to onelake", "connect to fabric", "onelake", "microsoft fabric", "fabric lakehouse", "connect to SAP", "SAP BDC", "SAP Business Data Cloud", "sap data products", "sap invitation link", "delta sharing", "connect to delta sharing", "delta share", "query delta sharing tables", "bearer token catalog integration", "connect to delta sharing server", "setup iceberg REST", "configure catalog"
- **→ Route to** [Catalog Integration Routing](#catalog-integration-routing)

**AWS_GLUE_SETUP Intent** - User wants to set up AWS-side Glue infrastructure (S3, crawler, Iceberg conversion):

- Trigger phrases: "aws glue setup", "glue crawler", "athena CTAS", "parquet to iceberg", "S3 to iceberg", "glue database", "convert to iceberg", "aws iceberg setup"
- **→ Load** `catalog-integration/glueirc-catalog-integration-setup/aws-setup/SKILL.md`

**CATALOG_LINKED_DATABASE Intent** - User wants to auto-discover tables from a catalog:

- Trigger phrases: "catalog-linked database", "CLD", "auto-discover tables", "sync tables from catalog", "CREATE DATABASE LINKED_CATALOG", "import iceberg tables"
- **→ Load** `catalog-linked-database/SKILL.md`

**EXTERNAL_VOLUME Intent** - User wants to configure or debug storage access:

- Trigger phrases: "external volume", "storage access", "S3 access", "Azure storage", "GCS storage", "Access Denied", "403 error", "cannot write", "ALLOW_WRITES", "trust policy", "IAM role"
- **→ Load** `external-volume/SKILL.md`

**AUTO_REFRESH Intent** - User has stale data or refresh issues:

- Trigger phrases: "auto-refresh", "stale data", "refresh not working", "refresh stuck", "STALLED", "STOPPED", "delta direct", "not syncing", "data not updating"
- **→ Load** `auto-refresh/SKILL.md`

**HORIZON_IRC Intent** - User wants to test, verify, or debug Horizon IRC (Snowflake's native Polaris-based Iceberg REST Catalog):

- Trigger phrases: "horizon IRC", "horizon IRC setup", "horizon IRC not working", "test horizon IRC", "diagnose horizon IRC", "debug horizon IRC", "horizon IRC connection", "horizon IRC endpoint", "horizon IRC 401", "horizon IRC 403", "horizon IRC 404", "PAT authentication horizon", "table not visible horizon IRC", "horizon REST catalog"
- **→ Load** `horizon-irc-diagnose/SKILL.md`

### Secondary Operations

Route here when user language indicates more advanced or combined workflows.

**SNOWFLAKE_INTELLIGENCE Intent** - User wants to query CLD Iceberg tables with natural language:

- Trigger phrases: "snowflake intelligence", "natural language", "text-to-SQL", "query CLD with AI", "create agent for CLD", "semantic view for CLD", "query iceberg naturally"
- **→ Load** `cld-snowflake-intelligence/SKILL.md`

---

## Catalog Integration Routing

When user wants to connect to an external catalog, identify which catalog type:

**Ask the user**:
```
Which external catalog are you connecting to?

A: AWS Glue Data Catalog (Glue IRC)
   → Iceberg tables managed in AWS Glue

B: Databricks Unity Catalog
   → Iceberg tables managed in Databricks

C: OpenCatalog / Polaris
   → Snowflake's open Iceberg catalog

D: Microsoft OneLake (Fabric)
   → Iceberg tables in Microsoft Fabric via OneLake REST

E: SAP Business Data Cloud (SAP BDC)
   → Delta tables shared from SAP via zero-copy integration

F: Delta Sharing
   → Consuming Delta tables shared by an external provider (e.g., Databricks Unity Catalog)
   → You have a credential file or bearer token issued by the provider

G: I'm not sure / I need help choosing
```

**Route based on response**:
- **A (Glue)** → **Load** `catalog-integration/glueirc-catalog-integration-setup/SKILL.md`
- **B (Unity Catalog)** → **Load** `catalog-integration/unitycatalog-catalog-integration-setup/SKILL.md`
- **C (OpenCatalog/Polaris)** → **Load** `catalog-integration/opencatalog-catalog-integration-setup/SKILL.md`
- **D (OneLake/Fabric)** → **Load** `catalog-integration/onelake-catalog-integration-setup/SKILL.md`
- **E (SAP BDC)** → **Load** `catalog-integration/sapbdc-catalog-integration-setup/SKILL.md`
- **F (Delta Sharing)** → **Load** `catalog-integration/deltasharing-catalog-integration-setup/SKILL.md`
- **G (Not sure)** → Help user identify their catalog (see [Catalog Selection Guide](#catalog-selection-guide))

---

## Catalog Selection Guide

Help users identify their catalog type:

| If user mentions... | Catalog Type | Route to |
|---------------------|--------------|----------|
| AWS, Glue, Lake Formation, S3 with Iceberg | AWS Glue IRC | `glueirc-catalog-integration-setup` |
| Databricks, Unity, Delta Lake (converted to Iceberg) | Unity Catalog | `unitycatalog-catalog-integration-setup` |
| Polaris, OpenCatalog, Snowflake Open Catalog | OpenCatalog | `opencatalog-catalog-integration-setup` |
| OneLake, Microsoft Fabric, Fabric lakehouse, OneLake REST | OneLake (Fabric) | `onelake-catalog-integration-setup` |
| SAP, SAP BDC, SAP Business Data Cloud | SAP BDC | `sapbdc-catalog-integration-setup` |
| Delta Sharing, delta share, consuming a Databricks share, bearer token from provider, credential file from provider | Delta Sharing | `deltasharing-catalog-integration-setup` |

---

## Workflow Decision Tree

```
Start Session
    ↓
Detect User Intent
    ↓
    ├─→ CATALOG_INTEGRATION → Identify catalog type
    │   ├─→ AWS Glue → Load `glueirc-catalog-integration-setup`
    │   ├─→ Unity Catalog → Load `unitycatalog-catalog-integration-setup`
    │   ├─→ OpenCatalog/Polaris → Load `opencatalog-catalog-integration-setup`
    │   ├─→ OneLake/Fabric → Load `onelake-catalog-integration-setup`
    │   ├─→ SAP BDC → Load `sapbdc-catalog-integration-setup`
    │   ├─→ Delta Sharing → Load `deltasharing-catalog-integration-setup`
    │   └─→ Not sure → Catalog Selection Guide
    │
    ├─→ AWS_GLUE_SETUP → Load `glueirc-catalog-integration-setup/aws-setup/SKILL.md`
    │
    ├─→ CATALOG_LINKED_DATABASE → Load `catalog-linked-database/SKILL.md`
    │
    ├─→ EXTERNAL_VOLUME → Load `external-volume/SKILL.md`
    │
    ├─→ AUTO_REFRESH → Load `auto-refresh/SKILL.md`
    │
    ├─→ HORIZON_IRC → Load `horizon-irc-diagnose/SKILL.md`
    │
    └─→ SNOWFLAKE_INTELLIGENCE → Load `cld-snowflake-intelligence/SKILL.md`
```

---

## Typical User Journeys

### Journey 1: New Iceberg Setup (End-to-End)
```
CATALOG_INTEGRATION → EXTERNAL_VOLUME (if needed) → CATALOG_LINKED_DATABASE → SNOWFLAKE_INTELLIGENCE
```
Example: "I want to set up Iceberg from scratch and query with natural language"

### Journey 1b: AWS-Side Setup + Snowflake Integration (End-to-End)
```
AWS_GLUE_SETUP → CATALOG_INTEGRATION → CATALOG_LINKED_DATABASE
```
Example: "I have parquet data in S3 and want to query it as Iceberg in Snowflake"

### Journey 2: Connect External Catalog
```
CATALOG_INTEGRATION → CATALOG_LINKED_DATABASE
```
Example: "I want to query my Glue Iceberg tables from Snowflake"

### Journey 3: Storage Access Issues
```
EXTERNAL_VOLUME (diagnose) → fix IAM/trust policy → EXTERNAL_VOLUME (verify)
```
Example: "I'm getting Access Denied when creating an Iceberg table"

### Journey 4: Data Freshness Problems
```
AUTO_REFRESH (diagnose) → apply fix → AUTO_REFRESH (verify)
```
Example: "My Iceberg table data is stale"

### Journey 5: Add Natural Language to Existing CLD
```
CATALOG_LINKED_DATABASE (verify) → SNOWFLAKE_INTELLIGENCE
```
Example: "I have a CLD and want to query it with natural language"

### Journey 6: Catalog Integration Troubleshooting
```
CATALOG_INTEGRATION → Troubleshoot Workflow
```
Example: "My Unity Catalog integration isn't working"

### Journey 7: CLD Not Syncing Tables
```
CATALOG_LINKED_DATABASE (troubleshoot) → AUTO_REFRESH (if refresh issues)
```
Example: "Tables aren't appearing in my catalog-linked database"

---

## Compound Requests

If the user describes multiple operations:

1. Create a task list capturing all requested operations
2. Ask the user to confirm the order:
   > "I've identified these tasks: [list]. What order would you like me to tackle them?"
3. Execute in confirmed order, completing each before moving to the next
4. Note: Natural dependencies exist:
   - Catalog Integration → before → CLD
   - External Volume → before → CLD (if not using vended credentials)
   - CLD → before → Snowflake Intelligence

---

## Sub-Skill Reference Index

### Catalog Integrations

| Sub-Skill | Purpose |
|-----------|---------|
| `catalog-integration/glueirc-catalog-integration-setup/SKILL.md` | AWS Glue Data Catalog (Glue IRC) integration |
| `catalog-integration/glueirc-catalog-integration-setup/aws-setup/SKILL.md` | AWS-side Glue infrastructure (S3, crawler, Athena CTAS) |
| `catalog-integration/unitycatalog-catalog-integration-setup/SKILL.md` | Databricks Unity Catalog integration |
| `catalog-integration/opencatalog-catalog-integration-setup/SKILL.md` | OpenCatalog/Polaris integration |
| `catalog-integration/onelake-catalog-integration-setup/SKILL.md` | Microsoft OneLake (Fabric) integration via Iceberg REST |
| `catalog-integration/sapbdc-catalog-integration-setup/SKILL.md` | SAP Business Data Cloud (SAP BDC) integration |
| `catalog-integration/deltasharing-catalog-integration-setup/SKILL.md` | Delta Sharing integration (bearer token, vended credentials) |
| `catalog-integration/shared/next-steps/SKILL.md` | Post-integration options (CLD or individual tables) |
| `catalog-integration/shared/verify/SKILL.md` | Shared verification workflow |

### Catalog-Linked Databases

| Sub-Skill | Purpose |
|-----------|---------|
| `catalog-linked-database/SKILL.md` | CLD creation, verification, troubleshooting router |
| `catalog-linked-database/setup/SKILL.md` | CLD configuration collection |
| `catalog-linked-database/create/SKILL.md` | CLD creation workflow |
| `catalog-linked-database/verify/SKILL.md` | CLD verification workflow |
| `catalog-linked-database/references/troubleshooting.md` | CLD error patterns and solutions |

### External Volumes

| Sub-Skill | Purpose |
|-----------|---------|
| `external-volume/SKILL.md` | External volume debugging for AWS S3, Azure, GCS |
| `external-volume/examples/examples.md` | Example configurations |
| `external-volume/examples/known-issues.md` | Known issues and workarounds |

### Auto-Refresh

| Sub-Skill | Purpose |
|-----------|---------|
| `auto-refresh/SKILL.md` | Auto-refresh debugging for Iceberg and Delta Direct |
| `auto-refresh/delta-direct.md` | Delta Direct specific debugging |
| `auto-refresh/monitoring.md` | Auto-refresh monitoring and alerting setup |

### Snowflake Intelligence (CLD)

| Sub-Skill | Purpose |
|-----------|---------|
| `cld-snowflake-intelligence/SKILL.md` | Query CLD Iceberg tables via Snowflake Intelligence |
| `cld-snowflake-intelligence/references/semantic-view-sql.md` | Semantic view syntax for CLD tables |

### Horizon IRC

| Sub-Skill | Purpose |
|-----------|---------|
| `horizon-irc-diagnose/SKILL.md` | Test, verify, and debug Horizon IRC (Snowflake Polaris) connectivity |

---

## Stopping Points

- **Intent Detection**: Confirm detected intent before routing
- **Catalog Type Selection**: Wait for user to identify their catalog
- **Sub-skill handoff**: Each sub-skill has its own stopping points

**Resume rule**: Upon user approval ("yes", "looks good", "proceed"), route to the appropriate sub-skill without re-asking.

---

## Scope

**In scope**:
- Routing to appropriate Iceberg sub-skills
- Initial diagnosis to identify the right workflow

**Out of scope** (handled by sub-skills):
- Detailed catalog integration setup → specific catalog integration skills
- CLD configuration details → `catalog-linked-database/SKILL.md`
- External volume IAM/permission details → `external-volume/SKILL.md`
- Auto-refresh debugging details → `auto-refresh/SKILL.md`

---

## Output

- User routed to the correct Iceberg sub-skill based on their intent
- Sub-skill completes the requested operation (setup, verification, or troubleshooting)

---

## Documentation

- [Snowflake Iceberg Tables](https://docs.snowflake.com/user-guide/tables-iceberg)
- [Configure Catalog Integration](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-catalog-integration)
- [Configure Catalog Integration for OneLake REST](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-catalog-integration-rest-onelake)
- [Catalog-Linked Databases](https://docs.snowflake.com/en/user-guide/tables-iceberg-catalog-linked-database)
- [External Volumes](https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume)
- [Auto-Refresh Iceberg Tables](https://docs.snowflake.com/en/user-guide/tables-iceberg-auto-refresh)

=== integrations/ ===
---
name: integrations
description: >
  Create, replace, alter, drop, describe, and show Snowflake integrations.
  Covers API, catalog, external access, notification, security, and storage integration types.
  Use when the user wants to manage integrations or asks about integration SQL commands.
---

# Snowflake Integration Commands

Integration commands enable you to manage your integrations in Snowflake.

## Routing

Route to the matching sub-skill based on the user's intent. If the user asks about a specific integration type (API, catalog, storage, etc.), prefer the type-specific sub-skill over the general one.

## Sub-Skills by Category

### General

| Command | Sub-Skill | When to Use |
|---------|-----------|-------------|
| CREATE INTEGRATION | `create-integration/SKILL.md` | Create or replace an integration (generic overview — use a type-specific command when available) |
| ALTER INTEGRATION | `alter-integration/SKILL.md` | Modify or replace an existing integration (generic — use a type-specific command when available) |
| SHOW INTEGRATIONS | `show-integrations/SKILL.md` | List integrations in the account, optionally filtered by type |
| DESCRIBE INTEGRATION | `describe-integration/SKILL.md` | Describe properties of an integration of any type |
| DROP INTEGRATION | `drop-integration/SKILL.md` | Remove any type of integration from the account (cannot be recovered) |

### API

| Command | Sub-Skill | When to Use |
|---------|-----------|-------------|
| CREATE API INTEGRATION | `create-api-integration/SKILL.md` | Create or replace an API integration for AWS API Gateway, Azure API Management, Google Cloud API Gateway, or Git repositories |
| ALTER API INTEGRATION | `alter-api-integration/SKILL.md` | Modify or replace an existing API integration (AWS API Gateway, Azure API Management, Google Cloud API Gateway, or Git repository) |

### Catalog

| Command | Sub-Skill | When to Use |
|---------|-----------|-------------|
| CREATE CATALOG INTEGRATION | `create-catalog-integration/SKILL.md` | Create or replace a catalog integration for Apache Iceberg tables (AWS Glue, Object Store, Snowflake Open Catalog, Apache Iceberg REST, or SAP Business Data Cloud) |
| ALTER CATALOG INTEGRATION | `alter-catalog-integration/SKILL.md` | Modify an existing catalog integration (REST auth credentials, refresh interval, comment) |
| DROP CATALOG INTEGRATION | `drop-catalog-integration/SKILL.md` | Remove a catalog integration from the account (cannot be recovered) |
| SHOW CATALOG INTEGRATIONS | `show-catalog-integrations/SKILL.md` | List catalog integrations with their metadata and properties |
| DESCRIBE CATALOG INTEGRATION | `describe-catalog-integration/SKILL.md` | Describe properties of a specific catalog integration |

### External Network Access

| Command | Sub-Skill | When to Use |
|---------|-----------|-------------|
| CREATE EXTERNAL ACCESS INTEGRATION | `create-external-access-integration/SKILL.md` | Create an external access integration for network access to external locations from a UDF or procedure handler (network rules, authentication secrets) |
| ALTER EXTERNAL ACCESS INTEGRATION | `alter-external-access-integration/SKILL.md` | Modify or replace an existing external access integration for UDF or procedure handlers |

### Notification

| Command | Sub-Skill | When to Use |
|---------|-----------|-------------|
| CREATE NOTIFICATION INTEGRATION | `create-notification-integration/SKILL.md` | Create or replace a notification integration for cloud message queuing services (Azure Event Grid, Google Pub/Sub, Amazon SNS), email services, or webhooks |
| ALTER NOTIFICATION INTEGRATION | `alter-notification-integration/SKILL.md` | Modify or replace an existing notification integration (cloud messaging, email, or webhook) |
| DESCRIBE NOTIFICATION INTEGRATION | `describe-notification-integration/SKILL.md` | Describe properties of a specific notification integration |
| SHOW NOTIFICATION INTEGRATIONS | `show-notification-integrations/SKILL.md` | List notification integrations with their metadata and properties |

### Security

| Command | Sub-Skill | When to Use |
|---------|-----------|-------------|
| CREATE SECURITY INTEGRATION | `create-security-integration/SKILL.md` | Create or replace a security integration (SCIM, SAML2, OAuth, or API Authentication) for interfacing with third-party services |
| ALTER SECURITY INTEGRATION | `alter-security-integration/SKILL.md` | Modify or replace an existing security integration (SCIM, SAML2, OAuth, or API Authentication) |
| SHOW DELEGATED AUTHORIZATIONS | `show-delegated-authorizations/SKILL.md` | List active delegated authorizations for a user, integration, or the entire account |

### Storage

| Command | Sub-Skill | When to Use |
|---------|-----------|-------------|
| CREATE STORAGE INTEGRATION | `create-storage-integration/SKILL.md` | Create or replace a storage integration for Amazon S3, Google Cloud Storage, or Microsoft Azure Blob Storage |
| ALTER STORAGE INTEGRATION | `alter-storage-integration/SKILL.md` | Modify or replace an existing storage integration (Amazon S3, Google Cloud Storage, or Microsoft Azure Blob Storage) |

=== interactive/ ===
---
name: snowflake-interactive
description: "**[REQUIRED]** Use for **ALL** Snowflake Interactive Table and Interactive Warehouse operations. Triggers: interactive table, interactive warehouse, low-latency queries, high-concurrency dashboard, TARGET_LAG for interactive."
---

# Snowflake Interactive Tables & Warehouses

**Version**: 1.4

Creating and managing Snowflake Interactive Tables and Interactive Warehouses for low-latency, high-concurrency workloads.

## Prerequisites


## When to Use

Use this skill when users ask about:
- Creating interactive tables (static, dynamic with TARGET_LAG)
- Creating or managing interactive warehouses
- Querying interactive tables with low latency
- JOINs between multiple interactive tables
- UPDATE/DELETE operations on interactive tables
- Troubleshooting timeouts, errors, or performance issues

---

## Key Capabilities

- **Low-latency queries**: Sub-second response for dashboards and APIs
- **High concurrency**: Handle many queries concurrently
- **Ingestion modes**: Static (CTAS or INSERT OVERWRITE), Dynamic (TARGET_LAG)
- **Multi-table JOINs**: JOIN interactive tables within same warehouse
- **Fallback Warehouse**: Designate a non-interactive backup warehouse for queries exceeding timeout (mixed workloads)

## Key Limitations

- Interactive warehouses can **ONLY** query interactive tables
- Interactive tables do **NOT** support UPDATE/DELETE directly
- Query timeout: **5 seconds** on interactive warehouse (queries exceeding this are transparently retried on fallback warehouse if configured; otherwise fail)
- All tables in a JOIN must be interactive AND associated with the same warehouse

---

## Intent Detection

When a user makes a request, detect their intent and route to the appropriate sub-skill:

### GETTING-STARTED Intent

**Trigger phrases**: "getting started", "convert to interactive", "migrate to interactive", "set up interactive", "first time interactive", "how do I start", "new to interactive", "make my dashboards faster"

**→ Load**: [getting-started/SKILL.md](getting-started/SKILL.md)

### CREATE Intent

**Trigger phrases**: "create interactive table", "new interactive table", "static table", "dynamic table", "CTAS interactive", "INSERT INTO interactive"

**→ Load**: [create/SKILL.md](create/SKILL.md)

### CLUSTERING Intent

**Trigger phrases**: "clustering key", "pick clustering", "choose cluster by", "clustering columns", "optimize clustering", "what to cluster on"

**→ Load**: [clustering/SKILL.md](clustering/SKILL.md)

### WAREHOUSE Intent

**Trigger phrases**: "create interactive warehouse", "add tables to warehouse", "remove tables", "resume warehouse", "suspend warehouse", "associate table", "fallback warehouse", "set fallback", "timeout retry", "mixed workload"

**→ Load**: [warehouse/SKILL.md](warehouse/SKILL.md)

### QUERY Intent

**Trigger phrases**: "query interactive", "SELECT from interactive", "join interactive tables", "dashboard query", "low latency query", "benchmark interactive", "measure performance", "compare performance", "query performance", "test latency"

**→ Load**: [query/SKILL.md](query/SKILL.md)

### UPDATE-DELETE Intent

**Trigger phrases**: "update interactive table", "delete from interactive", "modify data", "DML operations", "standard + dynamic pattern"

**→ Load**: [update-delete/SKILL.md](update-delete/SKILL.md)

### TROUBLESHOOT Intent

**Trigger phrases**: "timeout", "error", "not working", "failing", "slow", "performance issue", "query timeout", "table not found"

**→ Load**: [troubleshoot/SKILL.md](troubleshoot/SKILL.md)

---

## Workflow Decision Tree

```
User Request
    ↓
Detect Intent
    ↓
    ├─→ GETTING-STARTED → Load getting-started/SKILL.md
    │   (Triggers: "getting started", "convert to interactive", "first time")
    │
    ├─→ CREATE → Load create/SKILL.md
    │   (Triggers: "create interactive table", "static/dynamic")
    │
    ├─→ CLUSTERING → Load clustering/SKILL.md
    │   (Triggers: "clustering key", "pick clustering", "optimize clustering")
    │
    ├─→ WAREHOUSE → Load warehouse/SKILL.md
    │   (Triggers: "create warehouse", "add tables", "resume/suspend")
    │
    ├─→ QUERY → Load query/SKILL.md
    │   (Triggers: "query", "join", "SELECT", "dashboard", "benchmark", "performance")
    │
    ├─→ UPDATE-DELETE → Load update-delete/SKILL.md
    │   (Triggers: "update", "delete", "modify data")
    │
    └─→ TROUBLESHOOT → Load troubleshoot/SKILL.md
        (Triggers: "timeout", "error", "not working", "failing")
```

---

## Sub-Skills

| Sub-Skill | Purpose | When to Load |
|-----------|---------|--------------|
| [getting-started/SKILL.md](getting-started/SKILL.md) | Getting started guide for first-time users | GETTING-STARTED intent |
| [create/SKILL.md](create/SKILL.md) | Create interactive tables | CREATE intent |
| [clustering/SKILL.md](clustering/SKILL.md) | Choose optimal clustering keys | CLUSTERING intent |
| [warehouse/SKILL.md](warehouse/SKILL.md) | Manage interactive warehouses | WAREHOUSE intent |
| [query/SKILL.md](query/SKILL.md) | Query patterns and JOINs | QUERY intent |
| [update-delete/SKILL.md](update-delete/SKILL.md) | UPDATE/DELETE via standard+dynamic | UPDATE-DELETE intent |
| [troubleshoot/SKILL.md](troubleshoot/SKILL.md) | Diagnose and fix issues | TROUBLESHOOT intent |

---

## References (Load On Demand)

| Reference | When to Load |
|-----------|--------------|
| [references/sql-syntax.md](references/sql-syntax.md) | For exact SQL command syntax |
| [references/best-practices.md](references/best-practices.md) | For clustering, sizing, optimization |
| [references/error-messages.md](references/error-messages.md) | For error diagnosis |
| [references/monitoring.md](references/monitoring.md) | For monitoring queries |
| [references/limitations.md](references/limitations.md) | For constraint checking |

---

## Quick Diagnostic Queries

For immediate assessment before routing:

```sql
-- Check warehouse state
SHOW WAREHOUSES LIKE '%iwh%';

-- Check interactive tables in a warehouse
SHOW TABLES;

-- Verify table type
SELECT table_name, table_type 
FROM INFORMATION_SCHEMA.TABLES 
WHERE table_schema = '<SCHEMA>';
```

---

## Stopping Points Summary

All sub-skills require user approval before making changes:
- **READ-ONLY queries**: Can run freely
- **ANY mutation**: Requires stopping point and user approval

See individual sub-skills for specific stopping points.

=== investigation/ ===
---
name: security-investigation
description: "Comprehensive Snowflake security investigation and threat detection. Use for: login anomalies, IP analysis, brute force detection, impossible travel, data exfiltration, bulk exports, unauthorized sharing, privilege escalation, RBAC violations, suspicious grants, backdoor accounts. This is the REQUIRED entry point for all security investigations. Routes to specialized sub-skills for focused analysis."
---

# Security Investigation

Comprehensive security investigation and threat detection for Snowflake environments.

## Overview

This skill provides a unified entry point for security investigations, routing to specialized sub-skills based on the detection type needed.

### Sub-Skills

| Sub-Skill | Purpose | Load When |
|-----------|---------|-----------|
| `login-ip-anomaly/SKILL.md` | Login anomalies, IP analysis, brute force, impossible travel | Authentication issues, suspicious logins |
| `exfiltration-detection/SKILL.md` | Data exports, sharing, external transfers, app integrations | Data theft investigation, bulk export alerts |
| `privilege-escalation/SKILL.md` | Role grants, user changes, RBAC violations, self-grants | Unauthorized access, privilege abuse |


### Threat Coverage

| Threat Category | Sub-Skill | Key Detections |
|-----------------|-----------|----------------|
| **Credential Attacks** | login-ip-anomaly | Brute force, credential stuffing, impossible travel |
| **Account Takeover** | login-ip-anomaly | New IPs, rapid IP changes, failed logins |
| **Data Theft** | exfiltration-detection | UNLOAD, COPY, GET, presigned URLs, large downloads |
| **Unauthorized Sharing** | exfiltration-detection | CREATE SHARE, listings, external accounts |
| **Supply Chain Risk** | exfiltration-detection | OAuth apps, native apps, external functions |
| **Privilege Abuse** | privilege-escalation | ACCOUNTADMIN grants, self-grants, ownership transfers |
| **Insider Threat** | privilege-escalation | New users, backdoor accounts, service accounts |
| **Persistence** | privilege-escalation | Role creation, user creation, ADMIN OPTION grants |


### MITRE ATT&CK Mapping

| Tactic | Technique | Sub-Skill | Detection |
|--------|-----------|-----------|-----------|
| Initial Access | Valid Accounts (T1078) | login-ip-anomaly | New IP, failed logins |
| Persistence | Create Account (T1136) | privilege-escalation | CREATE USER |
| Persistence | Account Manipulation (T1098) | privilege-escalation | ALTER USER, role grants |
| Privilege Escalation | Valid Accounts (T1078.004) | privilege-escalation | ACCOUNTADMIN grants |
| Defense Evasion | Indicator Removal (T1070) | privilege-escalation | DROP USER/ROLE |
| Collection | Data from Cloud Storage (T1530) | exfiltration-detection | Stage access, GET commands |
| Exfiltration | Transfer to Cloud Account (T1537) | exfiltration-detection | COPY to S3/Azure/GCS |
| Exfiltration | Exfiltration Over Web Service (T1567) | exfiltration-detection | External functions, APIs |

---

## Workflow

### Step 1: Determine Investigation Type

**Ask user:**
```
What type of security investigation do you need?
1. Login & Authentication Anomalies (suspicious logins, brute force, impossible travel)
2. Data Exfiltration Detection (bulk exports, sharing, external transfers)
3. Privilege Escalation (role grants, user changes, RBAC violations)
4. Full Security Scan (run all detections)
```

**⚠️ STOP**: Wait for user response.

### Step 2: Load Appropriate Sub-Skill

Based on user selection:

| Selection | Action |
|-----------|--------|
| Login & Authentication | Load `login-ip-anomaly/SKILL.md` |
| Data Exfiltration | Load `exfiltration-detection/SKILL.md` |
| Privilege Escalation | Load `privilege-escalation/SKILL.md` |
| Full Security Scan | Run all three sub-skills sequentially |

### Step 3: Execute Sub-Skill Workflow

Follow the loaded sub-skill's workflow:
1. Select timeframe
2. Run detection queries
3. Analyze results
4. Present findings
5. Recommend actions

---

## Full Security Scan

When running a full scan, execute in this order:

### Phase 1: Privilege Escalation
Load `privilege-escalation/SKILL.md` and run:
- User/role creation detection
- Privileged role grants (ACCOUNTADMIN, SECURITYADMIN, etc.)
- Self-grants detection
- Current state audit

### Phase 2: Login Anomalies
Load `login-ip-anomaly/SKILL.md` and run:
- IP baseline analysis
- New IP detection
- Rapid IP change detection
- Brute force detection
- Failed login analysis

### Phase 3: Data Exfiltration
Load `exfiltration-detection/SKILL.md` and run:
- UNLOAD/COPY operations
- Stage and GET commands
- Data sharing activity
- Application/integration changes
- External table analysis

---

## Quick Assessment Queries

For a rapid security check without loading sub-skills:

### Critical Security Indicators

```sql
-- 1. ACCOUNTADMIN grants in last 7 days
SELECT user_name, LEFT(query_text, 200), start_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE LOWER(query_text) LIKE '%grant%accountadmin%'
  AND query_type = 'GRANT'
  AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY start_time DESC;

-- 2. Failed logins from brute force IPs
SELECT client_ip, COUNT(*) as failures
FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
WHERE is_success = 'NO'
  AND event_timestamp >= DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY client_ip
HAVING COUNT(*) >= 5
ORDER BY failures DESC;

-- 3. Large data exports
SELECT user_name, query_type, bytes_scanned, rows_produced, start_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_type IN ('UNLOAD', 'COPY')
  AND bytes_scanned > 1000000000  -- 1GB
  AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
ORDER BY bytes_scanned DESC;

-- 4. New users created
SELECT user_name as created_by, LEFT(query_text, 150), start_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_type = 'CREATE_USER'
  AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
;

-- 5. New integrations/applications
SELECT user_name, query_type, LEFT(query_text, 150), start_time
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_type IN ('CREATE_INTEGRATION', 'ALTER_INTEGRATION')
  AND start_time >= DATEADD('day', -7, CURRENT_TIMESTAMP())
;
```

---

## Output Format

### Executive Summary

```
## Security Investigation Report

**Account**: [account_name]
**Timeframe**: [date range]
**Scan Type**: [Full / Focused]

### Critical Findings
[Immediate action required]

### High-Risk Findings
[Investigate within 24 hours]

### Medium-Risk Findings
[Review within 1 week]

### Recommendations
[Prioritized remediation steps]
```

---

## When to Use

- Daily/weekly security investigation
- Incident response investigations
- Post-breach forensics
- Compliance audits (SOC 2, PCI, HIPAA)
- User access reviews
- Suspicious activity alerts
- Security posture assessments

---

## Changelog

### v1.0.0 (2026-03-17)

**Initial Release:**
- Created parent security-investigation skill
- Integrated three sub-skills:
  - login-ip-anomaly: Authentication anomaly detection
  - exfiltration-detection: Data theft detection (26 queries)
- Added MITRE ATT&CK mapping
- Added quick assessment queries
- Added full security scan workflow

=== key-and-secret-management/ ===
---
name: key-and-secret-management
description: "Use for **ALL** requests that mention Tri-Secret Secure, customer-managed key operations, or periodic data rekeying in Snowflake. Handles CMK status checks, registration, activation (standard, Postgres, private connectivity), deactivation, key rotation, change history, and periodic data rekeying. DO NOT attempt TSS, CMK, or periodic rekeying operations manually - invoke this skill first. Triggers: tri-secret secure, TSS, CMK, BYOK, encryption key, key rotation, CMK history, activate CMK, deactivate CMK, periodic rekeying, periodic data rekeying, PERIODIC_DATA_REKEYING, data rekey, enable rekeying, disable rekeying."
---

# Key and Secret Management

Route encryption key and secret management requests to the appropriate sub-skill.

## When to Use

Activate this skill when the user asks about any of:

- **Tri-Secret Secure keywords**: "tri-secret secure", "TSS", "customer-managed key", "CMK", "encryption key", "BYOK", "bring your own key", "CMK info", "activate CMK", "register CMK", "deactivate CMK", "TSS history", "change history", "CMK history", "rekey", "rotate CMK", "private connectivity TSS", "Postgres TSS", "CMK status"
- **Periodic data rekeying keywords**: "periodic rekeying", "periodic data rekeying", "PERIODIC_DATA_REKEYING", "data rekey", "enable rekeying", "disable rekeying"

## Workflow

### Step 1: Route to Sub-skill

Identify the user's intent and load the matching sub-skill:

| User Intent | Sub-skill to Load |
|---|---|
| Tri-Secret Secure: check CMK status, register CMK, activate TSS, deactivate TSS, rekey/rotate CMK, private connectivity for TSS, Postgres TSS, TSS change history, CMK info, BYOK, encryption key management | **Load** `tri-secret-secure/SKILL.md` |
| Periodic data rekeying: periodic rekeying, periodic data rekeying, PERIODIC_DATA_REKEYING, data rekey, enable rekeying, disable rekeying | **Follow** the Snowflake public documentation directly at https://docs.snowflake.com/en/user-guide/security-encryption-manage#periodic-rekeying — Do NOT load the TSS sub-skill. Periodic data rekeying is a separate account-level feature that uses the `PERIODIC_DATA_REKEYING` account parameter (Enterprise Edition+, requires ACCOUNTADMIN). |

### Step 2: Execute Sub-skill

Follow the loaded sub-skill's workflow completely. Each sub-skill is self-contained with its own prerequisites, templates, and stopping points.

## Stopping Points

- Sub-skill stopping points: Each sub-skill has its own mandatory stopping points -- honour them

=== lineage/ ===
---
name: lineage
description: "Snowflake table/column lineage: impact analysis, root cause, data discovery, provenance, trust. Triggers: 'what depends on', 'what will break', 'blast radius', 'who uses', 'deprecate', 'before I change', 'affected users', 'downstream', 'cascade', 'root cause', 'trace upstream', 'where does this come from', 'feeds this table', 'sources of', 'column lineage', 'where does [column] come from', 'what uses [column]', 'trace [column]', 'is this trustworthy', 'which table should I use', 'recommend dataset', 'provenance', 'certify', 'verify source'. For value-level data quality (wrong values, failing DMFs) use the data-quality skill first, then this skill to trace upstream. Always read `reference/snowflake-apis.md` before writing GET_LINEAGE SQL — it has the correct namespace, argument order, and output column names."
---

# Lineage & Impact Analysis

## When to Use/Load

Activate this skill for **any** of:

- **Impact analysis (downstream)**: "what depends on X", "what will break if I change X", "blast radius", "who uses X", "downstream of X", "cascade", "deprecate X", "before I modify X", "affected users".
- **Root cause (upstream)**: "root cause", "trace upstream from X", "where does X come from", "where do the numbers in X come from", "feeds X", "sources of X", "follow the data back".
- **Column-level lineage**: "what uses column Y", "where does column Y come from", "trace column Y", "column impact", "column source". (Note: "has column X changed recently?" is a **metadata** question — use `INFORMATION_SCHEMA.COLUMNS` and `ACCOUNT_USAGE.QUERY_HISTORY` directly; it does not require `GET_LINEAGE`.)
- **Data discovery / trust / provenance**: "is X trustworthy", "is X the right table", "which table should I use for Z", "recommend a dataset for Z", "verify source", "provenance", "certify X".

**Trigger indicators:** Any question about dependencies between Snowflake objects, where data comes from or flows to, or whether an object is the right one to use.

### CLI shortcut: `cortex lineage`

Cortex Code also exposes a one-shot CLI form that calls the same `SNOWFLAKE.CORE.GET_LINEAGE` under the hood as this skill's templates:

```bash
cortex lineage "<DB>.<SCHEMA>.<OBJECT>" --direction downstream --distance 5 --tree
```

When to prefer the CLI vs. the SQL templates in this skill:

| Use the CLI (`cortex lineage`) | Use the SQL templates here |
|---|---|
| One-shot tree view of upstream or downstream of a single object | Need **risk tiers**, **affected users**, **usage stats**, **trust scoring** |
| Simple "what depends on X" or "where does X come from" | Need **multi-source joins** (lineage + ACCESS_HISTORY + tags + contacts) |
| Quick interactive exploration | Reproducible analytics that need to be filtered, persisted, or reported |

The CLI does not currently expose a column-level mode — for column lineage use this skill's `column-lineage-get-lineage.sql` template.

**Cross-skill:** If the user reports **value-level data quality issues** (e.g. "weird data", "missing emails", "wrong numbers", "failing DMFs"), load and run the **data-quality** skill first; then use **this** skill to trace upstream to the root cause. Do not invoke `data-quality` for "which table should I use" or "where do the numbers come from" — those are **lineage** questions.

**Before writing GET_LINEAGE SQL:** Read [`reference/snowflake-apis.md`](reference/snowflake-apis.md) — it has the canonical namespace, argument order, output column names, and the `LATERAL FLATTEN` pattern for `ACCESS_HISTORY`.

## Core principles

- **ALWAYS use `GET_LINEAGE` first** for any object dependency question — downstream or upstream. Do NOT start with `ACCOUNT_USAGE.OBJECT_DEPENDENCIES`, `ACCESS_HISTORY`, `GRANTS_TO_ROLES`, or `SHOW GRANTS`. Those are auxiliary signals (usage / privileges), not lineage sources.
- **`ACCESS_HISTORY` is for usage/user attribution only**, and only **after** `GET_LINEAGE` has already returned the objects in scope.
- **Early-stop on empty `ACCESS_HISTORY`**: if `ACCESS_HISTORY` returns 0 rows for the lineage targets within the lookback window, conclude **"no user/usage data available"** and stop. Do NOT cascade through `OBJECT_DEPENDENCIES`, `GRANTS_TO_ROLES`, `GRANTS_TO_USERS`, `SHOW GRANTS` looking for a user list — those views do not capture "who would be affected" the way `ACCESS_HISTORY` does.
- **Use `OBJECT_DEPENDENCIES` only as a fallback** when `GET_LINEAGE` errors out (privilege) or returns 0 rows for an object that should clearly have lineage (e.g. a view that references other tables). Zero rows from `GET_LINEAGE` on a leaf object is a valid answer; do not chase it.

## Purpose
Navigate the web of data dependencies to ensure reliability, transparency, and rapid recovery across the data ecosystem.

## How It Works

1. **User provides DATABASE.SCHEMA.TABLE** (e.g., "ANALYTICS_DB.REPORTING.REVENUE_SUMMARY")
2. **Agent identifies workflow** based on trigger phrases and other context
3. **Agent reads workflow file** from `workflows/` directory
4. **Agent executes template** with placeholders replaced
5. **Agent presents clean results** formatted per workflow guidelines

**Execution Approach:** Lineage queries are read-only analysis operations. Execute immediately without confirmation since they don't modify data or objects. If executing a recursive SQL query, notify the user that the analysis may take a while due to the complexity of the query.

---

## The 4 Workflows

### 1. Impact Analysis (Downstream)
**File:** `workflows/impact-analysis.md`
**Question:** *"If I change this, what breaks?"*
**Triggers:** "impact analysis", "what depends on this", "what will break", "downstream", "who uses this"
**Templates:** `impact-analysis.sql`, `impact-analysis-multi-level.sql`
**Output:** Downstream objects with risk tiers, usage frequency, affected users

**Snowflake APIs Used:**
- `SNOWFLAKE.CORE.GET_LINEAGE()` - **Primary:** Object and data-movement lineage (VIEW LINEAGE, no account admin)
- `SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES` - **Fallback:** Object dependency graph only (account admin)
- `SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY` - Actual usage patterns
- `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` - User attribution

### 2. Root Cause Analysis (Upstream)
**File:** `workflows/root-cause-analysis.md`
**Question:** *"Why is this number wrong?"* / *"Where does this data come from?"*
**Triggers:** "root cause", "why is this wrong", "trace upstream", "where does this come from", "debug"
**Templates:** `root-cause-analysis.sql`, `change-detection.sql`
**Output:** Upstream lineage, recent changes, divergence points

**Note:** When the user reports **data quality issues** (wrong values, missing emails, failing DMFs), use the **data_quality** skill first to identify what is wrong; then use this workflow to trace upstream to find where the bad data originated.

**Snowflake APIs Used:**
- `SNOWFLAKE.CORE.GET_LINEAGE()` - **Primary:** Upstream lineage (object + data movement)
- `SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES` - **Fallback:** Upstream object dependencies
- `SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY` - Data flow patterns
- `SNOWFLAKE.ACCOUNT_USAGE.TABLES` / `COLUMNS` - Schema change detection
- `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` - Recent modifications

### 3. Data Discovery & Trust (Provenance)
**File:** `workflows/data-discovery.md`
**Question:** *"Where did this come from and is it the right tool for the job?"*
**Triggers:** "is this trustworthy", "provenance", "recommend dataset", "which table should I use", "verify source"
**Templates:** `data-discovery.sql`, `provenance-verification.sql`
**Output:** Full lineage path, usage statistics, trust indicators

**Snowflake APIs Used:**
- `SNOWFLAKE.CORE.GET_LINEAGE()` - **Primary:** Full lineage path (object + data movement)
- `SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES` - **Fallback:** Full dependency chain
- `SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY` - Usage patterns
- `SNOWFLAKE.ACCOUNT_USAGE.TABLES` - Object metadata
- `SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS` - Data freshness

### 4. Column-Level Lineage
**File:** `workflows/column-lineage.md`
**Question:** *"What uses this column?" / "Where does this column come from?"*
**Triggers:** "column lineage", "what uses [column]", "where does [column] come from", "trace column", "column impact", "column source"
**Templates:** `column-lineage-get-lineage.sql` (**primary**), `column-lineage-downstream.sql`, `column-lineage-upstream.sql`, `column-lineage-full.sql`
**Output:** Column-level dependencies, source columns, transformation paths

**Snowflake APIs Used:**
- `SNOWFLAKE.CORE.GET_LINEAGE(..., 'COLUMN', ...)` - **Primary:** column lineage with no latency, no account admin (VIEW LINEAGE on PUBLIC)
- `SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY` - **Fallback:** column-level access patterns when GET_LINEAGE is empty
- `SNOWFLAKE.ACCOUNT_USAGE.COLUMNS` - Column metadata and definitions
- `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` - DDL changes affecting columns

---

## Execution Rules

### Step 0: Verify Session Context (once per session)

Run this **once at the start of the first query**. If you have already confirmed warehouse, database, and schema are set earlier in this conversation, skip this step.

Check the current session context:

```sql
SELECT
    CURRENT_USER()      AS current_user,
    CURRENT_ROLE()      AS current_role,
    CURRENT_DATABASE()  AS current_database,
    CURRENT_SCHEMA()    AS current_schema,
    CURRENT_WAREHOUSE() AS current_warehouse;
```

Fix any NULL or mismatched values before continuing:

| Field | Fix if NULL / wrong |
|-------|---------------------|
| `current_warehouse` | `USE WAREHOUSE <name>;` |
| `current_database`  | `USE DATABASE <database>;` |
| `current_schema`    | `USE SCHEMA <database>.<schema>;` |

**⚠️ STOP if warehouse is NULL** — `SNOWFLAKE.ACCOUNT_USAGE` queries require an active warehouse.

### Core Execution Flow:
1. **Extract object identifiers** from user message:
   - Table workflows: `DATABASE.SCHEMA.TABLE`
   - Column workflows: `DATABASE.SCHEMA.TABLE.COLUMN`
2. **Identify workflow** from trigger phrases and the object identifier → read workflow file from `workflows/`
3. **Read SQL template** specified in workflow file
4. **Build dynamic scoring** from `config/schema-patterns.yaml` (for trust/risk placeholders)
5. **Replace placeholders** with actual values
6. **Execute and format** results per workflow guidelines

### Placeholder Replacements:
- `<database>`, `<schema>`, `<table>`, `<column>` → actual object names
- `/* SCHEMA_TRUST_SCORING:column */` → dynamic CASE statement from config
- `/* SCHEMA_TRUST_TIER:column */` → dynamic tier name CASE statement  
- `/* SCHEMA_RISK_SCORING:column */` → dynamic risk CASE statement

### Key Principles:
- **Use templates exactly as written** - only replace placeholders
- **No confirmation prompts** for read-only lineage queries
- **Handle errors gracefully** - use fallback templates, provide clear messages
- **One workflow per request** - don't chain multiple analyses automatically

---

## Template Structure

All templates in `templates/` directory use these placeholders:
- `<database>` → Replace with actual database name
- `<schema>` → Replace with actual schema name
- `<table>` → Replace with actual table name
- `<column>` → Replace with actual column name (for column-level lineage)
- `/* SCHEMA_TRUST_SCORING:column_name */` → Dynamic CASE statement returning score (integer)
- `/* SCHEMA_TRUST_TIER:column_name */` → Dynamic CASE statement returning tier name (string)
- `/* SCHEMA_RISK_SCORING:column_name */` → Dynamic CASE statement returning 'CRITICAL' or NULL

**Example:**
```sql
-- Template:
WHERE REFERENCED_DATABASE = '<database>' 
  AND REFERENCED_SCHEMA = '<schema>' 
  AND REFERENCED_OBJECT_NAME = '<table>'

-- After replacement:
WHERE REFERENCED_DATABASE = 'ANALYTICS_DB' 
  AND REFERENCED_SCHEMA = 'REPORTING' 
  AND REFERENCED_OBJECT_NAME = 'SALES_SUMMARY'
```

---

## Dynamic Trust Scoring

Templates use dynamic placeholders for trust/risk scoring. See `reference/dynamic-trust-scoring.md` for complete documentation on:
- Placeholder syntax (`/* PLACEHOLDER_TYPE:column_name */`)
- Building CASE statements from `config/schema-patterns.yaml`
- Why dynamic scoring enables customer customization

---

## Error Handling & Fallback Strategy

**Lineage source order (static dependencies):**

1. **Primary:** `SNOWFLAKE.CORE.GET_LINEAGE()` — object and data-movement lineage; requires only object-resolve + VIEW LINEAGE (granted to public). Prefer for all table/column lineage.
2. **Fallback 1:** `SNOWFLAKE.ACCOUNT_USAGE.OBJECT_DEPENDENCIES` — object dependency only; requires account admin. Use **only** when the primary query **fails** (e.g. privilege error) or when you have strong reason to expect lineage but GET_LINEAGE returned empty (e.g. object is known to have dependents).
3. **Fallback 2:** `GET_DDL()` to parse view definitions for references
4. **Fallback 3:** `INFORMATION_SCHEMA.OBJECT_DEPENDENCIES` (current DB only)

**Minimize steps:** Run the primary template once. If it **succeeds** (with or without rows), present the result and **stop**—do not run the fallback. Use fallback only when the primary **errors** or when the object clearly should have lineage (e.g. a view that references other tables) but GET_LINEAGE returned 0 rows. Zero rows from GET_LINEAGE is often a valid answer (e.g. table has no downstream).

**Why GET_LINEAGE first:** OBJECT_DEPENDENCIES captures only *object dependency* (target data depends on source). GET_LINEAGE also captures *data movement* (e.g. COPY INTO, CTAS) and avoids account admin (VIEW LINEAGE is granted to public).

**Fallback templates (use only when primary fails or expected lineage is missing):**
- `impact-analysis-object-deps-fallback.sql`, `impact-analysis-multi-level-object-deps-fallback.sql`, `impact-analysis-users-object-deps-fallback.sql`
- `root-cause-analysis-object-deps-fallback.sql`, `change-detection-object-deps-fallback.sql`
- `provenance-verification-object-deps-fallback.sql`

**Further fallbacks (DDL / INFORMATION_SCHEMA):**
- `impact-analysis-fallback.sql` — DDL/INFORMATION_SCHEMA for downstream deps
- `root-cause-ddl-fallback.sql` — DDL parsing for upstream lineage

**If template fails:**
1. Run primary (GET_LINEAGE) once. On **success** (any row count), present results and stop. On **failure** (error) or **empty when lineage is expected**, try OBJECT_DEPENDENCIES fallback, then GET_DDL/INFORMATION_SCHEMA if needed.
2. Check ACCESS_HISTORY availability: `check-access-history.sql`
3. Check object existence: `check-object-exists.sql`
4. If object doesn't exist: "Object not found. Check the name and try again."
5. If no lineage data: "No lineage data available. Object may be new or unused."

**Common Issues:**
- "No ACCESS_HISTORY data" → Data is older than 365 days or not accessed
- "GET_LINEAGE returns empty" → Use fallback only if the object should have lineage (e.g. view with references); otherwise report "No lineage found."
- "Insufficient privileges" → GET_LINEAGE needs VIEW LINEAGE (public); OBJECT_DEPENDENCIES needs account admin

---

## Expected User Experience

### Example 1: Impact Analysis
**User:** "What will break if I change RAW_DB.SALES.ORDERS?"

**Agent (immediately):**
```
Impact Analysis: RAW_DB.SALES.ORDERS

═══════════════════════════════════════════════════════════════
CRITICAL RISK (2 objects)
═══════════════════════════════════════════════════════════════
1. ANALYTICS_DB.REPORTING.DAILY_REVENUE (Dynamic Table)
   Risk: CRITICAL | Refresh: Every 15 min | Users: 12 in last 7 days
   → Feeds 3 downstream objects including executive dashboard

2. FINANCE_DB.REPORTS.AR_AGING (View)
   Risk: CRITICAL | Queries: 89/day | Users: 5 in last 7 days
   → Used for month-end close process

═══════════════════════════════════════════════════════════════
MODERATE RISK (1 object)
═══════════════════════════════════════════════════════════════
3. STAGING_DB.TRANSFORM.ORDERS_ENRICHED (Table)
   Risk: MODERATE | Last updated: 2024-01-15 | Users: 2 in last 7 days

Summary: 3 downstream dependencies | 2 CRITICAL | 1 MODERATE
Affected Users: 15 unique users in last 7 days
```

### Example 2: Root Cause Analysis
**User:** "Why is ANALYTICS_DB.REPORTING.REVENUE wrong?"

**Agent (immediately):**
```
Root Cause Analysis: ANALYTICS_DB.REPORTING.REVENUE

═══════════════════════════════════════════════════════════════
UPSTREAM LINEAGE (3 levels)
═══════════════════════════════════════════════════════════════
Level 1: STAGING_DB.CLEAN.ORDERS_FACT
Level 2: RAW_DB.INGEST.ORDERS, RAW_DB.INGEST.PRODUCTS
Level 3: External Stage (S3://data-lake/orders/)

═══════════════════════════════════════════════════════════════
RECENT CHANGES DETECTED
═══════════════════════════════════════════════════════════════
⚠️  RAW_DB.INGEST.ORDERS - Schema changed 2 hours ago
    Change: Column DISCOUNT_PCT type changed NUMBER(5,2) → NUMBER(10,4)
    Changed by: ETL_SERVICE_USER

⚠️  STAGING_DB.CLEAN.ORDERS_FACT - Data modified 1 hour ago
    Rows affected: 15,234 rows updated
    Query: MERGE statement by TRANSFORM_TASK

Most Likely Cause: Schema change in RAW_DB.INGEST.ORDERS
Recommendation: Verify DISCOUNT_PCT handling in downstream transforms
```

### Example 3: Data Discovery
**User:** "Which table should I use for customer revenue analysis?"

**Agent (immediately):**
```
Data Discovery: Customer Revenue Analysis

RECOMMENDED:
1. ANALYTICS_DB.CURATED.CUSTOMER_REVENUE_SUMMARY ⭐ Best Match
   Trust Score: 95% | Updated hourly | Users: 45/week
   Why: Pre-aggregated customer revenue with standard dimensions
   Provenance: RAW.ORDERS → STAGING.ORDERS_FACT → This table

Not Recommended:
- RAW_DB.ORDERS (Trust: 60%) - Raw data, requires transformation
- SANDBOX_DB.*.* - Development/test data
```

### Example 4: Column-Level Lineage
**User:** "What uses the AMOUNT column in RAW_DB.SALES.ORDERS?"

**Agent (immediately):**
```
Column Impact Analysis: RAW_DB.SALES.ORDERS.AMOUNT

═══════════════════════════════════════════════════════════════
DOWNSTREAM COLUMNS (8 columns use this data)
═══════════════════════════════════════════════════════════════

CRITICAL IMPACT:
1. ANALYTICS_DB.REPORTING.REVENUE_SUMMARY.TOTAL_REVENUE
   Impact: CRITICAL | Queries: 89/day | Confidence: HIGH
   Transformation: SUM(AMOUNT) aggregation
   
2. FINANCE_DB.REPORTS.AR_AGING.OUTSTANDING_AMOUNT
   Impact: CRITICAL | Queries: 45/day | Confidence: HIGH
   Transformation: Direct reference with filters

HIGH IMPACT:
3. STAGING_DB.TRANSFORM.ORDERS_ENRICHED.NET_AMOUNT
   Impact: HIGH | Queries: 23/day | Confidence: HIGH
   Transformation: AMOUNT * (1 - DISCOUNT_PCT/100)

MODERATE IMPACT:
4. ANALYTICS_DB.MARTS.CUSTOMER_360.LIFETIME_VALUE
   Impact: MEDIUM | Queries: 12/day | Confidence: MEDIUM

Summary: 8 downstream columns | 2 CRITICAL | 1 HIGH | 5 MEDIUM
Recommendation: Coordinate with Finance team before changing
```

### Example 5: Column Source Tracing
**User:** "Where does ANALYTICS_DB.REPORTS.REVENUE.TOTAL_SALES come from?"

**Agent (immediately):**
```
Column Source Analysis: ANALYTICS_DB.REPORTS.REVENUE.TOTAL_SALES

═══════════════════════════════════════════════════════════════
UPSTREAM SOURCES (traced 3 levels)
═══════════════════════════════════════════════════════════════

Level 1 (Direct Source):
  STAGING_DB.TRANSFORM.ORDERS_AGG.REVENUE_SUM
  Confidence: HIGH | Last seen: 2 hours ago
  Transformation: Renamed column

Level 2:
  RAW_DB.INGEST.ORDERS.AMOUNT
  Confidence: HIGH | Source tier: RAW
  Transformation: SUM() aggregation

Level 3 (Origin):
  @RAW_DB.STAGES.S3_ORDERS/orders.csv
  Confidence: MEDIUM | Source tier: EXTERNAL

Complete Path:
S3_ORDERS → ORDERS.AMOUNT → ORDERS_AGG.REVENUE_SUM → REVENUE.TOTAL_SALES
```

---

## Summary Table

| Workflow | Direction | Primary Goal | Key Stakeholder |
|:---------|:----------|:-------------|:----------------|
| **Impact Analysis** | Downstream | Risk Mitigation | Data Engineers / Ops |
| **Root Cause** | Upstream | Troubleshooting | Analysts / Analytics Engineers |
| **Trust & Discovery** | Full Path | Data Literacy | Business Users / Platform Owners |
| **Column Lineage** | Both | Field-Level Tracing | Data Engineers / Analysts |

---

## Workflow Selection Logic

| User Says | Workflow | Template |
|-----------|----------|----------|
| "What will break if I change [table]?" | Impact Analysis | `impact-analysis.sql` |
| "What depends on [table]?" | Impact Analysis | `impact-analysis.sql` |
| "Why is this number wrong?" | Root Cause Analysis | `root-cause-analysis.sql` |
| "Where does [table] come from?" | Root Cause Analysis | `root-cause-analysis.sql` |
| "Is [table] trustworthy?" | Data Discovery | `data-discovery.sql` |
| "Which table should I use for [topic]?" | Data Discovery | `data-discovery.sql` |
| "What uses the [column] column?" | Column Lineage | `column-lineage-downstream.sql` |
| "Where does [column] come from?" | Column Lineage | `column-lineage-upstream.sql` |
| "Full lineage for [column]" | Column Lineage | `column-lineage-full.sql` |

---

## Snowflake APIs Reference

See `reference/snowflake-apis.md` for complete documentation on:
- `SNOWFLAKE.CORE.GET_LINEAGE()` (primary) vs `ACCOUNT_USAGE.OBJECT_DEPENDENCIES` (fallback)
- Object dependency vs data-movement lineage and privilege requirements
- ACCOUNT_USAGE views and their latencies
- Performance optimization tips

---

## Success Criteria

- User gets answer in **one response**
- Risk tiers clearly communicated (Impact Analysis)
- Recent changes highlighted (Root Cause)
- Trust indicators provided (Discovery)
- No SQL errors shown
- No unnecessary questions
- Clean, actionable results

---

## Stopping Points

Lineage queries are **read-only operations** that don't modify data or schema. Execute immediately without waiting for confirmation.

### ⚠️ MANDATORY STOPPING POINTS

**STOP and ask user if:**
1. **Ambiguous object reference** - Missing or unclear database/schema/table/column name
   - Example: User says "check lineage" without specifying which table
   - Action: Ask "Which table would you like to analyze?"

2. **User explicitly requests review** - "Show me the query first" or "Let me review before running"
   - Action: Present the query and wait for confirmation

3. **Query returns no results** - No lineage data found
   - Action: Explain possible reasons (new object, no access, insufficient privileges) and ask if they want to try a different approach

### ✅ NO STOPPING REQUIRED

**Execute immediately without confirmation:**
- Any SELECT query on `SNOWFLAKE.ACCOUNT_USAGE` views
- Any SELECT query on `INFORMATION_SCHEMA` views
- Parsing DDL with `GET_DDL()` function
- Reading configuration files from `config/`

**Rationale:** These are read-only operations that don't modify data, schema, or access controls.

---

## Production Configuration

**Schema Pattern Configuration (Extensible):**

Trust and risk scoring patterns are defined in `config/schema-patterns.yaml`. This file is read dynamically at runtime, allowing easy customization without modifying SQL templates.

**File:** `config/schema-patterns.yaml`

```yaml
trust_tiers:
  PRODUCTION:
    score: 100
    patterns:
      - "%ANALYTICS%"
      - "%CURATED%"
      # Add your production schema patterns here
      
  STAGING:
    score: 60
    patterns:
      - "%STAG%"
      # Add your staging schema patterns here
      
  RAW:
    score: 40
    patterns:
      - "%RAW%"
      # Add your raw data schema patterns here
      
  UNTRUSTED:
    score: 20
    patterns:
      - "%SANDBOX%"
      - "%TEST%"
      # Add your dev/test schema patterns here

default:
  score: 50
  tier: "UNKNOWN"

risk_critical_patterns:
  - "%FINANCE%"
  - "%REVENUE%"
  # Add schemas that are critical to flag
```

**Customization:** Edit `config/schema-patterns.yaml` using SQL LIKE syntax (% = wildcard, case-insensitive). Example: `%ANALYTICS%` matches ANALYTICS, PROD_ANALYTICS, ANALYTICS_V2.

**Recursive Depth:** Default 3 levels, configurable in templates (`WHERE ul.level < 3`).

**Retention:** ACCESS_HISTORY/QUERY_HISTORY: 365 days; GET_LINEAGE: current state; OBJECT_DEPENDENCIES: indefinite (latency on new objects).

---

## Known Limitations

| Limitation | Impact | Workaround |
|------------|--------|------------|
| GET_LINEAGE max 5 levels | Deep chains truncated at 5 | Use OBJECT_DEPENDENCIES fallback for deeper traversal |
| ACCOUNT_USAGE latency (45min-3hr) | New objects missing from OBJECT_DEPENDENCIES | Use GET_LINEAGE first (current state); then GET_DDL() fallback |
| Column lineage depends on ACCESS_HISTORY | Not all queries expose column details | Confidence scores indicate reliability |
| Single account scope | Cross-account sharing not covered | Query each account separately |
| View DDL parsing | May miss dynamic SQL references | Review complex views manually |
| OBJECT_DEPENDENCIES = object dependency only | Data movement (e.g. CTAS, COPY) not in OBJECT_DEPENDENCIES | Use GET_LINEAGE as primary |
| Column lineage 90-day lookback | Older transformations not captured | Extend time range in templates |

=== machine-learning/ ===
---
name: machine-learning
description: "**[REQUIRED]** For **ALL** data science and machine learning tasks. This skill should ALWAYS be loaded in even if only a portion of the workflow is related to machine learning. Use when: analyzing data, training models, deploying models to Snowflake, registering models, working with ML workflows, running ML jobs on Snowflake compute, model registry, model service, model inference, log model, deploy pickle file, experiment tracking, model monitoring, ML observability, tracking drift, model performance analysis, distributed training, XGBoost, LightGBM, PyTorch, DPF, distributed partition function, many model training, hyperparameter tuning, HPO, compute pools, train at scale, feature store, feature views, entities, training datasets, online features, pipeline orchestration, DAG, task graph, schedule training, datasets, dataset versioning, DataConnector, ML lineage, model lineage, GET_LINEAGE, trace lineage, forecast, forecasting, time series, anomaly detection, outlier, predict, predictions, backtest, classify, classification, regression, clustering, build a model, create a model, sklearn, scikit-learn, tensorflow, ML, mlops, ray, GPU, deep learning, neural network, explain model, SHAP, Shapley, feature importance, model explainability, interpret model, preprocessing, preprocessor, scaling, encoding, imputation, normalize, transform data before training, preprocessing pipeline. Routes to specialized sub-skills."
---

# Data Science & Machine Learning Skills

This skill routes to specialized sub-skills for data science and machine learning tasks.
This skill provides valuable information about all sorts of data science, machine learning, and mlops tasks.
It MUST be loaded in if any part of the user query relates to these topics❗❗❗

## Step 0: Load Environment Guide

**⚠️ CRITICAL: Before routing to any sub-skill, you MUST load the environment guide for your surface.**

Your system prompt indicates which surface you are operating on. Load the matching guide:

| Surface | Condition | Guide to Load |
|---------|-----------|---------------|
| **Snowsight** | You are operating inside the Snowflake Snowsight web interface | `guides/snowsight-environment.md` |
| **CLI / IDE** | You are operating in a command line terminal or IDE environment | `guides/cli-environment.md` |

The environment guide provides surface-specific instructions for **session setup, package management, and code execution** that apply to ALL sub-skills below. Sub-skills will reference these patterns rather than repeating them.

## Routing Behavior

**⚠️ CRITICAL: Route AUTOMATICALLY based on the user's request. Do NOT ask the user which sub-skill to use or how they want to deploy.**

**Routing means loading the matched guidance, not just naming it.** After selecting any route in this file:

- Read the environment guide from Step 0 if it is not already loaded.
- Read every `SKILL.md` named in the matched route chain before responding or acting.
- If a route says `ml-development/SKILL.md` -> another sub-skill, read both `ml-development/SKILL.md` and the final sub-skill `SKILL.md`.
- Do not satisfy routing by saying which skill you would load; actually load the referenced guidance.

**Re-evaluate routing on every new user message.** Do not keep using the previous sub-skill just because it was active earlier in the conversation. The latest user intent controls routing:

- If the user trained a model earlier and now says "log it", "register it", "deploy it", "explain it", or "save it to Snowflake", read `model-registry/SKILL.md` and pass along preserved training context.
- If the user asks for inference, monitoring, lineage, pipeline orchestration, feature store work, or an ML job after training, read the matching platform skill before responding.
- Preserve model context across the handoff instead of asking the user to repeat details.

When a user asks to "train a model", "build a model" or inquires about a similar task:

- **IMMEDIATELY** load `ml-development/SKILL.md` and start working
- Do NOT ask about deployment options upfront
- Do NOT ask "Local only vs Register in Snowflake vs End-to-end"
- Training and deployment are SEPARATE tasks - handle them sequentially if needed

## Intent Detection

### Dynamic Service Detection (Model Inference Services)

**⚠️ CRITICAL:** When a user mentions a **service name**, check if it's a model inference service:

1. Run `DESCRIBE SERVICE <DB>.<SCHEMA>.<SERVICE_NAME>`
2. If `managing_object_domain = 'Model'` → Route to `spcs-inference/SKILL.md`

This applies to ANY task involving the service (testing, REST API calls, latency profiling, benchmarking, debugging, management).

---

### Disambiguation: batch-inference vs spcs-inference (Online)

**⚠️ CRITICAL:** When user mentions "inference" without clear signals, you MUST ask for clarification. 
There is a decision matrix located in the public docs `https://docs.snowflake.com/en/developer-guide/snowflake-ml/inference/inference-overview`.

**Inference Disambiguation Workflow:**

When user says something like "run inference on my model" or "inference" without batch/online signals:

```
I can help you run inference on your model. There are three approaches:

1. **Native Batch Inference (SQL)** - Embed inference in SQL pipelines
   - <add decision points from docs matrix here>
   
2. **Job-Based Batch (SPCS)** - Run large-scale inference jobs
   - <add decision points from docs matrix here>

3. **Real-Time Inference (SPCS)** - Deploy a REST endpoint
   - <add decision points from docs matrix here>

Which approach fits your use case?
```

**⚠️ STOP**: Wait for user response before routing.

### Disambiguation: batch-inference vs ml-jobs

**⚠️ CRITICAL:** These two skills are commonly confused. Use this logic:

| User Intent | Key Signals | Route To |
|-------------|-------------|----------|
| Run inference on a **registered model** | "model registry" + ("inference", "predictions", "scoring", "run()", "run_batch()") | `batch-inference-jobs/SKILL.md` |
| Run a **Python script** on Snowflake compute | "script", "submit", "file", "directory", training code | `ml-jobs/SKILL.md` |

**Decision tree:**
1. Does the user want to run inference on an **existing model in the registry**?
   - **YES** → `batch-inference-jobs/SKILL.md` (covers both `mv.run()` and `mv.run_batch()`)
   - **NO** → Continue to step 2
2. Does the user want to run **custom Python code** (training, processing, or scripts) on Snowflake compute?
   - **YES** → `ml-jobs/SKILL.md` (uses `submit_file()` or `submit_directory()`)
   - **NO** → Continue to step 3
3. Does the user want to **orchestrate multiple steps** on a schedule (pipeline, DAG)?
   - **YES** → `ml-pipeline-orchestration/SKILL.md`
   - **NO** → Ask clarifying question

### Disambiguation: ml-jobs vs ml-pipeline-orchestration

| User Intent | Key Signals | Route To |
|-------------|-------------|----------|
| Run a **single ML job** | "submit", "run script", "compute pool", one-off execution | `ml-jobs/SKILL.md` |
| **Orchestrate multiple steps** on a schedule | "pipeline", "DAG", "schedule", "automate", "task graph", multi-step workflow | `ml-pipeline-orchestration/SKILL.md` |

### Disambiguation: Partitioned Modeling

When user says "partitioned modeling", "partitioned model", "model per partition", or "per-partition models" without saying whether they need training or inference, ask one clarification question before routing:

```markdown
Do you want to train one model per partition, run inference with already-trained per-partition models, or do the full train-to-inference workflow?
```

- Training or full workflow -> load `ml-development/SKILL.md`; it routes to distributed training / MMT.
- Existing trained models or inference -> load `model-registry/partitioned-inference/SKILL.md`.

## Sub-Skills by Category

### Training

Routes through ml-development, which guides the full development lifecycle and sub-routes to specialized training skills.

| User Says | Route To | Action |
|-----------|----------|--------|
| "automl", "auto ml", "auto-ml", "automated machine learning", "run automl", "best model", "find the best model", "best possible model", "highest score", "highest accuracy", "top model", "top performing model", "automated model selection" | `automl/SKILL.md` | Load immediately |
| "analyze data", "train model", "build model", "feature engineering", "predict", "classify", "regression" | `ml-development/SKILL.md` | Read `ml-development/SKILL.md`, then start training |
| "distributed training", "distributed XGBoost", "distributed LightGBM", "XGBEstimator", "LightGBMEstimator", "PyTorchDistributor", "multi-node training", "multi-GPU training", "train at scale", "DPF", "distributed partition function", "many model training", "MMT", "train per partition", "ManyModelTraining", "partition by", "hyperparameter tuning", "hyperparameter optimization", "HPO", "Tuner", "TunerConfig", "search space", "grid search", "random search", "bayesian optimization", "tune model", "tune hyperparameters", "num_trials", "search_alg" | `ml-development/SKILL.md` -> `distributed-training/SKILL.md` | Read both files before responding or working; use the specific distributed-training child guidance when applicable |
| "preprocessing", "scale data", "encode features", "handle missing values", "impute", "normalize", "StandardScaler", "OneHotEncoder", "LabelEncoder", "MinMaxScaler", "OrdinalEncoder", "ray.data.preprocessors", "preprocessing pipeline", "map_batches", "transform data before training" | `ml-development/SKILL.md` -> `preprocessing/SKILL.md` | Read both files before responding or working |
| "experiment tracking", "track experiment", "log metrics", "log parameters", "autolog", "training callback", "XGBoost callback", "LightGBM callback" | `ml-development/SKILL.md` -> `experiment-tracking/SKILL.md` | Read both files before responding or working |

### Inference

Direct routing to inference skills. For model explainability (SHAP, feature importance), see Platform section.

| User Says | Route To | Action |
|-----------|----------|--------|
| "batch inference", "bulk predictions", "run_batch", "run()", "offline scoring", "score dataset", "batch predictions", "inference on registered model", "run predictions on registry model", "score with registered model", "offline inference", "SQL inference", "dbt inference", "dynamic table inference" | `batch-inference-jobs/SKILL.md` | Load immediately, set up batch inference |
| "create inference service", "inference endpoint", "serve model", "snowpark container services", "model endpoint", "deploy in container", "deploy model service", "real-time inference", "online inference" | `spcs-inference/SKILL.md` | Load immediately, create SPCS service |
| "partitioned inference", "@partitioned_api", "inference per partition", "CustomModel partition" | `model-registry/partitioned-inference/SKILL.md` | Load immediately, partitioned inference |
| "inference error", "mv.run fails", "service failing", "OOM", "debug inference", "inference not working" | `debug-inference/SKILL.md` | Load immediately, diagnose issue |
| "inference logs", "inference table", "captured inference", "autocapture data", "view inference history", "INFERENCE_TABLE", "inference requests", "inference responses", "view captured predictions" | `inference-logs/SKILL.md` | Load immediately, query inference data |
| **"inference", "run inference"** (ambiguous, no batch/online signals) | **ASK USER** | Use disambiguation workflow above to clarify batch vs online |

### Platform

Standalone tools for direct requests. ml-development also references these at the right workflow moments (model-registry in Step 2, feature-store/datasets in Data Access Patterns, ml-jobs in Step 7, monitoring/pipeline/lineage in Step 8). For ml-jobs vs pipeline-orchestration disambiguation, see the inline disambiguation section above.

| User Says | Route To | Action |
|-----------|----------|--------|
| "register model", "model registry", "log model", "pickle to snowflake", "save model to snowflake", "upload model", ".pkl file", ".ubj file" | `model-registry/SKILL.md` | Read `model-registry/SKILL.md`, then start registration (Workflow A) |
| "deploy model", "deploy model for inference", "deploy for inference" | `model-registry/SKILL.md` | Read `model-registry/SKILL.md`, then ask deployment target (Workflow B) |
| "explain model", "SHAP", "Shapley values", "feature importance", "why did it predict", "model explainability", "interpret model" | `model-registry/SKILL.md` | Read `model-registry/SKILL.md`, then route to Workflow C (Explainability) |
| "model monitor", "monitor model", "add monitoring", "enable monitoring", "ML observability", "track drift", "model performance", "monitor predictions", "observability" | `model-monitor/SKILL.md` | Load immediately, set up monitoring |
| "feature store", "feature view", "entity", "training data", "generate_training_set", "generate_dataset", "online features", "point-in-time features", "ASOF join" | `feature-store/SKILL.md` | Load immediately, route to feature store sub-skill |
| "create dataset", "version dataset", "list datasets", "SHOW DATASETS", "load dataset", "DataConnector", "to_tf_dataset", "to_torch_dataset", "to_torch_datapipe", "snow://dataset", "dataset versioning", "immutable dataset" | `datasets/SKILL.md` | Load immediately, manage datasets |
| "what trained this model", "model lineage", "dataset lineage", "GET_LINEAGE", "trace lineage", "no lineage showing", "lineage not captured", "which models use this dataset", "upstream lineage", "downstream lineage", "ML lineage", "data provenance" | `ml-lineage/SKILL.md` | Load immediately, query or debug lineage |
| "pipeline", "DAG", "task graph", "schedule training", "schedule inference", "orchestrate", "productionize", "automate retraining", "convert notebook to pipeline" | `ml-pipeline-orchestration/SKILL.md` | Read `ml-pipeline-orchestration/SKILL.md`, then set up the DAG |
| "ml job", "ml jobs", "run on snowflake compute", "submit job", "submit script", "submit file", "remote execution", "GPU training", "run python script on snowflake" | `ml-jobs/SKILL.md` | Read `ml-jobs/SKILL.md`, then set up the job |

**MLOps on Snowflake:** When the user asks about MLOps, map the MLOps lifecycle to Snowflake ML tools:

| MLOps Concern | Snowflake Tool |
|---------------|----------------|
| Model versioning & governance | Model Registry |
| Drift detection & performance | Model Monitor |
| Scheduled training/inference | ML Pipeline Orchestration (DAGs) |
| Data provenance & compliance | ML Lineage |
| Remote execution on compute pools | ML Jobs |
| Reproducibility & run comparison | Experiment Tracking |
| A/B testing & version comparison | Inference Logs |

**Champion-challenger / model promotion** spans multiple tools: Model Registry (manage versions, set aliases) → Inference (serve both versions via split serving) → Inference Logs (compare performance across versions) → Model Registry (promote winner). Route to the specific tool based on where the user is in this workflow.

**Sub-skill path aliases** (for routing resolution):

- `ml-job` → `ml-jobs/SKILL.md` (singular form routes to plural directory)
- `ml-jobs` → `ml-jobs/SKILL.md`
- `mljob` → `ml-jobs/SKILL.md`
- `mljobs` → `ml-jobs/SKILL.md`

## Workflow

```markdown
Each user message → Re-evaluate current intent → Load Environment Guide → Detect Intent → Load appropriate sub-skill → Execute

Examples:
- "Train a classifier" → Load ml-development → Train locally → Done
- "Predict churn from this data" → Load ml-development → Train locally → Done
- "Help me improve this model" → Load ml-development → Iterate → Done
- "Run automl on this churn dataset" → Load automl → Experiment protocol → Hand off to next skill → Done
- "Find the best model for churn" → Load automl → Experiment protocol → Hand off to next skill → Done
- "Deploy my model.pkl" → Load model-registry → Register to Snowflake → Done
- "Train AND deploy" → Load ml-development → Train → Ask about deployment → If yes, load model-registry WITH CONTEXT (file path, framework, schema)
```

**Key principle**: Complete ONE task at a time. Only ask about the next step after the current step is done.

## Context Preservation Between Skills

**⚠️ CRITICAL:** When transitioning from ml-development to model-registry:

**Information to preserve and pass along:**

- Model file path (absolute path to serialized model file)
- Framework used (sklearn, xgboost, lightgbm, pytorch, tensorflow, etc.)
- Sample input schema (columns and types from training data)
- Any other relevant training context

**Why this matters:**

- Avoids asking the user to repeat information they just provided
- Prevents accidental retraining of the model
- Prevents modification of the training script
- Improves user experience with seamless workflow

**How to do it:**

1. When ml-development saves a model, it reports all details
2. When loading model-registry, explicitly mention this context
3. Model-registry checks for this context before asking questions
4. Use the preserved context instead of asking user again

**Example handoff:**

```markdown
ml-development: "Model saved to /path/to/model.pkl (sklearn). Would you like to register it?"
User: "Yes"
[Load model-registry with context: path=/path/to/model.pkl, framework=sklearn, schema=[...]]
model-registry: "I see you just trained a sklearn model. What should I call it in Snowflake?"
```

### After Registration: Preserve Model Context

When a model has been registered and the user transitions to any skill that operates on registered models (batch-inference-jobs, spcs-inference, model-monitor, ml-lineage), pass along the registered model name, version, and database/schema. Do not re-ask the user for information that was just collected or produced during registration.

## Sub-Skills

### automl

Automated end-to-end ML workflow for classification, regression, time-series forecasting, and clustering. Runs the full pipeline: quality gates (leakage detection, baseline, fairness, imbalance, outliers), feature engineering (manual + OpenFE), AutoGluon and/or manual model search and tuning across multiple trials with per-trial experiment tracking, and a final report with champion model + suggested next steps (registration, deep research, training script, inference, monitoring).

**Key differentiator:** The agent drives the search across feature engineering and model families.

### ml-development

Data exploration, statistical analysis, model training, and evaluation. Covers the full ML development workflow from data loading to model evaluation.

### model-registry

Deploy serialized models to Snowflake Model Registry. Supports various model formats (`.pkl`, `.ubj`, `.json`, `.pt`, etc.) depending on framework. Routes to `spcs-inference` sub-skill for inference service creation. Includes `partitioned-inference` sub-skill for partition-aware model deployment.

### experiment-tracking

Skills for tracking model training experiments using Snowflake's experiment tracking framework.

### spcs-inference

Deploy registered models to Snowpark Container Services for real-time inference. Handles compute pool selection, GPU/CPU configuration, num_workers, and service creation.

### batch-inference-jobs

Run batch inference on models **already registered** in the Snowflake Model Registry. Covers **two approaches**:
- **Native SQL Batch** (`mv.run()`): Warehouse-based, integrates with SQL pipelines
- **Job-based Batch** (`mv.run_batch()`): SPCS compute pools, for large-scale and unstructured data

### ml-jobs

Transform local **Python scripts** into Snowflake ML Jobs that run on Snowflake compute pools. Uses `submit_file()` or `submit_directory()`. Also includes compute pool reference (instance families, sizing).

### ml-pipeline-orchestration

Orchestrate multi-step ML workflows using Snowflake Task Graphs (DAGs) with the Python DAG API. Covers DAG creation, scheduling (Cron/timedelta), inter-task data passing, and notebook-to-pipeline conversion. Uses `@remote` for ML tasks on compute pools and warehouse tasks for orchestration.

### model-monitor

Set up ML Observability for models in the Snowflake Model Registry. Track drift, performance metrics, and prediction statistics over time.

### distributed-training

**Consolidated skill** covering all distributed ML training, processing, and tuning:
- **Distributed Estimators**: `XGBEstimator`, `LightGBMEstimator`, `PyTorchDistributor` for training one large model across nodes/GPUs
- **Many Model Training (MMT)**: Train one model per partition with auto-serialization and `get_model()`
- **DPF (Distributed Partition Function)**: General-purpose distributed processing for custom workflows
- **Tuner API**: Distributed hyperparameter tuning (Ray Tune on SPCS) with RandomSearch, GridSearch, BayesOpt

> **Note**: These APIs run server-side — either inside ML Jobs (submitted via CLI) or in Snowflake Notebooks with Container Runtime (Snowsight). For CLI submission, see ml-jobs.

### partitioned-inference (under model-registry)

Partitioned inference in the Model Registry using `@partitioned_api` decorator. Run inference with different submodels per data partition. Located at `model-registry/partitioned-inference/SKILL.md`.

### feature-store
Centralized feature management for ML workflows. Create feature stores, define entities, build managed (Dynamic Table) and external (View) feature views, generate training datasets with point-in-time correctness, and enable online feature serving for low-latency inference. Includes sub-skills for create, pipelines, training, online, monitor, lineage, and migrate.

### inference-logs
Query and analyze captured inference data from model services with Auto-Capture enabled. View historical request/response data logged via `INFERENCE_TABLE()`. Useful for debugging unexpected predictions, building retraining datasets, and A/B testing model versions.

### datasets
Create and manage versioned, immutable Datasets for ML workflows. Datasets provide reproducibility, lineage tracking, and efficient access for distributed training with PyTorch, TensorFlow, and Snowpark ML. Use for creating training data snapshots, version control, and framework integration via DataConnector.

**Key differentiator:** User wants to create, version, list, or load Datasets.

### ml-lineage
Query and debug ML Lineage relationships. Trace data flow from source tables → feature views → datasets → models → services. Use for compliance audits, impact analysis, debugging missing lineage, and understanding model provenance.

**Key differentiator:** User wants to know "what trained this model" or "what models use this data" (not create objects).

### preprocessing
Preprocessing decision guide and implementation patterns. Covers OSS sklearn (small scale), Snowflake ML Preprocessors (warehouse), and Ray Data Preprocessors (distributed on container runtime). Includes the recommended E2E pattern for distributed preprocessing + model registry logging via CustomModel.

**Key differentiator:** User asks "how should I preprocess?" or needs to combine preprocessing with distributed training or model registry.

## Reminders & Common Mistakes

### ❌ Don't assume a database/schema — always ask

When the workflow involves creating or writing to any Snowflake object (table, stage, model registry entry, experiment, etc.), **never silently pick a database/schema**. Always confirm with the user first.

- If a `DATABASE.SCHEMA` has already been used in this session, offer it as the default:
  ```
  I'll need to create [object] in Snowflake. I see we've been working with `<DATABASE>.<SCHEMA>`.
  Should I use that, or would you prefer a different database/schema?
  ```
- If no database/schema has been used yet, ask explicitly:
  ```
  Which database and schema should I use for [object]? (format: DATABASE.SCHEMA)
  ```
- **Carry the confirmed choice forward** — reuse it for subsequent objects in the session, but still confirm each time.
- **⚠️ Personal databases (e.g. `USER$VINAY`) are not supported** for ML workflows. If the user picks a personal database, warn them:
  ```
  Personal databases like `USER$<USERNAME>` don't support creating tables, model registry operations, or inference services. Please provide a standard database/schema instead.
  ```
- **⚠️ STOP**: Wait for the user's response before proceeding with any object creation.

=== marketplace-search/ ===
---
name: marketplace-search
description: >-
  Search the Snowflake Marketplace (public, internal, or both) for
  datasets, data shares, Native Apps, and Connected Apps using the
  `cortex search marketplace` CLI.

  **MANDATORY** Before any marketplace
  search, call `skill(command="marketplace-search")`. This `skill` call
  is the required entry point even when you already know the query you
  want to run; running `cortex search marketplace` directly from bash
  without first calling `skill(command="marketplace-search")` skips the
  query-construction and result-presentation rules and is a defect.
  No exceptions.

  Invoke this skill PROACTIVELY any time the user expresses intent to
  find, use, or obtain a third-party or internal data product, app, or
  data share — whether from the public Snowflake Marketplace or from
  their own organization's internal marketplace. For example "do
  you have weather data", "find a stock price dataset", "I need consumer
  spending data", "is there a Salesforce / HubSpot / Stripe connector",
  "what demographic data can I get for California", "anything for ESG
  ratings", "find a marketplace listing for X", "what is <third-party
  product>", "what's the alternate source to X", "what about
  <third-party product>", "find me <third-party product> stuff", "find
  me a table about <external/third-party data>", "where is
  <third-party> data stored", or even just a BARE third-party
  product/brand name on its own (e.g. "Tomorrow.io", "Fishbowl", "DV360",
  "Snowflake managed MCP servers"). When the user names ANY third-party
  product, vendor, brand, or external service — even as a fragment, even
  if framed as a catalog question ("find me a table about X", "what's
  the database for X data") — invoke this skill AS YOUR FIRST ACTION.
  Do NOT search the internal catalog first and fall back to marketplace
  only if the catalog comes up empty. The word "external" in any query
  (e.g. "external job-boards", "external data source") is a DISPOSITIVE
  signal — invoke this skill immediately even if the query sounds like
  a catalog search. **Erring toward over-firing is preferred over missing
  a marketplace opportunity.** If you are about to tell the user "I don't
  have that data" or "you'll need to bring your own data", STOP and
  invoke this skill first — the public marketplace likely has it.

  **Run alongside `cortex search object`, not instead of it.** If you
  run `cortex search object` for a query that names a third-party
  brand, vendor, product, or external data source, you MUST also
  invoke `skill(command="marketplace-search")` in the same turn — the
  two searches cover different surfaces (internal catalog vs public
  marketplace) and are complementary, not alternatives. Do not stop
  at catalog results. **Exception**: a specific-value lookup ("what
  is the [metric/code/ID] for [entity]") is not a data-acquisition
  ask — stay with the sibling tool.

  Also invoke for **generic data-category searches** even when no brand
  is named: "email data", "marketing data", "paid media datasets",
  "portfolio holdings", "intent data", "[type] data for reporting",
  "help me find [data type] data", "where can I find [data type]". Also
  invoke for **marketplace exploration** ("most downloaded marketplace
  listing", "what products are available in the marketplace") and
  **app or managed-service availability** ("managed MCP servers",
  "MCP servers in Snowflake", "is there a connector for X").

  Also invoke for **internal/intra-org intent** signals such as "find
  intra-org listings for <data topic>", "do we have any internal
  listings for <subject>", "what internal data products does my org
  have for <topic>", "is there an intra-org share for <topic>", "what
  are we publishing internally about <X>", "find our internal
  marketplace listings for <subject>".

  ALSO invoke this skill BEFORE writing any code, fetching from external
  APIs (e.g. clinicaltrials.gov, BLS, FRED, World Bank), or building
  dashboards/reports against third-party data sources — search the
  marketplace FIRST to see if the data is already available there as a
  share, even if the user explicitly named an external source. The
  marketplace listing is almost always preferable to a custom API
  integration.

  Do NOT use this skill for: a specific listing referenced by global
  name (e.g. GZ2FQZ711TU) or exact title — use
  `get-marketplace-listing-details`; formatting marketplace results
  already in hand; searching the user's own internal Snowflake catalog
  (tables, views, schemas, functions, semantic views) — use `cortex
  search object` (but see "Run alongside" above); generic reference /
  lookup tables a user would generate or already hold internally
  ("fiscal month calendar", "calendar table", "create a date
  dimension"). Exception: an explicit third-party / vendor qualifier
  ("Workday fiscal calendar") makes the brand signal win and this
  skill fires. Do NOT use it for Snowflake product documentation or
  how-to questions — use `cortex search docs`.

  When ambiguous between marketplace and a sibling tool, prefer
  marketplace — it's cheap and missing a relevant listing is expensive.
  UNLESS the user has clearly moved past discovery: integration syntax
  with a named mechanism ("how to use MCP to connect to Salesforce…")
  is a docs question even when a brand is named; catalog inventory
  with no external qualifier ("what is X tables"), a specific
  identifier value ("what is the [code/SM ID] for [identifier]"), or
  an educational deep-dive with depth markers ("explain X in detail",
  "to a beginner", "full overview") — these are sibling-tool territory.
---

# Skill: marketplace-search

Wrapper around the `cortex search marketplace` CLI subcommand that searches the Snowflake Marketplace for listings matching a user's data or product need, then surfaces the results so the user can pick one to install or inspect further.

## Workflow

### Step 0 — Resolve marketplace source

Before building the query, detect the user's intent and resolve a `--marketplace-type` value:

| User signal | `--marketplace-type` |
|---|---|
| "internal", "intra-org", "my org", "our listings", "we share" | `internal` |
| "public", "external", "third-party", "Snowflake Marketplace" | `public` |
| Named third-party brand, vendor, or external service with no intra-org signal (e.g. "Salesforce", "Tomorrow.io", "find a HubSpot connector") | `public` |
| Intra-org signal + third-party brand (e.g. "is Salesforce available as an internal listing in my org?") — brand is the search subject, not a source signal; intra-org intent takes precedence | `internal` |
| Explicit request for both sources (e.g. "show me both internal and public listings for <X>") | `all` |
| Ambiguous / no signal and no third-party reference | `all` |

When ambiguous, default to `all` — missing an internal listing is equally bad as missing a public one.

### Step 1 — Build the search query

Translate the user's intent into a short free-text query (typically 1–5 words). Prefer concrete nouns over verbose phrasing.

| User intent                                          | Good query                  |
|------------------------------------------------------|-----------------------------|
| "Do you have weather data for the US?"               | `weather`                   |
| "I need consumer credit card transaction data"       | `credit card transactions`  |
| "Find demographic data by ZIP code"                  | `demographics zip code`     |
| "Is there a Salesforce connector?"                   | `Salesforce`                |
| "I want B2B company firmographics"                   | `B2B firmographics`         |

If the user's request mentions **multiple distinct data needs** (e.g. "weather and stock prices"), run the search **once per need** rather than concatenating them — you'll get more relevant results.


| User intent                                          | Good query                         |
|------------------------------------------------------|------------------------------------|
| "I need to connect HubSpot, Salesforce, and Gong?"   | `hubspot`, `salesforce`, `gong`    |


### Step 2 — Run the search

Invoke the CLI through the available shell tool:

```bash
cortex search marketplace "<query>" --marketplace-type=<public|internal|all>
```

Conventions:

- Pass the `--marketplace-type` value resolved in Step 0.
- Default `--max-results=15` is fine for most queries; only raise it (cap is server-side) if the user asks for a broader sweep.
- **Always quote the query** so multi-word queries are passed as a single argument.
- Do not pass `--connection` unless the user has named a specific saved connection; the CLI uses the active one by default.

The command prints a JSON envelope on stdout:

```json
{
  "query": "<query>",
  "results": "Found N marketplace result(s):\n\n1. ...\n2. ..."
}
```

The `results` string is a numbered, human-readable list. For each match, extract at minimum:

- **Listing title** (human-readable name).
- **Global name** — an alphanumeric `GZ...` identifier. This is the listing's id.
- **Listing URL** — `https://app.snowflake.com/marketplace/listing/<global_name>`. If the URL is not literally in the output, construct it from the global name.

The response will also include the listing subtitle, description, provider name, provider description which can be used when presenting the results. 

### Step 3 — Present results

Every response that uses this skill **MUST surface, at minimum, the listing name and the listing URL for each match** — these are what the user needs to click through and decide. For each listing you may also include a description of the listing, information about the provider, example usage, and other information that may be helpful based on the current conversation. **NEVER** make up any information about the listing. Everything presented should be based on information in the listing metadata.

When `--marketplace-type=all`, the CLI already labels results by source in the output (`## Snowflake Marketplace Results` and `## Internal (Intra-Org) Marketplace Results`). Preserve these section headers when presenting results to the user.

If `cortex search marketplace` returns "No marketplace listings found" or zero matches:
- For `--marketplace-type=internal`: suggest both (1) rephrasing the query and (2) re-running with `--marketplace-type=all` or `--marketplace-type=public` — the data may exist on the public marketplace even if the org hasn't published it internally.
- For `--marketplace-type=public` or `--marketplace-type=all`: suggest one or two alternative query phrasings (a synonym, a broader category) before giving up.

## Troubleshooting

- **`Marketplace search failed: ...`** — surface the error verbatim. Common causes: no active Snowflake connection (run `cortex connections list` to inspect), expired session token, or transient network issue. Ask the user how to proceed rather than retrying the same query blindly.
- **`Connection '<name>' not found`** — the `--connection` flag was passed but does not match any saved connection. Drop the flag (so the active connection is used) or have the user run `cortex connections set <name>` first.
- **`results` is empty / "No marketplace listings found"** — treat the same as the zero-match case in Step 3: tell the user, then suggest reformulated queries.
- **`cortex: command not found`** — the Cortex Code CLI is not installed on this machine. Tell the user; DO NOT attempt to install it silently.

## CRITICAL - Anti-patterns

- Do not default to `--marketplace-type=internal` or `=all` when the user's intent is clearly public/third-party. Use `internal` or `all` only when the user's message signals intra-org intent or is ambiguous between both sources.
- NEVER use `cortex search object --types=marketplace`. 
- NEVER re-run the same query just because the first attempt found something the user did not ask for — refine the query string instead.
- NEVER invent listing titles, providers, URLs, or descriptions that did not appear in the search output. If a field is missing, omit it.
- NEVER skip the search and answer "the marketplace might have it" — actually run the command and report what came back.

=== migration-guide/ ===
---
name: migration-guide
description: "Migration and conversion of databases, SQL, stored procedures, DDL, ETL/integration workloads into Snowflake. Uses Snowflake migrations plugin, including SnowConvert-based code conversion. ALWAYS invoke this skill — DO NOT answer source-vendor SQL questions directly — for: (1) any Snowflake equivalent of non-Snowflake SQL, even simple syntax questions single statements (T-SQL MERGE / sp_send_dbmail, Oracle CONNECT BY / SYSDATE / DUAL / DBMS_OUTPUT, MySQL ON DUPLICATE KEY UPDATE); (2) decommissioning, sunsetting, replatform, lift-and-shift, or modernization of a legacy data warehouse / ETL stack — even when 'Snowflake' isn't named yet (3) any request to convert source code to Snowflake, even if one-off. Triggers: migrate, migration, into snowflake, snowconvert, conversion report, unsupported objects, PL/SQL, plsql, T-SQL, Transact-SQL, tsql, SQL Server, MSSQL, SSMS, MySQL, BigQuery, Redshift, Netezza, SSIS, Informatica, CDC, data migration, data validation, migration testing, decommission, sunset, replatform, modernize, consolidate, legacy data warehouse."
---

# Migration Guide

Helps users migrate database and ETL objects to Snowflake. Walks through confirmation, installs the migration plugin via `cortex plugin install`, and hands off to the full migration skill.

## Instructions

Follow the steps below **in order**. Do not skip ahead.

### Step 1 — Confirm plugin installation

Tell the user:

> To guide you through the migration I'll install a **Snowflake migration plugin** as a managed Cortex plugin to help migrate database, ETL, and reporting workloads to Snowflake. No data is sent anywhere during installation.
>
> Shall I go ahead and install it?

Wait for explicit approval. If the user declines, respect their decision and stop.

### Step 2 — Install the plugin

Once the user approves, run the installer script. It calls `cortex plugin install` to clone and register the managed plugin, then disables the bundled `migration-guide` stub in settings.

**macOS / Linux:**
```bash
python3 scripts/install_plugin.py
```

**Windows:**
```cmd
python scripts\install_plugin.py
```

- If the script fails because **git is not installed or not on PATH** (surfaced by `cortex plugin install`), tell the user they need to install git and restart their terminal / PowerShell before continuing and point them to <https://git-scm.com/downloads>. **Stop here** until they confirm git is installed, then re-run the script. Do NOT try to debug — without git the plugin cannot be cloned.

- If the script reports the plugin is **already installed**, tell the user no changes were needed; the script is idempotent and they can proceed.

- If the install **succeeds**, tell the user:
  > Plugin installed and bundled stub disabled. Please run `/plugin reload` in this Cortex session to hot-reload the plugin runtime — no restart needed. Once reloaded, say "migrate" to start the migration workflow.

Once the user says "migrate", try to load the `snowflake-migration:migration` skill to start their workflow. If that is not available, ask the user to run `/plugin reload` again.

=== native-app-consumer/ ===
---
name: native-app-consumer
description: "**[REQUIRED]** for ALL Snowflake Native App consumer tasks: installing apps from listings as a consumer, configuring installed apps (granting privileges, approving specifications, reviewing references), managing maintenance policies, understanding native app cost and credit usage, adding native apps to budgets. Triggers: native app, install native app, configure native app, approve spec, decline spec, maintenance policy, maintenance window, upgrade schedule, control upgrades, app cost, app budget, app spending, native app cost, native app credits, how much does my app cost."
---

# Snowflake Native App — Consumer

This is a **routing skill**. It detects the user's intent and directs you to the correct sub-skill. You **MUST** load the sub-skill before doing any work — do NOT attempt native app tasks using only the information on this page.

## Running in Snowsight?

**⚠️ MANDATORY**: If your system prompt mentions Snowsight, load [`../native-app-provider/references/native-apps-snowsight.md`](../native-app-provider/references/native-apps-snowsight.md) before routing. It governs all env-specific decisions for everything below.

## Key Concepts

- **Snowflake Native App**: The application object created in the consumer account when they install the application from a listing
- **Listing**: A published entry on the Snowflake Marketplace or a private data exchange through which consumers discover and install native apps

## Routing Table

**Before starting any work**, scan the user's full request and identify ALL matching intents from the table below. If the request spans multiple intents, load each relevant sub-skill before performing that phase of work — do NOT attempt SQL from memory.

| Intent | Triggers | Sub-Skill to Load |
|--------|----------|--------------------|
| **Install Application** — Install a native app from a Marketplace listing | "install app", "install from listing", "get app", "install native app", "consumer install", "get app from marketplace", "install application from listing" | `install-app/SKILL.md` |
| **Configure Application** — Review/grant privileges, approve specs, review references for an installed app | "configure app", "review app privileges", "grant app privileges", "app specifications", "approve spec", "decline spec", "configure native app", "app references", "review app", "check app" | `configure-app/SKILL.md` |
| **Manage Maintenance Policies** — Control when Native App upgrades happen by creating and applying maintenance policies | "maintenance policy", "maintenance window", "upgrade schedule", "control upgrades", "upgrade timing", "app maintenance", "manage upgrades", "set maintenance window", "create maintenance policy", "when upgrades happen" | `manage-maintenance-policy/SKILL.md` |
| **Enable Logging & Troubleshoot** — Set up event table, enable event sharing, query app logs/traces/errors | "enable logging", "event sharing", "troubleshoot app", "app logs", "event table", "telemetry", "debug app", "app errors", "trace events", "enable events", "app diagnostics" | `enable-logging/SKILL.md` |
| **App Cost & Budgets** — Understand and manage ongoing cost of an installed app | "app cost", "app spending", "app credits", "budget for app", "how much does app cost", "monitor app cost", "app usage", "cost of native app", "app billing" | `app-cost/SKILL.md` |

**If the intent is ambiguous**, ask the user to clarify before proceeding.

=== native-app-provider/ ===
---
name: native-app-provider
description: "Use for **ALL** Snowflake Native App Framework tasks: creating app packages, writing manifest files, writing setup scripts, sharing data, testing, versioning, publishing, configuring telemetry and health status reporting, monitoring app health and lifecycle events, setting up event sharing, and debugging apps. Also use for **ALL** SPCS (Snowpark Container Services) work within native apps: adding containers, upgrading container services, building and pushing images, writing service specs, configuring compute pools, and managing service lifecycle. This is the **REQUIRED** entry point for any native app work. DO NOT attempt native app development manually - invoke this skill first. Triggers: native app, app package, application package, manifest.yml, setup script, CREATE APPLICATION, Snowflake marketplace, listing, native app framework, build native app, walk me through, guide me, get started, add version, register version, add patch, release channel, release directive, publish app, publish version, upgrade consumers, telemetry, health status, SYSTEM$REPORT_HEALTH_STATUS, log_level, trace_level, event definitions, event sharing, APPLICATION_STATE, lifecycle events, monitor app, debug app, observability, add streamlit, streamlit dashboard, add dashboard, streamlit UI, add UI to native app, native app streamlit, streamlit frontend, get_active_session, default_streamlit, SPCS native app, container native app, native app containers, native app SPCS, add containers, container_services, grant_callback, specification file, version_initializer, restricted caller, RCR, restricted callers rights, EXECUTE AS RESTRICTED CALLER, GRANT CALLER, caller rights, caller grants, restricted_callers_rights, access consumer data, consumer's role, caller's privileges, consumer's privileges."
---

# Snowflake Native App Framework

This is a **routing skill**. It detects the user's intent and directs you to the correct sub-skill. You **MUST** load the sub-skill before doing any work — do NOT attempt native app tasks using only the information on this page.

## Running in Snowsight?

**⚠️ MANDATORY**: If your system prompt mentions Snowsight, load [`references/native-apps-snowsight.md`](references/native-apps-snowsight.md) before routing. It governs all env-specific decisions (CLI vs Workspaces vs stage fallback) for everything below.

## Key Concepts

- **Application Package**: Encapsulates the data content, application logic, metadata, and setup script required by an application. Also contains version and patch information
- **Manifest File** (`manifest.yml`): Defines configuration and setup properties required by the application, including the location of the setup script, versions, privileges, and references
- **Setup Script**: Contains SQL statements that run when a consumer installs or upgrades an application. Location is specified in the manifest file
- **Snowflake Native App**: The database object created in the consumer account when they install the application

## Snow CLI Support

The following sub-skills support an optional Snow CLI path alongside the default SQL path:

- **Setup** (`setup-app/SKILL.md`)
- **Deploy & Test** (`deploy-test/SKILL.md`)

When routing to one of these sub-skills, **load** `references/snow-cli-detection.md` and run the detection probe **before** loading the sub-skill. Pass the result (`snow_cli_available`, `snow_cli_version`) to the sub-skill.

For all other sub-skills, skip CLI detection — they use SQL only.

## Workflow Rules (All Sub-Skills)

These rules apply to **every** sub-skill loaded from the routing table below. Follow them regardless of which sub-skill you are executing.

### Rule 1: Generate a Task List Before Proceeding

Before executing any steps in a sub-skill, generate a numbered task list of the steps you plan to take and present it to the user for confirmation. **Do NOT begin work until the user approves the plan.** This educates the user on what will happen and surfaces potential issues early. Example:

```
Here's what I'll do:
1. Read manifest.yml and setup script
2. Add CREATE EXTERNAL ACCESS INTEGRATION privilege to manifest
3. Generate network rule and EAI in setup script
4. Generate app specification
5. Validate all objects

Shall I proceed?
```

### Rule 2: Generate a Task History After Completion

After completing all steps in a sub-skill, present a **task history summary** to the user. Include:

- **Steps taken**: Numbered checklist of what was done, with pass/fail status for each
- **Configuration**: Key names, roles, and settings used
- **Issues encountered**: Any errors hit and how they were resolved (or "None")
- **Next steps**: What the user should do next

### Rule 3: Generate a Knowledge Handoff for Issues

If any issues were encountered and resolved during execution, include a **knowledge handoff** section in the task history summary:

- **Issue & Resolution table**: What went wrong, root cause, and fix applied
- **Gotchas for future work**: Non-obvious lessons learned during this session
- **Key decisions made**: Approach selections or design choices that were made

### Rule 4: Consult Troubleshooting Before Speculating on Errors

When an error occurs during any step, **read `references/troubleshooting.md` first** before speculating on the cause. Common errors (privilege failures, object conflicts, missing grants) have known root causes documented there. Do not assume a cause (e.g., missing privileges) without first checking whether a simpler explanation (e.g., name collision with an existing account-level object) is listed.

## Routing Table

**Before starting any work**, scan the user's full request and identify ALL matching intents from the table below. If the request spans multiple intents (e.g., sharing data AND deploying a version), load each relevant sub-skill before performing that phase of work — do NOT attempt SQL from memory.

| Intent | Triggers | Sub-Skill to Load |
|--------|----------|--------------------|
| **Setup** — Create a new app from scratch | "create native app", "new app package", "set up app", "write manifest", "setup script", "build native app", "walk me through", "get started" | `setup-app/SKILL.md` |
| **Add Containers (SPCS)** — Add Snowpark Container Services to a native app | "container", "SPCS", "Snowpark Container Services", "compute pool", "service spec", "container_services", "grant_callback", "add containers", "specification file", "specification template", "container native app", "default_web_endpoint", "uses_gpu", "upgrade service", "version_initializer", "SPCS upgrade", "service upgrade", "ALTER SERVICE", "services", "service job" | `add-containers/SKILL.md` |
| **Shared Data** — Share tables/views with consumers | "share data", "share table", "secure view", "grant data", "external table", "Iceberg table", "REFERENCE_USAGE", "shared content", "data content" | `shared-data/SKILL.md` |
| **Deploy & Test** — Deploy files and test the app | "deploy app", "test app", "install app", "development mode", "upgrade app", "create application", "test from version", "test from stage" | `deploy-test/SKILL.md` |
| **Debug App** — Debug an app in a developer account | "debug app", "debug mode", "session debug", "inspect objects", "query history", "redaction", "DISABLE_APPLICATION_REDACTION", "SYSTEM$BEGIN_DEBUG_APPLICATION", "debug setup script", "see all objects", "view app queries", "reproduce consumer issues" | `debug-app/SKILL.md` |
| **Version & Release** — Register versions, manage release channels, publish | "register version", "add version", "add patch", "release channel", "publish app", "release directive", "upgrade consumers", "publish to customers" | `app-version-release/SKILL.md` |
| **Privilege Config** — Configure auto-granted privileges for the app | "privilege", "auto-grant", "manifest privileges", "app permissions", "privilege configuration", "consumer privileges", "missing privileges", "request privileges", "configure privileges" | `request-account-privilege/SKILL.md` |
| **External Access Integration** — Configure external API access (EAI) | "external access integration", "EAI", "external API", "network rule", "app spec EAI", "consumer EAI", "external access", "egress", "outbound API", "host_ports", "allowed_network_rules", "configuration_callback" | `request-external-access-integration/SKILL.md` |
| **Security Integration** — Configure OAuth / API authentication | "security integration", "OAuth", "API authentication", "CLIENT_CREDENTIALS", "AUTHORIZATION_CODE", "JWT_BEARER", "OAuth token endpoint", "OAuth scopes", "CREATE SECURITY INTEGRATION" | `request-security-integration/SKILL.md` |
| **Add Streamlit** — Add a Streamlit UI to an existing or new native app (warehouse runtime). **Load this whenever the request mentions Streamlit, even if you are building from scratch.** | "add streamlit", "streamlit native app", "native app UI", "streamlit frontend", "add UI", "streamlit in native app", "CREATE STREAMLIT", "default_streamlit", "environment.yml", "get_active_session", "with a streamlit", "streamlit UI", "native app with streamlit", "create app with streamlit", "with streamlit" | `add-streamlit-warehouse/SKILL.md` |
| **Object Access Request** — Request access to consumer objects | "object reference", "consumer table", "consumer object", "access consumer", "register_callback", "SYSTEM$REFERENCE", "request reference", "bind object", "reference definition", "consumer warehouse", "consumer view", "access existing object" | `request-object-access/SKILL.md` |
| **Add RCR** — Add restricted caller rights to access consumer data or perform account-level operations | "restricted caller", "RCR", "EXECUTE AS RESTRICTED CALLER", "GRANT CALLER", "caller rights", "access consumer data", "consumer data from app", "restricted_callers_rights", "caller grants", "consumer's role", "caller's privileges", "consumer's privileges" | `use-rcr/SKILL.md` |
| **Configure Telemetry & Health** — Configure telemetry levels, event definitions, health reporting, object-level overrides | "health status", "logging", "tracing", "telemetry", "event definitions", "log_level", "trace_level", "metric_level", "SYSTEM$REPORT_HEALTH_STATUS", "configure telemetry", "health check", "health update" | `configure-telemetry-event-and-health-update/SKILL.md` |
| **Monitor App Telemetry & Status** — Query APPLICATION_STATE, lifecycle events, consumer health | "APPLICATION_STATE", "lifecycle events", "monitor app", "query health", "check app status", "upgrade tracking", "audit trail", "consumer health", "app monitoring" | `monitor-app-telemetry-event-and-status/SKILL.md` |
| **Configure Event Sharing** — Configure event routing tables, event accounts, event tables, and centralized event sharing to receive consumer telemetry across regions | "centralized event sharing", "event sharing", "event accounts", "event sharing setup", "event routing", "event routing table", "CREATE EVENT ROUTING TABLE", "ALTER ORGANIZATION SET EVENT ROUTING TABLE", "SYSTEM$SET_EVENT_SHARING_ACCOUNT_FOR_REGION", "provider event table", "event account region", "configure event sharing", "receive consumer telemetry", "cross-region events" | `configure-event-sharing/SKILL.md` |
| **Listing** — Share data back to provider or third-party accounts | "listing", "share data back", "CREATE SHARE", "CREATE LISTING", "data sharing", "compliance reporting", "telemetry", "shareback", "target accounts", "cross-region sharing", "auto-fulfillment" | `request-listing/SKILL.md` |
| **Publish Listing** — Create a listing to publish the app package to consumers | "publish listing", "create listing", "publish to marketplace", "make available to consumers", "share app", "private listing", "marketplace listing", "publish app to consumers" | `references/publish-listing.md` |
| **Manifest Reference** — Look up manifest field details | "manifest reference", "manifest fields", "manifest_version", "artifacts field", "privileges field", "references field" | `references/manifest-reference.md` |
| **Troubleshooting** — Look up common errors and fixes | "error", "not working", "failed", "troubleshooting" | `references/troubleshooting.md` |

**If the intent is ambiguous** or the user seems new to native apps, ask the user to clarify before proceeding.
=== network-security/ ===
---
name: network-security
description: "Recommend, evaluate, and migrate Snowflake network policies using built-in security procedures. Use when: generating network policy recommendations from access history, evaluating candidate policies before deployment, migrating existing policies to use Snowflake-managed SaaS rules, creating hybrid policies combining custom rules with SaaS rules. Triggers: recommend network policy, evaluate network policy, candidate policy, migrate policy, SaaS rules, hybrid policy."
---

# Network Security

Foundational knowledge for managing Snowflake network rules and policies.

## Core Concepts

- **Network rules** define lists of IP addresses (IPV4, INGRESS/EGRESS). They live in a database and schema.
- **Network policies** reference one or more network rules to allow or block traffic. Policies are account-level objects (no database/schema).
- **Hybrid policies** combine custom network rules with Snowflake-managed SaaS rules. This is the recommended pattern because SaaS rules are automatically updated by Snowflake when providers change their IP ranges.
- **Snowflake SaaS rules** are pre-built network rules in `SNOWFLAKE.NETWORK_SECURITY` for common integrations (dbt, Tableau, Power BI, Qlik, GitHub Actions, Sigma, ThoughtSpot, etc.).

### Internal vs External IPs

- **Internal IPs**: `10.x.x.x`, `172.16-31.x.x`, `192.168.x.x`, `0.0.0.0` (Snowflake infrastructure/VPN). These won't match SaaS rules — this is expected. Include them in custom rules.
- **External IPs**: All other public IPs. These may be covered by Snowflake SaaS rules.

### Creation Order

**Network rules MUST be created BEFORE the network policy that references them.** The policy creation will fail if a referenced network rule does not exist.

---

## SaaS Coverage Check

Use this query to determine which IPs are covered by Snowflake's pre-built SaaS network rules.

```sql
WITH input_ips AS (
    -- Replace with the IPs to check
    SELECT column1 as ip FROM VALUES
        ('<ip1>'), ('<ip2>'), ('<ip3>')
),
snowflake_saas_rules AS (
    SELECT name, value_list
    FROM snowflake.account_usage.network_rules 
    WHERE database = 'SNOWFLAKE' AND schema = 'NETWORK_SECURITY'
    AND deleted IS NULL
),
flattened_cidrs AS (
    SELECT 
        name as rule_name,
        TRIM(f.value::STRING) as cidr_block
    FROM snowflake_saas_rules,
    LATERAL FLATTEN(input => SPLIT(value_list, ',')) f
),
ip_to_int AS (
    SELECT 
        ip,
        (SPLIT_PART(ip, '.', 1)::INT * 16777216) + 
        (SPLIT_PART(ip, '.', 2)::INT * 65536) + 
        (SPLIT_PART(ip, '.', 3)::INT * 256) + 
        (SPLIT_PART(ip, '.', 4)::INT) as ip_int
    FROM input_ips
),
cidr_ranges AS (
    SELECT 
        rule_name,
        cidr_block,
        (SPLIT_PART(SPLIT_PART(cidr_block, '/', 1), '.', 1)::INT * 16777216) + 
        (SPLIT_PART(SPLIT_PART(cidr_block, '/', 1), '.', 2)::INT * 65536) + 
        (SPLIT_PART(SPLIT_PART(cidr_block, '/', 1), '.', 3)::INT * 256) + 
        (SPLIT_PART(SPLIT_PART(cidr_block, '/', 1), '.', 4)::INT) as network_int,
        COALESCE(TRY_TO_NUMBER(SPLIT_PART(cidr_block, '/', 2)), 32) as prefix_len
    FROM flattened_cidrs
)
SELECT 
    i.ip as checked_ip,
    c.rule_name as snowflake_saas_rule,
    c.cidr_block as matching_cidr
FROM ip_to_int i
JOIN cidr_ranges c 
    ON i.ip_int >= c.network_int 
    AND i.ip_int <= c.network_int + POW(2, 32 - c.prefix_len)::INT - 1
ORDER BY i.ip, c.rule_name;
```

**Interpreting results:**

| Result | Action |
|--------|--------|
| IPs covered by SaaS rules | Use Snowflake-provided rules in hybrid policy |
| No coverage | IPs go into a custom network rule |
| Mixed (most common) | Create hybrid policy combining SaaS rules + custom rule |

---

## Creating a Hybrid Network Policy

A hybrid policy uses both custom network rules (for environment-specific IPs) and Snowflake-managed SaaS rules (auto-updated).

### Step 1: Gather Database Context

Network rules require a database and schema.

**Ask user:**
```
To create the network rule, I need:
1. **Database name**: Which database should contain the network rule?
2. **Schema name**: Which schema in that database? (e.g., PUBLIC)
```

### Step 2: Create Custom Network Rule

```sql
CREATE OR REPLACE NETWORK RULE <db>.<schema>.<RULE_NAME>
    TYPE = IPV4
    MODE = INGRESS
    VALUE_LIST = (
        -- Internal IPs (Snowflake infrastructure/VPN)
        '<internal_ip1>/32', '<internal_ip2>/32',
        -- External IPs NOT covered by SaaS rules
        '<external_ip1>/32', '<external_ip2>/32'
    );
```

### Step 3: Verify Rule Creation

```sql
SHOW NETWORK RULES LIKE '<RULE_NAME>' IN <db>.<schema>;
```

### Step 4: Create Hybrid Policy

```sql
CREATE OR REPLACE NETWORK POLICY <POLICY_NAME>
    ALLOWED_NETWORK_RULE_LIST = (
        '<db>.<schema>.<RULE_NAME>',
        'SNOWFLAKE.NETWORK_SECURITY.<SAAS_RULE_1>',
        'SNOWFLAKE.NETWORK_SECURITY.<SAAS_RULE_2>'
    )
    COMMENT = 'Hybrid policy: custom IPs + SaaS rules';
```

**Common Error:** If you see `Network rule 'X' does not exist or not authorized`, ensure the network rule was created successfully and the fully qualified name is correct.

---

## DDL Reference

**Load** [references/ddl-reference.md](references/ddl-reference.md) for full DDL syntax (CREATE/ALTER/DROP for network rules and policies, policy assignment, view assignments).

---

## Network Policy Advisor

Advisory workflows for Snowflake network policies using built-in security procedures.

### Intent Detection

**Ask user:**
```
What would you like to do?
1. Generate network policy recommendations
2. Evaluate a candidate network policy
3. Migrate existing policy to use SaaS rules
```

- **Option 1** → Continue to [Recommend Workflow](#recommend-workflow)
- **Option 2** → Continue to [Evaluate Workflow](#evaluate-workflow)
- **Option 3** → Continue to [Migrate Workflow](#migrate-workflow)

---

### Recommend Workflow

#### Step 1: Gather Parameters

**Ask user:**
```
To generate network policy recommendations:

1. **Scope**: User-level or Account-level?
   - User-level: Provide username (e.g., "JOHN_DOE")
   - Account-level: Skip this parameter

2. **Lookback period**: How many days of history? (default: 90)
```

**⚠️ STOP**: Confirm parameters before proceeding.

#### Step 2: Execute Recommendation Procedure

**For user-level recommendation:**
```sql
CALL snowflake.network_security.recommend_network_policy('<USERNAME>', <LOOKBACK_DAYS>);
```

**For account-level recommendation:**
```sql
CALL snowflake.network_security.recommend_network_policy(lookback_days => <LOOKBACK_DAYS>);
```

#### Step 3: Present Results

1. **ALWAYS display the complete raw output** from the procedure in a code block:
   ```
   <full procedure output here - do not truncate or summarize>
   ```

2. **Identify external IPs** from the recommendation (see [Internal vs External IPs](#internal-vs-external-ips)).

#### Step 4: Automatic SaaS Coverage Check

**ALWAYS automatically check** whether any external IPs are covered by Snowflake SaaS rules. Use the [SaaS Coverage Check](#saas-coverage-check) query with all external IPs from the recommendation.

#### Step 5: Present Hybrid Policy Recommendation

**ALWAYS recommend a hybrid policy by default.** Present the recommendation to the user:

```
Based on the analysis, I recommend creating a **hybrid network policy**:

**SaaS Rules (auto-updated by Snowflake):**
- SNOWFLAKE.NETWORK_SECURITY.<MATCHING_RULE_1>
- SNOWFLAKE.NETWORK_SECURITY.<MATCHING_RULE_2>
- ... (list all matching SaaS rules)

**Custom Rule (for remaining IPs):**
- X internal IPs (Snowflake infrastructure/VPN)
- Y external IPs (not covered by SaaS rules)

This approach ensures:
1. SaaS provider IPs stay automatically updated by Snowflake
2. You only manage custom IPs that are specific to your environment
```

**⚠️ STOP**: Get user approval before creating the policy.

#### Step 6: Create Hybrid Network Policy

Follow the [Creating a Hybrid Network Policy](#creating-a-hybrid-network-policy) pattern to:
1. Gather database/schema context
2. Create the custom network rule
3. Create the hybrid policy referencing both the custom rule and matched SaaS rules

#### Step 7: Offer to Evaluate the Policy

After creating the hybrid policy, **always offer to evaluate it**:

```
The hybrid policy has been created. Would you like me to evaluate it against
the same lookback period to confirm 100% coverage?
```

If user agrees, run:
```sql
CALL snowflake.network_security.evaluate_candidate_network_policy(
    '<USERNAME>_HYBRID_NETWORK_POLICY',
    '<USERNAME>',
    <LOOKBACK_DAYS>
);
```

Present evaluation results showing allowed vs blocked IPs. If any IPs would be blocked, offer to expand the custom rule.

#### Stopping Points (Recommend)

- ✋ Step 1: After gathering parameters
- ✋ Step 5: After presenting hybrid policy recommendation (get approval)
- ✋ Step 7: After offering evaluation

#### Notes (Recommend)

- The procedure executes with CALLER privileges and accesses sensitive user activity data
- Recommended lookback periods:
  - Quick review: 7-14 days
  - Standard analysis: 30 days
  - Comprehensive audit: 90+ days

---

### Evaluate Workflow

Evaluate a candidate network policy against user activity to simulate the effect if that policy had been applied to either the account level or a specific user.

#### Step 1: Gather Parameters

**Ask user:**
```
To evaluate a network policy:

1. **Policy name**: Name of the network policy to evaluate
2. **User scope**: Specific user or all users?
   - Specific user: Provide username (e.g., "JOHN_DOE")
   - All users: Skip this parameter
3. **Lookback period**: How many days of history? (default: 90)
```

**⚠️ STOP**: Confirm parameters before proceeding.

#### Step 2: Execute Evaluation Procedure

**IMPORTANT**: Use `CALL` syntax (not `SELECT * FROM TABLE()`).

```sql
CALL snowflake.network_security.evaluate_candidate_network_policy(
    '<POLICY_NAME>',
    '<USERNAME>',  -- or NULL for all users
    <LOOKBACK_DAYS>
);
```

#### Step 3: Present Results

1. **ALWAYS display the complete tabular output** from the procedure
2. **Then** provide analysis:
   - Users/IPs that would be blocked
   - Users/IPs that would be allowed
   - Potential access disruptions
   - Compliance summary

**⚠️ STOP**: Review results with user.

#### Step 4: Recommendations

Based on results, suggest:
- Policy adjustments if too restrictive
- Additional IP ranges to include/exclude
- Users who may need exceptions

#### Stopping Points (Evaluate)

- ✋ Step 1: After gathering parameters
- ✋ Step 3: After presenting evaluation results

#### Notes (Evaluate)

- Executes with CALLER privileges - access to sensitive security data
- Use cases:
  - Test policies before deployment to avoid lockouts

---

### Migrate Workflow

Analyze an existing network policy to identify IP addresses that can be replaced with Snowflake-managed SaaS rules (auto-updated).

#### Step 1: Select Existing Policy

**List policies:**
```sql
SHOW NETWORK POLICIES IN ACCOUNT;
```

**Ask user:** Which policy would you like to analyze for SaaS migration?

**⚠️ STOP**: Confirm policy selection.

#### Step 2: Extract IP Addresses

**Get policy details:**
```sql
DESCRIBE NETWORK POLICY <selected_policy>;
```

Parse the `ALLOWED_IP_LIST` column to extract all IP addresses. If the policy uses `ALLOWED_NETWORK_RULE_LIST`, describe each rule:
```sql
DESCRIBE NETWORK RULE <db>.<schema>.<rule_name>;
```

#### Step 3: SaaS Coverage Check

Use the [SaaS Coverage Check](#saas-coverage-check) query with the extracted IPs.

#### Step 4: Present Migration Recommendation

Present results:
```
**SaaS Coverage Analysis for <policy_name>:**

IPs covered by SaaS rules (can be replaced):
- <ip1> -> SNOWFLAKE.NETWORK_SECURITY.<RULE_NAME>
- <ip2> -> SNOWFLAKE.NETWORK_SECURITY.<RULE_NAME>

IPs not covered (keep in custom rule):
- <ip3>, <ip4>, ...

**Recommendation:** Create hybrid policy with:
- SaaS rules: <list matching rules>
- Custom rule: <remaining IPs>
```

**⚠️ STOP**: Get user approval before creating replacement policy.

#### Step 5: Create Replacement Policy

Follow the [Creating a Hybrid Network Policy](#creating-a-hybrid-network-policy) pattern to create:
1. Custom network rule (non-SaaS IPs only)
2. Hybrid network policy (custom rule + SaaS rules)

#### Step 6: Evaluate and Swap

1. **Evaluate** new policy using [Evaluate Workflow](#evaluate-workflow)
2. If successful, swap policies (see [Policy Assignment](#policy-assignment)):
```sql
-- If assigned to user
ALTER USER <username> SET NETWORK_POLICY = '<new_hybrid_policy>';

-- If assigned to account
ALTER ACCOUNT SET NETWORK_POLICY = '<new_hybrid_policy>';

-- Remove old policy
DROP NETWORK POLICY <old_policy>;
```

**⚠️ STOP**: Confirm before swapping policies.

#### Stopping Points (Migrate)

- ✋ Step 1: After selecting policy
- ✋ Step 4: After presenting migration recommendation
- ✋ Step 6: Before swapping policies

=== notification/ ===
---
name: notification
description: "Router for Snowflake notification skills. Routes to integration creation/management, content formatting, or sending. Triggers: notification, notification integration, email notification, webhook, slack, teams, pagerduty, send notification, notification content."
---

# Snowflake Notifications

Router for notification-related tasks. Routes to the appropriate sub-skill based on user intent.

## Workflow

### Step 1: Detect Intent

| Intent | Triggers | Action |
|--------|----------|--------|
| Create or manage integration | "create notification integration", "email integration", "webhook integration", "alter integration", "drop integration", "show integrations" | **Load** [notification-integration/SKILL.md](notification-integration/SKILL.md) |
| Format notification content | "notification content", "format notification", "email content", "webhook content", "slack message", "teams message" | **Load** [notification-content/SKILL.md](notification-content/SKILL.md) |
| Send notification | "send notification", "send email", "send slack", "send teams", "send pagerduty", "SYSTEM$SEND_SNOWFLAKE_NOTIFICATION" | **Load** [notification-send/SKILL.md](notification-send/SKILL.md) |

### Step 2: Route to Specialized Skill

**Mandatory:** Load one of the sub-skills below. This router does not contain enough detail to handle any task directly.

**If request involves creating, altering, describing, or dropping notification integrations:**
- **-> Load**: [notification-integration/SKILL.md](notification-integration/SKILL.md)
- Handles email and webhook (Slack, Teams, PagerDuty) integrations, secret creation, grants

**If request involves formatting notification content (HTML email, Slack Block Kit, Teams Adaptive Cards, PagerDuty):**
- **-> Load**: [notification-content/SKILL.md](notification-content/SKILL.md)
- Takes query_id or message body, generates SQL content block for `SYSTEM$SEND_SNOWFLAKE_NOTIFICATION`

**If request involves sending a notification:**
- **-> Load**: [notification-send/SKILL.md](notification-send/SKILL.md)
- Takes content and integration, wraps and executes `SYSTEM$SEND_SNOWFLAKE_NOTIFICATION`

**If request involves alert notification muting/throttling (for example "send at most once per hour"):**
- **-> Load reference**: [references/alert-muting.md](references/alert-muting.md)
- Use action-level mute logic with a tracking table; keep detection logic in alert condition.

## Related Skills

- [notification-integration/SKILL.md](notification-integration/SKILL.md) - Create and manage notification integrations
- [notification-content/SKILL.md](notification-content/SKILL.md) - Format query results as notification content
- [notification-send/SKILL.md](notification-send/SKILL.md) - Send notifications via `SYSTEM$SEND_SNOWFLAKE_NOTIFICATION`
- [references/alert-muting.md](references/alert-muting.md) - Action-level muting/throttle pattern for alerts

## Stopping Points

- After routing: Sub-skill handles its own stopping points

=== openflow/ ===
---
name: openflow
description: Openflow data integration operations. Openflow is a Snowflake NiFi-based product for data replication and transformation. Use for connector deployment, configuration, diagnostics, and custom flows.
dependencies: python>=3.9, nipyapi[cli]>=1.5.0
min_nipyapi_version: "1.5.0"
skill_version: "2026-01-25"
---

# Openflow

## Session Prerequisites (Always First)

Before any operation, validate session state. Operations will fail without a valid session.

1. Load `references/core-guidelines.md` and `references/core-session.md`
2. Follow the Session Start Workflow (cache check, profile selection)
3. Only proceed once a profile is confirmed

**Context Management:**

- **Read references fully** when loading them, not just partial sections
- **Re-read references** at key workflow steps to ensure context is fresh
- If unsure of exact command syntax, run `--help` on the function before executing

---

## Routing Principles

1. **Session first** - Always validate session before routing to any operation
2. **Confirm before executing** - State detected intent, ask user for confirmation
3. **Primary wins ties** - If ambiguous between tiers, choose Primary
4. **Never suggest Advanced** - Only route to Advanced on explicit technical language
5. **Diary for complexity** - Use investigation diary methodology when Secondary/Advanced operations become complex

**Confirmation checkpoint** (use before starting any workflow):

> "It sounds like you want to [detected intent]. Is that right, or were you looking for something else?"

---

## Primary Operations

These are the common operations users perform regularly. Route here confidently for any general data integration request.

### Connector Name Detection

If the user mentions a data source by name, route to Primary tier:

**Known sources:** PostgreSQL, MySQL, SQL Server, SharePoint, Google Drive, Kafka, Salesforce, Box, Jira, Kinesis, Workday, Slack, Google Sheets, Google Ads, LinkedIn Ads, Meta Ads, Amazon Ads, Dataverse, MongoDB, HubSpot

- **New connector request:** "I need PostgreSQL" → Deploy workflow
- **Existing connector:** "How's my PostgreSQL connector?" → Status workflow

### Primary Routing Table

| User Language | Operation | Reference |
|---------------|-----------|-----------|
| Deploy, set up, install, get X into Snowflake, new connector, add connector | Deploy Connector | `references/connector-main.md` |
| Status, check, how is it doing, what's running, health, is it working | Check Status | `references/ops-status-check.md` |
| Start, stop, pause, resume, turn on, turn off, enable, disable | Control Flow | `references/ops-status-check.md` |
| Upgrade, update, new version, stale, outdated | Upgrade Connector | `references/connector-upgrades.md` |
| Errors, bulletins, any problems, warnings, what's wrong | Check Bulletins | `references/ops-status-check.md` |
| List, show me, what connectors exist, what's deployed | List Flows | `references/ops-status-check.md` |
| Setup, first time, connect, missing profile, discover infrastructure | Initial Setup | `references/setup-main.md` |

---

## Secondary Operations

Route here when user language contains explicit problem or operational indicators. These operations may become complex - consider using investigation diary methodology if they exceed 5-10 exchanges.

**Confirm before routing:**

> "It sounds like you're experiencing [issue/need]. Would you like me to help with that?"

### Secondary Routing Table

| Explicit Indicators | Operation | Reference |
|---------------------|-----------|-----------|
| Investigate, troubleshoot, debug, figure out why, not working as expected | Investigation | `references/ops-flow-investigation.md` |
| Error, 401, can't connect, failed, access denied, connection error | Error Remediation | `references/core-troubleshooting.md` |
| Configure parameters, change settings, update credentials, set values | Parameter Config | `references/ops-parameters-main.md` |
| Create parameter context, bind context, delete context, assign context | Context Lifecycle | `references/ops-parameters-contexts.md` |
| EAI, network rule, firewall, external access, UnknownHostException | Network Access | `references/platform-eai.md` |
| Test network, validate connectivity, port blocked | Network Testing | `references/ops-network-testing.md` |
| Runtime errors, pod failures, logs, events table, crash loop | Platform Diagnostics | `references/platform-diagnostics.md` |
| Force stop, terminate threads, purge flowfiles, delete flow | Advanced Lifecycle | `references/ops-flow-lifecycle.md` |
| Inspect connection, FlowFile content, queue contents, peek data | Connection Inspection | `references/ops-connection-inspection.md` |
| Component state, CDC table state, clear state, reset processor | Component State | `references/ops-component-state.md` |
| Set processor properties, set controller properties, configure component | Component Config | `references/ops-component-config.md` |
| Upload asset, JAR, certificate, driver, binary file | Asset Upload | `references/ops-parameters-assets.md` |
| Snowflake destination, KEY_PAIR, auth errors, writes to Snowflake | Snowflake Auth | `references/ops-snowflake-auth.md` |
| Verify config, test connection, validate before start | Config Verification | `references/ops-config-verification.md` |
| LOCALLY_MODIFIED, version change without commit | Tracked Modifications | `references/ops-tracked-modifications.md` |

---

## Advanced Operations

Route here ONLY when user explicitly uses technical NiFi terminology. These users know what they're asking for. Do not suggest these operations to users who haven't asked.

Use investigation diary methodology for these operations - they are inherently complex.

### Advanced Routing Table

| Technical Language Required | Operation | Reference |
|-----------------------------|-----------|-----------|
| Custom flow, build from scratch, author, create new flow, design flow | Custom Authoring | `references/author-main.md` |
| Processor, add processor, create processor, modify flow structure | Component CRUD | `references/author-building-flows.md` |
| Export, import, backup, migrate, download flow | Flow Export/Import | `references/ops-flow-export.md` |
| Version control, commit, rollback, Git, save changes | Version Control | `references/ops-version-control.md` |
| Expression Language, EL, ${...}, attribute manipulation | EL Syntax | `references/nifi-expression-language.md` |
| RecordPath, record field, /path/to/field, JSON transformation | RecordPath | `references/nifi-recordpath.md` |
| Date format, timestamp conversion, epoch, SimpleDateFormat | Date Formatting | `references/nifi-date-formatting.md` |
| NAR, extension, upload NAR, Python processor, custom processor | Extensions | `references/ops-extensions.md` |
| Layout, position, organize canvas, tidy flow | Layout | `references/ops-layout.md` |
| Find processor, what processor for X, component selection | Component Selection | `references/author-component-selection.md` |
| Write to Snowflake, type mapping, logicalType, PutSnowpipeStreaming | Snowflake Destination | `references/author-snowflake-destination.md` |
| NiFi concepts, FlowFile, connections, backpressure | NiFi Concepts | `references/nifi-main.md` |
| REST API ingestion, file processing, ActiveMQ, JMS | Flow Patterns | `references/author-main.md` |
| GenerateJSON, synthetic data, test data, DataFaker, fake data | Data Generation | `references/author-pattern-data-generation.md` |

---

## Compound Requests

If the user describes multiple operations:

1. Create a todo list capturing all requested operations
2. Ask the user to confirm the order:
   > "I've identified these tasks: [list]. What order would you like me to tackle them?"
3. Execute in confirmed order, completing each before moving to the next
4. Note: Some operations have natural dependencies (e.g., deploy before configure before start)

---

## Reference Index

### Core (Load at Session Start)

| Reference | Purpose |
|-----------|---------|
| `references/core-guidelines.md` | Tool hierarchy, deployment types, workflow modes, safety reminders |
| `references/core-session.md` | Session check workflow, cache schema, profile selection |
| `references/core-investigation-diary.md` | Diary methodology for complex operations |
| `references/core-troubleshooting.md` | Error patterns and remediation |

### Connector Operations

| Reference | Purpose |
|-----------|---------|
| `references/connector-main.md` | Connector deployment workflow and routing |
| `references/connector-upgrades.md` | Version management for connectors |
| `references/connector-cdc.md` | CDC connector specifics (PostgreSQL, MySQL) |
| `references/connector-sqlserver.md` | SQL Server CDC connector (Change Tracking setup, multi-DB replication, troubleshooting) |
| `references/connector-oracle.md` | Oracle CDC connector (Embedded & BYOL licensing, XStream setup, troubleshooting) |
| `references/connector-googledrive.md` | Google Drive connector specifics |
| `references/connector-sharepoint-simple.md` | SharePoint connector specifics |
| `references/connector-hubspot.md` | HubSpot connector (Private App Token auth) |
| `references/connector-jira.md` | Jira Cloud connector (API token auth; core + optional agile flow; legacy-to-current migration) |

### Flow Operations

| Reference | Purpose |
|-----------|---------|
| `references/ops-status-check.md` | Quick status checks, list flows, basic start/stop (Primary) |
| `references/ops-flow-lifecycle.md` | Advanced lifecycle: force stop, purge, delete (Secondary) |
| `references/ops-flow-investigation.md` | Problem-oriented diagnostic workflows |
| `references/ops-flow-deploy.md` | Deploy flows from registries (used by connector-main) |
| `references/ops-flow-export.md` | Export/import flow definitions (Advanced) |

### Parameter Operations

| Reference | Purpose |
|-----------|---------|
| `references/ops-parameters-main.md` | Parameter context management router |
| `references/ops-parameters-contexts.md` | Create, bind, delete parameter contexts |
| `references/ops-parameters-assets.md` | Binary asset upload (JARs, certificates) |
| `references/ops-snowflake-auth.md` | Snowflake destination authentication |
| `references/ops-config-verification.md` | Validate configuration before start |

### Platform Operations

| Reference | Purpose |
|-----------|---------|
| `references/platform-eai.md` | External Access Integration for SPCS |
| `references/platform-diagnostics.md` | Runtime/pod diagnostics |
| `references/ops-network-testing.md` | Network connectivity validation |

### Flow Authoring (Advanced)

| Reference | Purpose |
|-----------|---------|
| `references/author-main.md` | Flow authoring router and design principles |
| `references/author-building-flows.md` | Component CRUD, inspect-modify-test cycle |
| `references/author-component-selection.md` | Find the right processor |
| `references/author-snowflake-destination.md` | Type mapping for Snowflake writes |
| `references/author-pattern-rest-api.md` | REST API ingestion pattern |
| `references/author-pattern-files.md` | Cloud file processing pattern |
| `references/author-pattern-activemq.md` | ActiveMQ/JMS messaging pattern |
| `references/author-pattern-data-generation.md` | Synthetic test record data with GenerateJSON |

### NiFi Technical (Advanced)

| Reference | Purpose |
|-----------|---------|
| `references/nifi-main.md` | NiFi reference router |
| `references/nifi-expression-language.md` | FlowFile attribute manipulation |
| `references/nifi-recordpath.md` | Record field transformation |
| `references/nifi-date-formatting.md` | Date/time patterns |
| `references/nifi-concepts.md` | FlowFile, connections, backpressure |

### Development

| Reference | Purpose |
|-----------|---------|
| `references/core-skill-development.md` | Guidelines for extending this skill |

=== organization-management/ ===
---
name: organization-management
description: "Snowflake organization management — accounts, org users, org insights, org spending, org security, globalorgadmin. ORGANIZATION_USAGE views, cross-account analytics, org-wide metrics. Use when the user asks about: 30 day summary of my organization, 30-day summary, 30 day summary, accounts in my organization, list accounts, how many accounts, account editions, account regions, account inventory, organization users, organization user groups, executive summary of my org, org overview, org spending, org cost, org security posture, org reliability, org auth posture, org hub, org usage views, trust center, MFA readiness, login failures, warehouse credits, storage trends, edition distribution, who has globalorgadmin, what is globalorgadmin, globalorgadmin role, orgadmin role, organization administrator, org admin, enable orgadmin, disable orgadmin, org admin permissions, account admins, ORGANIZATION_USAGE, org-level, cross-account, org-wide."
---

# Organization Management

Router skill for organization management workflows.

## When to Use

Use this skill for:
- Account inventory and edition visibility
- Account control-plane operations
- Organization control-plane operations
- Organization user and organization user group operations
- Org Hub executive insights
- Org Usage view mapping

## Intent Detection

**Automatically detect user intent and IMMEDIATELY load the matching sub-skill:**

| Intent | Triggers | Load |
|--------|----------|------|
| **ACCOUNT_LIFECYCLE** | "create account", "create new account", "provision account", "alter account", "modify account", "account edition", "upgrade edition", "change edition", "account region" | `account-lifecycle/SKILL.md` |
| **READER_ACCOUNTS** | "reader account", "managed account", "create reader account", "share with non-snowflake customer" | `reader-accounts/SKILL.md` |
| **CLIENT_REDIRECT** | "connection url", "client redirect", "create connection", "failover", "disaster recovery" | `client-redirect/SKILL.md` |
| **REPLICATION_SETUP** | "enable replication", "account replication", "create replication group", "replicate across accounts" | `replication-setup/SKILL.md` |
| **ACCOUNT_INSIGHTS** | "list accounts", "how many accounts", "account inventory", "account editions", "edition distribution", "reader accounts", "role analytics" | `accounts/SKILL.md` |
| **ORG_USERS_CREATE** | "create organization user", "create org user", "create organization user group", "create org group", "drop organization user", "alter organization user", "set visibility" | `organization-users/create/SKILL.md` |
| **ORG_USERS_IMPORT** | "import organization user group", "import org group", "import users into account", "add group to account", "unimport group", "enable users in account" | `organization-users/import/SKILL.md` |
| **ORG_USERS_TROUBLESHOOT** | "resolve import conflicts", "user already exists", "link user", "x/y users imported", "import shows conflicts", "matching login_name" | `organization-users/troubleshoot/SKILL.md` |
| **ORG_HUB_INSIGHTS** | "executive summary", "30 day summary of my organization", "30-day summary", "30 day summary", "org overview", "org spending", "cost drivers", "security posture", "reliability risks", "login failures", "org hub", "cost trends", "cost spikes", "cost optimizations", "compare service costs", "fastest growing costs", "service optimizations", "contract utilization", "forecast contract", "trust center violations", "violation trends", "trust center coverage", "MFA readiness", "MFA adoption", "login failure patterns", "auth method distribution", "admin distribution", "security admin coverage", "dormant users", "dormant user risk", "failed queries", "query failure patterns", "warehouse queued load", "warehouse load distribution", "capacity planning", "storage growth", "storage consumers", "storage optimization", "top queries by cost", "expensive queries" | `org-hub/SKILL.md` |
| **ORG_USAGE_VIEWS** | "which org usage views are available", "which view should I use for billing", "feature to view mapping", "what role do I need for org usage" | `org-usage-view/SKILL.md` |
| **GLOBAL_ORG_ADMIN** | "what is globalorgadmin", "who has globalorgadmin", "orgadmin role", "enable orgadmin", "org admin permissions" | `globalorgadmin/SKILL.md` |

## Routing Decision Tree

```
User Request
    ↓
Detect Intent
    ├─→ ACCOUNT_LIFECYCLE → IMMEDIATELY Load account-lifecycle/SKILL.md
    │
    ├─→ READER_ACCOUNTS → IMMEDIATELY Load reader-accounts/SKILL.md
    │
    ├─→ CLIENT_REDIRECT → IMMEDIATELY Load client-redirect/SKILL.md
    │
    ├─→ REPLICATION_SETUP → IMMEDIATELY Load replication-setup/SKILL.md
    │
    ↓
    ├─→ ACCOUNT_INSIGHTS → IMMEDIATELY Load accounts/SKILL.md
    │
    ├─→ ORG_USERS_CREATE → IMMEDIATELY Load organization-users/create/SKILL.md
    │
    ├─→ ORG_USERS_IMPORT → IMMEDIATELY Load organization-users/import/SKILL.md
    │
    ├─→ ORG_USERS_TROUBLESHOOT → IMMEDIATELY Load organization-users/troubleshoot/SKILL.md
    │
    ├─→ ORG_HUB_INSIGHTS → IMMEDIATELY Load org-hub/SKILL.md
    │
    ├─→ ORG_USAGE_VIEWS → IMMEDIATELY Load org-usage-view/SKILL.md
    │
    └─→ GLOBAL_ORG_ADMIN → IMMEDIATELY Load globalorgadmin/SKILL.md
```

## ⚠️ DO NOT PROCEED WITHOUT LOADING SUB-SKILL

This router provides NO implementation details. All workflows, SQL commands, and procedures are in the sub-skills above.

## Setup

1. **Load** `references/global_guardrails.md`: Required context for all organization management operations.

=== semantic-view/ ===
---
name: semantic-view
description: "Use for ALL requests that mention: create, build, debug, fix, troubleshoot, optimize, improve, or analyze a semantic view — AND for requests about VQR suggestions, verified queries, verified query representations, seeding/generating queries, suggesting metrics, suggesting filters, recommending metrics/filters/facts, importing Tableau (.twb/.twbx/.tds/.tdsx) or Power BI (.pbit/.pbix) files, or enriching a semantic view. This is the entry point - even if the request seems simple. DO NOT attempt to create, debug, or generate suggestions for semantic views manually - always invoke this skill first. This skill guides users through creation, setup, auditing, VQR suggestion generation, filter & metric suggestions, Tableau/Power BI imports, and SQL generation debugging workflows for semantic views with Cortex Analyst."
---

# Semantic View Skill

## When to Use

When a user wants to create, debug, optimize semantic views, generate VQR (verified query) suggestions, or get filter & metric suggestions for Cortex Analyst. This is the entry point for all semantic view workflows including VQR and filter/metric suggestion generation.

## Prerequisites

- Fully qualified semantic view name (DATABASE.SCHEMA.VIEW_NAME)
- Snowflake access configured
- Python dependencies: `tomli`, `urllib3`, `requests`, `pyyaml`, `snowflake-connector-python`
  - Install via: `uv pip install tomli urllib3 requests pyyaml snowflake-connector-python`

## ⚠️ MANDATORY INITIALIZATION (Required Before ANY Workflow)

**Before creating, auditing, or debugging semantic views, you MUST complete initialization:**

### Step 1: Complete Setup ✋ BLOCKING

**Load**: [setup/SKILL.md](setup/SKILL.md)

**This will:**

- Get BASE_WORKING_DIR from user (where to create files)
- Create session directory WORKING_DIR (timestamped)

**After setup completes, you will have these variables:**

- `SKILL_BASE_DIR` - Script location
- `BASE_WORKING_DIR` - User's chosen base directory
- `WORKING_DIR` - Session directory: `{BASE_WORKING_DIR}/semantic_view_{TIMESTAMP}`

**DO NOT PROCEED until setup is complete.**

### Step 2: Workflow Routing and Available Skills ✋

**After setup completes**, you will be routed to the appropriate workflow based on whether you're working with a NEW or EXISTING semantic view.

#### Workflow Decision Tree

```
Setup/SKILL.md Part 2: Workflow Routing
    ↓
Determine: NEW, IMPORT, EXISTING, VQR SUGGESTIONS, or FILTER & METRIC SUGGESTIONS?
    ↓
┌────┴────┬──────────┬──────────┬──────────┐
↓         ↓          ↓          ↓          ↓
NEW     IMPORT    EXISTING   VQR       FILTERS &
↓         ↓          ↓      SUGGEST.   METRICS
Load    Load        Continue   ↓          ↓
creation/ import_     to     Load       Load
SKILL.md  tableau/  Part 3   vqr_       filters_and_
       OR import_           suggestions/ metrics_suggestions/
       powerbi/             SKILL.md    SKILL.md
       SKILL.md
    ↓        ↓          ↓
Create   Import     Create
creation/ Tableau   optimization/
subdir   or PBI     subdir
         file
    ↓        ↓          ↓
Generate Generate   Download
semantic semantic   existing
model    model      model
                       ↓
                   Present mode
                   selection
                       ↓
                   ┌───┴───┐
                   ↓       ↓
               AUDIT    DEBUG
                MODE     MODE
```

#### Supporting Skills Available

Throughout any workflow, you can load these supporting skills as needed:

**Validation**:

- **Load**: [validation/SKILL.md](validation/SKILL.md)
- **Purpose**: Validation procedures used by both audit and debug workflows
- **When to use**: To validate semantic models before applying changes

**Optimization Patterns**:

- **Load**: [optimization/SKILL.md](optimization/SKILL.md)
- **Purpose**: Library of optimization patterns for semantic view improvements (dimensions, metrics, filters, relationships, custom instructions)
- **When to use**: When you need guidance on specific optimization techniques for descriptions, synonyms, named filters, etc.

**Modeling Patterns** (advanced DDL/YAML constructs):

- **Load**: [patterns/SKILL.md](patterns/SKILL.md)
- **Purpose**: Catalog of 14 advanced Semantic View modeling patterns — each ships a tight DDL/YAML snippet for a specific modeling intent (period-over-period comparison, rolling/lag/YTD metrics, SCD2 / ASOF temporal joins, snapshot facts that must not sum across time, accumulating-snapshot funnels, multi-path metrics, role-playing dimensions, cross-entity derived metrics, multi-fact layouts, `PRIVATE` facts, computed-FK joins, AI metadata steering Cortex Analyst, and a six-scenario structural diagnostic).
- **When to use**: User wants to compare a metric to the same period last year/month (YoY, MoM, SPLY); build a rolling average, year-to-date total, or lag-N comparison; model a slowly-changing-dimension lookup (`valid_from`/`valid_to`, ASOF, "address active at order time"); track a snapshot fact that must not sum across time ("balance / inventory / headcount over time"); model a funnel across multiple milestone dates ("loan funnel", "applied → reviewed → decided → funded"); add a cross-entity derived metric (`% of total`, `net = gross − returns`); expose a `PRIVATE` fact only used inside the SV; join on a computed (non-physical) key; steer Cortex Analyst with verified queries / AI metadata; or diagnose a fan trap, "multi-path relationship not supported" error, or numbers that look inflated. Also when an audit / debug step identifies a structural issue that maps to one of these patterns.

**Upload**:

- **Load**: [upload/SKILL.md](upload/SKILL.md)
- **Purpose**: Upload optimized semantic view YAML to Snowflake
- **When to use**: Only when user explicitly requests deployment to Snowflake

**SVA verified-query SQL (reference)**:

- **Load**: [reference/sva_validate_verified_queries.md](reference/sva_validate_verified_queries.md) — compile-check VQR SQL (`validate_verified_queries`), bulk or inline
- **Load**: [reference/sva_expand_truncate_verified_query.md](reference/sva_expand_truncate_verified_query.md) — semantic ↔ physical SQL (`expand_verified_query` / `truncate_verified_query`)
- **When to use**: User asks to validate VQRs compile, expand/truncate verified query SQL, or you need SQL templates for `SYSTEM$CORTEX_ANALYST_SVA_TOOL` (use with a local YAML path from optimization setup or user-provided file)

**Time Tracking** (Optional):

- **Load**: [time_tracking/SKILL.md](time_tracking/SKILL.md)
- **Purpose**: Track execution time for tool calls and workflow steps
- **When to use**: Only if user explicitly requests time tracking

**⚠️ After setup, refer to Core Capabilities below for detailed information on each workflow.**

## Core Capabilities

**Routing note:** `setup/SKILL.md` Part 2 only chooses **Creation** vs **Optimization** (existing view → Part 3 download). **VQR Suggestions**, **Filters & Metrics Suggestions**, **Tableau Import**, and **Power BI Import** below are loaded **directly from this list** when the user’s intent matches — they **do not** require Part 3. For SVA SQL against a downloaded model, complete optimization setup first or use a user-supplied YAML path.

### Creation Mode

Create new semantic views from scratch with proper structure, relationships, and validation using table metadata and VQRs (SQL Queries).

**When to use**: User wants to CREATE a new semantic view (not optimize an existing one)

**Action**: Load [creation/SKILL.md](creation/SKILL.md)

### VQR Suggestions

Generate verified query suggestions by mining Cortex Analyst usage and Snowflake query history. Runs both modes in parallel and merges results.

**When to use**: User wants to suggest, generate, seed, or populate VQRs for a semantic view — including right after creation

**Action**: Load [vqr_suggestions/SKILL.md](vqr_suggestions/SKILL.md)

### Filters & Metrics Suggestions

Suggest metrics, named filters, and computed facts for a semantic view by mining Snowflake query history via `SYSTEM$CORTEX_ANALYST_SVA_TOOL`.

**When to use**: User wants to suggest, recommend, or auto-generate metrics, filters, or facts for a semantic view

**Action**: Load [filters_and_metrics_suggestions/SKILL.md](filters_and_metrics_suggestions/SKILL.md)

### Tableau Import Mode

Import Tableau workbooks (.twb, .twbx) and datasources (.tds, .tdsx) into Snowflake Semantic Views. Handles published datasources, custom SQL, and provides flexible deployment options.

**When to use**: User wants to IMPORT or CONVERT a Tableau file to a semantic view

**Trigger keywords**: import Tableau, convert Tableau, Tableau to semantic view, migrate workbook, .twb, .twbx

**Action**: Load [import_tableau/SKILL.md](import_tableau/SKILL.md)

### Power BI Import Mode

Import Power BI templates (.pbit) and desktop files (.pbix) into Snowflake Semantic Views. Handles M-query table resolution, DAX measures (with non-transpilable measures dropped), and target DB/schema remapping.

**When to use**: User wants to IMPORT or CONVERT a Power BI file to a semantic view

**Trigger keywords**: import Power BI, convert Power BI, Power BI to semantic view, migrate dashboard, .pbit, .pbix

**Action**: Load [import_powerbi/SKILL.md](import_powerbi/SKILL.md)

### Optimization, Audit, and Debug

For working with EXISTING semantic views.

**When to use**: User wants to optimize, audit, or debug an existing semantic view

**Action**: Continue in setup/SKILL.md (Part 3)

#### 1. Audit and Optimize Loop

Comprehensive audit system for semantic views including:

1. VQR testing (behavioral — CA without VQR hints)
2. Best Practices verification
3. Custom Criteria evaluation
4. SVA VQR compile check (`validate_verified_queries` — see [reference/sva_validate_verified_queries.md](reference/sva_validate_verified_queries.md))

**Load**: [audit/SKILL.md](audit/SKILL.md) when user chooses AUDIT MODE

#### 2. Debug Loop

Targeted problem-solving for specific issues with SQL generation from natural language queries.

**Load**: [debug/SKILL.md](debug/SKILL.md) when user chooses DEBUG MODE

## Supporting Skills

### Validation

**Load**: [validation/SKILL.md](validation/SKILL.md) - Validation procedures used by both audit and debug workflows

### Optimization Patterns

**Load**: [optimization/SKILL.md](optimization/SKILL.md) - Library of optimization patterns for semantic view improvements (descriptions, synonyms, named filters, relationships, custom instructions)

### Modeling Patterns

**Load**: [patterns/SKILL.md](patterns/SKILL.md) when the user wants to apply a specific advanced modeling intent: a period-over-period comparison (YoY / MoM / SPLY); a rolling, YTD/QTD/MTD, or lag-N metric; an SCD2 lookup with `valid_from`/`valid_to` or an ASOF event-time join; a snapshot fact that must not sum across time (balance / inventory / headcount); an accumulating funnel across multiple milestone dates; routing a metric through a specific FK when one fact has two FKs to the same dim (multi-path `USING`); reusing the same physical dim under multiple roles; a cross-entity derived metric (`% of total`, `net = gross − returns`); splitting shared dims across multiple fact tables; a `PRIVATE` fact used only inside the SV; a join on a key that doesn't exist as a physical column (computed FK); steering Cortex Analyst with verified queries / `AI_SQL_GENERATION` / `AI_QUESTION_CATEGORIZATION` metadata; or diagnosing a fan trap / "multi-path relationship not supported" error / numbers that look inflated. Each pattern ships a tight DDL/YAML snippet, gotchas grounded in upstream `queries.sql`, and verbatim docs links.

### Time Tracking (Optional)

**Load**: [time_tracking/SKILL.md](time_tracking/SKILL.md) - Track execution time for tool calls and workflow steps (only load if user explicitly requests time tracking)

### Upload

**Load**: [upload/SKILL.md](upload/SKILL.md) - Upload optimized semantic view YAML to Snowflake (only load when user wants to deploy/upload)

### SVA verified-query SQL (reference)

**Load**: [reference/sva_validate_verified_queries.md](reference/sva_validate_verified_queries.md), [reference/sva_expand_truncate_verified_query.md](reference/sva_expand_truncate_verified_query.md) — Snowflake Analyst VQR compile validation and semantic/physical SQL conversion

## Workflow Decision Tree

**Complete visual representation of the initialization and routing flow:**

```
Start Session
    ↓
Step 1: Load setup/SKILL.md ✋
    ├─ Part 1: Directory Initialization
    │   ├─ Capture SKILL_BASE_DIR
    │   ├─ Get BASE_WORKING_DIR (ask or infer)
    │   └─ Create WORKING_DIR (semantic_view_{TIMESTAMP})
    │
    ├─ Part 2: Workflow Routing
    │   └─ Determine: NEW, IMPORT, EXISTING, VQR SUGGESTIONS, or FILTER & METRIC SUGGESTIONS?
    │       ↓
    │   ┌───┴───┬─────┬──────────┬──────────┐
    │   ↓       ↓     ↓          ↓          ↓
    │  NEW   IMPORT EXISTING  VQR       FILTERS &
    │   ↓       ↓     ↓      SUGGEST.   METRICS
    │  Load   Load  Continue    ↓          ↓
    │ creation/ import_ Part 3 Load       Load
    │ SKILL.md tableau/       vqr_        filters_and_
    │       OR import_       suggestions/ metrics_suggestions/
    │       powerbi/         SKILL.md    SKILL.md
    │       SKILL.md
    │
    └─ Part 3: Optimization Setup (if EXISTING)
        ├─ Create {WORKING_DIR}/optimization/
        ├─ Download semantic model
        └─ Present mode selection
            ↓
        ┌───┴───┐
        ↓       ↓
    AUDIT    DEBUG
     MODE     MODE
```

**See above for supporting skills available throughout any workflow.**

## Key Principles

1. **Progressive Disclosure**: Load skills incrementally as needed
2. **Modularity**: Each skill is self-contained and reusable
3. **User Confirmation**: Stop at mandatory checkpoints for user input
4. **Validation First**: Always validate before applying changes

## Rules

1. **⚠️ Test Locally First**: By default, test with local YAML files using `semantic_model_file` parameter. Only upload to Snowflake when user explicitly requests deployment.
2. **⚠️ MANDATORY CHECKPOINT FOR ALL OPTIMIZATIONS**: Before any actual semantic view optimization:
   - Wait for explicit user approval (e.g., "approved", "looks good", "proceed")
   - NEVER chain separate optimization edits without user approval between them
3. **⚠️ Always use `uv run python` for scripts**. DO NOT use `python script.py` or `python3 script.py`.

=== setup-snowflake-sso/ ===
---
name: setup-snowflake-sso
description: |
  Set up Single Sign-On (SSO) for Snowflake with your Identity Provider (IdP).
  Supports Microsoft Entra ID (Azure AD), Okta, and other SAML 2.0 providers including
  OneLogin, Ping Identity, Google Workspace, Auth0, Duo, JumpCloud, and more.
  Includes advanced scenarios: Allowed Interfaces, Auto Redirect, and Snowflake Intelligence tile setup.
triggers:
  - set up SSO
  - configure SSO
  - setup single sign-on
  - configure single sign-on
  - SSO for Snowflake
  - identity provider setup
  - IdP setup
  - Entra ID
  - Azure AD
  - Microsoft Entra
  - Okta SSO
  - Okta SCIM
  - SAML SSO
  - SAML 2.0
  - generic SAML
  - OneLogin
  - Ping Identity
  - PingOne
  - Google Workspace SAML
  - Auth0
  - Duo
  - JumpCloud
  - advanced SSO
  - allowed interfaces
  - limited interfaces
  - auto redirect
  - Snowflake Intelligence tile
  - add Snowflake Intelligence tile
---

# Set Up Snowflake SSO

This skill helps you configure Single Sign-On (SSO) and user provisioning for Snowflake with your Identity Provider (IdP).

## Workflows

This skill contains the following workflows:

| Workflow | Description |
|----------|-------------|
| `workflows/okta-sso.md` | Okta SAML SSO and SCIM provisioning |
| `workflows/entra-sso.md` | Microsoft Entra ID SAML SSO and SCIM provisioning |
| `workflows/generic-saml.md` | Generic SAML 2.0 setup for other IdPs |
| `workflows/advanced-scenarios.md` | Allowed Interfaces and Auto Redirect configuration |
| `workflows/snowflake-allowed-interfaces.md` | Configure Allowed Interfaces via SQL |
| `workflows/okta-allowed-interfaces.md` | Configure Allowed Interfaces via Okta SCIM |
| `workflows/entra-allowed-interfaces.md` | Configure Allowed Interfaces via Entra ID SCIM |
| `workflows/add-snowflake-intelligence-tile.md` | Add Snowflake Intelligence tile to IdP app launcher |
| `workflows/okta-api-token-setup.md` | Okta API token setup for Automated and Self-service API methods |

---

## Important Instructions for AI

**DO NOT** attempt to:
- Install any CLI tools, SDKs, or PowerShell modules
- Download or run any scripts to manage the Identity Provider (IdP)
- Sign in to any IdP on behalf of the user

**IdP API calls are allowed ONLY when the user explicitly opts into the "Automated (API)" method.** In that case, the agent may execute `curl` commands against the IdP's API using the appropriate environment variables. Every command must be accompanied by a description of what it does, and the user must confirm before execution.

For all other methods (Self-service Curl commands and Manual UI guide), the agent must NOT execute any commands that interact with the user's IdP.

**IMPORTANT: Step-by-step delivery**
- Do NOT send all instructions at once
- Present one logical section at a time
- Use AskUserQuestion for confirmations between steps

**IMPORTANT: Error handling**
- If an API command fails or returns an unexpected result, do NOT automatically run additional commands to diagnose or fix the issue
- Instead, show the error to the user and ask how they would like to proceed:

```python
AskUserQuestion(
  questions=[{
    "question": "The command returned an error. How would you like to proceed?",
    "header": "Error",
    "multiSelect": false,
    "options": [
      {"label": "Review the docs", "description": "I'll check the API documentation or IdP admin console to investigate"},
      {"label": "Run diagnostic commands", "description": "Let the agent run additional API commands to help diagnose the issue"},
      {"label": "Skip this step", "description": "Move on to the next step"},
      {"label": "Cancel", "description": "Stop the workflow"}
    ]
  }]
)
```

---

## MANDATORY: Display Security Notice First

**Before doing anything else, you MUST display the following notice to the user:**

> **Security Notice**
>
> This skill supports up to three methods for configuring your Identity Provider (IdP), depending on which IdP you use:
>
> 1. **Manual (UI guide)** — Step-by-step instructions for you to follow in your IdP's admin console. Always available. No API token needed.
>
> 2. **Self-service API (Curl commands)** — The agent provides ready-to-run curl commands for you to copy-paste and execute yourself. The agent does NOT run any commands. Requires you to set up an API token and domain as environment variables first. Available when API automation is supported for your IdP.
>
> 3. **Automated (API)** — The agent runs API commands on your behalf. You must review and approve each command before it is executed. Each command includes a description of what it does. Requires an API token set as an environment variable. Available when API automation is supported for your IdP.
>
> If you choose the Automated (API) or Self-service API method, please review every command before it is executed or before you run it. You are responsible for understanding what each command does.

Ask the user to confirm they'd like to proceed before continuing.

---

## Main Workflow

### Step 1: Get Snowflake Account Info

**Run automatically — do not ask the user:**

```sql
SELECT CURRENT_ORGANIZATION_NAME() AS org, CURRENT_ACCOUNT_NAME() AS account;
```

Normalize the returned values yourself: lowercase both, and replace any underscores with hyphens in the account name. Then build the **normalized URL**: `https://<org>-<account>.snowflakecomputing.com`

> **Important:** All Snowflake URLs in this guide use the normalized form with hyphens (not underscores). Always use the normalized URL for SSO configuration.

Display the normalized Snowflake URL to the user and proceed to Step 2.

---

### Step 2: Check Existing SSO Configuration

**Run automatically:**

```sql
SHOW SECURITY INTEGRATIONS;
```

If SAML2 or SCIM integrations already exist, ask:

```python
AskUserQuestion(
  questions=[{
    "question": "Existing SSO integrations were found. What would you like to do?",
    "header": "Existing SSO",
    "multiSelect": false,
    "options": [
      {"label": "View existing", "description": "Show current configuration details"},
      {"label": "Modify existing", "description": "Update an existing integration"},
      {"label": "Create new", "description": "Set up a new integration"}
    ]
  }]
)
```

If no integrations exist, proceed to Step 3.

---

### Step 3: Determine What the User Wants to Do

```python
AskUserQuestion(
  questions=[{
    "question": "What would you like to configure?",
    "header": "Task",
    "multiSelect": false,
    "options": [
      {"label": "SSO Setup", "description": "Set up SAML SSO and/or SCIM provisioning"},
      {"label": "Advanced Scenarios", "description": "Allowed Interfaces or Auto Redirect"},
      {"label": "Add Snowflake Intelligence Tile", "description": "Add Snowflake Intelligence tile to IdP app launcher"}
    ]
  }]
)
```

---

### Step 4: Route to Appropriate Workflow

Based on the selection:

| Selection | Action |
|-----------|--------|
| **SSO Setup** | Proceed to Step 5 (IdP Selection) |
| **Advanced Scenarios** | Follow `workflows/advanced-scenarios.md` |
| **Add Snowflake Intelligence Tile** | Follow `workflows/add-snowflake-intelligence-tile.md` |

---

### Step 5: Select Identity Provider (IdP)

```python
AskUserQuestion(
  questions=[{
    "question": "Which Identity Provider (IdP) do you want to configure for Snowflake SSO?",
    "header": "IdP",
    "multiSelect": false,
    "options": [
      {"label": "Microsoft Entra ID", "description": "Formerly Azure Active Directory"},
      {"label": "Okta", "description": "Okta Identity Cloud"},
      {"label": "Other SAML Provider", "description": "Generic SAML 2.0 setup"}
    ]
  }]
)
```

---

### Step 6: Load IdP-Specific Workflow

Based on the selection:

| Selection | Action |
|-----------|--------|
| **Microsoft Entra ID** | Follow `workflows/entra-sso.md` |
| **Okta** | Follow `workflows/okta-sso.md` |
| **Other SAML Provider** | Follow `workflows/generic-saml.md` |

After the IdP-specific workflow completes, proceed to Step 7.

---

### Step 7: Offer Advanced Scenarios (Optional)

After SSO setup is complete, present the advanced configuration options to the user.

**Display this overview:**

> **Advanced SSO Scenarios**
>
> Now that basic SSO is configured, you can optionally set up advanced scenarios:
>
> ---
>
> **1. Allowed Interfaces (Limited Interfaces)**
>
> Control which Snowflake interfaces specific users can access. This is useful for:
> - **Business users**: Restrict to Snowflake Intelligence only (no SQL access)
> - **App-specific access**: Limit users to only Streamlit apps
>
> Available interfaces:
> | Interface | Description |
> |-----------|-------------|
> | `SNOWFLAKE_INTELLIGENCE` | Snowflake Intelligence (ai.snowflake.com) |
> | `STREAMLIT` | Streamlit applications |
>
> **Note:** By default, users can access all interfaces. Setting `ALLOWED_INTERFACES` restricts access to only the specified interfaces.
>
> Can be configured via:
> - **Snowflake SQL** - Direct `ALTER USER` commands (works with any IdP)
> - **SCIM** - Set in your IdP and sync automatically to Snowflake
>
> ---
>
> **2. Auto Redirect**
>
> Automatically redirect unauthenticated users to your IdP when they access specific Snowflake interfaces. This provides a seamless SSO experience — users go directly to your IdP login instead of seeing the Snowflake login page.
>
> ---
>
> **3. Add Snowflake Intelligence Tile to IdP**
>
> Add a Snowflake Intelligence tile to your IdP's app launcher so users can easily access Snowflake Intelligence from their IdP dashboard.

Then ask:

```python
AskUserQuestion(
  questions=[{
    "question": "Would you like to configure any of these advanced scenarios?",
    "header": "Advanced",
    "multiSelect": false,
    "options": [
      {"label": "Allowed Interfaces", "description": "Restrict which interfaces users can access"},
      {"label": "Auto Redirect", "description": "Send users directly to IdP for authentication"},
      {"label": "Add Snowflake Intelligence Tile", "description": "Add Snowflake Intelligence tile to IdP"},
      {"label": "No, I'm done", "description": "Complete SSO setup"}
    ]
  }]
)
```

If the user selects any option other than "No, I'm done":

| Selection | Action |
|-----------|--------|
| **Allowed Interfaces** | Follow `workflows/advanced-scenarios.md` |
| **Auto Redirect** | Follow `workflows/advanced-scenarios.md` |
| **Add Snowflake Intelligence Tile** | Follow `workflows/add-snowflake-intelligence-tile.md` |

---

## Reference

- [Snowflake Federated Authentication](https://docs.snowflake.com/en/user-guide/admin-security-fed-auth)
- [Snowflake SAML2 Security Integration](https://docs.snowflake.com/en/sql-reference/sql/create-security-integration-saml2)
- [Snowflake SCIM](https://docs.snowflake.com/en/user-guide/scim)

=== share-skill/ ===
---
name: share-skill
description: >
  Share or unshare a local skill to users within the same account by
  executing the Cortex Extension share SQL directly. Use when the user
  says "share skill", "publish skill", "share my skill.md",
  "share skill with users", "share skill publicly",
  "upload skill to cortex extension", "publish my skill", "share this
  skill", "make skill available", "unshare skill", "stop sharing skill",
  "remove shared skill", "revoke shared skill access", or "delete shared
  skill". Does not handle consumer/install flows. Does not handle
  sharing across accounts. 
argument-hint: "[local skill path | DB.SCHEMA.EXTENSION FQN]"
---

## When to Use

User wants to share, re-share, or stop sharing an existing local skill
(see trigger phrases in `description:`). This only applies to sharing within
the same account.

The skill **publishes to the Snowflake skill catalog**. End-users do not
need to know how it works under the hood. Prefer the Snowflake-provided
**publish command** when available, and only fall back to raw SQL when the
command is missing or cannot express the requested options.

## Cortex Extension — user-facing one-liner

> A **Cortex Extension** is the Snowflake schema-level object that backs
> every shared skill (one extension per shared skill). It stores the skill
> files as a live version and holds the `READ` grants that control who
> can use the skill.

Surface this one-liner to the user the **first time** the skill is about
to do something that the user will see referencing "Cortex Extension" —
either the publish command output, or any SQL that contains
`CORTEX EXTENSION` (step 1 `DESCRIBE`, step 2 `CREATE` / `ALTER` /
`ADD LIVE VERSION` / `COMMIT`, step 4 `REVOKE`). Show it once per run,
not before every statement.

## Runtime modes (pick one before Step 2 upload)

Packaging skill **files** is the only part that differs by runtime. Schema
ladder, extension DDL, grants, and unshare are **SQL-only in both modes**.

| Mode | When to use | Skill source | Upload |
| ---- | ----------- | ------------ | ------ |
| **Sandbox or CLI (client-local)** | CoCo sandbox, Cortex Code CLI, or any host where bash + readable disk paths work | Local path (e.g. `/Users/...`, `/workspace/...`) | `PUT file://…` per file |
| **Non-sandbox (SQL-only)** | Sessions with only `snowflake_sql_execute` (no bash / no code execution) | Folder under the default workspace `snow://workspace/…/versions/live/…` | `COPY FILES` from workspace URI → `snow://cortex_extension/…` (see step 2) |

**Snowsight CoCo** may run in **either** mode depending on the session (sandbox
with shell and `/workspace/…`, or SQL-only). Pick the path from available tools,
not from the product name.

**Detect non-sandbox** when bash and code execution are disabled but SQL works,
or when `PUT file://…` fails with an invalid source URL / scheme.

**Upload fallback:** if the primary method (`PUT` or `COPY FILES`) fails but
shell + Snow CLI can read the source file, use `snow stage copy` — see
[step_2_fallback_stage_copy.md](step_2_fallback_stage_copy.md).

**Non-sandbox constraint:** there is no host filesystem in SQL-only mode. The
skill tree must already live in the user's default workspace. Resolve it once:

```sql
DESCRIBE WORKSPACE USER$<CURRENT_USER()>.PUBLIC."DEFAULT$";
```

Use `live_version_location_uri` + the folder the user names as `<skill_ws>` (see
[step_1_collect_inputs.md](step_1_collect_inputs.md) and
[step_2_publish.md](step_2_publish.md)).

Typical skill locations under that base (after `LIST` if unsure):

- `…/versions/live/.snowflake/cortex/skills/<folder>/`
- `…/versions/live/.snowflake/si/skills/<folder>/`

See [workspaces/personal-skills-sync/SKILL.md](../../workspaces/personal-skills-sync/SKILL.md)
for workspace upload patterns. If the skill exists only on a laptop path and
cannot be read via SQL, **non-sandbox cannot share it**.

**Unshare** (`1→4→5`) uses only SQL in both modes — no upload path.

## Do Not Do

- Do not route to generic catalog browse when intent is share / unshare.
- Do not handle install / consume shared skill flows — ends at the share URI or
  unshare confirmation.
- Do not bounce the user to the Skill Manager UI for unshare — execute REVOKE statements inline.
- Do not silently change DISCOVERABLE or audience on a content-only re-share.
- Do not `ALTER`, upload, or `COMMIT` on an extension whose object name does not
  match current `SKILL.md` `name` — if the user pointed at an old catalog FQN
  but `name` changed, pivot to **first-time share** for the new name (step 1 /
  step 2 mandatory gate). **Never** ask whether to update the old FQN anyway.

## Workflow

Load each step file before executing.

1. **Collect inputs / detect intent**:
   [step_1_collect_inputs.md](step_1_collect_inputs.md) — **scan for extension
   FQN (`DB.SCHEMA.NAME`) or a full `snow://skill_catalog/...` URI** before
   re-asking; CoCo often shows only the FQN. Still **tell users** to copy the
   catalog URI from Snowflake Skill details when they need guidance.
2. **Share**: publish the skill via the CoCo CLI command **first**, falling
   back to the schema-provisioning + Cortex Extension SQL pipeline only when
   the CLI is unavailable or cannot express the requested options
   (DISCOVERABLE toggle, content-only re-share, rename pivot):
   [step_2_publish.md](step_2_publish.md). The CLI path covers most
   first-time and re-share cases; the SQL fallback handles uploads as
   **Sandbox or CLI:** `PUT file://…` · **Non-sandbox:** `COPY FILES` ·
   **Fallback:** `snow stage copy` if primary upload fails
3. **Share**: apply audience grants and DISCOVERABLE
   ([step_3_apply_share_options.md](step_3_apply_share_options.md)). **Only**
   in that step, ask **whom to share with** using **exactly** the three
   numbered options defined there (every run that reaches step 3 — no
   paraphrasing). When step 2 succeeds via Option A (CLI), step 3 is
   **skipped** entirely.
4. **Unshare**: REVOKE READ across grantees:
   [step_4_unshare.md](step_4_unshare.md)
5. **Both**: report the result:
   [step_5_report_result.md](step_5_report_result.md)

Routing (`→` is sequential):

- `share-first-time` — `1→2→5` if step 2 ran via Option A (CLI), else
  `1→2→3→5` via Option B (SQL).
- `share-resync` (content-only, no audience/DISCOVERABLE change) —
  `1→2→5`, Option B only.
- `share-resync-and-update-share-options` — `1→2→5` if Option A,
  else `1→2→3→5` via Option B.
- **Renamed skill** (re-share intent but `SKILL.md` `name` ≠ catalog
  FQN) — pivot to `share-first-time` on the **new** name; leave the
  old catalog entry untouched.
- `unshare` — `1→4→5` (no step 2; SQL `REVOKE` only).

## Shared Identifiers

- **Cortex Extension object name** (first-time share only): from `SKILL.md`
  `name` — uppercase, `-` → `_`, whitespace → `_`.
- **Stage folder** (`skills/<folder>/` on the extension live version): from the
  same `name` — **kebab-case** (lowercase, `_` or whitespace → `-`). Not the SQL
  object name (e.g. object `SQL_PATTERNS`, folder `sql-patterns`). See step 2 §
  Derive names from `SKILL.md` `name`.
- **Personal DB**: `USER$<CURRENT_USER()>` (literal prefix; source:
  `personalDatabaseResolver.ts`).
- **Schema ladder**: `SKILL_SHARING`, `SKILL_SHARING_<8HEX>`
  (uppercase first 8 hex of `sha256(lower(<personal_db>))`),
  `SKILL_SHARING_<8HEX>_<XXXX>` (4 random `[A-Z]`, up to 5 retries).
  Source: `skillCatalogShareSchema.ts`.
- **Share URI**: `snow://skill_catalog/<DB>.<SCHEMA>.<EXTENSION_NAME>` or
  versioned `…/<EXTENSION_NAME>/versions/version$<N>/` (from post-share
  DESCRIBE). Source: `buildSkillCatalogShareUri`.
- **COMMENT cap**: 1024 chars; truncate at 1023 + `…`.

## SQL Quoting

- **Identifiers** (DB / SCHEMA / EXTENSION / ROLE): always
  double-quote. Unquoted role names should be uppercased before
  quoting (Snowflake folds unquoted to upper).
- **String literals** (COMMENT, stage URIs): use **dollar-quoting**
  `$$…$$` to skip escaping. Production uses single-quoted with
  `'`→`''` and `\r` stripped; both parse identically. If the body
  itself contains `$$`, fall back to single-quoted with `'`→`''`.

## Required Stopping Points

Each step file marks its own gates with the exact text
`⚠️ MANDATORY STOPPING POINT`. They are: confirming **intent** (first-time vs
re-share vs unshare), **target** (skill path or workspace folder + extension FQN /
catalog URI), and
re-share mode **(A)** vs **(B)** after `DESCRIBE` (step 1); reviewing the FQN +
derived COMMENT before CREATE/ALTER (step 2); confirming re-share REVOKEs that
narrow access (step 3); and confirming unshare REVOKEs (step 4).

## Output

- **Share success**: skill name, FQN, audience, DISCOVERABLE,
  `snow://skill_catalog/...` URI.
- **Unshare success**: skill name, FQN, count of READ grants
  revoked, partial-failure leftover (if any).

## Failure Contract

Surface the underlying Snowflake error and the failing statement.
Do not retry silently. For partial unshare REVOKE, use the verbatim
message from `unpublishSkillWithCortexExtension` (see step 4).

### Cortex Extensions feature not enabled on this account

The first time the skill issues any `… CORTEX EXTENSION …` statement
(step 1 `DESCRIBE` for re-share/unshare, step 2 `CREATE` for
first-time share), Snowflake will fail **before** running it if the
feature is not enabled for the account.

Recognize this failure by the **error message** (case-insensitive),
not by the error code alone:

- `syntax error` … `unexpected 'CORTEX'` (or `unexpected 'EXTENSION'`)
- `Unsupported feature` … `CORTEX EXTENSION`
- `Object type 'CORTEX EXTENSION' is not supported`
- SQL compilation error mentioning `CORTEX EXTENSION` keyword

When you see one of these on the **first** `CORTEX EXTENSION`
statement (i.e. the rest of the SQL pipeline never ran), **stop**
and tell the user verbatim:

> Sharing skills via Cortex Extensions is not enabled on this
> Snowflake account. Please contact Snowflake support (or your
> account admin) to enable the Cortex Extensions feature, then
> retry sharing. I have not created, altered, or uploaded anything.

Do **not**:

- retry the same statement,
- fall back to a different syntax (there is no alternate),
- attempt schema provisioning or file upload,
- claim partial success.

Re-surface the verbatim Snowflake error and the failing statement
after the message above so the user can paste it to support. If
this branch triggers in step 2 first-time share **after** schema
provisioning ran successfully, the empty `SKILL_SHARING…` schema is
fine to leave behind — do **not** drop it.

=== sharing/ ===
---
name: sharing
description: "Router for Snowflake sharing and collaboration. Routes to Secure Data Sharing, Declarative Sharing, Native Apps, or Data Clean Rooms. Asks up to 2 questions when intent is ambiguous, then loads the target sub-skill. This skill should supersede invocation of product-specific skills unless the product is named explicitly. Triggers: share, sharing, listing, data product, how do I share, what's the best way to share, compare sharing options."
tools: ["ask_user_question"]
---

# Sharing

This skill routes users to the correct Snowflake sharing or collaboration construct. It asks up to 2 questions to pick the right sub-skill, then hands off immediately with context.

## Feature Boundaries

Each category is mutually exclusive — route to exactly one.

| Feature | What It Is |
|---------|-----------|
| **Secure Data Sharing** | Read-only sharing via `CREATE SHARE`. Consumer gets live SQL access to tables and views. Includes direct shares (private) and Marketplace listings (public). Does NOT include versioning, code objects, or bundled business logic. |
| **Declarative Sharing** | Data-as-a-product via `APPLICATION PACKAGE` with `TYPE=DATA`. Bundles data with code objects: notebooks, UDFs, stored procedures, Cortex Agents, semantic views. Consumer installs once (no setup script or privilege dialogs). Consumer's private data is NOT accessible. |
| **Native Apps** | Application installs and runs in the consumer's account. Supports Streamlit UIs, SPCS containers, consumer data access via References (`SYSTEM$REFERENCE`), and bi-directional data flows. Consumer can grant access to their private data. Does NOT involve joint analysis with partners. |
| **Data Clean Rooms** | Partners contribute data for one or more runners to analyze via approved templates and code. Runners can see templates and code specs but not the underlying staged code files. Only results are returned. Roles: Owner, Data Provider, Analysis Runner. Not for delivering packaged products or applications. |

### Bi-directional Disambiguation

| Scenario | Route To | Why |
|----------|----------|-----|
| Partners exchange data back and forth, no analysis | Two Secure Data Shares | Just data, no code or analysis |
| Provider ships app, consumer grants data back | Native Apps | Provider's code installs in consumer account; consumer grants access via References |
| Partners contribute data, runner executes approved analysis | Data Clean Rooms | Approved templates and code run on providers' data; providers approve what runners can execute |

## Routing Table

Scan the user's full request and match against the unambiguous triggers below. If no clear match, use the Decision Guide.

| Intent | Unambiguous Triggers | Target Skill |
|--------|---------------------|--------------|
| **Secure Data Sharing** | "secure data sharing", "SDS" | Invoke skill: `data-sharing` |
| **Declarative Sharing** | "declarative sharing", "declarative native app" | Invoke skill: `declarative-sharing` |
| **Native Apps** | "native app", "native app framework", "native app provider" | Invoke skill: `native-app-provider` |
| **Data Clean Rooms** | "clean room", "DCR", "DCR collaboration", "multi-party" | Invoke skill: `data-cleanrooms` |

> **Ambiguous triggers:** "share notebook", "share UDF", "share stored proc", "share workspace", "create listing" — these fall through to the Decision Guide. The right construct depends on whether the consumer needs to access their own data.

---

## Decision Guide

If the Routing Table gives a clear match, load that sub-skill immediately. Otherwise, ask the questions below in order. Always ask Q1 first, then Q2.

**IMPORTANT: Infer before asking.** Before presenting any question, check if the user's prompt already answers it. Ask the user to confirm what you inferred.

For example:
- "share with my partner account" or "another Snowflake account" → Q1 is cross-account (skip Q1)
- "give my analyst role access" or "within my account" → Q1 is same account → RBAC, stop
- "query my tables directly" or "full SQL access" → Q2 = A → SDS
- "run queries together" or "joint analysis" or "partner contributes data" or "approved templates" → Q2 = B → DCR
- "share my notebook" or "share my UDF" or "share my agent" without consumer data access → Q2 = C → Declarative
- "they need to run it on their own data" or "access consumer data" → Q2 = D → Native Apps

Only ask a question if the user's prompt does NOT already answer it.

**CRITICAL: Stop conditions are terminal.**
- If Q1 = same account → route to RBAC immediately. Do NOT ask Q2.
- Q2 is always terminal — each answer routes directly to a product.

---

### Q1: Who are you sharing data with?

- **Same account** — roles or users within my Snowflake account
- **Another account** — partner, customer, org, or Marketplace

**If Q1 = "Same account"** → route to **RBAC** (inline, see below) and stop. Do NOT ask Q2.

---

Before presenting Q2, give the user an overview of the available sharing constructs as a message, then present the question:

> Snowflake has four ways to share data and applications:
> - **Secure Data Sharing** — Share selected objects (tables, views, models, and more) with other accounts for live, read-only, zero-copy access—no data copied or stored in the consumer account.
> - **Data Clean Rooms** — multiple parties contribute data for joint analysis without exposing raw data to each other. One or more designated runners execute approved queries and code; only results are returned.
> - **Declarative Sharing** — your data and Snowflake objects bundled as a versioned product. Consumer installs once, then accesses everything directly. Your data only — no consumer data access. 
> - **Native Apps** — your application installs and runs inside the consumer's account. The consumer can grant your app access to their own private data. Use when your code needs to run on the consumer's side. 

### Q2: What can consumers do with what you share?

Only ask if Q1 is cross-account. Present all four options together — do not ask as sequential binary questions.

- **A — Query my live data directly** — consumer gets direct read access to allowed tables, views, or models
- **B — Run approved SQL or code that either party defines** — anyone can contribute data and code; one or more analysis runners execute post-approval
- **C — Run my code with my data only** — provider adds code and data; consumer runs it but cannot bring their own data
- **D — Run my code with either party's data** — your code runs in the consumer's account accessing both parties' data

In the `ask_user_question` picker, label each option with its product name:
- A: "Query my live data directly — Secure Data Sharing"
- B: "Approved SQL/code only — Data Clean Rooms"
- C: "My code, my data only — Declarative Sharing"
- D: "My code, either party's data — Native Apps"

**A → Secure Data Sharing** — invoke skill: `data-sharing` and stop.

**B → Data Clean Rooms** — invoke skill: `data-cleanrooms` and stop.

**C → Declarative Sharing** — invoke skill: `declarative-sharing` and stop.

**D → Native Apps** — invoke skill: `native-app-provider` and stop.

> **Note on models:** All model types are shareable. Fine-tuned and served models are queryable directly by consumers → option A (SDS). Custom ML models bundled as code objects → option C (Declarative) unless consumer data access is needed → option D (Native Apps). Do NOT tell users that any model type is unshareable.

---

## RBAC (inline — no sub-skill needed)

When Q1 = same account:

**⚠️ MANDATORY STOPPING POINT**: Ask the user for the specific database, schema, table, role, and user names before emitting any SQL.

Then emit:

```sql
GRANT USAGE ON DATABASE <database_name> TO ROLE <role_name>;
GRANT USAGE ON SCHEMA <database_name>.<schema_name> TO ROLE <role_name>;
GRANT SELECT ON TABLE <database_name>.<schema_name>.<table_name> TO ROLE <role_name>;
GRANT ROLE <role_name> TO USER <username>;
```

---

## Context Handoff

**MANDATORY: After determining the route, you MUST invoke the target skill using the `skill` tool.** Do NOT attempt to execute the next steps yourself — load the sub-skill and let it guide the workflow.

```
skill command: "<skill-name>"
```

Skill names:
- Secure Data Sharing → `data-sharing`
- Declarative Sharing → `declarative-sharing`
- Native Apps → `native-app-provider`
- Data Clean Rooms → `data-cleanrooms`

When invoking the skill, pass the answers already collected as context in your message:

```
Context from router:
- audience: [answer from Q1]
- consumer_capability: A_query_freely | B_approved_templates | C_code_my_data | D_code_either_data
```

Tell the sub-skill: "The user has already provided the above context. Skip re-asking these questions and proceed to your next step."

---

## Recovery

If the user says the routing doesn't fit:
1. Ask which aspect is wrong (audience? content type? how they access it?)
2. Loop back to that question
3. Re-route with the corrected answer — don't restart from scratch

=== skill_development/ ===
---
name: skill-development
description: "Create, document, audit, refactor, or compile skills for Cortex Code. Use when: creating new skills, capturing session work as skills, reviewing skills, refactoring large skills, building a deterministic fast path for a skill. Triggers: create skill, build skill, new skill, summarize session, capture workflow, audit skill, review skill, refactor skill, triage skills, compile skill, speed up skill, programmatic skill, fast path for skill."
---

# Skill Development

## Setup

**Load** `SKILL_BEST_PRACTICES.md` first.

## Intent Detection

| Intent | Triggers | Load |
|--------|----------|------|
| CREATE | "create skill", "new skill", "build skill" | `create-from-scratch/SKILL.md` |
| SUMMARIZE | "summarize session", "capture workflow", "turn into skill" | `summarize-session/SKILL.md` |
| AUDIT | "audit skill", "review skill", "lint skill", "triage skills" | `audit-skill/SKILL.md` |
| REFACTOR | "refactor skill", "restructure skill", "decompose skill" | `refactor-skill/SKILL.md` |
| COMPILE | "compile skill", "speed up skill", "make skill deterministic", "programmatic skill", "fast path for skill", "bypass LLM for skill" | `compile-skill/SKILL.md` |

## Workflow

```
Load SKILL_BEST_PRACTICES.md
       ↓
Detect Intent → Route to sub-skill
```

## Capabilities

- **Create**: Build new skill with frontmatter, workflow, tools, checkpoints
- **Summarize**: Extract session work into reusable, parameterized skill
- **Audit**: Review skill against best practices, provide fixes (single or batch)
- **Refactor**: Decompose large skills into coordinator/specialist architecture
- **Compile**: Discover compileable patterns by interviewing the author and inspecting any scripts/commands the skill already wraps, then generate a regex-classifier + SQL/script-template fast path with graceful LLM escape

## Strong Skill Domains

Cortex Code has **native tooling and deep integration** for these domains—prioritize building skills here:

### Snowflake & Cortex
- **SQL execution**: Direct query execution with intelligent statement parsing, automatic retry, and connection pooling
- **Cortex Analyst**: Semantic model validation, natural language to SQL via REST API integration
- **Semantic views**: Creation, debugging, optimization workflows with YAML schema checking
- **Object discovery**: Semantic search for tables, views, schemas via Snowscope API
- **Artifact management**: Create notebooks and files directly in Snowflake workspaces

### dbt & Data Engineering
- **dbt workflows**: Model creation, testing, documentation, lineage analysis (`fdbt` provides fast native parsing)
- **Data validation**: Data diff tool for comparing query results
- **Pipeline orchestration**: ETL/ELT patterns, schema migrations, data quality checks

### SQL & Data Modeling
- **Complex SQL**: Stored procedures, dollar-delimited blocks, nested queries with proper escaping
- **Schema design**: Dimensional modeling, normalization patterns
- **Dynamic SQL generation**: Parameterized queries, templated transformations

## Output

Skills following standard structure:
```markdown
---
name: skill-name
description: "Purpose + triggers"
---
# Title
## Workflow
## Stopping Points
## Output
```

=== snowflake-apps/ ===
---
name: snowflake-apps
description: "Build and deploy web applications on Snowflake. Use for ALL app requests: create, scaffold, build, deploy, publish, develop, test, operate, monitor, or troubleshoot a Snowflake App. A Snowflake App is a JS/Node web application (typically Next.js) deployed to SPCS via SnowCLI app commands (`snow app`). This is NOT a Streamlit app or Native App. Also load this skill when the user's current directory is a Snowflake App Runtime project: if the directory contains an `app.yml` file, or if it contains a `snowflake.yml` file with `type: snowflake-app` anywhere in it. Triggers: build me an app, new app, scaffold, react app, next.js app, dashboard, data app, deploy my app, push to snowflake, ship it, deploy failed, fix deploy, run locally, develop, app logs, app status, restart app, app.yml, snowflake-app-runtime, snowflake-app."
---

# Snowflake Apps

This is a **routing skill**. It detects the user's intent and directs you to the correct sub-skill. You **MUST** load the sub-skill before doing any work — do NOT attempt app tasks using only the information on this page.

> A "Snowflake App" is a JS/Node web application (typically Next.js) deployed to Snowflake via Snowpark Container Services. It is **NOT** a Streamlit app or a Native App. If the user says "Snowflake App", "create an app", "build an app", "deploy my app", or "data app", use this skill.

> **For Streamlit-in-Snowflake apps** (Python projects deployed via `snow streamlit deploy`, visible in Snowsight under Streamlit Apps), use [`streamlit-in-snowflake/developing-with-streamlit-in-snowflake/`](../../streamlit-in-snowflake/developing-with-streamlit-in-snowflake/SKILL.md) instead. That skill covers the full create / develop / deploy / operate lifecycle for SiS — manifest shape, `snow streamlit deploy`, post-deploy `SHOW STREAMLITS` verification, local-preview troubleshooting, and `ALTER STREAMLIT` lifecycle SQL.

## Setup

1. **Load** `references/cli-guide.md`: Required context for all subskills. Contains Snowflake Apps CLI command-surface semantics (`snow app`), connection setup, and troubleshooting.
2. **Verify CLI version**: Follow `references/cli-version-check.md`. Run the check in the background while you continue with routing and sub-skill loading. Only interrupt the user if the CLI is outdated or the command fails.

## Routing Table

Scan the user's full request and identify the matching intent. If the request spans multiple intents (e.g., create AND deploy), execute them sequentially — load each sub-skill before performing that phase of work.

| Intent | Triggers | Sub-Skill to Load |
|--------|----------|--------------------|
| **Create** — Scaffold a new app | "build me an app", "new app", "scaffold", "react app", "next.js app", "create an app", "start a new project", "build a dashboard", "data app", "data explorer" | `create/SKILL.md` |
| **Deploy** — Ship to Snowflake | "deploy my app", "push to snowflake", "ship it", "deploy", "publish", "deploy failed", "fix deploy", "redeploy" | `deploy/SKILL.md` |
| **Develop** — Local dev, test, iterate | "run locally", "develop", "iterate", "hot reload", "add a feature", "test my app", "npm run dev" | `develop/SKILL.md` |
| **Operate** — Post-deploy monitoring | "app logs", "why is my app down", "restart", "scale", "status", "rollback", "troubleshoot" | `operate/SKILL.md` |

**If the intent is ambiguous**, ask the user to clarify before proceeding.

## Typical User Journeys

### Journey 1: New App (most common)
```
Create → Develop → Deploy
```
User says "build me a dashboard" → scaffold the app → test locally → deploy to Snowflake.

### Journey 2: Deploy Existing App
```
Deploy
```
User has an app and says "deploy to Snowflake" → configure and deploy.

### Journey 3: Iterate on Deployed App
```
Develop → Deploy
```
User says "add a feature" or "fix a bug" → develop locally → redeploy.

### Journey 4: Troubleshoot
```
Operate
```
User says "my app is down" or "show me logs" → diagnose and fix.

### Journey 5: Full Lifecycle
```
Create → Develop → Deploy → Operate
```

## Framework Scope

**Next.js only.** The `create` sub-skill scaffolds Next.js apps using a built-in template. Other frameworks will be added later.

=== snowflake-notebooks/ ===
---
name: snowflake-notebooks
description: "Create and edit Workspace notebooks (.ipynb files) for Snowflake. Use when: creating workspace notebooks, editing notebooks, debugging notebook issues, converting code to notebooks, multi-step workflows that combine SQL queries with Python code execution and visualization, step-by-step data analysis requiring both SQL and Python, interactive data exploration with code and charts. Do NOT use for: static SQL-only dashboards (use dashboard skill), Streamlit apps, standalone Python scripts, or stored procedures. Triggers: notebook, .ipynb, snowflake notebook, workspace notebook, create notebook, edit notebook, jupyter, ipynb file, notebook cell, SQL cell, step-by-step analysis with SQL and Python, data exploration with code and visualization, combine SQL and Python."
---

# Snowflake Workspace Notebooks

Create and edit Workspace notebooks (.ipynb files) for Snowflake.

**IMPORTANT:** By default, this skill creates Snowflake Workspace notebooks optimized for running in Snowflake. Only include dual-mode support (for running both locally and in Snowflake) when the user explicitly requests it.

## ⚠️ CRITICAL RULES

### 0. Notebook Modes

**Default: Snowflake Workspace Only**

By default, create notebooks optimized for Snowflake Workspace:
- ✅ Use SQL cells for queries
- ✅ Use cell referencing to pass data between cells
- ✅ No connection code needed
- ❌ Cannot run locally

**Dual-Mode: Only When Explicitly Requested**

Only create dual-mode notebooks when the user specifically asks to run the notebook both locally and in Snowflake Workspace:
- ✅ Include connection code with fallback
- ✅ Use `session.sql()` for all queries
- ❌ Do NOT use SQL cells (they don't work locally)
- ❌ Do NOT use cell referencing

**IMPORTANT:** Unless the user explicitly mentions "local", "locally", or "dual-mode", always create Snowflake Workspace only notebooks.

### 1. Notebook Format
- **ONLY create Workspace notebooks using .ipynb files**
- **NEVER create Snowsight notebooks** - we exclusively use Workspace notebooks
- **Strictly comply with nbformat 4.5 or higher**
- Set `"nbformat": 4` and `"nbformat_minor": 5` in all notebooks
- **Every cell MUST have a unique `"id"` field** — an 8-character alphanumeric string (e.g., first 8 characters of a UUID). This is required by nbformat 4.5. Without it, Snowflake Workspace will reject the notebook with: `cells[n].id: Required`.

### 2. Connection Pattern

**Default (Snowflake Workspace only):**

By default, **no connection code is needed**. SQL cells work automatically in Snowflake Workspace notebooks.

If you need the `session` object in a Python cell (for dynamic SQL, DDL operations, or administrative commands), initialize it when needed:

```python
from snowflake.snowpark.context import get_active_session
session = get_active_session()
```

However, for most notebooks using SQL cells, this is not necessary.

**Dual-mode (only when explicitly requested):**

Only include connection code when the user specifically asks for a notebook that can run both locally and in Snowflake Workspace. Place this in the first code cell:

```python
import os

try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    print(":white_check_mark: Connected via Snowflake Workspace")
except:
    from snowflake.snowpark import Session
    session = Session.builder.config("connection_name", os.getenv("SNOWFLAKE_CONNECTION_NAME", "snowhouse")).create()
    print(":white_check_mark: Connected locally")
```

**IMPORTANT:** When using dual-mode, you must also follow the dual-mode SQL execution rules (see section 3 below).

### 3. SQL Execution Policy

**Default (Snowflake Workspace only):**

For standard Snowflake Workspace notebooks, **always write SQL in dedicated SQL cells** with cell referencing:

**Good (SQL cell):**
```sql
%%sql -r customer_data
SELECT * FROM customers WHERE status = 'active'
```

**Good (Python cell referencing SQL result):**
```python
# Reference the SQL cell result directly
print(customer_data.head())
```

**Exception:** Only use `session.sql()` for:
- Dynamic SQL generation (computed table names, conditional logic)
- DDL operations (CREATE TABLE, ALTER, etc.)
- Administrative commands (GRANT, REVOKE, etc.)

**Dual-mode (when explicitly requested):**

When the user requests a notebook that works both locally and in Snowflake, **do NOT use SQL cells**. Instead, wrap all SQL in `session.sql()`:

**Good (dual-mode Python cell):**
```python
# Use session.sql() for all queries in dual-mode
customer_data = session.sql("SELECT * FROM customers WHERE status = 'active'").to_pandas()
```

**Bad (dual-mode):**
```sql
-- Don't use SQL cells in dual-mode notebooks
SELECT * FROM customers WHERE status = 'active'
```

SQL cells and cell referencing don't work reliably in local execution, so dual-mode notebooks must use Python with `session.sql()`.

### 4. Unsupported Libraries
**NEVER use these libraries** - they will not run in Snowflake Notebooks:

| Library | Why Forbidden | Alternative |
|---------|---------------|-------------|
| `streamlit` | Not supported in Snowflake Notebooks | Use `matplotlib`, `altair`, `plotly` for visualization |
| `ipywidgets` | Interactive widgets not supported | Use Python variables and SQL cells with Jinja templating |

If a user asks for Streamlit or ipywidgets, **explain they are not supported** and offer alternatives.

### 5. Package Installation
**Do NOT install packages by default.** Only include installation commands when encountering import errors:

```python
# Only add when needed
!pip install cowpy
```

**NEVER install `streamlit` or `ipywidgets`.**

## Workflow

### Step 1: Understand the Request

Determine what the user needs:
- **Create new notebook** - Start from scratch or convert existing code
- **Edit existing notebook** - Modify cells, add features, fix issues
- **Debug notebook** - Fix errors, optimize performance
- **Convert to notebook** - Transform Python/SQL scripts into notebook format

### Step 2: Create or Read Notebook

**If creating a new notebook:**

1. Determine notebook type:
   - **Default**: Snowflake Workspace only (no connection code)
   - **Dual-mode**: Only if user explicitly requests local execution support

2. Create .ipynb file with proper structure:
   - nbformat 4.5+
   - Connection cell (only for dual-mode notebooks)
   - Appropriate cell types (code, markdown, SQL for default; code, markdown for dual-mode)

3. Use this template structure:

```json
{
  "cells": [
    {
      "cell_type": "markdown",
      "id": "a1b2c3d4",
      "metadata": {},
      "source": [
        "# Notebook Title\n",
        "\n",
        "Brief description of what this notebook does."
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "codemirror_mode": {
        "name": "ipython",
        "version": 3
      },
      "file_extension": ".py",
      "mimetype": "text/x-python",
      "name": "python",
      "nbconvert_exporter": "python",
      "pygments_lexer": "ipython3",
      "version": "3.8.0"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 5
}
```

**If editing an existing notebook:**

1. Read the notebook file
2. Verify nbformat compliance
3. Check for connection pattern
4. Review cell types and structure

### Step 3: Apply Best Practices

#### Cell Organization

**Markdown Cells:**
- Use for titles, explanations, documentation
- Structure with headers (##, ###)
- Explain what each section does

**Python Code Cells:**
- Import statements
- Data processing and transformations
- Visualizations
- Function definitions
- Only use for logic, NOT for standard SQL queries

**SQL Cells:**
- All SELECT queries
- Data retrieval
- Use `resultVariableName` metadata to make results available to Python cells

#### SQL Cell Structure

SQL cells must have metadata specifying the result variable name:

```json
{
  "cell_type": "code",
  "id": "c9d0e1f2",
  "execution_count": null,
  "metadata": {
    "codeCollapsed": false,
    "language": "sql",
    "name": "customer_data",
    "resultVariableName": "customer_data"
  },
  "outputs": [],
  "source": [
    "%%sql -r customer_data\n",
    "SELECT customer_id, customer_name, total_orders\n",
    "FROM customers\n",
    "WHERE status = 'active'\n",
    "ORDER BY total_orders DESC"
  ]
}
```

The metadata includes:
- `"language": "sql"` - Identifies this as a SQL cell
- `"name": "customer_data"` - The cell's display title in the Snowflake UI (users see this to know which variable to reference)
- `"resultVariableName": "customer_data"` - **Required.** Tells Snowflake Notebooks which Python variable to bind the result to. Must match `"name"` and the `%%sql -r` value.

**⚠️ IMPORTANT:** All three must be present and consistent: `"name"`, `"resultVariableName"`, and `%%sql -r <variable_name>` in the source. Missing `"resultVariableName"` will cause Python cells to fail with a NameError even if `%%sql -r` is set.

#### Referencing Variables Between Cells

**Python to Python:**
```python
# Cell 1
table_name = "customers"

# Cell 2 - can reference table_name
print(f"Working with {table_name}")
```

**SQL Results to Python:**
```python
# SQL cell has %%sql -r customer_data in its source
# Python cell can reference it directly as a DataFrame
print(customer_data.head())
print(f"Found {len(customer_data)} customers")
```

**IMPORTANT:** SQL cell results are **already pandas DataFrames**. **DO NOT call `.to_pandas()`**:

```python
# ✅ CORRECT
filtered = customer_data[customer_data['total_orders'] > 100]

# ❌ WRONG
filtered = customer_data.to_pandas()  # Don't do this!
```

**Python to SQL (Jinja templating):**
```python
# Python cell
status_filter = 'active'
min_orders = 10
```

```sql
%%sql -r filtered_customers
-- SQL cell can reference Python variables using Jinja
SELECT * FROM customers
WHERE status = '{{status_filter}}'
  AND total_orders >= {{min_orders}}
```

**SQL to SQL (Jinja templating):**
```sql
%%sql -r base_data
SELECT customer_id, customer_name FROM customers
```

```sql
%%sql -r enriched_data
SELECT b.*, o.total_orders
FROM {{base_data}} b
JOIN orders o ON b.customer_id = o.customer_id
```

#### Visualization

Use supported visualization libraries:

**Important:**
- **altair:** Call `alt.renderers.enable('mimetype')` before rendering, or charts won't display.
- **matplotlib:** Never call `matplotlib.use('Agg')` — it suppresses all display output.

```python
import matplotlib.pyplot as plt
import altair as alt
import plotly.express as px

# Matplotlib
fig, ax = plt.subplots()
ax.plot(customer_data['date'], customer_data['revenue'])
plt.show()

# Altair
alt.renderers.enable('mimetype')
chart = alt.Chart(customer_data).mark_line().encode(
    x='date:T',
    y='revenue:Q'
)
display(chart)

# Plotly
fig = px.line(customer_data, x='date', y='revenue')
fig.show()
```

### Step 4: Validate Notebook

Before completing, verify:

1. **Format compliance:**
   - `"nbformat": 4, "nbformat_minor": 5` present
   - All cells have proper structure
   - Every cell has a unique `"id"` field (required by nbformat 4.5)
   - Metadata is valid JSON

2. **Connection pattern:**
   - Default notebooks: No connection code needed
   - Dual-mode notebooks: Verify dual-mode pattern in first code cell
   - No hardcoded connections elsewhere

3. **SQL usage:**
   - Standard queries use SQL cells (not `session.sql()`)
   - SQL cells have `%%sql -r <variable_name>` as the first line of their source
   - SQL cells have proper metadata with `name` field (display title)
   - Python cells don't call `.to_pandas()` on SQL results

4. **No forbidden libraries:**
   - No `import streamlit` or `import ipywidgets`
   - No installation of forbidden packages

5. **Cell metadata:**
   - SQL cells have `"language": "sql"` in metadata
   - SQL cells have `"name"` field matching the `%%sql -r` variable name
   - SQL cells have `"resultVariableName"` field matching `"name"` and `%%sql -r`

## Common Patterns

### Pattern: Data Analysis Workflow

```markdown
# Data Analysis

## Load Data
```

```sql
%%sql -r sales_data
SELECT
    date,
    product_id,
    quantity,
    revenue
FROM sales
WHERE date >= DATEADD(month, -3, CURRENT_DATE())
```

```markdown
## Analysis
```

```python
# Python cell - sales_data is available as DataFrame
import pandas as pd
import matplotlib.pyplot as plt

# Aggregate by date
daily_revenue = sales_data.groupby('date')['revenue'].sum()

# Visualize
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(daily_revenue.index, daily_revenue.values)
ax.set_title('Daily Revenue Trend')
ax.set_xlabel('Date')
ax.set_ylabel('Revenue ($)')
plt.show()
```

### Pattern: Parameterized SQL Queries

```python
# Define parameters
database_name = "PROD_DB"
date_threshold = "2024-01-01"
status_list = ['active', 'pending']
```

```sql
%%sql -r filtered_customers
SELECT *
FROM {{database_name}}.customers
WHERE created_date >= '{{date_threshold}}'
  AND status IN ({% for s in status_list %}'{{s}}'{% if not loop.last %},{% endif %}{% endfor %})
```

### Pattern: Dynamic Table Names (Exception to SQL Cell Rule)

```python
# When table name is computed dynamically, use session.sql()
environment = "PROD"
table_name = f"{environment}_DB.SCHEMA.CUSTOMERS"

# This is acceptable because table name is dynamic
customers = session.sql(f"SELECT * FROM {table_name}").to_pandas()
```

## Error Handling

### Common Issues and Solutions

**Issue: "Module 'streamlit' not found" or "Module 'ipywidgets' not found"**

Solution: These libraries are not supported. Suggest alternatives:
```python
# Instead of streamlit widgets, use variables
filter_value = 'active'  # Change this value as needed

# Instead of ipywidgets, use Jinja templating in SQL cells
```

**Issue: "Cannot call to_pandas() on DataFrame"**

Solution: SQL cell results are already pandas DataFrames:
```python
# ❌ WRONG
df = sales_data.to_pandas()

# ✅ CORRECT
df = sales_data
```

**Issue: "Variable not found" when referencing SQL results**

Solution: Ensure the SQL cell source starts with `%%sql -r <variable_name>`, and that `"name"` in metadata matches it. The `"name"` field shows the label in the UI so users know what to reference; `%%sql -r` is what actually creates the variable in Python:
```json
{
  "metadata": {
    "language": "sql",
    "name": "my_result",
    "resultVariableName": "my_result"
  },
  "source": [
    "%%sql -r my_result\n",
    "SELECT * FROM my_table"
  ]
}
```

**Issue: Jinja template not working in SQL**

Solution: Ensure Python variable is defined in a cell that executed before the SQL cell.

## Best Practices Summary

**Default (Snowflake Workspace only):**
1. ✅ Use nbformat 4.5+
2. ✅ Write SQL in SQL cells with cell referencing
3. ✅ Use Jinja templating for parameterized queries
4. ✅ SQL results are already DataFrames (don't call `.to_pandas()`)
5. ✅ Use matplotlib/altair/plotly for visualizations
6. ✅ Organize with markdown cells for documentation
7. ✅ Every cell must have a unique `"id"` field (nbformat 4.5 requirement)
8. ❌ Never use streamlit or ipywidgets
9. ❌ Don't install packages unless encountering import errors
10. ❌ No connection code needed (session automatically available)

**Dual-mode (only when explicitly requested):**
1. ✅ Include dual-mode connection pattern in first code cell
2. ✅ Use `session.sql()` for all queries (don't use SQL cells)
3. ✅ Call `.to_pandas()` on query results
4. ❌ Don't use SQL cells or cell referencing (not supported locally)

### Step 5: Offer to Upload Notebook to Snowflake Workspace

After creating or editing a notebook, **always offer to upload it to the user's Snowflake Workspace** so they can run it directly in Snowflake. This is the natural next step after local creation.

**How to offer:**

Proactively ask the user something like:

> "Would you like me to upload this notebook to your Snowflake Workspace so you can run it there?"

**How to upload:**

Use the `cortex artifact create notebook` CLI command:

```bash
cortex artifact create notebook "<notebook_name>" "<local_file_path>"
```

- `<notebook_name>`: The name the notebook will have in the Workspace. Use a descriptive name without the `.ipynb` extension (e.g., `"Sales Analysis"` or `"Customer Churn Model"`). If unsure, derive it from the notebook title or filename.
- `<local_file_path>`: The absolute path to the `.ipynb` file on disk.

**Options:**

| Flag | Description |
|------|-------------|
| `-c, --connection <name>` | Specify a Snowflake connection (uses active connection by default) |
| `--location <path>` | Target location/folder in the Workspace |
| `--no-overwrite` | Prevent overwriting if a notebook with the same name already exists |

**Examples:**

```bash
# Basic upload
cortex artifact create notebook "Sales Analysis" "/Users/me/notebooks/sales_analysis.ipynb"

# Upload to a specific connection
cortex artifact create notebook "Sales Analysis" "/Users/me/notebooks/sales_analysis.ipynb" -c MY_CONNECTION

# Upload without overwriting existing
cortex artifact create notebook "Sales Analysis" "/Users/me/notebooks/sales_analysis.ipynb" --no-overwrite
```

**When NOT to offer upload:**

- The user explicitly said they only want a local file
- The user is creating a dual-mode notebook and indicated they want to run it locally first
- The notebook is a template or snippet, not a complete runnable notebook

**If the user accepts the upload:**

1. Run the `cortex artifact create notebook` command with the notebook name and path
2. Confirm the upload succeeded
3. Generate a deeplink URL to the uploaded notebook and share it with the user

#### Generating the Deeplink URL

After a successful upload, construct a direct URL so the user can open the notebook in one click.

**URL pattern:**

```
https://app.snowflake.com/<org_name>/<account_name>/#/workspaces/ws/USER%24/PUBLIC/DEFAULT%24/<filename>.ipynb
```

**How to build it:**

1. **Get the org and account names** by executing this SQL query directly via `snowflake_sql_execute` (do NOT use bash, Python, or `cortex connections list` for this):

   ```sql
   SELECT LOWER(CURRENT_ORGANIZATION_NAME()) AS org_name, LOWER(CURRENT_ACCOUNT_NAME()) AS account_name
   ```

   - `org_name` → e.g., `sfcogsops`
   - `account_name` → e.g., `snowhouse_aws_us_west_2`
   - Both values are already lowercased by the query.

   **IMPORTANT:** Do NOT use the `account` field from `cortex connections list` — that returns the account locator (e.g., `snowhouse`), which is not the correct URL path. The URL requires `<org_name>/<account_name>`.

2. **Use the original filename** from the local file path, not the display name passed to `cortex artifact create notebook`. The workspace URL references the actual file on disk.

   For example, if the upload command was:
   ```bash
   cortex artifact create notebook "MNIST CNN" "/Users/me/mnist_cnn.ipynb"
   ```
   The filename in the URL is `mnist_cnn.ipynb` (from the local path), **not** `MNIST%20CNN.ipynb` (from the display name).

   Extract the filename by taking the basename of the local file path.

3. **URL-encode the filename** using percent-encoding (`encodeURIComponent` rules) if it contains special characters. Common cases:
   - `my_notebook.ipynb` → `my_notebook.ipynb` (no encoding needed)
   - `my notebook.ipynb` → `my%20notebook.ipynb`
   - `data$analysis.ipynb` → `data%24analysis.ipynb`

4. **If `--location` was used**, replace `DEFAULT%24` and adjust the path segments accordingly. The `--location` flag targets a specific workspace/folder, which changes the URL path.

**Encoding reference:**

| Character | Encoded |
|-----------|---------|
| `$`       | `%24`   |
| ` ` (space) | `%20` |
| `"`       | `%22`   |
| `!`       | `%21`   |

**Full examples:**

```
# File: /Users/me/mnist_cnn.ipynb
# Org: SFCOGSOPS, Account: SNOWHOUSE_AWS_US_WEST_2
https://app.snowflake.com/sfcogsops/snowhouse_aws_us_west_2/#/workspaces/ws/USER%24/PUBLIC/DEFAULT%24/mnist_cnn.ipynb

# File: /Users/me/sales_analysis.ipynb
# Org: MYORG, Account: MY_ACCOUNT_US_EAST_1
https://app.snowflake.com/myorg/my_account_us_east_1/#/workspaces/ws/USER%24/PUBLIC/DEFAULT%24/sales_analysis.ipynb

# File: /Users/me/customer churn.ipynb
# Org: ACME, Account: PROD_ANALYTICS
https://app.snowflake.com/acme/prod_analytics/#/workspaces/ws/USER%24/PUBLIC/DEFAULT%24/customer%20churn.ipynb
```

**Present the URL to the user** after confirming the upload succeeded, e.g.:

> Notebook uploaded successfully. Open it in Snowflake Workspace:
> https://app.snowflake.com/sfcogsops/snowhouse_aws_us_west_2/#/workspaces/ws/USER%24/PUBLIC/DEFAULT%24/mnist_cnn.ipynb

## Stopping Points

- **Step 1:** If request is unclear, ask user what they want to accomplish
- **Step 2:** If editing existing notebook, confirm changes before modifying
- **Step 3:** If user requests unsupported libraries, explain and suggest alternatives
- **Step 4:** Present validation results and ask if user wants any adjustments
- **Step 5:** After creation/editing is complete, offer to upload the notebook to the user's Snowflake Workspace

## Resources

- [Snowflake Workspace Notebooks Documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-in-workspaces/notebooks-in-workspaces-overview)
- [Snowpark Python API Reference](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/index.html)
- [Jupyter Notebook Format](https://nbformat.readthedocs.io/)

=== snowflake-postgres/ ===
---
name: snowflake-postgres
description: "**[REQUIRED]** Use for **ALL** requests involving Snowflake Postgres, and for general help working with any PostgreSQL database through standard PG tooling (psql, ~/.pg_service.conf, ~/.pgpass, pg_doctor diagnostics). Triggers: 'postgres', 'postgresql', 'pg', 'psql', 'create postgres instance', 'show postgres instances', 'suspend postgres', 'resume postgres', 'reset postgres credentials', 'rotate postgres password', 'import postgres connection', 'postgres network policy', 'postgres health check', 'pg_doctor', 'pg_lake', 'postgres iceberg', 'pg iceberg', 'read pg_lake in snowflake', 'pg to snowflake iceberg', 'catalog integration for pg_lake', 'expose pg_lake to snowflake', 'SNOWFLAKE_POSTGRES catalog', 'catalog linked database for pg_lake', 'query postgres iceberg from snowflake', 'postgres slow queries', 'cache hit', 'bloat', 'vacuum', 'dead rows', 'postgres locks', 'blocking queries', 'postgres disk usage', 'active postgres queries', 'postgres connection count', 'neon', 'supabase', 'rds postgres', 'aurora postgres', 'azure postgres', 'crunchy bridge', 'external postgres', 'my postgres', 'migrate postgres', 'pg migration', 'postgres to snowflake', 'logical replication setup', 'pg_dump migration', 'migration assessment', 'cutover plan', 'rollback plan', 'migrate from RDS', 'migrate from Aurora', 'migrate from Azure postgres', 'migrate from Cloud SQL', 'move my postgres', 'transfer postgres'. Do NOT use for generic Iceberg / catalog integration / storage integration / data lake requests — those are owned by the `iceberg` skill, EXCEPT for catalog integrations scoped to pg_lake (`CATALOG_SOURCE = SNOWFLAKE_POSTGRES`), which are handled here. Only handle Iceberg when it is scoped to pg_lake (Postgres-resident Iceberg tables or the pg_lake-specific catalog integration path)."
---

# Snowflake Postgres

## When to Use

When a user wants to manage Snowflake Postgres instances via Snowflake SQL, **or** when they want help working with any Postgres database using standard PostgreSQL tooling (`psql`, saved connections in `~/.pg_service.conf` / `~/.pgpass`, health diagnostics).

## Snowflake Postgres vs. Non-Snowflake Postgres

A single skill covers both, but the available operations differ:

| Operation | Snowflake Postgres | Non-Snowflake Postgres (Neon, Supabase, RDS/Aurora, Azure, Cloud SQL, Crunchy Bridge, self-hosted, etc.) |
|---|---|---|
| `psql` via `~/.pg_service.conf` + `~/.pgpass` | ✅ | ✅ |
| `pg_connect.py --list` (list saved connections) | ✅ | ✅ |
| `pg_doctor.py` health checks | ✅ | ✅ — uses standard pg_catalog; portable. Some checks (e.g. `outliers`) require `pg_stat_statements` to be enabled. |
| Running any SQL the user asks for via `psql` | ✅ | ✅ |
| `pg_connect.py --create` / `--reset` / `--fetch-cert` | ✅ | ❌ Snowflake-only |
| `SHOW / DESCRIBE / ALTER POSTGRES INSTANCE` (Snowflake SQL) | ✅ | ❌ Snowflake-only — never run these on external Postgres |
| Network policy setup | ✅ | ❌ Snowflake-only |
| `pg_lake` / Iceberg | ✅ | ❌ Snowflake-only |

**How to tell which one you're dealing with:**
- Snowflake Postgres: host ends with `snowflakecomputing.com` or `postgres.snowflake.app`, or the user mentions a Snowflake account/instance.
- Non-Snowflake Postgres: host matches a known provider (`*.neon.tech`, `*.supabase.co`, `*.rds.amazonaws.com`, `*.postgres.database.azure.com`, `*.aivencloud.com`, `*.postgresbridge.com` / `*.crunchybridge.com` for Crunchy Bridge, etc.), the user supplies a `postgres://...` connection string, or they explicitly mention another provider.

> **Note on Crunchy Bridge:** Snowflake Postgres shares its roots with Crunchy's technology, and some users may be coming from (or still using) **Crunchy Bridge** as a standalone managed Postgres product. Crunchy Bridge is NOT Snowflake Postgres — it's a separate external service. Treat it exactly like any other non-Snowflake Postgres (standard PG tools only; none of the Snowflake-specific commands apply).

**For non-Snowflake Postgres:** do NOT run Snowflake SQL commands (they will error and confuse the user). See `connect/SKILL.md` → "Non-Snowflake Postgres" for how to save connections via standard PG files, then `psql` / `pg_doctor.py` work the same as on Snowflake Postgres.

## Setup

1. **Check for connection**: Verify a saved connection using the `connect/SKILL.md` workflow.
2. **Load references** as needed based on intent.

## Connection Storage (PostgreSQL Standard Files)

Connections use PostgreSQL's native configuration files instead of custom formats. This provides:
- Compatibility with all PostgreSQL tools (`psql`, pgAdmin, DBeaver, etc.)
- OS-enforced security (PostgreSQL rejects `.pgpass` if permissions are wrong)
- Separation of connection metadata from secrets

Never ask for credentials in chat.

### Service File: `~/.pg_service.conf`

PostgreSQL service file - stores named connection profiles (no passwords). Allows connecting with `psql service=<name>` instead of specifying all parameters:

```ini
[my_instance]
host=abc123.snowflakecomputing.com
port=5432
dbname=postgres
user=snowflake_admin
sslmode=verify-ca
sslrootcert=/Users/me/.snowflake/postgres/certs/my_instance.pem
```

When `sslrootcert` is present, `sslmode=verify-ca` verifies the server's identity using the CA certificate (MITM protection). The cert is fetched automatically on `--create` and `--reset`, or manually with `--fetch-cert`. Existing connections with `sslmode=require` continue to work.

Users can connect manually with: `psql service=my_instance` (if psql is installed)

### Password File: `~/.pgpass`

PostgreSQL password file - stores credentials separately from connection profiles. PostgreSQL clients automatically look up passwords from this file when connecting. Must have `chmod 600` permissions.

**⚠️ NEVER display `.pgpass` contents or format with actual passwords.** Always use `pg_connect.py` to manage passwords - it handles the file securely without exposing credentials in chat.

**Running queries:** Use `psql "service=<instance_name> connect_timeout=10" -c "<SQL>"` — authentication is handled automatically via the service file and pgpass. Never read or echo credential files.

**⚠️ Always include `connect_timeout=10`** in psql invocations. Without it, a psql call against an instance with no network policy (or a suspended instance) will hang for 2+ minutes before giving up. `connect_timeout=10` fails fast so the agent can diagnose and offer the right next step.

**⚠️ Bash timeout:** All Postgres commands (psql, pg_connect.py, pg_lake_setup.py, pg_lake_storage.py) require network round-trips and SSL negotiation. **Never set `timeout_ms` below 60000 (60 seconds).** For bulk operations (COPY, CREATE TABLE AS, large queries), use 120000+ (2 minutes). The default `timeout_ms` is sufficient — do not lower it.

**⚠️ Check instance state before psql:** An instance may be in SUSPENDED state (e.g., after a manual `ALTER POSTGRES INSTANCE … SUSPEND` or a maintenance operation). A psql connection to a suspended instance will hang (PG instances do NOT auto-resume on connection). **Before running any psql or pg_lake_setup.py command**, ensure the instance is READY:

```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_connect.py \
  --ensure-ready --instance-name <INSTANCE_NAME> \
  [--snowflake-connection <SF_CONN>]
```

This checks the instance state, auto-resumes if SUSPENDED, and waits up to 6 minutes for READY. The pg_lake_setup.py script also retries connections automatically (3 attempts with backoff), but `--ensure-ready` avoids wasting time on retries when the instance needs a full resume cycle.

## Progress Tracking

For multi-step operations, use `system_todo_write` to show progress:

```
┌──────────────────┬──────────────────────────────────────────────────────┐
│ Scenario         │ Create Todos                                         │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Create + setup   │ Create instance → Save connection → Network policy   │
├──────────────────┼──────────────────────────────────────────────────────┤
│ Batch operations │ One todo per instance/object                         │
└──────────────────┴──────────────────────────────────────────────────────┘
```

**Rules:**
- Mark `in_progress` BEFORE starting each step
- Mark `completed` IMMEDIATELY after finishing
- Add new todos if issues are discovered mid-workflow

## Intent Detection

| Intent | Trigger Phrases | Route |
|--------|-----------------|-------|
| **MANAGE** | "create instance", "show instances", "list instances", "suspend", "resume", "describe", "rotate password", "reset credentials", "reset access" | Load `manage/SKILL.md` |
| **CONNECT** | "my IP", "network policy", "can't connect", "add IP", "import connection", "save my postgres connection", "connect to my postgres", "add my neon/supabase/RDS connection", or any non-Snowflake Postgres setup question | Load `connect/SKILL.md` (Non-Snowflake Postgres subsection for external providers) |
| **DIAGNOSE** | "health check", "diagnose", "diagnostics", "insights", "pg_doctor", "cache hit", "bloat", "vacuum", "dead rows", "autovacuum", "locks", "blocking queries", "blocked", "waiting", "long running", "slow queries", "query performance", "outliers", "unused indexes", "table sizes", "disk usage", "storage", "connections", "connection count", "what's running", "active queries" | Load `diagnose/SKILL.md` |
| **PG_LAKE** | "pg_lake", "postgres iceberg", "pg iceberg", "iceberg table in postgres", "POSTGRES_EXTERNAL_STORAGE", "postgres COPY to S3", "postgres export to S3", "move data between postgres and snowflake", "read pg_lake in snowflake", "pg to snowflake iceberg", "catalog integration for pg_lake", "expose pg_lake to snowflake", "SNOWFLAKE_POSTGRES catalog", "catalog linked database for pg_lake", "query postgres iceberg from snowflake" | Load `pg-lake/SKILL.md` |
| **MIGRATE** | "migrate postgres", "pg migration", "postgres to snowflake", "move my postgres", "transfer postgres", "copy from postgres", "logical replication setup", "pg_dump migration", "migration assessment", "migration readiness", "cutover plan", "rollback plan", "resume my migration", "validate migration", "migration monitor", "migrate from RDS", "migrate from Aurora", "migrate from Azure postgres", "migrate from Cloud SQL", "migrate from Crunchy Bridge", "migrate from Neon", "migrate from Supabase" | Load `migrate/SKILL.md` |

Generic Snowflake Iceberg, catalog integration, external volume, and storage integration requests belong to the `iceberg` skill unless the user is clearly working with Postgres-resident Iceberg / `pg_lake`. **Exception:** `CATALOG_SOURCE = SNOWFLAKE_POSTGRES` (the pg_lake-specific catalog integration path, covered by the READ-FROM-SNOWFLAKE workflow in `pg-lake/SKILL.md`) belongs here, not in the generic `iceberg` skill — that path reads Iceberg metadata from a pg_lake PG instance, not from a user-supplied REST catalog.

### Unrecognized or Extended Operations

If the user's request involves Snowflake Postgres but doesn't match the intents above (e.g., fork, replica, maintenance window, upgrade, POSTGRES_SETTINGS):

1. **First** check `references/documentation.md` for the relevant doc URL
2. **Fetch** the official docs to get current syntax
3. **Apply** the same safety rules (approval for billable/destructive operations, no secrets in chat)

Examples of operations requiring doc lookup:
- Fork instance / point-in-time recovery
- Create read replica
- Set maintenance window
- Modify POSTGRES_SETTINGS
- Major version upgrades

## Routing

⚠️ **MANDATORY: Execute Sub-Skill Immediately**

After detecting intent, you MUST:
1. Load the sub-skill file
2. Execute its workflow **in this same response**
3. Do NOT stop after loading - continue to completion

| Intent | Action |
|--------|--------|
| **MANAGE** | Load `manage/SKILL.md` → Execute SQL immediately |
| **CONNECT** | Load `connect/SKILL.md` → Execute workflow immediately |
| **DIAGNOSE** | Load `diagnose/SKILL.md` → Execute diagnostics immediately |
| **PG_LAKE** | Load `pg-lake/SKILL.md` → Follow its workflow (has its own stopping points — present plan first for SETUP) |
| **MIGRATE** | Load `migrate/SKILL.md` → Follow its workflow (interactive scope gathering via `ask_user_question`; presents assessment / hybrid plan / cutover plan for approval before executing) |

❌ **WRONG:** Load skill, then stop or explain without doing anything
✅ **RIGHT:** Load skill, then follow its workflow (which may include presenting a plan and waiting for user confirmation before executing)

## Global Safety Rules

- Never ask for passwords in chat or echo secrets.
- **Never use `cat`, `echo`, heredoc (`<<`), or any shell command to create files containing `access_roles` or passwords** - these appear in chat history.
- Always require explicit approval for billable actions and network policy changes.
- For DESCRIBE responses, never show `access_roles`.
- **Prefer Cortex Search docs over web search for Snowflake-specific questions.** Check skill references and Snowflake documentation via Cortex Search first. Only fall back to web search if Cortex Search doesn't have what you need.
- For CREATE responses, never show raw SQL results - `access_roles` contains passwords.
- If any output might include secrets (passwords, access tokens), never display them in chat. Scripts save secrets to secure files (`~/.pgpass` with 0600 permissions) without echoing them.
- **For CREATE INSTANCE: MUST use `pg_connect.py --create`** - never use SQL tool directly. The script saves the connection automatically.
- **For RESET ACCESS: MUST use `pg_connect.py --reset`** - never use SQL tool directly. The script saves the password automatically.
- **Do NOT ask if user wants to save after CREATE/RESET** - the scripts save automatically.
- **Do NOT run RESET after CREATE** - CREATE already saves the password. RESET is only for rotating passwords later.
- **Never execute destructive operations (DROP TABLE, DROP COLUMN, DELETE, TRUNCATE, DROP INTEGRATION) without the user explicitly requesting it.** If the user asks to "clean up" or "remove" something, confirm exactly what will be deleted before executing. DROP TABLE on Iceberg tables permanently deletes S3 data files.

## Tools

### Tool: ask_user_question

**Description:** Ask the user to choose from a fixed list of options.

**When to use:** Present configuration menus (instance size, storage, HA, version, network policy).

### Script: network_policy_check.py

**Description:** Check whether an IP is allowed by a Snowflake network policy.

**Usage:**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/network_policy_check.py \
  --policy-name <POLICY_NAME> \
  [--ip <IP>]
```

### Script: pg_connect.py

**Description:** Manage Snowflake Postgres connections. Handles CREATE, RESET, and connection file management (`~/.pg_service.conf` and `~/.pgpass`) without exposing credentials.

**Usage (create instance - executes SQL + saves connection + probes port 5432):**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_connect.py \
  --create \
  --instance-name <NAME> \
  --compute-pool <COMPUTE_FAMILY> \
  --storage <GB> \
  [--enable-ha] \
  [--postgres-version <VERSION>] \
  [--network-policy <POLICY_NAME>] \
  [--auth-authority <POSTGRES|POSTGRES_OR_SNOWFLAKE>] \
  [--storage-integration <INTEGRATION_NAME>] \
  [--postgres-settings '<JSON>'] \
  [--comment '<TEXT>'] \
  [--use-role <SNOWFLAKE_ROLE>] \
  [--snowflake-connection <NAME>]
```

For valid compute families, storage limits, and HA restrictions, see `references/instance-options.md`.

After a successful CREATE the script runs a 20s TCP probe against `host:5432` and prints one of: reachable, timeout (no network policy), refused (still provisioning), or dns_error (hostname not yet propagated). **The agent must act on the probe result** — see `manage/SKILL.md` Step 7.

**Usage (reset credentials - executes SQL + updates password):**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_connect.py \
  --reset \
  --instance-name <NAME> \
  [--role <snowflake_admin|application>] \
  [--host <HOST>] \
  [--use-role <SNOWFLAKE_ROLE>] \
  [--snowflake-connection <NAME>]
```
Use `--host` to create the service entry if it doesn't exist (e.g., from DESCRIBE output).

**`--use-role`** (applies to `--create`, `--reset`, `--fetch-cert`, `--ensure-ready`, `--upgrade-ssl`): overrides the Snowflake session role for this invocation only. Passed to the Snowflake connector; does not modify `~/.snowflake/connections.toml` or `~/.snowflake/config.toml`. Use when the default role lacks `CREATE POSTGRES INSTANCE` or other required privileges.

**Usage (fetch CA certificate for server identity verification):**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_connect.py \
  --fetch-cert \
  --instance-name <NAME> \
  [--snowflake-connection <NAME>]
```
Fetches the CA certificate via `DESCRIBE POSTGRES INSTANCE` and upgrades the service entry to `sslmode=verify-ca`. Run this for existing connections that use `sslmode=require`.

**Usage (list saved connections):**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_connect.py --list
```

**Usage (ensure instance is ready before PG operations):**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_connect.py \
  --ensure-ready \
  --instance-name <NAME> \
  [--snowflake-connection <NAME>] \
  [--no-auto-resume]
```
Checks instance state via Snowflake, auto-resumes if SUSPENDED, waits for READY. Use `--no-auto-resume` to only check without resuming.

Uses Snowflake connection from `~/.snowflake/connections.toml` or environment variables. Use `--snowflake-connection` to specify a named connection.

### Script: pg_doctor.py

**Description:** Run Postgres health diagnostics. All queries run in readonly mode with statement timeout.

**Usage (full health check):**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_doctor.py \
  --connection-name <NAME>
```

**Usage (single check):**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_doctor.py \
  --connection-name <NAME> \
  --check <CHECK_NAME>
```

**Flags:** `--json`, `--detailed`, `--category <CATEGORY>`, `--all`, `--list-checks`, `--timeout <MS>`

### Script: pg_lake_setup.py

**Description:** pg_lake extension setup and verification on Postgres. Checks extensions, enables pg_lake, configures S3, verifies access, manages Iceberg tables.

**Usage:**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_setup.py \
  --check-extensions --connection-name <PG_CONN> --json
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_setup.py \
  --enable-extensions --connection-name <PG_CONN>
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_setup.py \
  --verify-s3 --connection-name <PG_CONN> --json
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_setup.py \
  --list-iceberg --connection-name <PG_CONN> --json
```

### Script: pg_lake_storage.py

**Description:** Snowflake storage integration management for pg_lake. Creates, describes, attaches, and drops POSTGRES_EXTERNAL_STORAGE integrations. Sensitive IAM values written to secure temp files.

**Usage:**
```bash
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_storage.py \
  create --name <NAME> --role-arn <ARN> --locations s3://bucket/ \
  --snowflake-connection <SF_CONN> --json
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_storage.py \
  describe --name <NAME> --snowflake-connection <SF_CONN>
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_storage.py \
  check-aws --role-arn <ARN> \
  --expected-principal <IAM_USER_ARN> --expected-external-id "<EXT_ID>" \
  [--aws-profile <PROFILE>] --json
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_storage.py \
  update-aws --role-arn <ARN> --sensitive-file <DESCRIBE_OUTPUT_FILE> \
  [--aws-profile <PROFILE>] --json
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_storage.py \
  attach --instance <INST> --integration <NAME> --snowflake-connection <SF_CONN>
uv run --project <SKILL_DIR> python <SKILL_DIR>/scripts/pg_lake_storage.py \
  verify --instance <INST> --snowflake-connection <SF_CONN> --json
```

## Output

Routes to the correct workflow and returns the results from that sub-skill.

## Stopping Points Summary

| Operation | Approval Required |
|-----------|-------------------|
| CREATE instance | ⚠️ Yes (billable) |
| SUSPEND instance | ⚠️ Yes (drops connections) |
| Network policy changes | ⚠️ Yes |
| CREATE storage integration | ⚠️ Yes (cloud resources, ACCOUNTADMIN) |
| Update AWS trust policy | ⚠️ Yes (manual AWS step) |
| RESUME instance | No |
| LIST/DESCRIBE | No |
| Health check / diagnostics | No (readonly) |

**Resume rule:** On approval ("yes", "proceed", "approved"), continue without re-asking.

## Troubleshooting

**Error: `invalid property 'STORAGE_SIZE'`**
→ Use `STORAGE_SIZE_GB` (not `STORAGE_SIZE`)

**Error: `Missing option(s): [AUTHENTICATION_AUTHORITY]`**
→ Add `AUTHENTICATION_AUTHORITY = POSTGRES`

**Error: Network policy not working**
→ Verify rule uses `MODE = POSTGRES_INGRESS`

**Error: Connection refused**
→ IP not in network policy. Offer to check IP and add to policy.

**Error: `Insufficient privileges to operate on account`**
→ The current Snowflake role lacks `CREATE POSTGRES INSTANCE ON ACCOUNT` (or equivalent). Retry the `pg_connect.py` call with `--use-role ACCOUNTADMIN`. If no available role has the grant, ask the account admin to run `GRANT CREATE POSTGRES INSTANCE ON ACCOUNT TO ROLE <role>;`. The `--use-role` flag overrides the role for that one invocation only — it does not mutate `connections.toml` or `config.toml`.

**Error: `INTERNAL_ERROR: PostgresUtils::getOrCreateTeamAndTeamIamRole():team_iam_role_arn_not_found`**
→ Server-side error, not a client-side issue. Retry once — transient cases sometimes resolve. If persistent, verify Postgres availability in the account's region and escalate with the exact error text.

**Error: `SHOW POSTGRES INSTANCES` fails with "unsupported feature" / "syntax error"**
→ Snowflake Postgres may not be enabled on this account. Contact the account admin to verify regional availability and confirm enablement. Do not attempt `CREATE POSTGRES INSTANCE` until the pre-flight check passes.

**Error: psql hangs on connect / `connection timed out`**
→ No network policy allows the client IP. Always include `connect_timeout=10` in psql so hangs fail fast (e.g. `psql "service=<name> connect_timeout=10"`). Fix: route to `connect/SKILL.md` → Setup Network Policy.

## References

- `references/instance-options.md` - Valid compute families, storage limits
- `references/instance-states.md` - Instance state descriptions
- `references/documentation.md` - Official Snowflake docs URLs (fallback for commands not covered here)
- `references/thresholds.md` - Health check thresholds and recommended actions

=== snowpark/ ===
---
name: snowpark-python
description: "**[REQUIRED]** Use for **ALL** requests involving Snowpark Python — writing pipelines, transforming data, loading files, deploying stored procedures/UDFs, OR observability. MUST invoke this skill even for seemingly simple tasks because Snowflake DataFrame semantics differ from Pandas in ways that silently produce wrong results (NULL handling, division by zero, GREATEST, datediff, type casting). Always load this skill BEFORE writing any Snowpark code. Triggers: Snowpark, Python, DataFrame, pipeline, ETL, ingest, transform, load data, CSV, Parquet, JSON, XML, join, aggregate, window function, UDF, UDTF, UDAF, Stored Procedure, deploy, snow snowpark CLI, DBAPI, JDBC, external database, pull data, event table, logging, tracing, trace events, profiler, debug UDF, debug procedure, observability, telemetry, slow procedure, alert on error, monitor."
---

# Snowpark Python

## Project Structure

```
project/
├── src/
│   ├── __init__.py
│   ├── pipeline.py          # Main pipeline code
│   └── udf_def.py            # UDF definitions
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   ├── test_pipeline.py      # Pipeline tests
│   └── data/
│       ├── input_sample.csv  # Test input data
│       └── expected_output.csv
├── configs.sql               # DDLs and permission grants
└── pyproject.toml
```

---

## Prerequisites

### Install `uv`
**Check if `uv` is installed** by running `uv --version`. If it's not installed, prompt the user to install it using one of these methods:
   - `curl -LsSf https://astral.sh/uv/install.sh | sh` (recommended)
   - `brew install uv` (macOS)
   - `pip install uv`

### Create a Python Project
Use `uv init` to create a Python project if the folder is empty.

### Create a Python Interpreter
Use `uv venv --python 3.13` to create Python environment.

### Install Python Packages
Use `uv add` to add project dependency packages.
Use `uv pip install` to install Python packages for development only.

---

## Primary Operations

These are the common operations users perform regularly. Route here confidently for any general Snowpark request.

### Plan the data pipeline
Plan the code in steps and explain to the user the plan. The plan may have these components depending the user's question but not limited to:
1. Load data from data sources.
2. Transform data. If this step is complex, break it down so it's easier for the user to understand.
3. Save the data to the destination table or stage location.

### Write Code
Use Snowpark Python Client to write code according to the above plan.

### Run and debug
Run the code using `uv` to try and fix the problems. Iterate until the problem is fixed.
If you find there are permission or other configuration problems, fix them and put the SQL statement in configs.sql.

### Deploy Code

Deploy stored procedures directly or as a snow snowpark CLI project. For more details, read `references/snowpark-deployment.md`.

### Data Flow Detection

If the user describes a data workflow, route to Primary tier:

**Common patterns:**
- **Write code:** "I need to build data pipeline using Snowpark Python Client" → Write Snowpark Code
- **Run and debug:** "Run the code", "Fix the error", "Debug my pipeline" → Run and debug code
- **Deploy code:** "Deploy my Python as stored procedure", "Deploy my project using snow snowpark CLI" → Deployment workflow

### Primary Routing Table

| User Language | Operation | Reference |
|---------------|-----------|-----------|
| Write code, build pipeline, load data, ingest data, transform data, Snowpark basics, ETL, DataFrame, CSV, Parquet, JSON, stage, join, aggregate, window function, UDF, UDTF, UDAF, vectorized UDF, DBAPI, JDBC, external database, pull data | Write Snowpark Code | `references/snowpark-authoring.md` |
| Deploy Python, Python stored procedure, Python UDF, register sproc, productionize Python, snow snowpark, snow init, generate project, snowflake.yml, build and deploy | Deployment | `references/snowpark-deployment.md` |
| Add logging to UDF, add tracing to procedure, profile Python code, instrument Snowpark code, slow UDF, slow procedure, snowflake-telemetry-python, Python profiler, ACTIVE_PYTHON_PROFILER | Observability | `references/snowpark-observability.md` |

**⚠️ MANDATORY** — If the task involves writing, building, or transforming data with Snowpark Python, you MUST read `references/snowpark-authoring.md` BEFORE writing any code. It contains critical Snowflake-specific behaviors that differ from standard Python/Pandas (NULL handling, division semantics, date functions, data loading). Skipping this reference will produce subtly broken code.

**⚠️ MANDATORY** — If the task involves deploying Snowpark Python code, read `references/snowpark-deployment.md` first.

**⚠️ MANDATORY** — If the task involves instrumenting Python code (logging, tracing) or profiling UDFs/procedures, read `references/snowpark-observability.md` first. For Event Table setup, alerts, or notifications, use the dedicated `event-table`, `alert`, or `notification` skills instead.
---

## Secondary Operations

Route here when the user language contains explicit problems or operational indicators. These operations may become complex.

**Only perform these when user explicitly asks.**

### Create Test Data

Write a Python program to generate the test data and run it only if the user asks.
Put the data into the folder `tests/data`.

### Create Test Code

Use `pytest` to write the test code. Put the test code in folder `tests`.

### Secondary Routing Table

| Explicit Indicators | Operation | Reference |
|---------------------|-----------|-----------|
| Create test data, generate sample data, mock data, test fixtures | Create Test Data | Not yet supported |
| Write tests, create test code, unit tests, test my code | Create Test Code | Not yet supported |
| Add logging, add tracing, profile, instrument, slow UDF, slow procedure, snowflake-telemetry-python, Python profiler | Observability | `references/snowpark-observability.md` |
| Error, failing, debug, not working, fix, troubleshoot, why is it failing | Troubleshooting | Not yet supported |

---

## Compound Requests

If the user describes multiple operations:

1. Create a todo list capturing all requested operations
2. Ask the user to confirm the order:
   > "I've identified these tasks: [list]. What order would you like me to tackle them?"
3. Execute in confirmed order, completing each before moving to the next
4. Note: Some operations have natural dependencies (e.g., ingest before transform before deploy)

**Typical Customer Journey:**
```
Write Code → Deploy → Monitor → Troubleshoot (if needed)
```

**Typical Observability Journey:**

1. **Setup**: Create Event Table, configure account default
2. **Instrument**: Add logging/tracing to Python code
3. **Deploy & Enable**: Deploy code, set LOG_LEVEL
4. **Alert**: Set up notifications for errors/warnings
5. **Debug**: Query Event Table to understand failures
6. **Profile** (if slow): Enable profiler, find hotspots
7. **Optimize**: Fix code based on profiler output

All steps are covered in `references/snowpark-observability.md`.

---

## Reference Index

### Core Operations (Primary)

| Reference | Purpose |
|-----------|---------|
| `references/snowpark-authoring.md` | Pipeline authoring: session setup, loading data, transformations, saving results, UDF/UDTF/UDAF, performance, local testing |
| `references/snowpark-deployment.md` | Deploy Python code as Snowflake stored procedures or UDFs |
| `references/snowpark-observability.md` | Python instrumentation (logging, tracing) and profiling for Snowpark UDFs and stored procedures |

### Operational (Secondary)

| Reference | Purpose |
|-----------|---------|
| Write Tests | Write tests with pytest (only when user asks) — Not yet supported |
| Troubleshooting | Debug errors, diagnose failures, fix issues — Not yet supported |

---

## Stopping Points Summary

All references follow this philosophy: **NO changes without explicit user approval.**

- **READ-ONLY queries**: Can run freely (diagnostics, monitoring, telemetry queries)
- **ANY mutation**: Requires stopping point and user approval

See individual references for specific stopping points.

=== snowpipe-streaming/ ===
---
name: snowpipe-streaming
description: "**[REQUIRED]** Use for ALL Snowpipe Streaming tasks: setup, configure, troubleshoot, monitor, optimize, or migrate streaming pipelines. Covers the High-Performance Architecture exclusively. Triggers: snowpipe streaming, streaming ingestion, low-latency ingestion, real-time ingestion, Snowpipe Streaming SDK, channel, insertRows, appendRows, streaming channel, PIPE object, streaming pipe, snowpipe v2, high-performance streaming, migrate classic streaming, troubleshoot streaming."
---

# Snowpipe Streaming (High-Performance Architecture)

Guides users through setting up, troubleshooting, monitoring, optimizing, and migrating Snowpipe Streaming pipelines using the High-Performance Architecture.

## Important Context

- **Only the High-Performance Architecture** — classic is planned for deprecation mid-2026
- **Python SDK** (`snowpipe-streaming` PyPI package) is the primary SDK; Java SDK is an alternative
- The High-Performance Architecture uses **PIPE objects** — channels open against pipes, not directly against tables
- Default pipe naming: `<TABLE_NAME>-STREAMING` (auto-created on first use)
- **Schema evolution**: Default pipes automatically adapt to source schema changes (new columns added automatically). Schematization via Kafka Connect is optional, not required.
- Key-pair authentication is required for SDK access

## Intent Detection

| Intent | Triggers | Route |
|--------|----------|-------|
| **SETUP** | "set up", "create", "configure", "new pipeline", "get started", "quickstart" | `setup/SKILL.md` |
| **TROUBLESHOOT** | "debug", "fix", "error", "failing", "not working", "troubleshoot", "channel error", "offset gap" | `troubleshoot/SKILL.md` |
| **MONITOR** | "monitor", "status", "check", "health", "dashboard", "channel status", "costs", "billing" | `monitor/SKILL.md` |
| **OPTIMIZE** | "optimize", "improve", "throughput", "latency", "performance", "cost reduction", "tune" | `optimize/SKILL.md` |
| **MIGRATE** | "migrate", "upgrade", "classic to v2", "move from classic", "switch SDK", "deprecation", "high-performance" | `migrate/SKILL.md` |

## Workflow

```
User Request
  ↓
Detect Intent (see table above)
  ↓
  ├─→ SETUP    → Load setup/SKILL.md
  ├─→ TROUBLESHOOT → Load troubleshoot/SKILL.md
  ├─→ MONITOR  → Load monitor/SKILL.md
  ├─→ OPTIMIZE → Load optimize/SKILL.md
  └─→ MIGRATE  → Load migrate/SKILL.md
```

If intent is ambiguous, ask the user:

```
What would you like to do with Snowpipe Streaming?

1. Set up a new pipeline
2. Troubleshoot an existing pipeline
3. Monitor pipeline health & costs
4. Optimize performance or costs
5. Migrate from classic to High-Performance Architecture
```

## Tools

### Script: health_check.py

**Description**: Checks pipeline health — channel status, offset progress, row errors, ingestion gaps. Auto-detects timestamp column or accepts `--timestamp-column` override.

**Usage:**
```bash
# Via uv run
uv run --project <SKILL_DIR>/scripts python <SKILL_DIR>/scripts/health_check.py \
  --database <DB> --schema <SCHEMA> --table <TABLE> \
  --connection <CONNECTION_NAME>

# Or install and use CLI entry point
cd <SKILL_DIR>/scripts && uv pip install -e .
ss-health-check --database <DB> --schema <SCHEMA> --table <TABLE>
```

### Script: stream_demo.py

**Description**: End-to-end demo — creates table, opens channel, streams sample rows, verifies ingestion.

**Usage:**
```bash
# Via uv run
uv run --project <SKILL_DIR>/scripts python <SKILL_DIR>/scripts/stream_demo.py \
  --database <DB> --schema <SCHEMA> --table <TABLE> \
  --private-key-path <KEY_PATH> --account <ACCOUNT> --user <USER>

# Or install and use CLI entry point
ss-demo --database <DB> --schema <SCHEMA> --table <TABLE> \
  --private-key-path <KEY_PATH> --account <ACCOUNT> --user <USER>
```

## References

### SDK Code Samples

**Load** the relevant file based on the user's integration method:
- `references/python-sdk.md` — Python SDK (minimal, production service, FastAPI, offset tracking)
- `references/java-sdk.md` — Java SDK (minimal, batch, self-healing)
- `references/rest-api.md` — REST API (JWT auth, append rows, compression)
- `references/kafka-connect.md` — Kafka Connect (basic, schematized, Iceberg, Docker Compose)
- `references/common-patterns.md` — Profile JSON, key-pair generation, VARIANT best practices

### Monitoring Queries

**Load** `references/monitoring-queries.md` for SQL queries covering channel health, throughput, offset gaps, and cost analysis.

## Key Documentation Links

- [Snowpipe Streaming Overview](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/data-load-snowpipe-streaming-overview)
- [High-Performance Architecture](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-overview)
- [Python SDK Reference](https://docs.snowflake.com/en/user-guide/snowpipe-streaming-sdk-python/reference/latest/index)
- [Best Practices](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-best-practices)
- [Getting Started Tutorial](https://docs.snowflake.com/en/user-guide/snowpipe-streaming/snowpipe-streaming-high-performance-getting-started)

=== spark-migration/ ===
---
name: spark-migration
description: |
  Migrate Spark scripts and notebooks to Snowflake. Routes to one of two bundled conversion paths and orchestrates the post-conversion pipeline. **Default path: Snowpark Connect (SCOS)**, which preserves the PySpark API surface. The SMA / Snowpark API path is invoked only when the user explicitly asks for it.
  Triggers: convert spark, migrate pyspark, migrate spark, migrate to snowpark, convert to snowpark, snowpark connect, scos, scos migration, migrate to snowpark connect, migrate to scos, snowpark api, sma cli, sma conversion, run sma, snowflake.snowpark rewrite, already migrated, already ran sma, sma dashboard, fix ewis, stage conversion, dvp orchestrator, resume dvp.
---

# Spark Migration

Routes Spark → Snowflake conversion requests to one of two bundled paths and owns the cross-path configuration, intent classification, and per-step dispatch.

## ⛔ Default Path: Snowpark Connect (SCOS)

Any unqualified request to "convert spark", "migrate pyspark", "migrate to snowpark", etc. routes to **`snowpark-connect/SKILL.md`**, which preserves the PySpark API surface (`withColumn`, `groupBy`, `spark.createDataFrame`). This is the recommended default for the vast majority of users.

Route to **`snowpark-api/SKILL.md`** (SMA CLI / `snowflake.snowpark` snake_case rewrite) **only** when the user explicitly mentions:

- "SMA", "SMA CLI", or "run sma"
- "Snowpark API" or "`snowflake.snowpark`"
- An already-migrated SMA output (intents like "open sma dashboard", "fix ewis", "run stage conversion", "resume dvp")
- An existing project config with `conversion_type` set to `snowpark-api` (or any legacy alias)

If the intent is ambiguous, ask the user which path they want — **do not silently default to the SMA path**.

## Flows

1. **(a) Already migrated** — User already has SMA/snowpark-connect output. Provide the result path, verify structure, initialize git, then run the post-conversion pipeline.
2. **(b) Snowpark Connect conversion** — Load `snowpark-connect/SKILL.md`. **This is the default.**
3. **(c) Snowpark API conversion (SMA CLI)** — Load `snowpark-api/SKILL.md`. **Explicit opt-in only.**

## Output Format

Every time you begin a step, sub-step, or significant action, prefix the message with a timestamp in the format `[YYYY-MM-DD HH:MM:SS]`. Obtain the current time by running `date '+%Y-%m-%d %H:%M:%S'` in bash.

⛔ **Final Summary:** the active conversion path owns its own Final Summary template. For the Snowpark API path, see [`snowpark-api/references/final-summary-template.md`](snowpark-api/references/final-summary-template.md). For the Snowpark Connect path, follow `snowpark-connect/SKILL.md`. Do NOT improvise your own summary format.

## Sub-skill Loading Convention

All sub-skills referenced by name in this document (`snowpark-connect`, `snowpark-api`, and `snowflake-notebook-migration`) are bundled **inside this skill's own directory tree** — they are NOT separately installed top-level skills and they will NOT appear in the skill registry. This is intentional: the parent owns user-facing triggers; sub-skills are workers loaded on demand to avoid trigger collisions.

To run a sub-skill (NOT via `skill("<name>")`):

1. Resolve its `SKILL.md` path relative to **this** SKILL.md's directory (`<skill_directory>`):

   | Sub-skill | Bundled path |
   |---|---|
   | `snowpark-connect` | `<skill_directory>/snowpark-connect/SKILL.md` |
   | `snowpark-api` | `<skill_directory>/snowpark-api/SKILL.md` |
   | `snowflake-notebook-migration` | `<skill_directory>/snowflake-notebook-migration/SKILL.md` |

2. **Read** that file with the Read tool and follow its instructions verbatim, passing the orchestrator context inline as the next turn's content.

3. If the file is missing at the expected path, **STOP** and report:
   > The bundled `<name>` sub-skill is missing at `<path>`. Reinstall the `spark-migration` skill.

   Do NOT fall back to a registry lookup — that lookup will fail.

The `snowpark-api/` sub-skill further loads its own children (`migrate-pyspark-to-snowpark-api`, `validate-pyspark-to-snowpark-api`, `sma-dashboard-generator`, `stage-conversion`, `dvp/dvp-*`) using the same convention — see `snowpark-api/SKILL.md` for its own loading table.

## Directory Layout

```
spark-migration/                                    ← <skill_directory>
├── SKILL.md                                        (this file — thin router)
├── Diagram.md                                      (cross-path layout)
├── scripts/config_manager.py                       (shared config manager)
├── configurations/<project>.json                   (per-project state)
├── config.json                                     (global state, e.g. sma_cli_path)
├── snowflake-notebook-migration/                   (shared by both paths)
├── snowpark-connect/                               (SCOS path — DEFAULT)
│   ├── SKILL.md
│   ├── migrate-pyspark-to-snowpark-connect/
│   ├── migrate-spark-scala-to-snowpark-connect/
│   ├── validate-pyspark-to-snowpark-connect/
│   └── ...
└── snowpark-api/                                   (SMA / Snowpark API path)
    ├── SKILL.md                                    (router for the API path)
    ├── scripts/sma_api.py                          (SMA SQLite/git/EWI helpers)
    ├── references/                                 (extracted long-form docs)
    ├── migrate-pyspark-to-snowpark-api/SKILL.md
    ├── validate-pyspark-to-snowpark-api/SKILL.md
    ├── sma-dashboard-generator/SKILL.md
    ├── stage-conversion/SKILL.md
    └── dvp/dvp-*/SKILL.md   (orchestrator + 9 children)
```

For the historical moved-paths table (where files lived before this redesign), see [`Diagram.md`](Diagram.md).

## Usage

### Step 0: Prerequisites Check

Run at skill startup before any other step.

#### 0.1 Check Git

```bash
git --version 2>/dev/null && echo "found" || echo "not found"
```

If Git is **not found**, install it for the current platform:

| Platform | Command |
|----------|---------|
| macOS (Homebrew available: `brew --version`) | `brew install git` |
| macOS (no Homebrew) | Instruct user to run `xcode-select --install`, wait for it to complete, then confirm. |
| Linux (Debian/Ubuntu) | Verify sudo first: `sudo -n true 2>/dev/null \|\| echo "sudo password required"`. If available non-interactively: `sudo apt-get install -y git`. Otherwise instruct the user. |
| Linux (RHEL/CentOS/Amazon) | Same sudo check, then `sudo yum install -y git`. |
| Windows | `winget install --id Git.Git` |

Verify with `git --version` after install. Stop if still unavailable.

#### 0.2 Check SMA CLI (only when conversion_type = snowpark-api)

Skip this sub-step for SCOS and already-migrated SCOS flows.

```bash
SMA_FOUND=$(which sma 2>/dev/null)
if [ -z "$SMA_FOUND" ]; then
  SMA_FOUND=$(find /Users/Shared/AplicacionesSMA "$HOME/AplicacionesSMA" \
    "$HOME/Applications/SMA-CLI" /Applications/SMA-CLI /opt/sma /usr/local/bin \
    -maxdepth 4 -name "sma" -type f 2>/dev/null | head -1)
fi
echo "${SMA_FOUND:-not found}"
```

**Found:** save to global config and proceed:
```bash
python3 '<skill_directory>/scripts/config_manager.py' save-global '<skill_directory>' '{"sma_cli_path": "<SMA_FOUND>"}'
```
Print: `✅ SMA CLI found at <SMA_FOUND>`

**Not found:** ask the user for the absolute path to the `sma` binary (typically `/Users/me/SMA-CLI-arm64-mac/orchestrator/sma`). Validate with `test -x "<path>"`. On valid path, save globally as above. Do not proceed without a verified SMA CLI.

### Step 1: Load Configuration

**Record `<start_time>` = current time** (used for duration in the Final Summary).

Load the global config:

```bash
python3 '<skill_directory>/scripts/config_manager.py' load-global '<skill_directory>'
```

Store as `<global_config>`. `sma_cli_path` is read from here (not the project config).

List per-project configurations:

```bash
python3 '<skill_directory>/scripts/config_manager.py' list '<skill_directory>/configurations'
```

If configurations exist, display the numbered list and ask via `ask_user_question`:
- **Use existing configuration** — user selects by name or number → load it
- **Create new configuration** — proceed to step 1.3

If none exist, go directly to 1.3.

#### 1.2 Load Existing

```bash
python3 '<skill_directory>/scripts/config_manager.py' load '<config_path>'
```

`load` merges defaults for missing keys AND normalizes legacy `conversion_type` aliases (`scos`, `snowpark_connect`, `snowpark_api`) to their canonical forms (`snowpark-connect`, `snowpark-api`), persisting the normalized form back to disk.

Store the result as `<config>` and `<config_path>` for later writes. Go to Step 2.

#### 1.3 Create New

Ask for the 5 required project fields in one numbered list:

```
New configuration — please provide the following:

  1. Project Name:            (used as configuration filename)
  2. Source Code Path:        (PySpark or Spark Scala source directory)
  3. Output Folder:           (where converted code will be saved)
  4. Customer Email:
  5. Customer Company:

Example: "1. my_project, 2. /Users/me/spark-etl, 3. /Users/me/output, 4. user@co.com, 5. Acme Inc"
```

`#1` (Project Name) is **required**. `#2`–`#5` may be deferred.

```bash
python3 '<skill_directory>/scripts/config_manager.py' create '<skill_directory>/configurations' '<project_name>'
```

Then persist any provided fields:

```bash
python3 '<skill_directory>/scripts/config_manager.py' save '<config_path>' \
    '{"input_folder": "<input>", "output_folder": "<output>", "email": "<email>", "company": "<company>"}'
```

Include only keys the user provided. Store `<config_path>` and `<config>`. Go to Step 2.

### Step 2: Review Configuration

If `<config>` has saved values, present a single summary of all 18 settings (Project / Conversion / Post-Conversion) and ask:

- **Use these settings** — proceed
- **Edit settings** — present the numbered list below and accept partial updates

```
 ── Project ──────────────────────────────────
  1. Source Code Path:        <config.input_folder or (not set)>
  2. Output Folder:           <config.output_folder or (not set)>
  3. Customer Email:          <config.email or (not set)>
  4. Customer Company:        <config.company or (not set)>
  5. Project Name:            <config.project_name>

 ── Conversion ───────────────────────────────
  6. Conversion Type:         <config.conversion_type>     (snowpark-connect [default] / snowpark-api)
  7. Migration Status:        <config.migration_status>    (migrate / already_migrated)
  8. SMA CLI Path:            <global_config.sma_cli_path or (not set)>   (snowpark-api only; saved globally)
  9. Jupyter Conversion:      <config.enable_jupyter_conversion>  (yes / no; snowpark-api only)
 10. SQL Flavor:              <config.sql_flavor>          (SparkSql / HiveSql / Databricks; snowpark-api only)
 11. Generate Checkpoints:    <config.generate_checkpoints>  (yes / no; snowpark-api only)

 ── Post-Conversion ──────────────────────────
 12. Run Notebook Migration:  <config.run_notebook_migration>
 13. Run EWI Fixer:           <config.run_ewi_fixer>            (snowpark-api only)
 14. EWI Comments:            <config.run_ewi_fixer.ewi_comments>
 15. EWI Scope:               <config.run_ewi_fixer.ewi_scope>
 16. Run Stage Conversion:    <config.run_stage_conversion>     (snowpark-api only)
 17. Stage Name:              <config.run_stage_conversion.stage_name>
 18. Run DVP Orchestrator:    <config.run_dvp_orchestrator>     (snowpark-api only)
```

Map numbers to keys per the table in [`snowpark-api/references/configuration-schema.md`](snowpark-api/references/configuration-schema.md). Persist with `save` (project keys) and `save-global` (`sma_cli_path` only).

The post-conversion keys 13–18 are **SMA-only**. For SCOS flows, they are read but the post-conversion pipeline is owned by `snowpark-connect/`.

### Step 3: Determine Migration Status and Conversion Path

Use `<config.migration_status>` and `<config.conversion_type>` (canonical: `snowpark-connect` or `snowpark-api`) to route:

| `migration_status` | `conversion_type` | Route to |
|---|---|---|
| `already_migrated` | `snowpark-connect` | `snowpark-connect/SKILL.md` (already-migrated entry) |
| `already_migrated` | `snowpark-api` | `snowpark-api/SKILL.md` with `<intent>=already_migrated` |
| `migrate` | `snowpark-connect` (default) | `snowpark-connect/SKILL.md` |
| `migrate` | `snowpark-api` | `snowpark-api/SKILL.md` with `<intent>=migrate` |

If `<config.conversion_type>` is unset, default to `snowpark-connect`. If `<config.migration_status>` is unset, ask the user.

### Step 4: Validate Existing Output (already_migrated only)

When `<config.migration_status> = already_migrated`:

Ask for the output path (pre-fill `<config.output_folder>`). Store as `<output>`.

```bash
test -d "<output>/Output" && test -d "<output>/Reports" && echo "Valid" || echo "Invalid"
```

If invalid, check for SMA v1 `Conversion-*` subfolder:

```bash
ls -d "<output>"/Conversion-* 2>/dev/null | sort | tail -1
```

If present, resolve `<output>` to it and re-validate. If still invalid, ask the user for the correct path. (Full v1/v2/v3 resolution rules: [`snowpark-api/references/output-layouts.md`](snowpark-api/references/output-layouts.md).)

Once `<output>` is validated, go to Step 5.

### Step 5: Dispatch to Conversion Path

#### `snowpark-connect` route (default)

```bash
SNOWPARK_CONNECT_SKILL="<skill_directory>/snowpark-connect/SKILL.md"
```

Read with the Read tool and follow inline. Context block:

| Parameter | Value | Sub-skill variable |
|-----------|-------|--------------------|
| Source path | `<input>` | `$ARGUMENTS` |
| Output path | `<output>` | `$OUTPUT` |
| Customer Email | `<email>` | `$EMAIL` |
| Customer Company | `<company>` | `$COMPANY` |
| Project Name | `<project>` | `$PROJECT` |
| Invoker identity | `orchestrator` | `snowpark_connect_invoker` |
| Migration status | `<config.migration_status>` | Pass through unchanged |

Include `snowpark_connect_invoker: orchestrator` verbatim — the SCOS sub-skills read this flag to suppress their standalone Phase-6 notebook handoff (which would otherwise duplicate the work owned by `snowflake-notebook-migration`).

The SCOS sub-skill owns the entire conversion AND post-conversion pipeline for its path; control does not return here.

#### `snowpark-api` route (explicit opt-in)

```bash
SNOWPARK_API_SKILL="<skill_directory>/snowpark-api/SKILL.md"
```

Read with the Read tool and follow inline. Context block:

```
The following context was configured by the spark-migration orchestrator:
- <intent>           = migrate | already_migrated      (per Step 3 routing)
- <input>            = <config.input_folder>
- <output>           = <config.output_folder>          (already validated for already_migrated)
- <email>            = <config.email>
- <company>          = <config.company>
- <project>          = <config.project_name>
- <config_path>      = <skill_directory>/configurations/<project>.json
- <spark_migration_root> = <skill_directory>
- <snowpark_api_root>    = <skill_directory>/snowpark-api
- <start_time>       = <start_time>

Detect source language and route to the appropriate child.
Do NOT return here — the API path owns its own final summary.
```

The `snowpark-api/` router will:

1. Detect language (Python only is supported; Scala stops with a switch-to-SCOS prompt)
2. Route by `<intent>` to either `migrate-pyspark-to-snowpark-api/` (fresh conversion) or `validate-pyspark-to-snowpark-api/` (already-migrated / individual operations)
3. The chosen child runs the entire pipeline through the Final Summary

## Direct-Intent Triggers

When the user opens a session with intents like **"fix ewis"**, **"open sma dashboard"**, **"run stage conversion"**, or **"resume dvp"**, route them as follows:

1. Run Step 0 (prerequisites). SMA CLI check is skipped — these intents operate on existing output.
2. Run Step 1 to locate or create a config. Force-set `conversion_type=snowpark-api` and `migration_status=already_migrated` if not already.
3. Run Step 4 to validate `<output>`.
4. Skip Step 5 dispatch and load `snowpark-api/validate-pyspark-to-snowpark-api/SKILL.md` directly, passing the intent (`fix ewis` / `open sma dashboard` / etc.) in the context block — the validator's "Direct-Intent Behavior" table maps each intent to the subset of steps to run.

## Database & Helpers

The `sma_api.py` module (SQLite + git + EWI helpers) lives at:

```
<skill_directory>/snowpark-api/scripts/sma_api.py
```

For the function reference, see [`snowpark-api/references/sma-api-reference.md`](snowpark-api/references/sma-api-reference.md).

## Error Handling

| Condition | Action |
|---|---|
| Git unavailable after install attempt | Stop in Step 0.1; ask user to install manually |
| SMA CLI cannot be located/validated (API path only) | Stop in Step 0.2; ask user for path |
| `<config.conversion_type>` is `snowpark-api` but user clearly wants SCOS | Ask the user to confirm; offer to flip via Edit settings |
| `<output>` exists but lacks `Output/` and `Reports/` (already_migrated) | Stop in Step 4; ask for correct path |
| Bundled sub-skill missing at expected path | Stop and report: "The bundled `<name>` sub-skill is missing at `<path>`. Reinstall the `spark-migration` skill." |

Per-step error handling lives inside the bundled sub-skills. See `snowpark-connect/SKILL.md` and `snowpark-api/SKILL.md`.

## Outputs

Both conversion paths produce a converted workload with:

| Output | Location |
|--------|----------|
| Converted code | `<output>/Output/` |
| Issues report | `<output>/Reports/Issues.csv` |
| Inventory | `<output>/Reports/InputFilesInventory.csv` |
| Dependency inventory | `<output>/Reports/ArtifactDependencyInventory.csv` |
| EWI dashboard (snowpark-api) | `<output>/sma-dashboard/` |
| DVP workspace (snowpark-api) | `<output>/dvp/` |

The Snowpark Connect path produces an equivalent but path-distinct `Reports/` layout — see `snowpark-connect/SKILL.md`.

## Example Workflows

See [`snowpark-api/references/example-workflows.md`](snowpark-api/references/example-workflows.md) for concrete conversational walkthroughs of the four common entry points (fresh SMA, already-migrated, direct intent, Scala fallback).

For Snowpark Connect example walkthroughs, see `snowpark-connect/SKILL.md`.

=== sql-author/ ===
---
name: sql-author
description: "Use for ANY task that involves writing, running, or debugging SQL against Snowflake tables. Helps find the right table, verify columns exist, avoid timeouts on large tables, and validate joins. Triggers: write a query, sql for, query this table, author sql, build a query, fix this query, how many, how much, show me data, explore this table, describe table, select from."
---

# SQL Author

Write correct SQL by verifying every assumption before the query runs.

## Rules

1. **DESCRIBE before SELECT.** Run `DESCRIBE TABLE <db.schema.table>` before writing any query. Use only columns that appear in the output. Never guess a column name.

2. **Verify tables exist.** Before querying — and before telling the user a table *doesn't* exist — run `SHOW TABLES LIKE '<name>' IN SCHEMA <db.schema>` (try SHOW VIEWS too). If the user gives just a name, use `cortex search object "<name>"` to find it. Multiple candidates? Ask the user.

3. **Verify unfamiliar functions.** If you're not certain a Snowflake function exists, check first: `cortex search docs "<function_name>"` or test with a minimal `SELECT <function>('test')`. Don't invent functions.

4. **Check table size.** Query `INFORMATION_SCHEMA.TABLES` for `ROW_COUNT` before running against unfamiliar tables. Over 1B rows? Add date/partition filters. Over 100B? Filter on all clustering keys. No filters specified by user? Default to last 1 day and say so.

5. **State assumptions, ask if unsure.** Before executing, tell the user: which table, what date range, what filters, how you're computing the metric. If any of these feel like guesses, stop and ask — a one-turn clarification beats a confident wrong answer.

6. **Check for semantic views.** Before writing complex SQL, try `cortex semantic-views search "<topic>"`. Semantic views have verified metric definitions — prefer them when available.

7. **Default to LEFT JOIN.** NULLs in join keys silently drop rows with INNER JOIN. Before joining, check cardinality on both sides — if both have duplicates, pre-aggregate one side in a CTE.

8. **Re-read the request before executing.** Did they ask to exclude something you didn't filter? Ask for a specific column you missed? Want the *whole* statement, not a fragment? Check.

9. **Sanity-check results.** If a query returns 0 rows, don't just report it — investigate whether filters are too restrictive or you picked the wrong table. If numbers look implausible, check before presenting conclusions.

10. **Snowflake-specific gotchas.** `!= 'value'` doesn't match NULLs. `COUNT(col)` excludes NULLs, `COUNT(*)` doesn't. Use `QUALIFY` instead of subqueries for window filters. Use `ILIKE` not `LOWER() LIKE`. Use `DIV0NULL` not `DIV0`. Cast `VARIANT` fields explicitly. `ARRAY_CAT` only takes 2 arrays — nest calls for more.

11. **Diagnose permission errors with EXPLAIN_PRIVILEGES.** When a query fails with an access/privilege error, run `CALL EXPLAIN_PRIVILEGES(statement => '<failing_sql>', missing_only => true, for_role => '<role>')` to see exactly which privileges are missing. `missing_only => true` filters out already-granted privileges. `for_role` checks a specific role without switching to it — useful for diagnosing another role's access.

=== storage-lifecycle-policy/ ===
---
name: storage-lifecycle-policy
description: "Create, manage, and monitor Snowflake storage lifecycle policies. Use when: creating expiration or archival policies, attaching policies to tables, monitoring policy execution, retrieving archived data, managing data retention, reducing storage costs, saving on table storage. Triggers: storage lifecycle, lifecycle policy, archive data, expire data, COOL tier, COLD tier, data retention, archival storage, CREATE STORAGE LIFECYCLE POLICY, FROM ARCHIVE OF, ARCHIVE_FOR_DAYS, storage cost optimization, table is large, table is expensive, save on storage."
---

# Storage Lifecycle Policy

## When to Use

Use this skill when the user wants to:
- Create a storage lifecycle policy (expiration or archival)
- Attach or detach a policy from a table
- Monitor policy execution history
- Retrieve data from archive storage
- Understand archive tiers (COOL vs COLD)
- Optimize storage costs via automated data lifecycle management

## Key Concepts

- **Expiration policy**: Permanently deletes rows matching a condition. No `ARCHIVE_TIER`. Available on AWS, Azure, and GCP.
- **Archival policy**: Moves rows to cheaper storage (COOL or COLD tier), then expires after `ARCHIVE_FOR_DAYS`. COOL and COLD are archive tiers that only apply to archival policies.
  - **COOL tier**: Min 90-day archive period. Available on AWS, GCP, and Azure. Retrieval is fast but still requires `CREATE TABLE ... FROM ARCHIVE OF` — archived rows cannot be queried directly.
  - **COLD tier**: Cheapest storage, min 180-day archive period. Available on AWS and GCP. Retrieval can take up to 48 hours and also requires `CREATE TABLE ... FROM ARCHIVE OF`.
- **One policy per table**: A table can have only one storage lifecycle policy attached.
- **Tier is permanent**: Once a table is assigned an archive tier, it cannot be changed.
- **Daily execution**: Policies run automatically ~once every 24 hours using Snowflake-managed compute.

## Workflow

### Step 1: Determine Policy Type

Determine from the user's request:

- **Expire only** (user says "delete", "remove", "purge" old rows): No `ARCHIVE_TIER` needed
- **Archive then expire** (user says "archive", "move to cheaper storage", "retain"): Requires `ARCHIVE_TIER` and `ARCHIVE_FOR_DAYS`

### Step 2: Create the Policy and Attach to Table

**IMPORTANT**: A policy has no effect until attached to a table. Always create the policy AND attach it in the same step.

**Expiration policy** (deletes rows permanently):

```sql
CREATE STORAGE LIFECYCLE POLICY <policy_name>
  AS (<col_name> TIMESTAMP)
  RETURNS BOOLEAN ->
    TO_DATE(<col_name>) < TO_DATE(DATEADD(DAY, -<retention_days>, CURRENT_TIMESTAMP()));

ALTER TABLE <table_name> ADD STORAGE LIFECYCLE POLICY <policy_name>
  ON (<column_name>);
```

**Archival policy** (archive first, then expire):

```sql
CREATE STORAGE LIFECYCLE POLICY <policy_name>
  AS (<col_name> TIMESTAMP)
  RETURNS BOOLEAN ->
    TO_DATE(<col_name>) < TO_DATE(DATEADD(DAY, -<threshold_days>, CURRENT_TIMESTAMP()))
  ARCHIVE_TIER = COOL  -- or COLD (AWS and GCP only)
  ARCHIVE_FOR_DAYS = <archive_days>;

ALTER TABLE <table_name> ADD STORAGE LIFECYCLE POLICY <policy_name>
  ON (<column_name>);
```

**Best practice**: Always use `TO_DATE()` conversions in policy expressions for consistent execution regardless of time of day.

Requirements for attaching:
- Column count and types must match the policy signature
- The table must not already have a storage lifecycle policy attached
- If ALTER TABLE ADD fails because the table already has a policy, inform the user and ask if they want to drop the existing policy first using `ALTER TABLE <table_name> DROP STORAGE LIFECYCLE POLICY`

**Important**: A policy has no effect until attached. Always follow through with both CREATE and ALTER TABLE ... ADD — do not stop after creating the policy.

### Step 3: Verify Attachment

```sql
-- Check which policies are attached to a table
SELECT * FROM TABLE(
  INFORMATION_SCHEMA.POLICY_REFERENCES(
    REF_ENTITY_NAME => '<db.schema.table>',
    REF_ENTITY_DOMAIN => 'TABLE'
  )
) WHERE POLICY_KIND = 'STORAGE_LIFECYCLE_POLICY';
```

### Step 4: Monitor Execution

```sql
-- View execution history (last 14 days)
SELECT * FROM TABLE(
  INFORMATION_SCHEMA.STORAGE_LIFECYCLE_POLICY_HISTORY(
    REF_ENTITY_NAME => '<db.schema.table>',
    REF_ENTITY_DOMAIN => 'TABLE',
    TIME_RANGE_START => DATEADD('DAY', -7, CURRENT_TIMESTAMP()),
    RESULT_LIMIT => 100
  )
);

-- Or via ACCOUNT_USAGE (up to 365 days)
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_LIFECYCLE_POLICY_HISTORY
  WHERE SCHEDULED_TIME > DATEADD('DAY', -7, CURRENT_TIMESTAMP())
  ORDER BY SCHEDULED_TIME DESC;

-- List all policies in a schema
SHOW STORAGE LIFECYCLE POLICIES IN SCHEMA <db.schema>;

-- View a policy definition
DESCRIBE STORAGE LIFECYCLE POLICY <policy_name>;
```

## Retrieving Archived Data

**IMPORTANT**: Archived rows cannot be queried directly regardless of archive tier (COOL or COLD). You must use `CREATE TABLE ... FROM ARCHIVE OF` to create a new table containing the archived data before you can query it.

To view metadata about archived data (row count, column min/max values) without incurring retrieval costs:

```sql
SELECT SYSTEM$GET_TABLE_ARCHIVE_METADATA('<db.schema.table>');
```

To retrieve archived data, use `CREATE TABLE ... FROM ARCHIVE OF`:

```sql
CREATE TABLE <new_table>
  FROM ARCHIVE OF <source_table> AS st
  WHERE st.<column> BETWEEN '<start_date>' AND '<end_date>';
```

### Estimating Retrieval Cost Before Executing

Always run `EXPLAIN` before the actual retrieval to understand the cost and plan accordingly:

```sql
EXPLAIN
CREATE TABLE <new_table>
  FROM ARCHIVE OF <source_table> AS st
  WHERE st.<column> BETWEEN '<start_date>' AND '<end_date>';
```

The `EXPLAIN` output includes:

- A `createTableFromArchiveData` operation in the `operation` column
- `ARCHIVE OF <table>` in the `objects` column for the `TableScan` operation
- `assignedPartitions` — the number of partitions Snowflake will restore from archive to retrieve the data
- `bytesAssigned` — the number of bytes that will be retrieved

**After reviewing the EXPLAIN output, help the customer estimate the retrieval storage cost:**

#### Retrieval Storage Cost Estimate

Retrieval is charged as a one-time per-TB fee based on the archive tier, cloud provider, and region. Use `bytesAssigned` from the EXPLAIN output to calculate:

**Calculation**: `bytesAssigned` ÷ 1,099,511,627,776 × retrieval rate per TB = estimated retrieval storage cost

**Example**: Retrieving 500 GB from COOL tier on AWS US-East:
`500 GB ÷ 1024 = 0.488 TB × $30/TB = ~$14.65`

**Note**: This estimate covers retrieval storage cost only. The actual total cost will be higher due to warehouse compute charges incurred while running the retrieval query. For COLD tier, Snowflake also temporarily copies restored data into normal storage during retrieval, so you will pay additional storage charges for that temporary data until it is removed.

**AWS — COOL Tier Retrieval:** $30.00/TB (all regions)

**AWS — COLD Tier Retrieval (per TB data processed):**

| Region | $/TB |
|--------|------|
| US East (N. Virginia), US West (Oregon), US East 2 (Ohio), US East 1 Commercial Gov, US West (Commercial Gov - Oregon) | $2.50 |
| EU Dublin, Europe (Stockholm) | $3.00 |
| US Gov West 1, US Gov West 1 (Fedramp High Plus), US Gov East 1 (Fedramp High Plus), US Gov West 1 (DoD) | $3.40 |
| Middle East (UAE) | $3.30 |
| Asia Pacific (Malaysia), Asia Pacific (Thailand) | $4.50 |
| EU Frankfurt, Europe (London), Asia Pacific (Seoul, Osaka, Jakarta, Sydney, Singapore, Mumbai), Canada Central, EU (Paris), EU (Zurich), Africa (Cape Town) | $5.00 |
| South America East 1 (São Paulo) | $8.00 |

**Azure — COOL Tier Retrieval (per TB data processed):** (COLD tier not available on Azure)

| Region | $/TB |
|--------|------|
| East US 2 (Virginia), West US 2 (Washington), North Europe (Ireland), Sweden Central, East US (Virginia) | $30.00 |
| West Europe (Netherlands), Australia East, Canada Central (Toronto), Southeast Asia (Singapore), Japan East (Tokyo), UAE North (Dubai), Central India (Pune), UK South (London), Korea Central | $30.00 |
| US Gov Virginia, US Gov Virginia (Fed Ramp High Plus) | $30.00 |
| Mexico Central | $33.00 |
| South Central US (Texas) | $36.00 |
| US Central (Iowa) | $36.90 |
| Switzerland North | $42.90 |

**GCP — COOL Tier Retrieval:** $20.00/TB (all regions)

**GCP — COLD Tier Retrieval:** $50.00/TB (all regions)

**If the region cannot be found in the tables above**, fetch `https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf`, locate tables 3(e) and 5, and use the listed rate.

**After estimating cost, recommend the user adjust these settings before running the actual retrieval:**

1. **Warehouse size** — Choose the smallest warehouse size that can complete the retrieval in ~30 minutes. Archive retrieval insert throughput is approximately **25 MB/s per node** (observed range in production: 11–50 MB/s). Use the following formula:

   ```
   nodes_per_size = { XSMALL: 1, SMALL: 2, MEDIUM: 4, LARGE: 8, XLARGE: 16, 2XLARGE: 32 }
   megaBytesAssigned = bytesAssigned / 1048576
   required_nodes = ceil(megaBytesAssigned / 1800 / 25)
   recommended_size = smallest size where nodes >= required_nodes
   ```

   **Example**: `bytesAssigned` = 200 GB (204,800 MB):
   ```
   required_nodes = ceil(204800 / 1800 / 25) = ceil(4.55) = 5
   → Recommended size: LARGE (8 nodes)
   ```

   If `required_nodes` exceeds 32 (the largest standard warehouse), recommend 2XLARGE and note that the retrieval will take longer than 30 minutes — the statement timeout below must be increased accordingly.

   Only scale up — never lower the warehouse size. If the current size already meets or exceeds the recommendation, leave it unchanged. Before scaling up, record the current size so it can be restored after:
   ```sql
   -- Check current warehouse size first
   SHOW WAREHOUSES LIKE '<wh_name>';
   -- Note the current "size" value (e.g., 'MEDIUM')

   -- Only scale up if current size is smaller than recommended
   ALTER WAREHOUSE <wh_name> SET WAREHOUSE_SIZE = 'LARGE';
   -- Run the retrieval
   CREATE TABLE <new_table>
     FROM ARCHIVE OF <source_table> AS st
     WHERE st.<column> BETWEEN '<start_date>' AND '<end_date>';
   -- Restore to original size (not necessarily XSMALL — use whatever it was before)
   ALTER WAREHOUSE <wh_name> SET WAREHOUSE_SIZE = '<original_size>';
   ```

2. **Statement timeout** — Set based on the archive tier and estimated execution time. The lowest non-zero value between session and warehouse wins, so set both:

   Calculate the estimated execution time for the actual chosen warehouse:
   ```
   estimated_seconds = megaBytesAssigned / (nodes_in_chosen_size × 25)
   ```

   Note: if `required_nodes` exceeds 32, the recommended size is still 2XLARGE (32 nodes) but `estimated_seconds` will be longer than 1800. Use the actual `estimated_seconds` for timeout calculation regardless.

   Then set the timeout with a 2.5× buffer:
   - **COOL tier**: `timeout = estimated_seconds × 2.5`
   - **COLD tier**: COLD retrievals on AWS require up to 48 hours for file restoration from deep archive before the insert begins. `timeout = (48 × 3600) + (estimated_seconds × 2.5)`

   **Only increase the timeout — never lower it.** Check the current session and warehouse timeout values first. If the existing value is already >= the calculated timeout, leave it unchanged. Reducing the timeout could fail other long-running queries on the warehouse. The default `STATEMENT_TIMEOUT_IN_SECONDS` is 172800 (2 days), so only override if the calculated timeout exceeds the current value.

   ```sql
   -- Check current timeout values before changing
   SHOW PARAMETERS LIKE 'STATEMENT_TIMEOUT_IN_SECONDS' IN WAREHOUSE <wh_name>;
   SHOW PARAMETERS LIKE 'STATEMENT_TIMEOUT_IN_SECONDS' IN SESSION;

   -- Only set if calculated_timeout > current value
   ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = <calculated_timeout>;
   ALTER WAREHOUSE <wh_name> SET STATEMENT_TIMEOUT_IN_SECONDS = <calculated_timeout>;
   ```

3. **Abort detached query** — Must be FALSE so the retrieval continues if the session disconnects:
   ```sql
   ALTER SESSION SET ABORT_DETACHED_QUERY = FALSE;
   ```

## Removing a Policy

```sql
ALTER TABLE <table_name> DROP STORAGE LIFECYCLE POLICY;
```

Archived data remains accessible after policy removal.

## One-Time Operations

For one-time data cleanup (not ongoing):
1. Create and attach the policy
2. Wait for execution (~24 hours)
3. Monitor via `STORAGE_LIFECYCLE_POLICY_HISTORY`
4. Remove the policy to avoid recurring charges

## Important Constraints

- **Not supported on Iceberg tables**: Storage lifecycle policies cannot be applied to Iceberg tables. Only standard Snowflake-managed tables including dynamic tables are supported.
- Cannot change archive tier (COOL/COLD) once assigned to a table
- Subqueries in policy body may cause errors — keep expressions simple
- Policy signature cannot be changed while attached — drop and recreate
- Snowflake bypasses governance policies during evaluation
- Truncating a table does not affect archived data
- Replication: policies replicate but don't execute on secondary accounts

## Stopping Points

- Before removing a policy: Confirm with user

## Output

- Storage lifecycle policy created and attached to specified table(s)
- Monitoring queries provided for ongoing observation
- Archived data retrieved to new table when requested

=== team-workflow/ ===
---
description: "Multi-phase team orchestration for feature implementation. Supports two entry paths: explicit user request for teammates, or autonomous complexity-based assessment after entering plan mode. HIGHEST PRIORITY — must be loaded FIRST (before any domain skills) when user asks to use teammates, teams, or parallel agents. Triggers: use teammates, use a team, work in parallel with agents, delegate to teammates, swarm this, swarm, team up on this, team up, orchestrate with subagents, subagent-orchestrated, gated workflow, multi-phase workflow, coordinate agents, spawn workers, worker/verifier, parallel agents, run as a team, investigate with agents, research with agents, explore with agents."
---

# Skill: team-workflow

## Trigger

**PRIORITY**: When the user's message matches any trigger from the frontmatter description above, this skill MUST be loaded FIRST — before any domain-specific skills. Domain skills may be loaded later by subagents as needed.

This skill handles the teammate-or-not decision internally after entering plan mode. If assessment determines teammates are not needed, the skill exits cleanly and standard single-agent flow takes over.

---

## Main Agent Rules (Team Mode)

These rules apply when this skill is active. They OVERRIDE default agent behavior.

### CRITICAL — Read These First

1. **Complete the Setup sequence below BEFORE doing anything else.** No questions, no exploration, no spawning agents. Setup first, always.
2. **Assess intent after Setup.** Call `EnterPlanMode`, then run Teammate Assessment.

### Prohibitions

- Do NOT call `ASK_USER_QUESTION` before completing the setup sequence.
- `EnterPlanMode` is called once during Setup, before Teammate Assessment. Do NOT call it again until after an `ExitPlanMode`.
- If teammates are not needed, `ExitPlanMode` is called immediately after the main agent writes the plan. Then team cleanup runs and team-workflow is done.
- If teammates are needed, `ExitPlanMode` is called at the end of Phase 2 after Reviser/Validator agents complete.
- **`ExitPlanMode` is called exactly once per plan mode cycle**: each call must be paired with a preceding `EnterPlanMode`. Never call `ExitPlanMode` if not currently in plan mode.
- If ALL Phase 2 agents fail, the main agent still calls ExitPlanMode with the best-effort plan revision.
- If a revision-cycle Reviser fails, proceed with ExitPlanMode using the existing plan plus user feedback.
- Do NOT spawn Explore/general-purpose subagents outside of the phased workflow.
- NEVER edit source/implementation files directly. Delegate all code changes to teammates.

### User-Facing Communication

- Do NOT narrate internal orchestration mechanics to the user. Suppress messages like
  "Let me wait for the first explore agent", "All three explore agents are running",
  "Let me spawn the Plan agent now", "Let me check the step status", etc.
- Instead, provide brief user-friendly status updates: "Researching...", "Planning...",
  "Implementing...", "Reviewing...". Phase transitions (P1→P2→P3→P4) are the appropriate
  granularity for user-visible updates.
- Internal workflow details (polling, signaling, step management, agent spawning) should
  be invisible to the user.

### How the Main Agent Operates

- The main agent calls `EnterPlanMode` immediately after Setup.
- It runs Teammate Assessment using qualitative guidelines. 
- **If teammates are needed**: The main agent spawns Explore agents and one Plan agent
  concurrently. The plan agent drafts progressively as discoveries arrive. After all
  explore steps complete, the main agent sends PLAN_SIGNAL to finalize. After the plan
  is written, it runs Phase 2 (Reviser + Validator), calls `ExitPlanMode`, then
  proceeds through P3 (Implementors) and P4 (Tester + Reviewer).
- **If teammates are NOT needed**: The main agent researches and writes the plan itself,
  calls `ExitPlanMode`, and standard single-agent flow handles implementation. The team
  is deleted immediately and team-workflow is done.
- Beyond spawning teammates and managing plan mode, the main agent only runs `cortex ctx`
  commands and coordinates the workflow.

### Agent Budget

The main agent MUST track a cumulative `agents_spawned` counter throughout the workflow, starting at 0. This counter increments by 1 for every `Task` tool call with `run_in_background=true`.

**Hard budget: 45 agents per workflow.** Before every background agent spawn, check:
- If `agents_spawned >= 45`, do NOT spawn. The hard CLI limit is 50; the 5-agent margin reserves capacity for retries and edge cases.

**Per-phase advisory budgets** (soft guidance, cumulative 45 is mandatory):
| Phase | Max agents | Composition |
|-------|-----------|-------------|
| P1 Research | 6 | 5 explore + 1 plan |
| P2 Review | 4 | 2 reviser + 2 validator |
| P3 Implementation | 5 | prefer 3–4, hard cap 5 |
| P4 Review+Ship | 3 | 1 tester + 1 reviewer + 1 PR |
| Retries/revisions | 5 | across all retry and denial loops |

**When budget is exhausted:**
1. Complete remaining work directly (e.g., write the plan instead of spawning a plan agent)
2. Skip optional agents (PR agent, additional reviewers)
3. Consolidate remaining work into fewer agents

### Discovery Read Discipline
- The main agent should read discoveries **minimally** — only when:
  1. A subagent fails and the main agent needs context to respawn or complete the step itself
  2. At the end of Phase 2 to incorporate reviser feedback into the plan (use `--type reviser --team`)
  3. At the end of Phase 4 if the reviewer flagged issues (use `--type reviewer --team`)
- Subagents receive discoveries automatically via system reminder push notifications (up to 3/turn)
- Do NOT call `cortex ctx discovery list` without filters

### Required worker launch contract

When launching a background teammate for a team, the launch MUST include all of:

- `run_in_background=true`
- `team_name=team-workflow-<tid>` (or the active workflow team)
- `name=<role>-<step_id>` — **required for every team background worker**
- `prompt=<full worker prompt>`

Use stable unique worker names:

- Explore: `explore-<step_id>`
- Reviser: `reviser-<step_id>`
- Validator: `validator-<step_id>`
- Implementor: `implementor-<step_id>`
- Reviewer: `reviewer-<step_id>`
- Tester: `tester-<step_id>`
- Plan: `plan-<tid>` (one per workflow; named after task ID, not step ID)
- PR: `pr-<step_id>`

Never launch a team background worker without `name`. If `team_name` is present, `name` is mandatory.

## Shared Procedures

### Cleanup Procedure
```text
cortex ctx task done <tid>
cortex ctx team delete team-workflow-<tid>
```
Delete `{cwd}/.cortex/plans/plan-<tid>.md` using a platform-appropriate file deletion command or tool for the current OS before or after the task/team cleanup commands above. Do NOT assume Unix `rm` is available.
If `team delete` fails, run fallback:
```text
cortex ctx message clear --team team-workflow-<tid>
cortex ctx discovery clear --team team-workflow-<tid>
```

### Reviser Completion Flow
When the Reviser completes: run `cortex ctx step list -t <tid>` and confirm the Reviser's step is terminal (`done`, `failed`, or `cancelled`). **Do NOT call `ExitPlanMode` on the step-completion callback itself** — wait until `cortex ctx step list` confirms the step is terminal. Then read its discoveries, revise `{cwd}/.cortex/plans/plan-<tid>.md`, call **`ExitPlanMode`**. Return to User Response Handling.

### Step Status Refresh Rule
After any agent completion or failure callback, always run `cortex ctx step list -t <tid>` to refresh state before proceeding.

## Setup (run these first — no other tools in between)

These 5 commands must be the FIRST thing you do. Do NOT call ASK_USER_QUESTION, spawn subagents, or add steps before completing all 5.

1. Capture the current working directory as `{cwd}` — an absolute path. Use the working directory reported by the environment (NOT the skill directory). This value is used as `{cwd}` throughout the workflow for plan paths, cleanup, etc.
2. `cortex ctx task add "<user's request>"`   # → task_id
3. `cortex ctx task start <tid>`
4. `cortex ctx team create team-workflow-<tid>`
5. Register the skill on the task using the `task_update` tool: `task_update(task_id="<tid>", skill="{skill_dir}")`
   > **IMPORTANT**: Do NOT use `cortex ctx task update --skill` from a shell command — that CLI flag does not exist. You MUST use the `task_update` MCP tool which has a `skill` parameter.

After setup, call **`EnterPlanMode`** immediately. Then proceed to Teammate Assessment.

> **Path C note**: When entering via plan-time trigger (Entry Path C), skip the
> `EnterPlanMode` call after setup — plan mode is already active. After creating
> the team, register the plan file with `cortex ctx task update <tid> --plan <plan_path>` and set the skill
> with `task_update(task_id="<tid>", skill="{skill_dir}")`, then go directly to Phase 2 (Review & Validate).

---

## Teammate Assessment

After entering plan mode, assess whether the task warrants spawning teammate agents.
There are two entry paths:

### Entry Path A — Explicit user request
If the user explicitly requested teammates (e.g., "use teammates", "use a team",
"swarm this", "work in parallel"), **skip assessment** and proceed directly to Phase 1
with teammates. The user's intent is the decision.

### Entry Path B — Autonomous assessment
If the user did NOT explicitly request teammates, evaluate the task against these
criteria. A task warrants teammates when ANY of the following hold:

**Qualitative guidelines** (LLM evaluates):
1. **Multi-file scope**: The task touches 3+ files across 2+ directories, requiring
   parallel research into different parts of the codebase.
2. **Architectural impact**: The change affects how components interact, modifies
   interfaces/contracts, or changes system behavior in ways that need cross-cutting
   review.
3. **Design tradeoffs**: There are 2+ plausible approaches with real tradeoffs that
   benefit from parallel exploration before committing to one.
4. **Parallelizable research**: The task requires understanding 2+ independent
   subsystems or codebases that can be researched concurrently.
5. **Independently ownable subsystems**: The task spans 2+ subsystems that could be
   assigned to different developers (e.g., backend API + frontend UI, data layer +
   service layer), enabling parallel implementation.
6. **Meaningful architecture choices**: The task requires choosing between architectural
   patterns, data models, or system designs where the decision has lasting impact on
   the codebase.
7. **Parallelizable full-stack work**: The task involves real, concurrent implementation
   work across multiple stack layers (e.g., schema + API + UI) that teammates can
   execute in parallel.

**Complexity scoring checklist** (self-evaluate using this table):

| Signal | Points | How to evaluate |
|--------|--------|-----------------|
| File/component breadth | +5 per distinct file/module referenced or implied (max 25) | Count explicit paths AND semantic references ("the auth service") |
| Directory/layer breadth | +10 for 2+ unique parent directories, +20 for 3+ | Group files by their containing folder, count unique folders |
| Design keyword presence | +5 per keyword (max 20) | "refactor", "migrate", "restructure", "redesign", "architect", "rework", "overhaul", "rewrite" |
| Codebase-wide scope | +10 | "all files", "everywhere", "across the codebase", or implies global changes |
| Multi-step task | +5 per distinct action connected by "and"/"then" (max 15) | Count genuinely distinct actions, not trivial conjunctions |
| Design uncertainty | +10 | "how should we", "what's the best way", "tradeoff", "compare approaches" |
| Independent subsystem ownership | +10 | Can different parts be assigned to different devs? 2+ subsystems that could be separately owned |
| Architecture choice impact | +10 | Decision locks in a pattern that's costly to reverse; choosing between architectural patterns |
| Full-stack parallelism | +10 | Work across 2+ stack layers (frontend + backend, schema + service, etc.) that can proceed concurrently |

Score: 0–14 = low (single-agent sufficient), 15–34 = moderate (qualitative assessment is tiebreaker), 35+ = high (teammates recommended).

If a harness complexity score is present in the system reminders, use it as the
authoritative score. Otherwise, self-evaluate using the table above.

### Entry Path C — Plan-time trigger (from plan mode teammate assessment)
When the agent is in plan mode and its teammate assessment (in the plan mode reminder)
determines that teammates are warranted, it loads team-workflow instead of calling
exit_plan_mode. The agent has already drafted a plan. Plan mode is still active.
Proceed with: (1) Create task + team (Setup steps 1-4, but skip EnterPlanMode since
plan mode is already active), (2) Register the plan file on the task,
(3) Go directly to Phase 2 (Review & Validate) to have Reviser and Validator agents
review the drafted plan before presenting it to the user.

### Entry Path D — Team mode pre-enabled
When the system reminder indicates that team mode is active (user toggled it via Ctrl+G,
the /team command, or the UI toggle), **skip the entire Teammate Assessment** — do not
evaluate qualitative guidelines, do not calculate a complexity score. The user's mode
toggle IS the decision: teammates = yes. Proceed directly to Phase 1 with teammates.

### Decision
- **Entry Path A**: teammates = yes.
- **Entry Path B**: teammates = yes if ANY qualitative criterion is met OR complexity
  score ≥ 40.
- **Entry Path C**: The agent assessed its plan in plan mode and determined teammates are needed. Teammates = yes. Skip directly to Phase 2 (Review & Validate).
- **Entry Path D**: teammates = yes.
- **Otherwise**: teammates = no.

**You MUST state your reasoning.** When the decision is made autonomously (Entry Path B),
briefly explain which criteria were met (or not met) and the complexity score. Example:
> Teammate assessment: using teammates. Criteria met: multi-file scope (5 files across 3 directories),
> design tradeoffs (2 approaches for the API shape). Complexity score: 45/100.

This is required so the user understands why team mode was activated. For Entry Path A
(explicit user request) and Entry Path D (team mode toggle), no explanation is needed —
the user already indicated their intent.

### Proceeding with teammates
If teammates are needed, do NOT call ExitPlanMode yet. Proceed to Phase 1.

### Proceeding without teammates
If teammates are NOT needed:
1. The main agent researches and writes the plan itself (using Glob, Grep, Read — plan mode is active so these are allowed).
2. Call `ExitPlanMode` with the plan.
3. Run the **Cleanup Procedure**.
4. Standard single-agent flow handles implementation from ExitPlanMode's response. The team-workflow skill is done.

---

## Phase 1 — Research

```text
cortex ctx task update <tid> --active-form "Phase 1: Researching"
```

### Plan-Implement mode

1. Decompose the request into 2–5 focused **research questions** using the tiering guide below,
   then add all explore steps AND one plan-writer step in a single command:

   **Explore count guidance** (correlate with Teammate Assessment complexity score):
   | Complexity | Explore agents | When to use |
   |------------|---------------|-------------|
   | Narrow (score 20–29) | 2 | Single component, 1–2 files, clear requirements |
   | Moderate (score 30–44) | 3 | 2 components, 3–5 files, some design unknowns |
   | Broad (score 45–64) | 4 | 3+ components, cross-cutting concerns |
   | Very broad (score 65+) | 5 | System-wide, architectural, multiple unknowns |

   When in doubt, prefer fewer explorers with broader questions over many narrow ones — each agent has startup overhead.
   ```text
   cortex ctx step add -t <tid> "Explore <topic>" "Explore <topic2>" ... "Write plan: <task summary>"
   ```
   Note the plan-writer step ID as `<plan_sid>`.

2. Spawn ALL Explore agents AND the Plan agent in ONE single response (plan mode is
   already active from Setup). Launching the Plan agent immediately lets it absorb
   discoveries as they arrive, reducing plan-generation latency:
   ```text
   cortex ctx step start -t <tid> <explore_sid>
   # spawn Explore agent
   # ... repeat for each explore step ...
   cortex ctx step start -t <tid> <plan_sid>
   # spawn Plan agent (see Plan Spawn Template)
   ```
   Each Explore launch MUST set `run_in_background=true`, `team_name=team-workflow-<tid>`,
   `name=explore-<explore_sid>`.
   The Plan launch MUST set `run_in_background=true`, `team_name=team-workflow-<tid>`,
   `name=plan-<tid>`.

3. On each `Step <sid> complete: <summary>` or `Step <sid> FAILED: <reason>` callback (handle per the Completion and Failure Contracts section):
   a. Run `cortex ctx step list -t <tid>`
   b. Check for `[PLAN_AGENT_QUESTION]` messages (see Handling PLAN_AGENT_QUESTION below).
   c. Check whether all explore steps are in terminal state (done/failed/cancelled).

4. When ALL **explore** steps are in a terminal state (done, failed, or cancelled):
   - For any failed explore steps, log a gap discovery before proceeding:
     ```text
     cortex ctx discovery add "Explore step <sid> failed — gap in research: <step_text>" \
       --title "Explore failure" --tags explore-failure --team team-workflow-<tid>
     ```
      - *(See Plan Mode Pairing Rule in Prohibitions.)* Plan mode is already active from Setup.
      - **Stale PLAN_SIGNAL guard**: Before sending PLAN_SIGNAL, check the plan-writer step status via `cortex ctx step list -t <tid>`. If the plan-writer step is already `done` or `failed`, the plan agent finished early — skip PLAN_SIGNAL and go directly to next step (plan registration).
       - **Wait one polling cycle before sending PLAN_SIGNAL** — run `cortex ctx step list -t <tid>` once to ensure the plan agent has started its Phase A message poll. Always wait at least one polling cycle before sending PLAN_SIGNAL.
     - Send the finalize signal to the plan agent:
     ```text
     cortex ctx message send \
       --sender main \
       --recipient plan-<tid> \
       --content '[PLAN_SIGNAL] finalize plan_path={cwd}/.cortex/plans/plan-<tid>.md' \
       --summary "All explores done — finalize plan" \
       --team-name team-workflow-<tid> \
       --tags plan-signal
     ```
   - **Enter active polling loop** — while the plan-writer step is still running:
     ```text
     cortex ctx step list -t <tid>              # check if plan-writer done
     cortex ctx message list --recipient main --unread-only --json   # check for questions
     ```
      Handle any `[PLAN_AGENT_QUESTION]` messages found (see below). Repeat until
      plan-writer step is `done`, `failed`, or `cancelled`.

> **Note**: Discovery push notifications (up to 3/turn) are advisory only — they may be incomplete when many Explore agents fire simultaneously. The final `cortex ctx discovery list` sweep in Phase C is the authoritative completeness guarantee.

5. When the plan-writer step (`<plan_sid>`) completes:
   - Register the plan on the existing task immediately; the linked task plan is now the source of truth for Phase 2 and ExitPlanMode:
     ```text
     cortex ctx task update <tid> --plan {cwd}/.cortex/plans/plan-<tid>.md
     ```
   - **If the plan-writer step failed or was cancelled**: Check if the plan file exists
      on disk (using a platform-appropriate file existence check for `{cwd}/.cortex/plans/plan-<tid>.md`). If it exists, verify it is non-empty and
      contains at minimum a `## Steps` or `## Implementation Steps` section. If the file
      is empty or truncated, treat it as missing. If valid, register it and proceed.
      If missing or invalid, write the plan yourself (same structure as before — read
      `cortex ctx discovery list --team team-workflow-<tid>` and write the file).
   > **P1→P2 GATE**: `{cwd}/.cortex/plans/plan-<tid>.md` exists **and** `<tid>.plan` is set to that path in `tasks.yaml` — **immediately begin Phase 2**.

### Handling PLAN_AGENT_QUESTION messages

When a `[PLAN_AGENT_QUESTION]` message is found in the message list:
1. Parse the JSON payload from the content string. If JSON parsing fails, send an error
   message back to the plan agent and skip:
   ```text
   cortex ctx message send --sender main --recipient plan-<tid> \
     --content '[PLAN_AGENT_ANSWER] {"error": "Could not parse question JSON"}' \
     --team-name team-workflow-<tid> --tags plan-answer
   ```
2. If valid, call `AskUserQuestion` with the parsed questions to get the user's answers.
3. Mark the question message as read:
   ```text
   cortex ctx message mark-read --id <msg_id> --team-name team-workflow-<tid>
   ```
4. Send the answers back (multi-select answers encoded as comma-separated labels):
   ```text
   cortex ctx message send \
     --sender main \
     --recipient plan-<tid> \
     --content '[PLAN_AGENT_ANSWER] {"answers": {"<question text>": "<label or label1, label2>"}}' \
     --summary "Answer to plan agent question" \
     --team-name team-workflow-<tid> \
     --tags plan-answer
   ```

---

## Phase 2 — Review & Validate

```text
cortex ctx task update <tid> --active-form "Phase 2: Reviewing and validating plan"
```

> **REMINDER**: You are in plan mode from Phase 1. `{cwd}/.cortex/plans/plan-<tid>.md` has already been written by the Plan agent (`plan-<tid>`) at the end of Phase 1 and linked onto task `<tid>` via `cortex ctx task update --plan`.

> **HARD GATE**: You MUST spawn at least one Reviser agent AND at least one Validator agent, AND wait for ALL of them to complete BEFORE calling ExitPlanMode. The main agent does NOT review the plan itself — it delegates to Reviser agents and Validator agents.

1. Add review and validation steps:
   ```text
   cortex ctx step add -t <tid> "Review <aspect1>" "Review <aspect2>" "Write tests for <scope>" ...
   ```
   Prefer the smallest effective Phase 2:
   - Default: create **1 Reviser step** and **1 Validator step**
   - Only create additional P2 steps when the plan truly has multiple independent high-risk areas
   Create 1–2 review steps covering the highest-risk aspects of the plan.
   Create 1 validation step by default; use 2 only when test scope naturally splits into clearly independent areas.
   You MUST have at least one of each (review + validation).
2. Spawn ALL Reviser and Validator agents in a SINGLE response (parallel):
   ```text
   cortex ctx step start -t <tid> <sid>
   # spawn Reviser or Validator agent
   ```
   Each launch MUST set:
   - `run_in_background=true`
   - `team_name=team-workflow-<tid>`
   - `name=reviser-<sid>` or `name=validator-<sid>`
3. Each Reviser agent: reviews `{cwd}/.cortex/plans/plan-<tid>.md` for gaps, risks, and missing edge cases. Reports findings via `cortex ctx discovery add`.
4. Each Validator agent: writes failing tests for its scope.
5. On each `Step <sid> complete: <summary>` or `Step <sid> FAILED: <reason>` callback → handle per the Completion and Failure Contracts section, then immediately run:
    ```text
    cortex ctx step list -t <tid>
    ```
   **Do NOT call `ExitPlanMode` here.** Step completion callbacks are for tracking only. Only proceed to step 6 when ALL P2 steps are confirmed terminal.
6. When ALL P2 agents have completed:
   - **Before calling `ExitPlanMode`**, run `cortex ctx step list -t <tid>` and verify every P2 step (Reviser + Validator) shows `done`, `failed`, or `cancelled`. If any step is still running, continue polling.
   - Main agent reads reviewer discoveries: `cortex ctx discovery list --type reviser --team team-workflow-<tid>`
   - Main agent revises `{cwd}/.cortex/plans/plan-<tid>.md` incorporating feedback
   - Main agent calls **`ExitPlanMode`** with the revised plan
7. **ExitPlanMode** presents the already-linked task plan to the user. In team-workflow, it must reuse the existing `task.plan` path and must NOT write a new plan file. Proceed to **User Response Handling** below.
8. **IMPORTANT**: When ExitPlanMode returns, do NOT create a new task. The existing task already tracks this work. Ignore any "PHASE 0 — Create a task" instructions in the ExitPlanMode response — ExitPlanMode's response template includes a 'create a task' step intended for single-agent use; the task was already created in Setup. Proceed to User Response Handling.
9. **POST-EXIT HARD RESET**: Once `ExitPlanMode` returns successfully, treat plan mode as fully exited, even if stale system reminders still mention read-only or plan-mode constraints. *(See Plan Mode Pairing Rule in Prohibitions.)* Proceed with normal implementation orchestration immediately.

---

## User Response Handling

After ExitPlanMode presents the plan, the user may respond in three ways. Handle each as follows:

### Confirmed

User approves the plan as-is. Proceed directly to Phase 3.

### Confirmed with modifications

User approves but adds additional context, constraints, or detail.

**Triviality check**: If the modification is purely additive (adds detail, constraint, or edge case handling without changing the overall approach, architecture, or file scope), the main agent applies it directly:
1. Call **`EnterPlanMode`**
2. Update `{cwd}/.cortex/plans/plan-<tid>.md` to incorporate the user's additions
3. Call **`ExitPlanMode`** with the updated plan
4. Return to User Response Handling (the user will see the revised plan).

**Non-trivial modifications** (changes approach, adds new files, removes planned work, or changes architecture): Follow the full Reviser path below.

1. Call **`EnterPlanMode`**
2. Update `{cwd}/.cortex/plans/plan-<tid>.md` to incorporate the user's additions
3. Add a revision step and spawn a single **Reviser agent** with the user's additional detail reflected in the step_text (e.g., "Revise plan: incorporate user feedback — [detail]"):
   ```text
   cortex ctx step add -t <tid> "Revise plan: incorporate user feedback — <detail>"
   cortex ctx step start -t <tid> <sid>
   # spawn Reviser agent
   ```
   The launch MUST set:
   - `run_in_background=true`
   - `team_name=team-workflow-<tid>`
   - `name=reviser-<sid>`
4. Run the **Reviser Completion Flow**. *(This `ExitPlanMode` is a second plan mode cycle — `EnterPlanMode` was called above at step 1.)*

### Denied

User rejects the plan. Assess the scope of rejection:

- **Significant new research needed** (wrong approach, missing architecture understanding, needs a different direction entirely):
  1. Re-run Phase 1 in Plan-Implement mode: add new explore steps targeting the gaps. Spawn new Explore agents (all in parallel in one message) — do NOT call EnterPlanMode yet; call EnterPlanMode after all new explore steps complete.
  2. Wait for all new explore steps to complete, then write an updated `{cwd}/.cortex/plans/plan-<tid>.md` (use the plan structure defined in the Plan Spawn Template section) and register it.

  > **Budget note**: Denial loops consume from the same cumulative agent budget. If budget is low after a denial, the main agent should handle re-research itself rather than spawning new explore agents.
  3. Run Phase 2 with new Reviser + Validator agents
  4. **Verify you are in plan mode** before continuing: `EnterPlanMode` must have been called at the end of step 1 (after all new explore steps completed). This `ExitPlanMode` is a second plan mode cycle and is correct. Call **`ExitPlanMode`**
  5. Return to User Response Handling.

- **Revision with existing context** (wrong details, missed considerations, minor scope change — no new exploration required):
  1. Call **`EnterPlanMode`**
  2. Add a revision step and spawn a single **Reviser agent** with the denial reason in the step_text (e.g., "Revise plan: user rejected — [reason]"):
     ```text
     cortex ctx step add -t <tid> "Revise plan: user rejected — <reason>"
     cortex ctx step start -t <tid> <sid>
     # spawn Reviser agent
     ```
  3. Run the **Reviser Completion Flow**. *(This `ExitPlanMode` is a second plan mode cycle — `EnterPlanMode` was called above at step 1.)*

---

## Phase 3 — Implementation

Once the user accepts the plan:

```text
cortex ctx task update <tid> --active-form "Phase 3: Implementing"
```

> **HARD GATE**: The main agent MUST NOT use Edit, Write, or any file-mutation tools.
> ALL code changes are delegated to Implementor agents. If you find yourself about to
> edit a file, STOP — spawn an Implementor agent instead.

1. Add implementation steps based on the approved plan:
   ```text
   cortex ctx step add -t <tid> "<step1>" "<step2>" ...
   ```
   **Chunk sizing rule**: Prefer **3–4 implementor steps total** for a normal multi-file task, not one tiny worker per file.
   Group related file changes by ownership area or layer so each Implementor has enough work to justify startup overhead.
   Only exceed 4 concurrent Implementors when the task has truly independent, substantial workstreams.
2. Start all implementation steps first, then spawn all Implementor agents in the same turn with no extra reasoning in between:
   ```text
   cortex ctx step start -t <tid> <sid1> && cortex ctx step start -t <tid> <sid2> && ...
   # spawn all Implementor agents immediately after the step-start command returns
   ```
   Do NOT implement changes yourself. Spawn an agent for every step.
   **Do NOT pause to reinterpret plan-mode state, read stale reminders, or re-check whether implementation is allowed.** If the plan was accepted and Phase 3 has begun, implementation is allowed.
3. After launching the Implementor agents, do NOT assume the steps are done just because the workers were spawned. Wait for completion callbacks / agent outputs, then reconcile step status immediately (see Completion Contract below).
3a. **No ad hoc Phase 3 expansion**: After the initial Phase 3 implementation wave is launched, do NOT spawn additional Phase 3 workers unless:
   - an implementation step fails and needs a retry,
   - a previously blocked implementation step becomes ready, or
   - the approved plan explicitly included a later implementation batch.
   Do NOT spawn extra workers for monitoring, interpretation, side analysis, or "just in case" follow-up work.
4. On each `Step <sid> complete: ...` or `Step <sid> FAILED: ...` (handle per the Completion and Failure Contracts section):
   a. Run `cortex ctx step list -t <tid>` to see updated status and remaining steps
   b. Check for newly unblocked pending steps and spawn Implementor agents for them
4a. **Implementor failure protocol**: If an Implementor step reaches `failed` or `cancelled`
    (either via `Step <sid> FAILED:` or agent termination without a signal):
    a. Log the failure:
       ```text
       cortex ctx discovery add "Implementor step <sid> failed: <reason>" \
         --title "Implementor failure" --tags implementor-failure --team team-workflow-<tid>
       ```
    b. Check whether the failed step blocks downstream pending steps.
    c. First retry (re-spawn Implementor), if that fails have main agent implement the step, if that still fails skip (mark cancelled and continue — only if no steps depend on it), or abort (run Workflow Abort cleanup).
5. When all implementation steps are in a terminal state (done, failed, or cancelled) → Phase 3 complete.

---

## Phase 4 — Review + Ship

```text
cortex ctx task update <tid> --active-form "Phase 4: Reviewing and shipping"
```

1. Add the Tester step first:
   ```text
   cortex ctx step add -t <tid> "[P4] Run test suite"
   ```
   Note the step ID as `<test_sid>`.
2. Start the Tester step and spawn the Tester agent:
   ```text
   cortex ctx step start -t <tid> <test_sid>
   # spawn Tester agent (background) using the Tester spawn template
   ```
   The Tester is responsible for both running the test suite AND fixing any failures it finds before completing its step. By the time the Reviewer runs, all tests should be passing.
3. When the Tester step completes or fails (done, failed, or cancelled — handle per the Completion and Failure Contracts section):
   - Add and start the Reviewer step unconditionally:
     ```text
     cortex ctx step add -t <tid> "[P4] Review all changes"
     cortex ctx step start -t <tid> <review_sid>
     # spawn Reviewer agent (background) using the Reviewer spawn template
     ```
4. When the Reviewer step completes or fails (handle per the Completion and Failure Contracts section):
   - Confirm all P4 steps are terminal (per **Step Status Refresh Rule**).
   - If the reviewer flagged significant issues via discoveries:
      a. Read reviewer discoveries: `cortex ctx discovery list --type reviewer --team team-workflow-<tid>`
      b. Add an implementation step per issue: `cortex ctx step add -t <tid> "Fix: <issue>"`
      c. Spawn Implementor agents for each fix step.
      d. When all fix steps are in a terminal state (done, failed, or cancelled), proceed to cleanup.
   - **Ask the user if they want to create a PR.** If yes:
      ```text
      cortex ctx step add -t <tid> "[P5] Create pull request"
      cortex ctx step start -t <tid> <pr_sid>
      # spawn PR agent with pr_mode: create (see PR Agent Spawn Template)
      ```
      Wait for PR step to complete before running cleanup.
    - **Always** run the **Cleanup Procedure**.

---

## Completion and Failure Contracts (HIGHEST PRIORITY)

### Completion Contract

When ANY agent output contains `Step <sid> complete: <text>`, the subagent is signaling
that it has finished its assigned work. Immediately reconcile workflow state:
```text
cortex ctx step list -t <tid>
```
to see updated progress and unblock next steps.

**Monitoring discipline (lightweight cadence)**:
- Run `cortex ctx step list -t <tid>` on a light cadence — roughly once every 1–3 turns of orchestration work, or whenever a phase has been in flight long enough that completion is plausible. This is cheap and authoritative; do NOT skip it just because no push notification arrived.
- Treat push notifications (discoveries, completion callbacks) as opportunistic signals — they may arrive late, batched, or not at all for a given step. The `step list` sweep is the source of truth.
- Reserve `agent_output` (especially `wait=true`) for cases where you actually need the agent's text output to decide the next action — e.g., reading a strategy agent's question, debugging a failure, or when no other ready work is available.
- Between sweeps, do other useful orchestration work (drafting next-phase steps, reading discoveries, answering plan-agent questions) so polling never blocks progress.
- Do NOT call `agent_output(wait=true)` while other agents in the same phase are still running — this serializes parallel work. Only use `agent_output(wait=true)` after all parallel agents in a phase have completed, or when one specific agent's text output is required to decide the next action and no peer agents are concurrently in flight.

If `cortex ctx step list -t <tid>` still shows the step as `in_progress`, the main agent MUST run:
```text
cortex ctx step done <sid> -t <tid>
```
immediately before proceeding.

**Step ownership**:
- Preferred path: subagents both call `cortex ctx step done` and emit `Step <sid> complete`.
- Main-agent fallback: if a completion line is observed but the ctx step is still `in_progress`, the main agent marks it done immediately.
- Never leave a completed step `in_progress` while proceeding to later phases.

### Failure Contract

When ANY agent output contains `Step <sid> FAILED: <reason>`, handle it immediately:

1. Run `cortex ctx step list -t <tid>` to refresh visibility. If the step still shows `in_progress`, mark it terminal yourself (`cortex ctx step done <sid> -t <tid>` if the worker completed despite the missing state sync, or cancel/fail it using the appropriate workflow command/path before proceeding).
2. Report the failure via:
   ```text
   cortex ctx discovery add "Agent failed step <sid>: <reason>" --title "Step failure" --tags agent-failure --team team-workflow-<tid>
   ```
3. Decide how to proceed based on the current phase:
   - **P1 (Research)**: If other Explore agents are still running, wait for them. Partial research is acceptable — note the gap when writing the plan.
   - **P2 (Review/Validate)**: If a Reviser failed, proceed with remaining reviewer feedback. If a Validator failed, note missing test coverage in the plan — do NOT skip P2 entirely.
   - **P3 (Implementation)**: Retry the failed step ONCE by spawning a new Implementor agent with the same step text. If it fails again, halt the workflow and ask the user how to proceed.
     > **Budget note**: Retry spawns count against the cumulative budget. If a retry would exceed the 45-agent budget, the main agent should attempt the work directly instead of spawning a new Implementor.
   - **P4 (Review/Ship)**: If the Tester failed, re-run tests manually or spawn a new Tester. If the Reviewer failed, spawn a replacement Reviewer. Do NOT ship without both review and test results.

### Agent Timeout / Hang Detection

Agents may hang, crash, or terminate without emitting either a completion or failure line.
The main agent MUST monitor for this:

1. **After spawning agents**, periodically check their status. If an agent has terminated
   (its output stream has ended) without emitting `Step <sid> complete:` or `Step <sid> FAILED:`,
   treat it as an implicit failure:
   ```text
   cortex ctx discovery add "Agent for step <sid> terminated without completion signal" --title "Agent hang/crash" --tags agent-failure --team team-workflow-<tid>
   ```
   Then follow the Failure Contract (step 3) for the current phase.

2. **Do NOT wait indefinitely.** If all other agents in a phase have completed but one agent
   has produced no new output, check its status. If it has terminated, handle per above.
   If it is still running but stalled, allow additional time — but if it remains unresponsive
   after all peers have long finished, terminate it and treat as a failure.

---

## Phase Gate Summary

- **Setup → P1 → P2**: Skill triggered → `EnterPlanMode` → teammate assessment → Explore+Plan agents → plan registered → Reviser+Validator → revise plan → `ExitPlanMode`
- **P3 → P4 → P5**: User approves plan → Implementors → Tester+Reviewer → cleanup → (optional) PR agent
- **Alternate paths**: No-teammate exit (main agent writes plan → `ExitPlanMode` → team deleted → standard single-agent flow) · Entry Path C / Plan-time entry (Setup without `EnterPlanMode` → register plan → Phase 2)

### Workflow Abort

If the workflow is aborted or fatally fails before reaching P4 cleanup, always run the **Cleanup Procedure**. This prevents orphaned plan files, stuck tasks, dangling teams, and leftover messages/discoveries.

### Feedback and post-task analysis

Feedback collection, retrospective analysis, and user-summary follow-up are **not part of the critical path** for implementation.

- Do NOT spawn feedback/summary subagents before the implementation workflow is complete.
- Finish implementation, testing, review, and cleanup first.
- Only after the main workflow is complete should you collect retrospective feedback or run a postmortem-style agent, unless the user explicitly asks to interrupt delivery and switch to feedback collection.

---

### Discovery CLI Capabilities and Limits

- `discovery list` supports `--type`, `--tags`, and `--team` filters.
- Use `--type <role>` to scope reads by source agent type (e.g., `--type explore`, `--type reviser`). This is the primary filter for role-based access control.
- Use `--tags <tag>` for content-based filtering (secondary, human-readable).
- Always include `--team {team_name}` to prevent cross-team bleed in multi-task scenarios.
- `discovery search <query>` does full-text search but accepts no filter flags.
- `discovery add` supports `--sender` for attribution labeling. Use `--type <role>` to scope reads by source agent type. Role files pass `--type` explicitly in `discovery add` calls to label their output; the CLI does not auto-infer sender type on writes.

---

## Spawn Templates

> **`{skill_dir}`**: Replace with the base directory shown at the top of this skill output (`Base directory for this skill: ...`).

> **`{cwd}`**: The absolute path to the user's working directory, captured during Setup step 1. This is the project root — NOT the skill directory. All plan files and cleanup paths use this.
 
> **`{plan_path}`**: Use `{cwd}/.cortex/plans/plan-<tid>.md`.

### Base Spawn Template

All roles share this structure. Replace `<role>` with the role name from the overrides table below.

```
Read your role instructions from: {skill_dir}/roles/<role>.md

step_id: {step_id}
step_text: {step_text}
task_id: {task_id}
team_name: team-workflow-{task_id}
name: <role>-{step_id}
plan_path: {plan_path}
```

### Per-Role Overrides

| Role | Role file | subagent_type | Name override | Extra params | Notes |
|------|-----------|---------------|---------------|--------------|-------|
| Explore | explore.md | Explore | explore-{step_id} | *(none — no plan_path)* | Do NOT pass `allowed_tools` — Explore defaults include Read, Grep, Glob, shell access, ctx |
| Plan | plan.md | general-purpose | plan-{task_id} | plan_path: `{cwd}/.cortex/plans/plan-{task_id}.md` | Uses `{plan_sid}` not `{step_id}` for step_id param |
| Reviser | reviser.md | general-purpose | reviser-{step_id} | — | — |
| Validator | validator.md | general-purpose | validator-{step_id} | no_discovery_reminder: true | — |
| Implementor | implementor.md | general-purpose | implementor-{step_id} | — | — |
| Reviewer | reviewer.md | general-purpose | reviewer-{step_id} | — | — |
| Tester | tester.md | general-purpose | tester-{step_id} | no_discovery_reminder: true | — |
| PR | pr.md | general-purpose | pr-{step_id} | pr_mode: {pr_mode} | `pr_mode` is required — pr.md expects `create` or `update` |

=== trust-center/ ===
---
name: trust-center
description: "Use for ALL Snowflake Trust Center requests: security findings, scanner analysis, scanner management, finding remediation, severity distribution, CIS benchmarks, Security Essentials, Threat Intelligence, AI Security, enable/disable scanners, scanner schedules, notifications, webhook, notification integration, at-risk entities, security posture, vulnerability analysis, detection analysis, remediation guidance."
---

# Trust Center

Helps users analyze, manage, and remediate security findings from Snowflake Trust Center.

## When to Use

- User asks about Trust Center findings, scanners, or security posture
- User wants to enable/disable scanners or change schedules/notifications
- User wants to fix or remediate a specific security finding
- User asks about CIS Benchmarks, Security Essentials, Threat Intelligence, or AI Security

## Workflow

```
Start
  ↓
Intent Detection
  ├─→ ANALYZE FINDINGS  → Load findings-analysis/SKILL.md
  ├─→ ANALYZE SCANNERS  → Load scanner-analysis/SKILL.md
  ├─→ MANAGE SCANNERS   → Load api-management/SKILL.md
  └─→ REMEDIATE FINDING → Load finding-remediation/SKILL.md
```

### Step 1: Detect Intent

| User Intent | Keywords | Route |
|-------------|----------|-------|
| Analyze findings | findings, severity, new findings, resolved, trend, security posture, categories | [findings-analysis/SKILL.md](findings-analysis/SKILL.md) |
| Analyze scanners | scanners, scanner packages, coverage, disabled scanners, CIS, what scanners | [scanner-analysis/SKILL.md](scanner-analysis/SKILL.md) |
| Manage scanners | enable, disable, schedule, notification, webhook, notification integration, run scanner, execute | [api-management/SKILL.md](api-management/SKILL.md) |
| Remediate findings | fix, remediate, at-risk entities, suggested action, how to fix | [finding-remediation/SKILL.md](finding-remediation/SKILL.md) |

If intent is unclear, ask:
```
What would you like to do with Trust Center?
1. Analyze findings (severity, trends, categories)
2. Review scanners (inventory, coverage, health)
3. Manage scanners (enable/disable, schedules, notifications)
4. Remediate a finding (fix a specific security issue)
```

### Step 2: Load Reference and Sub-Skill

**MANDATORY: Load** [references/trust-center-api.md](references/trust-center-api.md) — this contains all Trust Center views, columns, stored procedures, and scanner mappings. Then route to the appropriate sub-skill based on detected intent.

## Response Style

All Trust Center sub-skills must follow these rules:

- **Be concise.** Lead with the answer or action. Omit filler sentences, preamble, and restatements of what the user already knows.
- **Do not speculate.** Never list possible causes, troubleshooting checklists, or "common issues" unless the user asks. If a remediation didn't work, say "wait for data refresh and re-run" — do not enumerate hypothetical reasons.
- **Show data, not prose.** Prefer tables and SQL results over narrative paragraphs. Skip formatting boilerplate (e.g., section headers for a single sentence).
- **One action at a time.** Present the next concrete step. Do not dump an entire multi-step plan when the user only needs the current step.
- **Skip the menu when intent is clear.** Only present option lists when the user's intent is genuinely ambiguous.

## Stopping Points

- ✋ Step 1: If user intent is unclear, ask for clarification

## Output

This skill routes to sub-skills, each of which produces its own output:

| Sub-Skill | Output |
|-----------|--------|
| findings-analysis | Findings counts, severity distribution, trends, categories |
| scanner-analysis | Scanner inventory, coverage gaps, health checks |
| api-management | Confirmation of scanner configuration changes |
| finding-remediation | Remediation steps, SQL, verification |

=== warehouse/ ===
---
name: warehouse
description: "Warehouse configuration, DDL, Gen2, adaptive warehouses, adaptive compute, MAX_QUERY_PERFORMANCE_LEVEL, QUERY_THROUGHPUT_MULTIPLIER, performance tuning, sizing, credit-per-hour rates, resume behavior, region availability, Snowpark-optimized limitations. Not for cost analytics or warehouse spend (cost-intelligence) or billing."
---

# Warehouse Skill Router

Route warehouse-related questions to the appropriate sub-skill.

> This router currently handles two sub-skills: gen2-warehouse and adaptive-warehouse. Additional sub-skills (sizing, monitoring, optimization, etc.) will be added here as they are developed.

## When to Use

Activate this skill when the user asks about any of:

- **Gen2 keywords**: "gen2", "generation 2", "GENERATION = '2'", "gen2 credit rate", "convert to gen2", "gen1 to gen2", "gen2 regions", "gen2 limitations", "gen2 performance", "warehouse generation", "gen2 benchmark", "compare gen1 gen2"
- **Performance keywords**: "DML performance", "slow DELETE", "slow MERGE", "slow resume", "resume time", "warehouse resume", "warehouse is slow", "speed up warehouse"
- **Warehouse creation/management**: "create warehouse", "alter warehouse", "warehouse size", "warehouse generation"
- **Warehouse cost/credits**: "warehouse credits", "warehouse cost", "how much is a warehouse", "warehouse pricing", "credits per hour"
- **Adaptive keywords**: "adaptive", "adaptive compute", "adaptive warehouse", "CREATE ADAPTIVE WAREHOUSE", "WAREHOUSE_TYPE = 'ADAPTIVE'", "MAX_QUERY_PERFORMANCE_LEVEL", "QUERY_THROUGHPUT_MULTIPLIER", "convert to adaptive", "adaptive warehouse billing"

## When NOT to Use

**Do NOT use this skill for Interactive Warehouse Questions.**
Questions like "what is an interactive warehouse" or "how do I use an interactive warehouse" should use the `interactive-warehouse` skill.

**Do NOT use this skill for warehouse spending or cost analytics.**
Questions like "how much did my warehouse spend?" or "show me warehouse credits used" belong to the `cost-intelligence` skill, which queries `SNOWFLAKE.ACCOUNT_USAGE`.
This skill covers warehouse configuration, DDL, Gen2, adaptive warehouses, and performance only.

## Routing

Match the user's question to keywords and load the corresponding sub-skill.

| Keywords | Sub-skill to Load |
|----------|-------------------|
| interactive warehouse, create interactive warehouse, add tables to warehouse, remove tables from warehouse, resume interactive warehouse, suspend interactive warehouse | **Route to** `snowflake-interactive` skill |
| adaptive, adaptive compute, adaptive warehouse, CREATE ADAPTIVE WAREHOUSE, WAREHOUSE_TYPE = 'ADAPTIVE', convert to adaptive, MAX_QUERY_PERFORMANCE_LEVEL, QUERY_THROUGHPUT_MULTIPLIER, adaptive billing, adaptive tuning | **Load** `adaptive-warehouse/SKILL.md` |
| gen2, generation 2, GENERATION = '2', create gen2, convert to gen2, gen1 to gen2, gen2 credit rate, gen2 regions, gen2 limitations, gen2 performance, gen2 benchmark, compare gen1 gen2 | **Load** `gen2-warehouse/SKILL.md` |
| DML performance, slow DELETE, slow MERGE, slow UPDATE, slow resume, resume time, warehouse resume, warehouse is slow, speed up warehouse, improve warehouse performance | **Load** `gen2-warehouse/SKILL.md` |
| warehouse creation, warehouse size, warehouse generation, alter warehouse | **Load** `gen2-warehouse/SKILL.md` |
| warehouse credits, warehouse cost, how much is a warehouse, warehouse pricing, credits per hour | **Load** `gen2-warehouse/SKILL.md` |

> **Note:** Interactive warehouse questions route to the `snowflake-interactive` skill. Adaptive warehouse questions route to `adaptive-warehouse/SKILL.md`. All other warehouse intents route to `gen2-warehouse/SKILL.md`. As new sub-skills are added, this routing table will expand.

## Workflow

### Step 1: Look Up the Warehouse (if a specific warehouse is named)

If the user mentions a **specific warehouse by name**, you **MUST** run a lookup before routing:

```sql
SHOW WAREHOUSES LIKE '<warehouse_name>';
```

**IMPORTANT:** Always use `SHOW WAREHOUSES LIKE '<name>'` with the LIKE clause — do NOT use bare `SHOW WAREHOUSES` as it may fail with `ENABLE_ERROR_ON_FETCH_FALLBACK` errors on some accounts.

From the result, extract and note these columns:

| Column | Why It Matters |
|--------|---------------|
| `type` (warehouse_type) | Determines routing: INTERACTIVE → interactive skill, ADAPTIVE → adaptive sub-skill, SNOWPARK-OPTIMIZED → Gen1-only (not supported in Gen2 or Adaptive), STANDARD → eligible for Gen2 |
| `generation` | If already `2`, tell the user it's already Gen2. If `1` or empty, may be a Gen2 candidate |
| `size` | Gen2 supports XSMALL through X4LARGE only. X5LARGE and X6LARGE are NOT supported |
| `resource_constraint` | Shows the resource constraint variant (e.g., `STANDARD_GEN_1`, `STANDARD_GEN_2`, `MEMORY_16X`). Confirms generation and warehouse configuration |

**Routing based on lookup results:**

| Condition | Action |
|-----------|--------|
| `type` = `INTERACTIVE` | **Stop.** Tell the user this is an Interactive warehouse — Gen2 does not apply. Route to the `snowflake-interactive` skill for interactive warehouse questions |
| `type` = `ADAPTIVE` | Load `adaptive-warehouse/SKILL.md` |
| `type` = `SNOWPARK-OPTIMIZED` | **Stop.** Tell the user Snowpark-Optimized is a Gen1-only warehouse type — Gen2 and Adaptive are not supported. See Gen2 limitations in `gen2-warehouse/SKILL.md` |
| `generation` = `2` | Tell the user the warehouse is already Gen2. No conversion needed |
| `size` = `X5LARGE` or `X6LARGE` | Tell the user Gen2 does not support this size. Suggest benchmarking on a Gen2 X4LARGE |
| `type` = `STANDARD` and `generation` = `1` (or empty) | Eligible for Gen2. Proceed with keyword-based routing below |

**IMPORTANT:** Do NOT skip this lookup. Even if the user's question contains Gen2 keywords, the warehouse type takes priority — an INTERACTIVE warehouse should never receive Gen2 advice.

### Step 2: Detect Intent and Route

If no specific warehouse was named, or after the lookup confirms the warehouse is a STANDARD warehouse (Gen1 or Gen2), match the user's question to keywords and load the matching sub-skill.

### Step 3: Execute Sub-skill

Follow the loaded sub-skill's workflow completely. Each sub-skill is self-contained with its own references, workflows, and stopping points.

## Sub-skills

| Sub-skill | Skill | Purpose |
|-----------|-------|---------|
| Interactive Warehouse | `snowflake-interactive` (full skill name — not a sub-skill of this router) | Interactive warehouse creation, table management, resume/suspend |
| Adaptive Warehouse | `adaptive-warehouse/SKILL.md` | Adaptive warehouse creation, conversion, parameters, limitations, billing, tuning, analysis |
| Gen2 Warehouse | `gen2-warehouse/SKILL.md` | Gen2 explanation, creation, conversion, limitations, regions, costs, benchmarking, performance recommendations |

## Stopping Points

- If intent is ambiguous and cannot be mapped to a sub-skill, ask the user to clarify before loading any sub-skill
- Honour all stopping points defined within loaded sub-skills

=== workload-performance-analysis/ ===
---
name: workload-performance-analysis
description: "Snowflake SQL query execution analysis via ACCOUNT_USAGE views. Triggers: spilling, partition pruning, cache hit rates, clustering keys, search optimization (SOS) candidates, query acceleration (QAS) eligibility, predicate column analysis for clustering/SOS, per-warehouse spill/prune/cache metrics, slow SQL query diagnosis. Not for: cost/credits (cost-intelligence), access audit (data-governance), writing or debugging user SQL."
---

# Workload Performance Analysis

**You are using the workload-performance-analysis skill. Follow these instructions exactly.**

This is a **unified performance analysis skill** that handles all Snowflake performance questions through a single entry point. It detects the entity type and depth from the user's input, then routes to the appropriate sub-skill for each phase.

---

## Step 0: Source Detection

Before doing entity detection, **inspect the system-reminder content** of the current invocation for one of three specific markers. Source detection is **positive identification** — only the explicit presence of a marker counts. Do not infer source from any other signal.

| Signal in system-reminder | Source | Route to |
|---|---|---|
| `${queryHistoryListContext}` present | UI_QUERY_HISTORY | Load `ui-query-history/summary/SKILL.md` and follow it exactly. Do NOT continue with the entity-detection flow. |
| `${queryDetailsContext}` present | UI_QUERY_DETAILS | Load `ui-query-details/summary/SKILL.md` and follow it exactly. Do NOT continue with the entity-detection flow. |
| `${performanceExplorerContext}` present | UI_PERFORMANCE_EXPLORER | Load `ui-performance-explorer/summary/SKILL.md` and follow it exactly. Do NOT continue with the entity-detection flow. |
| No marker present | CLI | Continue to Step 0A (Entity Detection) below. |

**Important:** Treat the "no marker" case as CLI even when the invocation may originate from a UI surface (e.g., a user typing into Cortex Code from inside Snowsight without clicking "Analyze with CoCo"). Do NOT attempt to infer UI context from any other signal — only the explicit `${queryHistoryListContext}` / `${queryDetailsContext}` / `${performanceExplorerContext}` system-reminder markers route to the UI sub-skills. Everything else, including UI-without-button scenarios, follows the CLI flow.

UI sources hand control fully to their dedicated sub-skill — do not layer additional WPA behavior on top.

---

## Step 0A: Detect Entity + Depth + Acquire Data

**Before doing any analysis, determine three things:**

### 0A. Entity Detection

Inspect the user's input and classify the primary entity:

**UI context detection:** The UI surfaces structured context data via two mechanisms — either inlined into the prompt as `${...}` variables (e.g. `${warehouseContext}`), or registered as a `get_page_context` provider that the agent invokes lazily (e.g. for `${performanceExplorerContext}`). When any UI context is detected via either mechanism, the skill is in **UI mode** — parse the available data (invoking `get_page_context` if registered) and use it directly instead of running SQL queries.

| Signal in Input | Entity Type |
|---|---|
| Specific query ID (UUID-like format, e.g. `01b24bb0-0007-9627-0000-0001234abcde`) | **QUERY** |
| `query_parameterized_hash` value or "query pattern" / "recurring queries" / "repeated queries" | **QUERY_PATTERN** |
| Warehouse name (e.g. "ANALYTICS_WH") without query ID | **WAREHOUSE** |
| Table name (e.g. "DB.SCHEMA.ORDERS") | **TABLE** |
| "spilling", "spillage", "memory pressure", "spill to disk", "remote spilling" | **SPILLING** |
| "pruning", "partitions scanned", "scan volume", "worst pruning" | **PRUNING** |
| "clustering", "clustering keys", "cluster by", "tables for clustering" | **CLUSTERING** |
| "search optimization", "search index", "SOS", "search opt candidates" | **SEARCH_OPT** |
| "QAS", "query acceleration", "acceleration service", "QAS eligible" | **QAS** |
| "cache hit", "cache rate", "cache efficiency", "worst cache", "local disk cache", "warehouse cache" | **CACHE** |
| `${...}` context containing multiple queries | **MULTI_QUERY** |
| `${...}` context containing a single query | **QUERY** |
| "stored procedure", "procedure analysis", "child queries", "procedure breakdown", "CALL analysis", "nested calls", "stored procedure runtime", OR a query_id whose resolved `query_type = 'CALL'` | **STORED_PROCEDURE** |
| Multiple query_ids (2+ UUIDs), "these queries", "this set of queries", "analyze these N queries", "the workload", a SQL `WHERE` fragment over `QUERY_HISTORY` ("queries by user X", "queries on warehouse Y last week", "queries matching …"), or a list of `query_parameterized_hash` values ("all executions of pattern <hash>") | **QUERY_SET** |
| No specific entity identified | **UNKNOWN** |

**Entity Identifier Validation:** The following entity types require a concrete identifier. If detected but the identifier is missing or unresolvable, **stop and ask the user to provide it before proceeding.**

| Entity Type | Required Identifier |
|---|---|
| QUERY | `query_id` (UUID format) |
| QUERY_PATTERN | `query_parameterized_hash` |
| WAREHOUSE | `warehouse_name` |
| TABLE | Fully qualified table name (`database.schema.table`) |
| STORED_PROCEDURE | `query_id` of the parent CALL (UUID format) |
| QUERY_SET | One of (a) list of 2–1000 `query_id` values, (b) SQL `WHERE` fragment over `QUERY_HISTORY` with a time bound, (c) list of `query_parameterized_hash` values with a time bound |

**If entity is UNKNOWN:** Ask the user:
```
What would you like me to analyze?

1. A specific entity — provide a warehouse name, query ID, table name, or query pattern hash
2. A stored procedure run — provide the parent CALL query_id (analysis covers the parent + recursive child queries)
3. A named set of queries — provide a list of query_ids, a filter over query_history, or a list of pattern hashes
4. Account-level health check — scan across all performance dimensions (spilling, pruning, cache, QAS)
```

**MANDATORY STOPPING POINT:** Wait for the user's response.

- If the user provides a specific entity, re-classify and route accordingly.
- If the user picks option 2, route as **STORED_PROCEDURE** entity.
- If the user picks option 3, route as **QUERY_SET** entity.
- If the user picks option 4, proceed as **ACCOUNT** entity.

### 0A.1. Resolve query_id metadata before routing

The QUERY vs STORED_PROCEDURE choice cannot be made statically — it depends on `query_type`, which lives in `QUERY_HISTORY`. **For any input that resolves to a single `query_id`** (whether typed by the user or extracted from `${...}` UI context), perform a SQL round-trip first:

1. Fetch and execute the verified query: `Find stored procedure parent CALL` with `<QUERY_ID>` set to the user's id and `<DAYS>` = 7.
2. Inspect the resulting `query_type`:
   - `query_type = 'CALL'` → route to **STORED_PROCEDURE**. Reuse the fetched row as the parent CALL row inside `stored-procedure/summary/SKILL.md` Step 1 (do NOT re-fetch).
   - any other `query_type` → route to **QUERY**. Reuse the fetched row inside `query/summary/SKILL.md` Step 1 (do NOT re-fetch).
   - 0 rows returned → expand the time window per the QUERY/STORED_PROCEDURE summary's expand-window stop point.

This is intentionally a static round-trip; it ensures auto-routing on `query_type='CALL'` is deterministic across all input channels (CLI direct prompt, UI single-query context, `0A` static pattern match).

For input forms with **multiple ids, a SQL filter, or a hash list** (QUERY_SET), no resolve-then-route step is needed — those forms route unconditionally to QUERY_SET regardless of the resolved set's contents.

### 0B. Depth Detection

| Depth | Trigger Keywords | Phases to Load |
|---|---|---|
| **SUMMARY** | "summary", "overview", "quick look", "high-level", "brief", "health check" | `summary/` only |
| **DIAGNOSIS** | "what's wrong", "issues", "problems", "bottlenecks", "analyze", "why is X slow", "root cause", "performance issues", "concurrency issues", "statement timeout" | `summary/` + `detection/` |
| **RECOMMENDATION** | "recommend", "suggestion", "what should I do", "how to fix", "how to improve", "optimize", "best practice", "action items" | `summary/` + `detection/` + `recommendation/` |

**Default:** If depth is unclear, default to SUMMARY — load `summary/` only, then ask if user wants deeper analysis.

### 0C. Data Acquisition

- **If `${...}` context data is present (UI mode):** Parse the context data first. Use whatever fields are available as a starting point. However, the context may only contain partial information (e.g., query execution metrics but no pruning or spilling breakdown). **If the analysis requires data not present in the context, run supplementary SQL queries** using verified queries from the semantic model (see "SQL Query Construction" section below).
- **If no context data (CLI mode):** Construct SQL using verified queries from the semantic model to fetch data from ACCOUNT_USAGE views.

---

## Phase Routing

After detecting entity and depth, load the appropriate sub-skills:

### Entity → Sub-Skill Routing Table

| Entity | Summary (Phase 1) | Detection (Phase 2) | Recommendation (Phase 3) |
|---|---|---|---|
| **UI_QUERY_HISTORY** | `ui-query-history/summary/SKILL.md` | *(not applicable)* | *(not applicable)* |
| **UI_QUERY_DETAILS** | `ui-query-details/summary/SKILL.md` | *(not applicable)* | *(not applicable)* |
| **UI_PERFORMANCE_EXPLORER** | `ui-performance-explorer/summary/SKILL.md` | *(not applicable)* | *(not applicable)* |
| **QUERY** | `query/summary/SKILL.md` | `query/detection/SKILL.md` | `query/recommendation/SKILL.md` |
| **QUERY_PATTERN** | `query-pattern/summary/SKILL.md` | `query-pattern/detection/SKILL.md` | `query-pattern/recommendation/SKILL.md` |
| **WAREHOUSE** | `warehouse/summary/SKILL.md` | `warehouse/detection/SKILL.md` | `warehouse/recommendation/SKILL.md` |
| **TABLE** | `table/summary/SKILL.md` | `table/detection/SKILL.md` | `table/recommendation/SKILL.md` |
| **SPILLING** | `spilling/summary/SKILL.md` | `spilling/detection/SKILL.md` | `spilling/recommendation/SKILL.md` |
| **PRUNING** | `pruning/summary/SKILL.md` | `pruning/detection/SKILL.md` | `pruning/recommendation/SKILL.md` |
| **CLUSTERING** | `pruning/summary/SKILL.md` | `pruning/detection/SKILL.md` | `pruning/recommendation/SKILL.md` |
| **SEARCH_OPT** | `pruning/summary/SKILL.md` | `pruning/detection/SKILL.md` | `pruning/recommendation/SKILL.md` |
| **QAS** | `qas/summary/SKILL.md` | `qas/detection/SKILL.md` | `qas/recommendation/SKILL.md` |
| **CACHE** | `cache/summary/SKILL.md` | `cache/detection/SKILL.md` | `cache/recommendation/SKILL.md` |
| **ACCOUNT** | `account/summary/SKILL.md` | `account/detection/SKILL.md` | `account/recommendation/SKILL.md` |
| **STORED_PROCEDURE** | `stored-procedure/summary/SKILL.md` | `stored-procedure/detection/SKILL.md` | `stored-procedure/recommendation/SKILL.md` |
| **QUERY_SET** | `query-set/summary/SKILL.md` | `query-set/detection/SKILL.md` | `query-set/recommendation/SKILL.md` |
| **MULTI_QUERY** | Aggregate across queries in context, then route to relevant bottleneck entities based on findings |

### Phase Loading Rules

1. **SUMMARY depth:** Load `<entity>/summary/SKILL.md` only. After presenting results, ask: "Want me to identify root causes or provide recommendations?"
2. **DIAGNOSIS depth:** Load `<entity>/summary/SKILL.md` → then `<entity>/detection/SKILL.md`. After presenting results, ask: "Want me to provide recommendations for the issues found?"
3. **RECOMMENDATION depth:** Load `<entity>/summary/SKILL.md` → `<entity>/detection/SKILL.md` → `<entity>/recommendation/SKILL.md`. After presenting results, wait for user follow-up.

### Stopping Points

- **[STOP]** After Phase 1 summary (if SUMMARY depth) — offer deeper analysis or recommendations
- **[STOP]** After Phase 2 detection results (if DIAGNOSIS depth) — offer recommendations
- **[STOP]** After Phase 3 recommendations — wait for user follow-up
- **[STOP]** After hybrid table detection — explain limitations
- **[STOP]** If no data found — explain possible reasons (see Empty Results Handling)
- **[STOP]** If user asks a vague question — ask for clarification before proceeding

---

## SQL Query Construction

### Step 0: Load the Semantic Model

**[MANDATORY]** Before constructing or running any SQL, read the file `semantic_model/default.yaml` (relative to this skill's directory). This file contains:
- **Table definitions** with column names, types, and descriptions for each ACCOUNT_USAGE view
- **Relationships** between tables (e.g., join keys)
- **Verified queries** — pre-written, tested SQL queries indexed by name (e.g., "Which warehouses have the most spilling?")
- **Custom instructions** for consistent SQL output (required columns, formatting rules, aggregation patterns)

**Usage rules:**
1. When a sub-skill references a verified query by name, look up that exact name in the `verified_queries` section and use its SQL verbatim.
2. When constructing new SQL not covered by a verified query, use the table definitions and custom instructions from the semantic model to ensure correct column names and consistent output formatting.
3. Never fabricate column names or table structures — always cross-reference the semantic model.
4. All verified queries and inline SQL use `SNOWFLAKE.ACCOUNT_USAGE` views. If a query fails due to insufficient privileges, inform the user that their role needs the `SNOWFLAKE.USAGE_VIEWER` database role (or `SNOWFLAKE.OBJECT_VIEWER` / `SNOWFLAKE.GOVERNANCE_VIEWER` depending on the view). The ACCOUNTADMIN can grant this: `GRANT DATABASE ROLE SNOWFLAKE.USAGE_VIEWER TO ROLE <user_role>;`

### Step 1: Query Adaptation

When the user's question specifies a subset of a verified query's scope, adapt the WHERE filter and ORDER BY to match:

| User specifies | Adapt |
|---|---|
| "local spilling" / "spill to local" | Filter: `bytes_spilled_to_local_storage > 0` — Order by: `bytes_spilled_to_local_storage DESC` |
| "remote spilling" / "spill to remote" | Filter: `bytes_spilled_to_remote_storage > 0` — Order by: `bytes_spilled_to_remote_storage DESC` |
| "spilling" (generic) | Filter: `bytes_spilled_to_local_storage > 0 OR bytes_spilled_to_remote_storage > 0` — Order by: total (local + remote) DESC |
| Specific warehouse name | Add: `AND warehouse_name = '<NAME>'` |
| Specific user | Add: `AND user_name = '<NAME>'` |
| Custom time range ("last 3 days") | Replace the DATEADD interval |

**[CRITICAL]** Always keep the verified query's column list and structure — only adapt filters and ordering. NEVER add, remove, or rename columns from a verified query.

### Step 3: Execute and Present

Run the SQL and present results following the Output Format section below.

---

## Critical Rules

### 1. Internal Warehouses
- `COMPUTE_SERVICE_WH_*` warehouses are Snowflake-internal compute service warehouses
- They appear in `QUERY_HISTORY` and `QUERY_ACCELERATION_ELIGIBLE` but are **NOT visible via `SHOW WAREHOUSES`** and are **NOT user-configurable**
- When they appear in top-N results (spilling, QAS, cache), note them as internal and focus recommendations on user-owned warehouses

### 2. Stored Procedure Auto-Routing

When a user supplies a `query_id` and the row in `QUERY_HISTORY` resolves to `query_type = 'CALL'`, **auto-route to the STORED_PROCEDURE entity** instead of QUERY. The procedure analysis covers the parent CALL plus its child queries (linked via `session_id` + the parent's `[start_time, end_time]` window). The call tree query is hard-capped at **500 rows** to bound runtime; truncation is surfaced in the summary. If the user explicitly wants only the parent metrics, they can re-invoke with the QUERY entity.

### 3. Query-Set Routing Precedence

When the user supplies query identifiers without an explicit entity choice:
- **Exactly 1 `query_id`** → QUERY (or STORED_PROCEDURE if `query_type = 'CALL'`).
- **2+ `query_id` values** → QUERY_SET.
- **A SQL `WHERE` fragment over `QUERY_HISTORY`** → QUERY_SET (regardless of resulting set size).
- **A list of `query_parameterized_hash` values** → QUERY_SET (regardless of how many query_ids resolve, subject to the 1,000 cap).

QUERY_SET hard-caps at 1,000 query_ids; truncation is surfaced in the scope card.

### 4. Default Limits and Summarization

| Question Type | Default LIMIT | Summarize |
|---|---|---|
| Query-level (slowest, spilling, QAS eligible) | 20 | Yes — "Found X total, showing top 20" |
| Warehouse-level aggregations | 20 | Yes — highlight key patterns |
| Column analysis | 20 | Yes — group by table |

**[WARNING]**
- DO NOT use LIMIT 100 or higher unless user explicitly requests
- Always provide a summary before listing results

### 5. Empty Results Handling

| Scenario | Response |
|---|---|
| No spilling | "No queries with spilling in the last 7 days. Warehouses are adequately sized." |
| No pruning data | "No pruning data found. Possible reasons: (1) No recent queries, (2) Data latency up to 4 hours, (3) Hybrid table." |
| No search opt candidates | "No search optimization candidates. Queries may already be well-optimized." |

**When entities (warehouse, table, view, query) are not found via SHOW commands:**

Possible causes to mention:
1. **Name misspelled** — Ask user to verify the exact name
2. **Insufficient permissions** — User's role may not have access to view this object
3. **Object doesn't exist** — It may have been dropped or never created
4. **Wrong database/schema context** — The object exists in a different database or schema

---

## Terminology

| Abbreviation | Full Term |
|---|---|
| WH | Warehouse |
| QAS | Query Acceleration Service |
| SOS | Search Optimization Service |

---

## Output Format

**[IMPORTANT] Always provide summary + top results, not raw data dumps:**

1. **Summary statement**: "Found X queries with [issue]. Here are the top 20:"
2. **Top results**: Show top 10-20 results — use indented list for query-level results, tables for warehouse/table aggregations
3. **Key insights**: Highlight patterns (common warehouses, time periods, etc.)
4. **Common causes** of the issue (see detection sub-skills for details)
5. **Format shortcut**: After presenting results, include: "You can say **'show as table'** or **'show as list'** to switch format."

---

## Important Guidelines

### Workload SLA: Speed vs Cost

Performance findings must be interpreted relative to the workload's Service Level Agreement — the customer's prioritization of speed vs cost:

| Dimension | Speed Priority | Cost Priority |
|---|---|---|
| **Queuing** | No queuing acceptable — upsize or add clusters immediately | Small amounts of queuing acceptable — saves credit cost |
| **Execution time** | Minimize at all costs — larger warehouses, QAS enabled | Longer execution times acceptable if credits are saved |
| **Multi-cluster scaling** | Standard policy — adds clusters as soon as queries queue | Economy policy — adds clusters only after sustained queuing |
| **Local disk cache / auto-suspend** | Higher auto-suspend to keep local disk cache warm — cache hit rate is critical for reporting warehouses that repeatedly scan the same tables | Lower auto-suspend to reduce idle credits — accept lower local disk cache hit rates |
| **Warehouse sizing** | Favor larger sizes to avoid spilling and reduce execution time | Favor smaller sizes — accept local spilling if execution time is tolerable |

When presenting recommendations that involve these tradeoffs, first explain both interpretations so the customer understands the concepts, then ask which priority applies to this warehouse/workload to tailor the guidance.

## Limitations

- ACCOUNT_USAGE views have latency (up to 45 min for QUERY_HISTORY, up to 4 hours for pruning views)
- Analyzes historical patterns only — cannot predict future performance
- Cannot estimate actual benefits of clustering/search optimization
- Hybrid tables have limited visibility in these views

