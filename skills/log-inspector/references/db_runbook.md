# Database Runbook: Connection Timeouts

## Symptoms
- ConnectionTimeout errors occurring in clusters.
- Spike in service latency and thread pool contention.

## Mitigation Steps
1. **Immediate Mitigation**:
   - Check active connection pool utilization against `max_connections`.
   - Scale connection pooler (e.g. PgBouncer) or purge orphaned connections.
2. **Investigation**:
   - Identify slow queries holding transactions open (`SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';`).
3. **Long-term Fix**:
   - Optimize slow queries, add missing indexes, and adjust service retry backoff.
