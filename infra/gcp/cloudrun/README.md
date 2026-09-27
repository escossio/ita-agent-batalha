# Cloud Shell package — prepared, not deployed

Run only in Google Cloud Shell. No gcloud/GCP execution on AGT. This package does not complete implementation stage 16. The next gate is **read-only preflight output reviewed with the operator**. No permission for IAM/registry/deployment is implied by a successful preflight.

From a fresh Cloud Shell:

```sh
git clone https://github.com/escossio/ita-agent-batalha.git
cd ita-agent-batalha
export ITA_GCP_PROJECT='<confirmed-project>' ITA_GCP_REGION=us-central1
export ITA_BIGQUERY_DATASET=hackathon_dados ITA_BIGQUERY_TABLE=extrato_sintetico
bash infra/gcp/cloudrun/preflight.sh
```

Preflight runs read-only gcloud list/describe, Docker version and BigQuery query dry-run (no rows, no prediction). It checks operator access, not the permissions of future runtime identities. Project mismatch is blocked. Vertex regional model listing verifies API visibility, not access to a specific Gemini model; previous manual HTTP 200 is an operator-confirmed fact, not reproduced by this package. It reports BLOCKED, operation/resource/error and the required human action; APIs are never enabled automatically. Reports may include metadata/account names; keep raw output private and sanitize before sharing publicly.

`env.example` lists external configuration. Save the filled file outside Git. Do not source it with shell tracing enabled. Cloud Shell wrappers enforce `set -euo pipefail` and refuse to execute outside Cloud Shell. Tests replace subprocesses; no gcloud runs during tests on AGT/CI.

## Later, only after preflight review and explicit permission

1. Select a Docker Artifact Registry repository through ITA_ARTIFACT_REPOSITORY. `artifact_repository.sh --apply` detects an existing repo or explicitly creates the selected one. Preflight never creates it.
2. Prepare an IdentityRegistry secret privately in Secret Manager using the existing contract in [COMPETITION_RUNTIME.md](../../../docs/demo/COMPETITION_RUNTIME.md). Set its resource name and numeric version. The secret contains session hashes and synthetic customer bindings, not Google credentials. Provision end-user sessions securely outside this repository. No IdP/login implementation is claimed.
3. Review and run `identities.sh --apply`: seven distinct SAs, scoped custom roles, table-only BigQuery read and per-secret accessor. Existing custom roles with different permissions are blocked. No SA keys are generated. Review inherited IAM separately; additive scripts cannot remove broad roles inherited from folders/organization.
4. Set ITA_CERTIFIED_SHA to the full **PR head SHA certified by Actions and distributed-foundation**, then `git checkout --detach "$ITA_CERTIFIED_SHA"`. Use a clean tree. `build_push.sh --apply` independently checks public GitHub certification, builds seven linux/amd64 images using the public Git context pinned to this exact 40-character SHA (ignored/untracked local files never enter the context), adds OCI revision/source/created labels, pushes SHA tags and writes image digests/timestamps/Dockerfile to ITA_DEPLOYMENT_MANIFEST. No latest tag, source edits, Cloud Build, or secret build args. Pinning/labels make the source reproducible; bit-for-bit layer reproducibility is not asserted. A partial manifest is retained on failure and cannot deploy; use a fresh output path on retry.
5. Set a unique ITA_CLOUD_RUN_PREFIX matching `ita-preview-*`. `deploy.sh --apply --phase bootstrap` creates only new private services, with business requests disabled (`ITA_CLOUD_BOOTSTRAP=1`). Health/startup works without URLs; Data validates BigQuery config without querying it. It refuses to overwrite existing names. Interrupted bootstrap requires inspection/explicit cleanup or a new prefix.
6. `deploy.sh --apply --phase configure` obtains canonical status.url values, checks ownership/invoker bindings, adds only the reviewed caller→callee IAM grants, then configures URL audiences and activates business routes. IAM remains required. Services are updated separately; this is not an atomic production rollout. No user traffic is allowed before configure and IAM review finish. URLs remain stable across revisions, avoiding circular bootstrap.
7. All services including Web remain private. Only `publish_web.sh --apply` may grant allUsers invoker to Web. No internal anonymous grant and no disabled IAM check. Domain-restricted sharing may forbid even this Web grant: report BLOCKED and ask the Google team for an approved entry design, never bypass organization policy.
8. `smoke.sh` explicitly calls real Vertex/BigQuery through Web (may incur normal query/model cost), checks incomplete context/consent deny and anonymous denial on every internal endpoint. Requires provisioned session file (0600) and UTC window. It prints only sanitized outcome/correlation ID. The public Web step must have been explicitly permitted; this script does not grant access automatically.
9. `destroy_preview.sh --apply --confirm-preview "$ITA_CLOUD_RUN_PREFIX"` verifies ownership of all seven services before deletion. It only deletes those preview services; accounts, custom roles, secrets, IAM on other resources and images need separate review. Missing/foreign resources cause a block rather than guessing ownership.

The scripts accept no Owner/Editor grants, Cloud SQL/VPC connector, API enablement, JSON keys or deployment from source. Organization policies, custom-role creation, actAs, Artifact Registry write/pull, Secret Manager mounts and actual service invocation remain **AINDA NÃO TESTADO** until run in GCP. Runtime IAM and deployment-operator IAM are different; see [GCP_IAM_BOUNDARIES.md](../../../docs/security/GCP_IAM_BOUNDARIES.md).

`ingress=all` is the initial no-VPC design: HTTPS endpoints are routable but protected by IAM and application caller verification. Choosing internal ingress requires a separately approved connectivity design; the script does not provision a connector or network. Region, model, source and budget are external; no domain rebuild is necessary when they change.

Docker Git context pinning follows the [official build-context contract](https://docs.docker.com/build/concepts/context/#url-fragments). The builder needs read access to public GitHub; no private Git token is required.
