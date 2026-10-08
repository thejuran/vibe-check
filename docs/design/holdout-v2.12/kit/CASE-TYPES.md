# Holdout case types

There are six case slots: three **catch** slots (C1, C2, C3) and three **quiet** slots
(Q1, Q2, Q3). A catch case is a change that introduces a real defect a careful reviewer
should report. A quiet case is a change that looks like it might be a problem but is not,
and a careful reviewer should stay quiet about it.

Every case is a base tree plus one diff. The definition of each slot below is the whole
test: a case belongs in a slot only if it meets that slot's definition and none of the
others better.

Proof convention (all slots): `proof/run` is an executable run with the current working
directory at the root of a tree. Exit 0 means the safe or expected behavior holds. It is
run once on the base tree and once on the changed tree (base tree with the diff applied).

## C1

**Definition:** newly reachable flaw in an unchanged helper.

**What qualifies.** The flawed helper function, method or module is not touched by the diff.
The diff adds a new call path (a new route, handler, command, job or caller) that passes
attacker-controlled or otherwise unvalidated input into that helper, so a flaw that was
unreachable or only reachable with trusted input becomes reachable. The defect is the new
exposure, and the key's location points at the new call path in the diff, not only at the
helper.

**What does not qualify.** A change that edits the helper itself (that is C2 or C3). A
helper weakness that the diff does not make any more reachable than it already was (that
is Q2).

**Proof shape.** The base tree passes `proof/run` because the flaw cannot be reached with
untrusted input; the changed tree fails it because the new path reaches the flaw. The proof
drives the new entry point, not the helper directly.

**Key format.** `{"slot": "C1", "class": "catch", "defect": str, "location": {"file": str,
"line_start": int, "line_end": int}, "causal_failure": str, "causal_failure_category": <one
of the categories below>}`

## C2

**Definition:** protection removed with no equivalent replacement.

**What qualifies.** The diff deletes or disables a check, guard, escape, limit, lock or
permission test, and nothing elsewhere in the changed tree performs an equivalent job on
the same path. The behavior the protection used to prevent is now possible.

**What does not qualify.** A protection that was moved to another layer and still covers
the same path (that is Q1). A removal of dead code that no input could ever reach.

**Proof shape.** The proof must call the code path that lost its protection and show the
behavioral loss: base passes because the protection refuses the bad input, changed fails
because the bad input now gets through. A proof that only greps for the removed text, diffs
files or tests that a file exists does not count.

**Key format.** Same as C1, with `"slot": "C2"`.

## C3

**Definition:** an unrelated ordinary bug.

**What qualifies.** The diff introduces an ordinary correctness bug (wrong condition,
off-by-one, wrong variable, broken error path, wrong default) that is not about removing a
protection and not about exposing an existing helper. It does not need to be a security
issue. "Unrelated" means it is not one of the C1 or C2 patterns.

**What does not qualify.** A defect that fits C1 or C2. A style issue, a missing test or a
behavior change the author clearly intended.

**Proof shape.** Base passes `proof/run`; changed fails it on the specific wrong behavior
the bug causes.

**Key format.** Same as C1, with `"slot": "C3"`.

## Q1

**Definition:** equivalent protection moved elsewhere.

**What qualifies.** The diff removes a check, guard, escape or limit from one place and adds
an equivalent one somewhere else (a middleware, a decorator, a caller, a schema, a shared
validator) that still covers every path the old one covered. Read in isolation, the removal
looks like C2; read with the whole tree, it is not.

**What does not qualify.** A replacement that covers fewer paths, is weaker, or runs after
the dangerous operation (that is C2).

**Proof shape.** Base and changed both pass `proof/run`. The proof sends the bad input
through the path that lost its local check and shows it is still refused. `exposure_check`
names where the protection now lives and why every old path still reaches it.

**Key format.** `{"slot": "Q1", "class": "quiet", "expected_quiet_rationale": str,
"supported_behavior": str, "exposure_check": str}`

## Q2

**Definition:** unchanged helper weakness with no new exposure.

**What qualifies.** The tree contains a helper with a real weakness, the diff touches code
near it or calls it, but every input the diff routes into it is trusted, already validated,
or no more exposed than before. The weakness pre-dates the change and the change does not
make it newly reachable.

**What does not qualify.** A diff that adds a path from untrusted input into the weak
helper (that is C1). A weakness the diff itself introduces.

**Proof shape.** Base and changed both pass `proof/run`. The proof exercises the diff's new
or changed path and shows the helper only ever receives the safe input. `exposure_check`
names the supported behavior and why the change opens no new exposure.

**Key format.** Same quiet format, with `"slot": "Q2"`.

## Q3

**Definition:** valid tightening of input validation.

**What qualifies.** The diff makes input validation stricter (a narrower pattern, a lower
limit, a new required field, a new type check) in a way that is correct: legitimate inputs
are still accepted and only invalid ones are newly refused.

**What does not qualify.** A tightening that breaks a supported legitimate input (that is a
C3 bug). A change that loosens validation.

**Proof shape.** Base and changed both pass `proof/run`. The proof sends the supported
legitimate inputs through the changed validation and shows they are still accepted.
`supported_behavior` names those inputs; `exposure_check` says why the stricter rule refuses
nothing that should pass.

**Key format.** Same quiet format, with `"slot": "Q3"`.

## Class pairs

- **C1 / Q2** distinguish new exposure from pre-existing weakness: both involve an
  unchanged weak helper; only C1 makes it newly reachable.
- **C2 / Q1** distinguish removed protection from moved protection: both delete a check;
  only Q1 puts an equivalent one back on every path.
- **C3 / Q3** are the ordinary-bug versus valid-tightening pair: both change ordinary logic;
  only C3 breaks a supported behavior.

## Causal-failure categories

A catch key MUST set `causal_failure_category` to exactly one of these strings. The
independent cross-check picks one of the same strings for its own verdict, and the two must
match.

- `missing-input-validation`: input reaches an operation without the check it needs.
- `missing-authz-check`: an action runs without verifying the caller is allowed to do it.
- `injection`: input is interpreted as code, query, command or markup.
- `path-traversal`: input selects a file or directory outside the intended root.
- `unsafe-deserialization`: untrusted bytes are decoded into live objects or executable state.
- `resource-exhaustion`: input can make memory, CPU, disk, connections or time grow without bound.
- `race-condition`: correctness depends on the timing or interleaving of concurrent work.
- `error-handling`: a failure is ignored, swallowed, mis-reported or leaves broken state.
- `crypto-misuse`: a cryptographic primitive, key, nonce, comparison or randomness source is used wrongly.
- `info-disclosure`: data or internal detail reaches someone who should not see it.
- `logic-error`: the code computes or decides the wrong thing (wrong condition, bound, variable, default).
- `other`: none of the above fits.

`other` is allowed in a key, with the failure explained in `causal_failure`, but it never
counts as agreement: if either the key or the cross-check says `other`, the independent
check cannot agree mechanically, so the owner will have to resolve the case with evidence
or replace it. Use it only when nothing else fits.
