# Primary free freshness plan, review required

## What this fixes and what it cannot promise

Use an independent free scheduler as the primary trigger for the existing collector, with GitHub cron as fallback. This avoids depending exclusively on GitHub's observed delayed schedule events. It does NOT guarantee that a new market price is published every five minutes. The scheduler can be late, the runner can queue, a source can fail or retain its price, and Pages publication can lag. Never describe an accepted dispatch as a fresh quote.

GitHub documents delayed and dropped scheduled runs:
https://docs.github.com/en/actions/how-tos/troubleshoot-workflows

cron-job.org explicitly does not guarantee punctuality:
https://cron-job.org/en/faq/

If a guaranteed deadline is mandatory, this free proposal does not meet it. Choose a service and operating agreement that cover the required interval, maximum delay, runtime and failure response before making that promise. This PR does not create or purchase such a service.

## Proposed free setup, not performed by this PR

1. Approve the external scheduler and account email first. Create a free cron-job.org account. Its service supports POST, custom headers/body, up to one execution per minute, failure notifications and execution history. No paid plan is necessary for a five-minute trigger.
2. Create a narrowly scoped GitHub credential for ONLY this repository, with the Actions write permission needed to dispatch this workflow. Set expiry and a rotation owner. It must never appear in repository code, public files, logs, screenshots or chat.
3. In the scheduler, create a job every five minutes with HTTP POST to the GitHub Actions workflow-dispatch endpoint for repository `ahmedmah1989/gold-board`, workflow `quotes.yml`, using ref `main`. Use `Accept: application/vnd.github+json`, a private Authorization Bearer header, API version header and body `{"ref":"main"}`. Exact GitHub endpoint contract:
https://docs.github.com/en/rest/actions/workflows#create-a-workflow-dispatch-event
4. Keep native GitHub cron as fallback. Both triggers use the same main-branch concurrency group; PR validation uses a separate group. Duplicate dispatches must not create overlapping collectors.
5. A dispatch should return204 quickly, within cron-job.org's30second timeout. Enable failure/recovery email notifications. A204 proves only accepted dispatch, not collection success.
6. Add an independent heartbeat check against the published `data/quotes.json`, `data/offers.json` and `data/collection-health.json`. Evaluate actual timestamps and future-time validity, not just HTTP200. Distinguish collection age from the source's own price age. Alarm if no new collection is published within the agreed grace period, for example ten minutes for this five-minute target. This PR produces the heartbeat receipt; it does not set up an independent checker. A static Pages URL cannot itself return an error when stale, so it is not a sufficient monitor without timestamp parsing.
7. After owner review/merge, test one dispatch and verify the resulting run, JSON timestamps and published website. Then observe multiple cycles, including missing-data and failed-dispatch cases. Keep a record of actual cadence before claiming improvement. Nothing in this PR activates the external job or merges code.

## Current mitigation in the PR

- Native cron moves away from minute zero, still only best effort.
- Current-price collection, audit and publication precede daily historical maintenance.
- `collection-health.json` records the previous gap, whether the target was missed, the current quote/offer snapshot ages and the absence of a scheduler guarantee.
- PR tests run with read-only repository permission and no production secrets.
- Frontend PR3 labels retail observations older than ten minutes as delayed while retaining their actual check time. It never relabels the check time as the market's own pricing timestamp.
- Gold Timo is an optional server-side free cross-check. It is not the scheduler, not a dealer-specific source and not a guarantee of accuracy.


## Provisioned account state, pending activation

The free cron-job.org account and free Healthchecks.io account are email-verified. Their login is saved in the user's shared preferred-password vault entry. The Healthchecks check has a5minute period and5minute grace, with email delivery to the account owner ON. It has not been seeded with a fake success ping.

The external dispatch job must remain disabled until its repository-scoped credential is installed and the owner-approved collector version is merged. GitHub token creation rejected two bounded attempts. The owner is supplying a fine-grained gold-board-only Actions read/write token through a secure vault request. No broader token was created.

`published_health.py` reads the actual public `quotes.json` and `offers.json` after publication. It requires the expected run timestamp, recent collection and offer-check times, recent primary iSagha source and fetch times, finite positive21k/24k bid/ask values and a nonempty offer snapshot. It never substitutes fetch time for source time. Only then does it send success to the secret `FRESHNESS_HEARTBEAT_URL`. Stale data, old cached generations, invalid prices or an outage send no success, so the independent monitor eventually emails after the5+5minute window. A check that has never received its first real ping is not active coverage. Missing secret is reported as not configured, not healthy.

This verifies primary local gold quote freshness, not every dealer's last price change. Published dealer observations are checks, not promises of executable prices. No free service supplies contractual end-to-end punctuality.
