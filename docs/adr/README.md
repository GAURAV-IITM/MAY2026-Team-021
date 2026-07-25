# Architecture Decision Records

Use an ADR when the team makes a decision that affects multiple modules or is
expensive to reverse, such as authentication strategy, API response shape,
tenant enforcement, allocation locking, or background-task execution.

Copy `000-template.md`, assign the next number, and use a short name:

```text
001-api-response-envelope.md
002-authentication-and-refresh-sessions.md
003-seat-allocation-conflict-locking.md
```

ADRs are committed with the code or contract that implements the decision.
