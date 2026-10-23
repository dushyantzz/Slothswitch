import json
from slothswitch.evaluation.workflow_benchmark import WorkflowBenchmarkRunner
from slothswitch.workflows.github_pr_management import create_github_workflow
from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter

with open('datasets/github_workflow_benchmark.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

test_samples = [d for d in data if d.get('split') == 'test']
wf = create_github_workflow()
laya = LayaDecisionAdapter()
runner = WorkflowBenchmarkRunner(workflow=wf, decision_adapter=laya)
res_c = runner.run_baseline_c_slothswitch(test_samples)

print("=== REMAINING MISMATCHES IN HELD-OUT TEST SET (BASELINE C) ===")
for r in res_c['records']:
    if not r['action_match'] or not r['outcome_match']:
        print(f"ID: {r['request_id']}")
        print(f"  Content: {r['content']}")
        print(f"  Expected: action={r['expected_action']}, outcome={r['expected_outcome']}")
        print(f"  Predicted: action={r['predicted_action']}, outcome={r['predicted_outcome']}")
        print(f"  Matches: action={r['action_match']}, outcome={r['outcome_match']}, task_success={r['task_success']}")
        print()
