# Launch review

Reviewed 1 November 2026.

ClauseLoom has passed local application and container checks. It has not yet
been deployed to a public host. The next step is a controlled hosted trial with
fictional documents, followed by the access, security and accuracy work below.

## What has been verified

The backend suite has 98 passing tests, and the frontend tests and production
build pass. Both Docker layouts build successfully. A local single-container
trial completed a rental review, OCR uploads, PDF export and deletion.

The [verification record](verification.md) gives the test conditions and measured
results. These checks establish that the tested flows work; they do not measure
legal accuracy or capacity under concurrent public traffic.

## Outstanding container advisories

The latest recorded Trivy scan of the standard image reported **73 high/critical
package-advisory entries across 28 unique advisories**: 72 high and one critical.
The scanner reported no available fixed Debian package version for those entries.
These counts describe scanner findings, not demonstrated exploits.

Affected components include Tesseract, libtiff, libxml2, X11 libraries and system
utilities. Some findings require conditions such as malicious traineddata, an
X server or privileged local mount operations. Reachability has not been fully
assessed. Scan reports are retained locally under `artifacts/` and are excluded
from Git.

Before accepting untrusted uploads, review those findings and decide how to
isolate document parsing. Byte, page and pixel limits bound input size, but
native parsers and OCR still run in the app container. Cancelling a review may
leave an in-flight parser thread running until it finishes.

## Work remaining

| Area | Required before launch |
| --- | --- |
| Hosting | Choose a host and visibility settings that keep source private; confirm memory, CPU, cost and data-handling terms |
| Hosted acceptance | Run the live verification scripts against the real HTTPS origin; check streaming, both languages, uploads, PDF export, deletion and restart |
| Access and abuse | Decide who may upload and add appropriate edge limits or access controls; the app has no login |
| Proxy behavior | Verify origins, streaming timeouts and client limits; the current direct-peer limiter may put all proxied visitors in one bucket |
| Security | Assess outstanding image advisories and parser isolation for untrusted files |
| Accuracy | Review representative contracts with authorized reviewers; measure missed findings, misleading explanations and fallback frequency |
| Capacity | Measure latency and memory under the expected concurrency on the chosen host |
| Operations | Set up liveness/readiness monitoring, an operator contact and incident handling; exclude document content and bearer session URLs from logs |

## Trial deployment constraints

Keep one API worker and one replica. Session state is not shared or persisted,
so reviews disappear when the service restarts, sleeps or rebuilds. Do not enable
autoscaling without changing session storage and routing.

Keep Ollama private and set `ALLOWED_ORIGINS` to the actual app origin. Start with
fictional samples and confirm `/api/ready` before running acceptance checks.
The [deployment guide](deployment.md) contains the commands, resource profiles
and provider-specific settings.

Keep the informational disclaimer and rule-only labels visible. The synthetic
rule corpus and small raw-model comparison are useful development checks, but
provide too little evidence to claim reliable performance on real contracts.
