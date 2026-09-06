# ADR-0004: Independent stack transactions with shared failure-domain gate

Status: Accepted design direction.

Decision: main and CV are separate update transactions. Failure of one does not mechanically abort the other; continuation is permitted only when Docker/shared infrastructure is healthy and the previous transaction left a known safe state.
