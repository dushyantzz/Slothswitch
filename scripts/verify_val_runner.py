import json

from slothswitch.adapters.decision.laya_adapter import LayaDecisionAdapter
from slothswitch.adapters.generative.gemma_local import LocalGemmaAdapter
from slothswitch.adapters.tools.github import GitHubToolAdapter
from slothswitch.evaluation.workflow_benchmark import WorkflowBenchmarkRunner
from slothswitch.workflows.github_pr_management import create_github_workflow

with open("datasets/github_workflow_benchmark.json", "r", encoding="utf-8") as f:
    samples = [s for s in json.load(f) if s.get("split") == "val"]

wf = create_github_workflow()
tool_adapter = GitHubToolAdapter()
dec_adapter = LayaDecisionAdapter(preload=True)
gen_adapter = LocalGemmaAdapter(model_id="TinyLlama/TinyLlama-1.1B-Chat-v1.0", lazy_load=False)

runner = WorkflowBenchmarkRunner(
    workflow=wf,
    decision_adapter=dec_adapter,
    generative_adapter=gen_adapter,
    tool_adapter=tool_adapter,
    execute_live_tools=False,
)

res = runner.run_baseline_c_slothswitch(samples)
print("Validation Baseline C Results:")
print("Action Accuracy:", res["action_accuracy"])
print("Outcome Accuracy:", res["outcome_accuracy"])
print("End-to-End Success Rate:", res["end_to_end_task_success_rate"])
print("Generative Calls:", res["gemma_calls"])
print("Avoided Generative Calls:", res["avoided_gemma_calls"], f"({res['avoided_gemma_pct']}%)")
