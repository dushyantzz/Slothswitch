import json
import os
from pathlib import Path

from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE

if (Path(HUGGINGFACE_HUB_CACHE) / "models--convaiinnovations--laya").exists():
    os.environ["HF_HUB_OFFLINE"] = "1"

from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter
from slothswitch.policy import WorkflowPolicy
from slothswitch.workflows.github_pr_management import create_github_workflow

with open("datasets/github_workflow_benchmark.json", "r", encoding="utf-8") as f:
    samples = [s for s in json.load(f) if s.get("split") == "val"]

wf = create_github_workflow()
adapter = LayaDecisionAdapter(preload=True)
policy = WorkflowPolicy(read_only_mode=False, require_approval_for_mutating=True, min_confidence=0.50)

correct_action = 0
correct_outcome = 0

for s in samples:
    req_content = s["content"]
    decision = adapter.predict_action(req_content, wf, request_id=s["request_id"])
    
    # Authorize through policy
    authorized = policy.evaluate_action(
        decision,
        wf,
        caller_permissions=["github:read", "github:write"],
        params=s.get("expected_parameters", {}),
        request_content=req_content,
    )

    exp_action = s["expected_action"]
    exp_outcome = s["expected_outcome"]
    act_match = (authorized.action_id == exp_action)
    out_match = (authorized.outcome.value == exp_outcome)
    if act_match:
        correct_action += 1
    if out_match:
        correct_outcome += 1
    print(f"[{s['request_id']}] Pred: {authorized.action_id} ({authorized.outcome.value}) | Exp: {exp_action} ({exp_outcome}) | Match: {act_match}/{out_match}")

print(f"\nReal Laya + Policy Validation Action Accuracy: {correct_action}/{len(samples)} ({correct_action/len(samples)*100:.1f}%)")
print(f"Real Laya + Policy Validation Outcome Accuracy: {correct_outcome}/{len(samples)} ({correct_outcome/len(samples)*100:.1f}%)")
