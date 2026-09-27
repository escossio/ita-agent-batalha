import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from infra.gcp.cloudrun import operator as op
from scripts.cloudrun_check import plan_violations, check
from scripts.architecture_check import violations


class CloudToolingTests(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(project="example-project", region="us-central1")
        self.patch = patch.dict(os.environ, dict(ITA_GCP_PROJECT="example-project", ITA_GCP_REGION="us-central1",
            ITA_CLOUD_RUN_PREFIX="ita-preview-ci", ITA_BIGQUERY_DATASET="demo", ITA_BIGQUERY_TABLE="ledger",
            ITA_BIGQUERY_CURRENCY="BRL", ITA_BIGQUERY_MONEY_UNIT="major", ITA_BIGQUERY_MAX_BYTES_BILLED="1000000",
            ITA_VERTEX_MODEL="gemini-configured", ITA_IDENTITY_SECRET="identity-registry", ITA_IDENTITY_SECRET_VERSION="1"), clear=True)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_guard_rejects_privilege_and_service_drift(self):
        self.assertEqual(check(), [])
        for change in ("public", "edge", "shared", "postgres"):
            plan = copy.deepcopy(op.PLAN)
            if change == "public":
                plan["data"]["public_candidate"] = True
            elif change == "edge":
                plan["agent"]["callees"].append("data")
            elif change == "shared":
                plan["data"]["service_account"] = plan["agent"]["service_account"]
            else:
                plan["postgres"] = dict(service_account="ita-db-sa", callees=[])
            self.assertTrue(plan_violations(plan))
        for component in ("data", "finance", "policy", "api"):
            for source in ("from google.cloud import aiplatform", "import vertexai", "url='https://us-central1-aiplatform.googleapis.com/v1'"):
                self.assertTrue(violations(Path(f"services/{component}/main.py"), source))

    def test_no_cloud_shell_no_gcloud(self):
        with patch("sys.argv", ["operator.py", "preflight"]), patch.object(op, "run") as run:
            with self.assertRaises(op.Blocked):
                op.main()
            run.assert_not_called()

    def test_mutations_need_explicit_apply(self):
        with patch.dict(os.environ, DEVSHELL_PROJECT_ID="example-project"), patch("shutil.which", return_value="/fake"), patch.object(op, "run") as run:
            for action in ("identities", "build_push", "deploy", "publish_web", "destroy_preview", "artifact_repository"):
                with patch("sys.argv", ["operator.py", action]), self.assertRaises(op.Blocked):
                    op.main()
            run.assert_not_called()

    def test_preflight_commands_are_read_only(self):
        calls = []
        def fake(args):
            calls.append(args)
            if args[1:4] == ["config", "get-value", "project"]:
                return "example-project"
            if "services" in args and "--enabled" in args:
                return "\n".join(op.APIS)
            return "[]"
        with patch.object(op, "run", side_effect=fake), patch("builtins.print"):
            op.preflight(self.cfg)
        self.assertTrue(any("--dry_run" in c for c in calls))
        for cmd in calls:
            self.assertFalse(set(cmd) & {"create", "update", "deploy", "enable", "add-iam-policy-binding", "push", "delete"})

    def test_environment_has_no_credentials_or_cross_privileges(self):
        urls = {s: "https://"+s+"-example.run.app" for s in op.PLAN}
        for service in op.PLAN:
            env = op.environment(self.cfg, service, urls, False)
            self.assertEqual(env["ITA_PLATFORM"], "cloudrun")
            self.assertNotIn("PORT", env)  # injected by Cloud Run
            self.assertFalse(any(k.startswith("DB_") or "PASSWORD" in k or "KEY_FILE" in k or "CREDENTIALS" in k for k in env))
            if service != "data":
                self.assertFalse(any(k.startswith("ITA_BIGQUERY") for k in env))
            if service != "agent":
                self.assertNotIn("ITA_VERTEX_MODEL", env)
        self.assertEqual(op.environment(self.cfg, "data", urls, False)["ITA_ALLOWED_CALLERS"], op.account(self.cfg, "tool-broker"))

    def test_bootstrap_closed_and_only_readonly_secret_mounts(self):
        commands = []
        def fake_gc(cfg, *args):
            commands.append(args)
            return "[]" if "list" in args else "{}"
        digests = {s: f"us-central1-docker.pkg.dev/example-project/repo/ita-{s}@sha256:"+"a"*64 for s in op.PLAN}
        with patch.object(op, "images", return_value=("b"*40, digests)), patch.object(op, "gc", side_effect=fake_gc):
            op.deploy(self.cfg, "bootstrap")
        deployments = [c for c in commands if c[:2] == ("run", "deploy")]
        self.assertEqual(len(deployments), 7)
        for args in deployments:
            self.assertIn("--no-allow-unauthenticated", args)
            self.assertIn("--invoker-iam-check", args)
            self.assertTrue(any(a.startswith("--image=") and "@sha256:" in a for a in args))
            self.assertFalse(any("vpc" in a or "cloudsql" in a or "--source" in a for a in args))

    def test_bootstrap_never_overwrites_existing(self):
        with patch.object(op, "images", return_value=("a"*40, {})), patch.object(op, "gc", return_value=json.dumps([{"metadata":{"name":"ita-preview-ci-web"}}])) as gc:
            with self.assertRaises(op.Blocked):
                op.deploy(self.cfg, "bootstrap")
            self.assertEqual(gc.call_count, 1)

    def test_repository_creation_never_implicit(self):
        with patch.dict(os.environ, ITA_ARTIFACT_REPOSITORY="repo"), patch.object(op, "gc", return_value="[]") as gc:
            with self.assertRaises(op.Blocked):
                op.repository(self.cfg)
            self.assertEqual(gc.call_count, 1)

    def test_destroy_rejects_unowned_resource_before_deletion(self):
        with patch.object(op, "describe", return_value={"metadata":{"name":"service","labels":{}}}), patch.object(op, "gc") as gc:
            with self.assertRaises(op.Blocked):
                op.destroy(self.cfg, "ita-preview-ci")
            gc.assert_not_called()

    def test_build_uses_only_certified_git_context_and_records_digests(self):
        sha, repo, calls = "a"*40, "registry/repo", []
        def fake_run(args):
            calls.append(args)
            if args[:3] == ["git", "show", "-s"]:
                return "2026-01-01T00:00:00Z"
            if args[:3] == ["docker", "image", "inspect"]:
                return json.dumps([{"RepoDigests": [args[3].split(":")[0]+"@sha256:"+"b"*64]}])
            return ""
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, ITA_DEPLOYMENT_MANIFEST=str(Path(temp)/"images.json")), \
                patch.object(op, "certified_sha", return_value=sha), patch.object(op, "repository", return_value=repo), \
                patch.object(op, "gc"), patch.object(op, "run", side_effect=fake_run), patch("builtins.print"):
            op.build_push(self.cfg)
            manifest = json.loads(op.artifact_path().read_text())
        self.assertEqual(len(manifest["images"]), 7)
        builds = [c for c in calls if c[:2] == ["docker", "build"]]
        self.assertEqual(len(builds), 7)
        for command in builds:
            self.assertEqual(command[-1], "https://github.com/escossio/ita-agent-batalha.git#"+sha)
            self.assertIn("--build-arg=VCS_REF="+sha, command)
        self.assertTrue(all("@sha256:" in item["digest"] for item in manifest["images"]))

    def test_digest_manifest_required(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, ITA_CERTIFIED_SHA="a"*40,
                ITA_DEPLOYMENT_MANIFEST=str(Path(temp)/"images.json")), patch.object(op, "repository", return_value="registry/repo"):
            op.artifact_path().write_text(json.dumps({"sha":"a"*40,"images":[]}))
            with self.assertRaises(ValueError):
                op.images(self.cfg)
