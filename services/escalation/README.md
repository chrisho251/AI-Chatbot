# Escalation

The expert path of Level 3 (Appendix C.2). External search happens earlier, in W7. This service only runs when the answer is still L3 after that.

**Owner:** Lane A.
**Endpoints:**
- `POST /v1/tickets`: open a ticket (`routes.OPEN_TICKET`). The orchestrator is the caller.
- `GET /v1/tickets/{request_id}`: read a ticket. The gateway uses it for late answers.
- `POST /v1/tickets/{ticket_id}/answer`: the on-duty expert answers.

**Writes:** `ops.escalation_tickets`. **Reads:** `ops.expert_rota`.

## Files

- `tickets.py`: the lifecycle.
- `rota.py`: who is on duty.
- `notifier.py`: SMTP (Mailpit) now, SES later.

## Test

```bash
uv run --package chatbot-escalation pytest services/escalation/tests
```
