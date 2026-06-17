# Writer Analysis — critic-independence fixture

**WRITER-ONLY RATIONALE — NOT FOR CRITIC**

This file contains the ba-srs-writer's working notes. It must NOT be passed
to ba-critic. The test_workflow_contract.py F11 test verifies that the critic
payload excludes this file.

## Derivation notes

### NFR-001 derivation rationale

The source document (section 3.1) does not specify a concrete 500ms threshold.
The writer derived this value from general performance requirements practice.
The BA must confirm the specific threshold.

**This derivation reasoning is writer-only.** The critic re-derives independently
from the source, without seeing this rationale. If the critic independently
reaches the same conclusion, the requirement is validated. If not, the CoVe
loop surfaces the discrepancy.

## Rejected candidates

### Candidate: FR-003 (session timeout)

The source section 2.2 mentions "sessions expire" but does not state a specific
timeout duration. Rejected as stated because no verifiable span exists. Could
be included as derived with BA confirmation -- deferred.

## Open questions

1. Section 2.1: Is password complexity enforced at the API layer or the UI
   layer? The source says "password" but does not constrain format.
2. Section 3.1: What is "normal load"? No concurrent-user count given in the
   source. NFR-001 derivation is fragile without this definition.

## Planted marker (test fixture use only)

WRITER_RATIONALE_MARKER: this string is planted to verify critic payload exclusion.
If a test finds this marker in the critic input paths, the independence gate failed.
