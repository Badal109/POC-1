import json
import sys
from agent.gap_agent import run_gap_analysis

if __name__ == "__main__":
    prd_path = sys.argv[1] if len(sys.argv) > 1 else "sample_prds/prd_l1_heavy.json"
    with open(prd_path) as f:
        prd = json.load(f)
    result = run_gap_analysis(prd)
    print("\n=== GAP REPORT ===")
    print(result["output"])