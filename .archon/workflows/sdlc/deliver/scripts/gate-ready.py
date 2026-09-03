"""Deterministic readiness join: certifies the review verdict before validate
and flip spend.

Bound inputs (no latch files -- values arrive through `with:` bindings):
- INPUTS_REVIEW_{READY,ACTION}: the validated initial verdict.
- INPUTS_CORRECTION_{READY,ACTION}: the validated final correction verdict,
  or false/null when the loop was skipped.

The correction loop completes for either `none` or `replan`; only `none` is
ready. A replan fails here with the draft PR and canonical report intact.
"""

import os
import sys

review_ready = os.environ.get("INPUTS_REVIEW_READY", "")
review_action = os.environ.get("INPUTS_REVIEW_ACTION", "null")
correction_ready = os.environ.get("INPUTS_CORRECTION_READY", "false")
correction_action = os.environ.get("INPUTS_CORRECTION_ACTION", "null")

if review_ready == "true" and review_action == "none":
    print('{"ready":"true"}')
    sys.exit(0)

if review_action == "correct" and correction_ready == "true" and correction_action == "none":
    print('{"ready":"true"}')
    sys.exit(0)

if review_action == "replan" or correction_action == "replan":
    print(
        "replan required: the review proved that the requested outcome cannot be "
        "completed inside the accepted work order. The pull request remains draft; "
        "see the canonical review report and discovery artifacts.",
        file=sys.stderr,
    )
    sys.exit(1)

print(
    "not ready: no validated ready verdict reached the delivery gate -- see the "
    "earliest failed or skipped node, the review report in the run artifacts, "
    "and the canonical PR comment.",
    file=sys.stderr,
)
sys.exit(1)
