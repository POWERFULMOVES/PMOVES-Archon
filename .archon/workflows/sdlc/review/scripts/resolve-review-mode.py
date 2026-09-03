import json
import os


prior_report = os.environ.get("INPUTS_PRIOR_REPORT", "").strip()
if prior_report and not os.path.isfile(prior_report):
    raise SystemExit(f"Previous review report does not exist: {prior_report}")

print(json.dumps({"continuation": bool(prior_report)}))
