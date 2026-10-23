"""Evaluate real Laya on validation set only."""
import json

from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter
from slothswitch.workflows.github_pr_management import create_github_workflow

with open("datasets/github_workflow_benchmark.json", "r", encoding="utf-8") as f:
    samples = [s for s in json.load(f) if s.get("split") == "val"]

print(f"Loaded {len(samples)} validation samples")
wf = create_github_workflow()
adapter = LayaDecisionAdapter(preload=True)

correct_action = 0
correct_outcome = 0

for s in samples:
    decision = adapter.predict_action(s["content"], wf)
    exp_act = s["expected_action"]
    exp_out = s["expected_outcome"]
    
    act_match = (decision.action_id == exp_act)
    out_match = (decision.outcome.value == exp_out)
    if act_match:
        correct_action += 1
    if out_match:
        correct_outcome += 1
    print(f"[{s['request_id']}] Pred: {decision.action_id} ({decision.outcome.value}) | Exp: {exp_act} ({exp_out}) | Match: {act_match}/{out_match}")

print(f"\nValidation Action Accuracy: {correct_action}/{len(samples)} ({correct_action/len(samples)*100:.1f}%)")
print(f"Validation Outcome Accuracy: {correct_outcome}/{len(samples)} ({correct_outcome/len(samples)*100:.1f}%)")
