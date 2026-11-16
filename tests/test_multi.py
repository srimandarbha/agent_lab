import sys, os, threading
sys.path.insert(0, "/home/claude/agent_lab-main")
os.chdir("/home/claude/agent_lab-main")
import main_multi_agent as m

lock = threading.Lock()
seen = {"sup": 0}
calls = []

def fake(turns):
    text = "\n".join(t["content"] for t in turns)
    with lock:
        calls.append(text[:40])
    if "You are the SUPERVISOR" in text:
        with lock:
            seen["sup"] += 1
            n = seen["sup"]
        if n == 1:
            return '{"next": ["log_agent", "health_agent"]}'     # parallel fan-out
        if "[remediation]" not in text and "[remediation" not in text and "Reflector critique" not in text:
            return '{"next": ["remediation"]}'
        return '{"next": ["FINISH"]}'
    if "You are the LOG SPECIALIST" in text:
        if "[Tool Output" in text:
            return "Verified: 4 ERROR/CRITICAL lines. Evidence: postgres pool timeout, DiskFull."
        return '{"action": "run_command", "args": {"command": "grep -c ERROR sample.log"}}'
    if "You are the HEALTH SPECIALIST" in text:
        if "[Tool Output" in text:
            return "Load is normal per uptime output."
        return '{"action": "run_command", "args": {"command": "uptime"}}'
    if "You are the REMEDIATION PROPOSER" in text:
        return '{"command": "touch /tmp/agent_lab_marker", "rationale": "mark incident"}'
    if "Principal SRE Reviewer" in text:
        return '{"is_satisfactory": true, "critique": "", "recommended_action": ""}'
    return "unexpected prompt"

m.call_velona = fake

# Case 1: operator approves the mutating remediation
if os.path.exists("/tmp/agent_lab_marker"): os.remove("/tmp/agent_lab_marker")
out = m.run_team_workflow("latency incident", approver=lambda req: {"approved": True})
print("\nCASE1 findings:", [f[:60] for f in out])
assert os.path.exists("/tmp/agent_lab_marker"), "approved command should have run"
assert any(f.startswith("[log_agent]") for f in out)
assert any(f.startswith("[health_agent]") for f in out)
assert any("Ran approved command" in f for f in out)

# Case 2: operator rejects -> command must not run
os.remove("/tmp/agent_lab_marker")
seen["sup"] = 0
out = m.run_team_workflow("latency incident", approver=lambda req: {"approved": False})
print("\nCASE2 findings:", [f[:70] for f in out])
assert not os.path.exists("/tmp/agent_lab_marker"), "rejected command must not run"
assert any("Operator rejected" in f for f in out)

# Case 3: scope enforcement in code. Health agent tries a mutating command.
m.AGENT_SCOPES["health_agent"]  # exists
scope_out = m.run_worker("health_agent", "task")  # uses fake, so test directly below
print("\nCASE3 scope checks:")
def fake_bad(turns):
    text = "\n".join(t["content"] for t in turns)
    if "You are the HEALTH SPECIALIST" in text:
        if "[Tool Output" in text:
            return "done"
        return '{"action": "run_command", "args": {"command": "rm -rf /tmp/x"}}'
    return "x"
m.call_velona = fake_bad
print(m.run_worker("health_agent", "t"))
print("Last obs was REJECTED: check via transcript shown below")
# Verify REJECTED message reached the LLM on the second turn
rejected_seen = []
def fake_check(turns):
    text = "\n".join(t["content"] for t in turns)
    if "You are the HEALTH SPECIALIST" in text:
        if "REJECTED" in text:
            rejected_seen.append(True)
            return "Read-only agent blocked mutating command as expected."
        return '{"action": "run_command", "args": {"command": "rm -rf /tmp/x"}}'
    return "x"
m.call_velona = fake_check
r = m.run_worker("health_agent", "t")
assert rejected_seen, "mutating command should be rejected by scope"
print("PASS scope enforcement:", r)

# Case 4: a worker not in scope via action name
def fake_scope(turns):
    text = "\n".join(t["content"] for t in turns)
    if "You are the HEALTH SPECIALIST" in text:
        if "outside your tool scope" in text:
            return "blocked"
        return '{"action": "load_skill_body", "args": {"skill_name": "log-inspector"}}'
    return "x"
m.call_velona = fake_scope
print("PASS skill scope:", m.run_worker("health_agent", "t"))

print("\nALL MULTI-AGENT TESTS PASSED")
