import sys, os
sys.path.insert(0, "/home/claude/agent_lab-main")
os.chdir("/home/claude/agent_lab-main")
import main_dual_loop as m

# --- command policy
assert m.is_mutating("rm -rf /tmp/x")
assert m.is_mutating("grep x f > out.txt")
assert m.is_mutating("find . -delete")
assert m.is_mutating("systemctl restart app")
assert m.is_mutating("touch /tmp/a")
assert not m.is_mutating("grep -i error sample.log | wc -l")
assert not m.is_mutating("tail -n 50 sample.log")
assert not m.is_mutating("ps aux && df -h")
print("policy OK")

def make_agent_fake(agent_responses, reflector_responses):
    a = iter(agent_responses); r = iter(reflector_responses)
    def fake(turns):
        text = "\n".join(t["content"] for t in turns)
        if "Principal SRE Reviewer" in text:
            return next(r)
        return next(a)
    return fake

MUT = '{"action": "run_command", "args": {"command": "touch /tmp/agent_lab_marker2"}}'
OK = '{"action": "run_command", "args": {"command": "grep -c ERROR sample.log"}}'
PASS = '{"is_satisfactory": true, "critique": "", "recommended_action": ""}'
FAIL = '{"is_satisfactory": false, "critique": "no remediation", "recommended_action": "add fix"}'

# --- A: mutating call rejected, agent recovers, verified
if os.path.exists("/tmp/agent_lab_marker2"): os.remove("/tmp/agent_lab_marker2")
seen_interrupts = []
def deny(req):
    seen_interrupts.append(req); return {"approved_ids": []}
m.call_velona = make_agent_fake(
    [MUT, "Final: 4 errors found, pool timeout. Remediation: check pool size."], [PASS])
out = m.run_agent_workflow("latency", approver=deny)
assert seen_interrupts, "mutating command must interrupt"
assert not os.path.exists("/tmp/agent_lab_marker2"), "rejected command must not run"
assert "Remediation" in out
print("A OK: interrupt raised, rejected, recovered")

# --- B: approved mutating call runs
seen_interrupts.clear()
m.call_velona = make_agent_fake([MUT, "Final: applied marker."], [PASS])
out = m.run_agent_workflow("latency", approver=lambda req: {"approved_ids": [c["id"] for c in req["commands"]]})
assert os.path.exists("/tmp/agent_lab_marker2"), "approved command should run"
os.remove("/tmp/agent_lab_marker2")
print("B OK: approved command executed")

# --- C: read-only call does NOT interrupt
seen_interrupts.clear()
m.call_velona = make_agent_fake([OK, "Final: 4 errors."], [PASS])
m.run_agent_workflow("latency", approver=deny)
assert not seen_interrupts, "read-only command must not interrupt"
print("C OK: read-only commands skip HITL")

# --- D: step budget stops an endless tool loop
old = m.MAX_STEPS; m.MAX_STEPS = 2
seen_interrupts.clear()
m.call_velona = make_agent_fake([OK, OK, OK, OK, OK], [PASS])
out = m.run_agent_workflow("latency", approver=deny)
m.MAX_STEPS = old
assert "Step budget exhausted" in out or "budget" in out.lower(), out
print("D OK: budget forced finalization")

# --- E: unparseable reflector fails closed, retries, then UNVERIFIED END
m.call_velona = make_agent_fake(["Final answer one.", "Final answer two.", "Final answer three."],
                                ["not json at all", "still garbage", "nope"])
out = m.run_agent_workflow("latency", max_retries=2, approver=deny)
print("E output:", out[:60])
print("E OK: fail-closed reflector terminates")

# --- F: reflector FAIL then PASS -> loops once and is verified
m.call_velona = make_agent_fake(["Draft one.", "Draft two with root cause."], [FAIL, PASS])
out = m.run_agent_workflow("latency", approver=deny)
assert out == "Draft two with root cause.", out
print("F OK: critique loop revises and verifies")

print("\nALL SINGLE-LOOP TESTS PASSED")
