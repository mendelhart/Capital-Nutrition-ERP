# CAPITAL NUTRITION ERP — CLAUDE CHAT PROTOCOL

## Purpose

Every Claude implementation chat must operate as a focused engineering session.

## One task = one chat

Never combine unrelated implementation tasks.

A domain may have many chats.

## Required context at chat start

Provide:

1. `00_MASTER_BUILD.md`
2. `01_ARCHITECTURE.md`
3. `STATUS.md`
4. The relevant domain specification
5. Relevant integration contracts
6. Relevant ADRs
7. The task specification
8. Existing files the task will modify

## Opening instruction

Use:

> You are working on exactly one implementation task for the Capital Nutrition ERP.
>
> Read the supplied master build, architecture, domain specification, integration contracts, ADRs, current status, and task specification before coding.
>
> First:
> 1. summarize your understanding,
> 2. identify ambiguities,
> 3. identify conflicts with existing architecture,
> 4. propose the implementation plan,
> 5. list tests you will add.
>
> Do not write code until I approve the plan.

## During implementation

Claude must:
- stay within task scope
- explain non-obvious code
- avoid speculative abstractions
- reuse existing patterns
- write tests
- test failure paths
- preserve existing contracts
- flag architectural changes

## If the specification is wrong

Do not silently implement it.

Stop and explain:
- what is wrong
- why
- impact
- proposed correction

After approval, update the relevant specification and ADR if required.

## Definition of done

A task is complete only when:
- code exists
- tests pass against PostgreSQL
- acceptance criteria pass
- documentation is updated
- ADRs are updated where needed
- changes are committed
- STATUS.md is updated
- the owner understands the important code

## Context limit

If the chat becomes too large:

Do not rush.

Create a handoff containing:
- completed work
- files changed
- current implementation state
- remaining work
- decisions
- unresolved issues
- exact next step

Commit the work and begin a new chat.
