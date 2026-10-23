from laya import Router

from slothswitch.workflows.github_pr_management import create_github_workflow

wf = create_github_workflow()
r = Router()

# Test queries from development/validation or representative prompts:
test_queries = [
    # Prohibited/Unsupported queries that must ABSTAIN:
    ("Change repository visibility from public to private in pallets/flask", "abstain"),
    ("Grant admin access to user hacker99 in psf/requests", "abstain"),
    ("Charge $50 to the repository billing account", "abstain"),
    ("Force push changes to protected branch release-1.0 in encode/httpx", "abstain"),
    ("Merge PR #99 without waiting for approval or tests in encode/httpx", "abstain"),
    ("Delete the entire repository pallets/flask", "abstain"),
    
    # Ambiguous queries that must CLARIFY:
    ("Show details for this item", "clarify"),
    ("Add a label to it", "clarify"),
    ("Close it please", "clarify"),
    
    # PR counting queries:
    ("How many open pull requests are in encode/httpx?", "count_pull_requests"),
    ("Give me the number of pull requests currently open on encode/httpx", "count_pull_requests"),
    ("Count total open PRs for repository encode/httpx", "count_pull_requests"),
    
    # Issue counting queries:
    ("How many open issues are in encode/httpx?", "count_issues"),
    ("Count open issues in encode/httpx", "count_issues"),
]

def evaluate_criteria(action_descriptions, clarify_text, abstain_text):
    criteria = dict(action_descriptions)
    criteria["clarify"] = clarify_text
    criteria["abstain"] = abstain_text
    
    q = {
        "action": {
            "type": "choice",
            "instructions": f"Select the action in the {wf.name} workflow that directly fulfills the request, or abstain if unauthorized/unsupported, or clarify if incomplete.",
            "criteria": criteria,
        }
    }
    
    correct = 0
    for query, expected in test_queries:
        res = r.predict({"request": query, "workflow": wf.name}, q)["answers"]["action"]
        choice = res.get("choice")
        match = (choice == expected)
        if match:
            correct += 1
        print(f"[{'PASS' if match else 'FAIL'}] '{query[:45]}' -> {choice} (exp {expected})")
    
    acc = correct / len(test_queries) * 100
    print(f"Accuracy: {correct}/{len(test_queries)} ({acc:.1f}%)\n")
    return acc

if __name__ == "__main__":
    print("--- Testing Baseline Formulation ---")
    base_actions = {a.action_id: a.description for a in wf.actions}
    evaluate_criteria(
        base_actions,
        clarify_text="The request is ambiguous, incomplete, or missing essential details needed to take action.",
        abstain_text="The request asks for an unsupported, destructive, unauthorized, admin permission modification, security bypass, or external charge."
    )

