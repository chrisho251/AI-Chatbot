# Escalation

The expert path of Level 3 (Appendix C.2). External search happens earlier, in W7. This service only runs when the answer is still L3 after that.

**Owner:** Lane A.
**Endpoints:**
- `routes.OPEN_TICKET`: open a ticket. The orchestrator is the caller.
- `routes.GET_TICKET`: read the ticket of a request. The gateway uses it for late answers.
- `POST /v1/tickets/{ticket_id}/answer`: the on-duty expert answers. This is the only public route.

**Runs in:** the api service. It calls `serve.HANDLERS` in process and mounts `serve.router` for the expert route. `serve.app` serves everything alone for tests.

**Writes:** `ops.escalation_tickets`. **Reads:** `ops.expert_rota`.

## Files

- `tickets.py`: the lifecycle.
- `rota.py`: who is on duty.
- `notifier.py`: SMTP (Mailpit) now, SES later.

## Test

```bash
uv run --package chatbot-escalation pytest services/escalation/tests
```
