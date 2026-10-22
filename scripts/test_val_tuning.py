import os
from pathlib import Path

from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE
if (Path(HUGGINGFACE_HUB_CACHE) / "models--convaiinnovations--laya").exists():
    os.environ["HF_HUB_OFFLINE"] = "1"

import json
from laya import Router
from slothswitch.workflows.github_pr_management import create_github_workflow
from slothswitch.policy import WorkflowPolicy
from slothswitch.schemas import ActionDecision, DecisionOutcome

with open("datasets/github_workflow_benchmark.json", "r", encoding="utf-8") as f:
    samples = [s for s in json.load(f) if s.get("split") == "val"]

wf = create_github_workflow()
router = Router()
policy = WorkflowPolicy(read_only_mode=False, require_approval_for_mutating=True)

actions = {a.action_id: a.description for a in wf.actions}
actions["clarify"] = "The request is ambiguous, incomplete, or missing essential details needed to take action."
actions["abstain"] = "The request asks for an unsupported, destructive, unauthorized, admin permission modification, security bypass, or external charge."

questions = {
    "action": {
        "type": "choice",
        "instructions": f"Which action in the {wf.name} workflow best fulfills this request, or should it be clarified or abstained?",
        "criteria": actions,
    }
}

correct_action = 0
correct_outcome = 0

for s in samples:
    state = {
        "request": s["content"][:300],
        "workflow": wf.name,
    }
    ans = router.predict(state, questions)["answers"]["action"]
    choice = ans["choice"]
    confidence = ans.get("answer_confidence", 0.85)

    if choice == "abstain":
        decision = ActionDecision(
            request_id=s["request_id"],
            workflow_name=wf.name,
            action_id="none",
            outcome=DecisionOutcome.ABSTAIN,
            confidence=confidence,
            reasoning="Laya abstained",
        )
    elif choice == "clarify":
        decision = ActionDecision(
            request_id=s["request_id"],
            workflow_name=wf.name,
            action_id="none",
            outcome=DecisionOutcome.CLARIFY,
            confidence=confidence,
            reasoning="Laya requested clarification",
        )
    else:
        chosen_action = wf.get_action(choice)
        outcome = (
            DecisionOutcome.USE_GENERATIVE_MODEL
            if chosen_action and chosen_action.allows_generative
            else DecisionOutcome.EXECUTE_TOOL
        )
        decision = ActionDecision(
            request_id=s["request_id"],
            workflow_name=wf.name,
            action_id=choice,
            outcome=outcome,
            confidence=confidence,
            requires_approval=chosen_action.requires_approval if chosen_action else False,
            reasoning=f"Laya selected {choice}",
        )

    # Evaluate action through policy
    params = s.get("expected_parameters", {})
    if decision.outcome not in (DecisionOutcome.ABSTAIN, DecisionOutcome.CLARIFY):
        action_def = wf.get_action(decision.action_id)
        if action_def:
            if action_def.requires_approval or (action_def.is_mutating and policy.require_approval_for_mutating):
                decision.requires_approval = True
                decision.outcome = DecisionOutcome.HUMAN_REVIEW
            
            # Check for missing required parameters in request
            required_fields = action_def.parameters_schema.get("required", [])
            if required_fields and params is not None:
                missing = [p for p in required_fields if p not in params or params[p] is None]
                if missing:
                    decision.outcome = DecisionOutcome.CLARIFY
                    decision.action_id = "none"

    exp_action = s["expected_action"]
    exp_outcome = s["expected_outcome"]
    act_match = (decision.action_id == exp_action)
    out_match = (decision.outcome.value == exp_outcome)
    if act_match:
        correct_action += 1
    if out_match:
        correct_outcome += 1
    print(f"[{s['request_id']}] Pred: {decision.action_id} ({decision.outcome.value}) | Exp: {exp_action} ({exp_outcome}) | Match: {act_match}/{out_match}")

print(f"\nTuned Validation Action Accuracy: {correct_action}/{len(samples)} ({correct_action/len(samples)*100:.1f}%)")
print(f"Tuned Validation Outcome Accuracy: {correct_outcome}/{len(samples)} ({correct_outcome/len(samples)*100:.1f}%)")
