import os
import json
from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from prompts.system_prompt import build_system_prompt
from tools.snowflake_metadata import fetch_all_metadata
from tools.prd_parser import parse_prd
from tools.gap_classifier import classify_field
from tools.semantic_search import semantic_search
from tools.profile_column import profile_column
from tools.confidence_scorer import compute_confidence

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

_metadata_cache = None

def get_metadata():
    global _metadata_cache
    if not _metadata_cache:
        _metadata_cache = fetch_all_metadata()
    return _metadata_cache

@tool
def fetch_metadata_tool(dummy: str = "") -> str:
    """Fetches all column metadata from RETAIL_DB across Bronze, Silver, Gold layers."""
    meta = get_metadata()
    summary = {layer: {t: len(cols) for t, cols in tables.items()} for layer, tables in meta.items()}
    return json.dumps(summary)

@tool
def classify_gap_tool(field: str) -> str:
    """
    Classifies a field using exact/partial string match first.
    Falls back to semantic search if no match found.
    Returns L1/L2/L3/L4 with confidence score and data profile.
    Only profiles L1/L2 fields to save tokens.
    """
    meta = get_metadata()

    # Step 1 — exact/partial match
    exact = classify_field(field, meta)
    match_type = None
    sim_score = 1.0

    if exact["level"] != "L4":
        match_type = "exact" if field.upper() in [
            c.upper() for cols in meta[exact["found_in_layer"]].values() for c in cols
        ] else "partial"
        # Only profile L1/L2 — L3 Bronze raw tables don't need SQL probes
        if exact["level"] in ("L1", "L2"):
            profile = profile_column(exact["found_in_table"], field, exact["found_in_layer"])
        else:
            profile = {"null_pct": 0, "quality": "UNKNOWN", "total_rows": None, "distinct_values": None}
    else:
        # Step 2 — semantic search fallback
        sem_results = semantic_search(field, top_k=1, threshold=0.35)
        if sem_results:
            best = sem_results[0]
            match_type = "semantic"
            sim_score = best["similarity"]
            layer_map = {"GOLD": "L1", "SILVER": "L2", "BRONZE": "L3"}
            exact = {
                "field": field,
                "level": layer_map[best["layer"]],
                "found_in_layer": best["layer"],
                "found_in_table": best["table"],
                "matched_column": best["column"],
                "action": {
                    "L1": "Ready for reporting (semantic match)",
                    "L2": "Promote to Gold — build aggregation (semantic match)",
                    "L3": "Transform Bronze → Silver → Gold pipeline needed (semantic match)"
                }[layer_map[best["layer"]]]
            }
            # Only profile if semantic match lands on L1/L2
            if layer_map[best["layer"]] in ("L1", "L2"):
                profile = profile_column(best["table"], best["column"], best["layer"])
            else:
                profile = {"null_pct": 0, "quality": "UNKNOWN", "total_rows": None, "distinct_values": None}
        else:
            # Genuinely missing — L4
            match_type = "none"
            sim_score = 0.0
            profile = {"null_pct": 0, "quality": "UNKNOWN", "total_rows": None, "distinct_values": None}

    # Step 3 — confidence score
    confidence = compute_confidence(
        match_type=match_type or "none",
        layer=exact.get("found_in_layer"),
        similarity=sim_score,
        null_pct=profile.get("null_pct", 0),
        quality=profile.get("quality", "UNKNOWN")
    )

    # Trimmed return — only essential fields back to LLM
    return json.dumps({
        "field": exact["field"],
        "level": exact["level"],
        "found_in_layer": exact.get("found_in_layer"),
        "found_in_table": exact.get("found_in_table"),
        "match_type": match_type,
        "confidence": confidence,
        "null_pct": profile.get("null_pct"),
        "quality": profile.get("quality"),
        "action": exact.get("action")
    })

tools = [fetch_metadata_tool, classify_gap_tool]

REACT_TEMPLATE = """
{system_prompt}

You have access to these tools:
{tools}

Tool names: {tool_names}

Use this format strictly:
Thought: what you're thinking
Action: tool name
Action Input: input to tool
Observation: tool result
... (repeat as needed)
Thought: I now have all classifications
Final Answer: <JSON list of all field classifications>

Begin!

PRD Fields to classify: {input}
{agent_scratchpad}
"""

prompt = PromptTemplate.from_template(REACT_TEMPLATE)
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=30
)

def run_gap_analysis(prd: dict) -> dict:
    fields = parse_prd(prd)
    return agent_executor.invoke({
        "input": json.dumps(fields),
        "system_prompt": build_system_prompt()
    })