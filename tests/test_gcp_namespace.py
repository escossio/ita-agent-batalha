"""All GCP subprocesses are simulated; never use operator credentials in tests."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from infra.gcp.cloudrun import namespace as ns
from infra.gcp.cloudrun import operator as op


class NamespaceTests(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(project=ns.PROJECT, region=ns.REGION)
        env = patch.dict(os.environ, dict(ITA_RESOURCE_PREFIX=ns.PREFIX, ITA_ARTIFACT_REPOSITORY=ns.PREFIX), clear=True)
        env.start()
        self.addCleanup(env.stop)

    def gc(self, *args):
        return ["gcloud", *args, "--project="+ns.PROJECT, "--quiet"]

    def rejected(self, args):
        with patch.object(op.subprocess, "run") as process, self.assertRaises(ns.Blocked):
            op.run(args)
        process.assert_not_called()

    def test_external_services_never_mutable(self):
        for target in ("agente", "ita-backend", "ita-escossioevil-web", "ita-escossio-other", "ita-preview-web"):
            for operation in ("delete", "add-iam-policy-binding"):
                with self.subTest(target=target, operation=operation):
                    self.rejected(self.gc("run", "services", operation, target, "--region="+ns.REGION))
            self.rejected(self.gc("run", "deploy", target))

    def test_external_accounts_and_secret_never_mutable(self):
        for target in ("squad-agent-sa", "123456789012-compute", "default Compute SA"):
            self.rejected(self.gc("iam", "service-accounts", "create", target))
            self.rejected(self.gc("iam", "service-accounts", "delete", target+"@"+"developer.gserviceaccount.com"))
        self.rejected(self.gc("secrets", "add-iam-policy-binding", "ita-backend-gcp-credentials"))
        self.rejected(self.gc("secrets", "versions", "add", "ita-backend-gcp-credentials"))

    def test_external_registries_never_reused(self):
        for repo in ("agentes", "batalha-agentes", "ita-escossio-other"):
            with patch.dict(os.environ, ITA_ARTIFACT_REPOSITORY=repo), patch.object(op, "gc") as gc:
                with self.assertRaises(ns.Blocked):
                    op.repository(self.cfg, create=True)
                gc.assert_not_called()

    def test_project_table_iam_and_unknown_operations_deny(self):
        for args in (self.gc("projects", "add-iam-policy-binding", ns.PROJECT),
                     ["bq", "--project_id="+ns.PROJECT, "add-iam-policy-binding", ns.PROJECT+":hackathon_dados.extrato_sintetico"],
                     self.gc("iam", "roles", "create", "itaEscossioRole"),
                     self.gc("services", "enable", "sqladmin.googleapis.com"),
                     self.gc("iam", "service-accounts", "keys", "create", "credentials.json")):
            self.rejected(args)

    def test_prefix_and_project_region_cannot_redirect(self):
        with patch.dict(os.environ, ITA_RESOURCE_PREFIX="ita"):
            self.rejected(self.gc("iam", "service-accounts", "create", "ita-agent-sa"))
        for cfg in (dict(project="other-project", region=ns.REGION), dict(project=ns.PROJECT, region="europe-west1")):
            with patch.object(op, "gc") as gc, self.assertRaises(ns.Blocked):
                op.repository(cfg, create=True)
            gc.assert_not_called()

    def test_first_mutation_creates_exactly_one_repository(self):
        calls = []
        def fake(args, **kwargs):
            calls.append(args)
            if args[1:4] == ["config", "get-value", "project"]:
                output = ns.PROJECT
            elif "list" in args:
                output = json.dumps([dict(name="projects/"+ns.PROJECT+"/locations/"+ns.REGION+"/repositories/agentes")])
            else:
                output = "created"
            return subprocess.CompletedProcess(args, 0, output, "")
        with patch.object(op.subprocess, "run", side_effect=fake), patch("builtins.print") as output:
            url = op.repository(self.cfg, create=True)
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[-1][1:5], ["artifacts", "repositories", "create", ns.PREFIX])
        self.assertIn("--immutable-tags", calls[-1])
        self.assertTrue(url.endswith("/"+ns.PROJECT+"/"+ns.PREFIX))
        self.assertTrue(any("OPERATION CREATE" in str(c) for c in output.call_args_list))

    def test_denied_create_stops_without_fallback(self):
        for error in ("PERMISSION_DENIED", "organization-policy denial"):
            calls = []
            def fake(args, **kwargs):
                calls.append(args)
                if "create" in args:
                    return subprocess.CompletedProcess(args, 1, "", error)
                return subprocess.CompletedProcess(args, 0, ns.PROJECT if "get-value" in args else "[]", "")
            with patch.object(op.subprocess, "run", side_effect=fake), patch("builtins.print"), self.assertRaisesRegex(ns.Blocked, error):
                op.repository(self.cfg, create=True)
            self.assertEqual(len(calls), 3)
            self.assertEqual(sum("create" in c for c in calls), 1)

    def test_active_project_mismatch_never_creates(self):
        with patch.object(op, "run", return_value="other-project"), patch.object(op, "gc") as gc, self.assertRaises(ns.Blocked):
            op.repository(self.cfg, create=True)
        gc.assert_not_called()

    def test_existing_repository_requires_ownership_and_immutable_tags(self):
        record = dict(name=f"projects/{ns.PROJECT}/locations/{ns.REGION}/repositories/{ns.PREFIX}",
                      format="DOCKER", labels=ns.OWNER, dockerConfig=dict(immutableTags=True))
        with patch.object(op, "run", return_value=ns.PROJECT), patch.object(op, "gc", return_value=json.dumps([record])) as gc, patch("builtins.print"):
            op.repository(self.cfg, create=True)
        self.assertEqual(gc.call_count, 1)
        for changed in (dict(record, labels={}), dict(record, dockerConfig={}), dict(record, format="MAVEN")):
            with patch.object(op, "gc", return_value=json.dumps([changed])) as gc, self.assertRaises(ns.Blocked):
                op.repository(self.cfg)
            self.assertEqual(gc.call_count, 1)

    def test_naming_plan_fits_google_constraints(self):
        names = set()
        for service in op.PLAN:
            sa = op.PLAN[service]["service_account"]
            self.assertRegex(sa, r"^[a-z][-a-z0-9]{4,28}[a-z0-9]$")
            self.assertEqual(sa, op.service_name(service)+"-sa")
            names.add(sa)
        self.assertEqual(len(names), 7)
        self.assertEqual(op.service_name("tool-broker"), "ita-escossio-broker")

    def test_accounts_collision_checked_before_any_creation(self):
        existing = dict(email=op.account(self.cfg, "finance"), description="another owner")
        with patch.object(op, "gc", return_value=json.dumps([existing])) as gc, self.assertRaises(ns.Blocked):
            op.identities(self.cfg)
        self.assertEqual(gc.call_count, 1)

    def test_identities_never_write_project_or_table_iam(self):
        calls = []
        def fake(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, "[]", "")
        with patch.object(op.subprocess, "run", side_effect=fake), patch("builtins.print"):
            op.identities(self.cfg)
        self.assertEqual(len(calls), 8)
        self.assertTrue(all(c[1:4] == ["iam", "service-accounts", "create"] for c in calls[1:]))

    def test_image_namespace_and_sha_enforced(self):
        base = ns.REGION+"-docker.pkg.dev/"+ns.PROJECT+"/"+ns.PREFIX+"/ita-escossio-web:"
        ns.command(["docker", "push", base+"a"*40])
        for value in (base+"latest", base+"shortsha", base.replace("/ita-escossio/", "/agentes/")+"a"*40,
                      base.replace("ita-escossio-web", "agente")+"a"*40):
            self.rejected(["docker", "push", value])

    def test_only_reviewed_invoker_edges(self):
        for caller, spec in op.PLAN.items():
            for callee in spec["callees"]:
                ns.command(self.gc("run", "services", "add-iam-policy-binding", op.service_name(callee),
                    "--region="+ns.REGION, "--member=serviceAccount:"+op.account(self.cfg, caller), "--role=roles/run.invoker", "--condition=None"))
        for member in ("allUsers", "allAuthenticatedUsers", "serviceAccount:"+op.account(self.cfg, "agent")):
            self.rejected(self.gc("run", "services", "add-iam-policy-binding", "ita-escossio-data", "--member="+member,
                                  "--role=roles/run.invoker", "--condition=None"))

    def test_deploy_command_rejects_external_identity_secret_and_credential_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp)/"env.json"
            env.write_text('{}')
            args = self.gc("run", "deploy", "ita-escossio-api", "--region="+ns.REGION,
                "--service-account="+op.account(self.cfg, "api"),
                "--image="+ns.REGION+"-docker.pkg.dev/"+ns.PROJECT+"/ita-escossio/ita-escossio-api@sha256:"+"a"*64,
                "--env-vars-file="+str(env), "--no-allow-unauthenticated", "--invoker-iam-check",
                "--labels="+",".join(k+"="+v for k, v in ns.OWNER.items()))
            ns.command(args)
            for account in ("squad-agent-sa"+"@"+ns.PROJECT+".iam.gserviceaccount.com",
                            "123456789012-compute"+"@"+"developer.gserviceaccount.com", op.account(self.cfg, "data")):
                self.rejected(["--service-account="+account if a.startswith("--service-account=") else a for a in args])
            self.rejected(args+["--set-secrets=/secrets/identity/registry.json=ita-backend-gcp-credentials:1"])
            self.rejected(args+["--allow-unauthenticated"])
            env.write_text(json.dumps(dict(GOOGLE_APPLICATION_CREDENTIALS="credentials.json")))
            self.rejected(args)

    def test_owned_labels_do_not_authorize_external_name(self):
        for name in ("agente", "ita-backend"):
            with self.assertRaises(ns.Blocked):
                op.owned(dict(metadata=dict(name=name, labels=ns.OWNER)))
