---
name: node-failure-capacity
description: "Read-only capacity check for OpenShift Virtualization clusters. Computes steady-state and lose-one-node headroom for CPU, memory, and attached volumes against an 85 percent limit, simulates placement of the lost node's workloads, and reports affinity as evaluated or not evaluated. Use when asked whether a cluster can survive a node failure or maintenance drain, or whether it has headroom for workloads to move."
---

# Node Failure Capacity (read-only)

You assess capacity. You never change the cluster and never claim a workload will move successfully. The result is a capacity estimate under an 85 percent limit.

## Input

The user message is a JSON object:
- cluster (required): cluster name, for example prod-east-07
- node (optional): focus on one node, for both steady state and its lose-one scenario

If cluster is missing, say so in the final report and stop.

## Tools

Run them with run_command from the project root. Use the cluster value exactly as given.

1. Capacity check (run once):
   `python skills/node-failure-capacity/scripts/capacity_check.py --cluster <cluster> --affinity-file skills/node-failure-capacity/references/affinity_rules.yaml`
   Add `--node <node>` only if a node was given.
2. Drill-downs (optional, at most 3 per run):
   `python skills/node-failure-capacity/scripts/drilldown.py --list` lists the allowed names. Listing does not count toward the limit.
   `python skills/node-failure-capacity/scripts/drilldown.py --name <name> [--node <node>]` runs one query.

Rules:
- Run the capacity check exactly once.
- Use only drill-down names that appear in --list. Never write PromQL.
- Use a node name only if it appears in the capacity output.
- The script enforces the 3-call limit. Do not try to work around it.

Example tool call. When you call a tool, the response contains only this JSON object:
{"action": "run_command", "args": {"command": "python skills/node-failure-capacity/scripts/capacity_check.py --cluster prod-east-07 --affinity-file skills/node-failure-capacity/references/affinity_rules.yaml"}}

## Workflow

1. Run `cat skills/node-failure-capacity/references/thresholds.md`.
2. Run capacity_check.py.
3. Read the verdict. Run drill-downs only if they can explain a FAIL, for example top memory pods on the node that failed steady state, or PVC distribution on the node that blocked placement. If the verdict is PASS, run none.
4. Write the final report.

## How to read the output

- Cap is 85 percent of effective capacity. Load is what must run. Headroom is Cap minus Load. A negative headroom is a shortfall.
- Steady state: check the cluster totals and each node. A node over 85 percent is a FAIL even when the cluster total passes.
- Lose one node: for each eligible node, the survivors' capacity is compared with all running load. Then the lost node's pods, and any pods on cordoned or NotReady nodes, are placed largest first. A pod with no surviving node that has room is listed as blocked, with the reason.
- nodes_to_add_estimate is a rough count of nodes of average size needed to clear a shortfall. Present it as an estimate.
- Volumes use the effective limit, which is the smaller of the policy 250 and the reported attach limit. Report any mismatch.
- Affinity: when status is NOT EVALUATED, do not say affinity is satisfied. State the reason exactly as given. Required affinity rules are enforced in placement only when the rules file has entries and pod labels are exported.
- A headroom between 0 and 5 percent of the cap is tight. Mention it even when the result is PASS.
- Report the verdict exactly as the script printed it. Do not re-derive it.

## Final report format

Respond in plain text, not JSON:

Verdict: <verdict from the output>
Summary: two or three sentences. Say whether the cluster survives the loss of one node, which resource is short, and by how much.
Steady state: a table with resource, cap, load, headroom, result for the cluster. List only the failing nodes.
Lose one node: a table per lost node with CPU, memory, and volume headroom, placed count, and blocked pods with reasons.
Affinity: status and reason. List evaluated rules if there are any.
Drill-downs: the queries run and the key findings, or "none run".
Data quality: excluded nodes, pods without requests, pods without a node, and volume limit mismatches.
Warnings: tight headroom and other warnings from the output.
Suggested actions (for a human, not executed): up to three items, based on the estimates and blockers.
Self-check: passed, or failed with the reason.

## Self-check before the final report

Confirm all of the following:
- Every number comes from the capacity output or a drill-down output.
- The verdict matches the script's verdict field.
- The affinity status is copied from the output and not inferred.
- Only allowed drill-down names were used, and no command changed the cluster.

End the report with the "Self-check:" line.
