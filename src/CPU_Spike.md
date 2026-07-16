🚨 **INCIDENT RUNBOOK: High CPU Utilization** 🚨

**Symptom:** Server CPU has exceeded the 80% threshold.
**Potential Causes:**
- Runaway background processes.
- Sudden spike in legitimate user traffic.
- Memory leak forcing high garbage collection CPU overhead.

**Immediate Triage Steps:**
1. SSH into the affected instance.
2. Run `htop` or `top` to identify the specific Process ID (PID) consuming resources.
3. If it is a known non-critical background task (e.g., `stress`), terminate it using `kill -9 <PID>`.
4. If it is application traffic, consider scaling up the Auto Scaling Group.

**Post-Incident:**
Wait for automated monitoring to confirm recovery, then review logs for root cause.