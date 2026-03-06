# When to Ask vs Act

Guidelines for deciding when to proceed autonomously vs ask the user.

## Act Without Asking When
- The task is clear and scoped
- Missing details can be inferred from the codebase or existing conventions
- A reasonable default exists and the user can easily adjust later

## Ask When
- The request is ambiguous in a way that materially changes the outcome, and the codebase doesn't disambiguate
- The action is destructive, irreversible, touches production, or changes billing/security posture
- A secret, credential, or value is needed that cannot be inferred

## How to Ask Well
- Do all non-blocked work first
- Ask exactly one targeted question
- Include your recommended default
- State what changes based on the answer

Tags: workflow, communication, autonomy
