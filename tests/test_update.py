import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "update.py"


class UpdateTest(unittest.TestCase):
    def run_update(self, agent_dir, repo_dir):
        env = os.environ | {
            "PI_CODING_AGENT_DIR": str(agent_dir),
            "PI_AGENT_COLLECTION_DIR": str(repo_dir),
        }
        return subprocess.run(
            [sys.executable, str(SCRIPT)], env=env, text=True, capture_output=True
        )

    def test_copies_latest_resources_but_skips_secrets_and_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = root / "agent"
            repo = root / "repo"
            (agent / "skills" / "new-skill").mkdir(parents=True)
            (agent / "skills" / "new-skill" / "SKILL.md").write_text("skill")
            (agent / "skills" / "new-skill" / ".env").write_text("API_KEY=private")
            (agent / "skills" / "new-skill" / "node_modules" / "pkg").mkdir(parents=True)
            (agent / "skills" / "new-skill" / "node_modules" / "pkg" / "index.js").write_text("dep")
            (agent / "extensions").mkdir(parents=True)
            (agent / "extensions" / "tool.ts").write_text("export {}")

            result = self.run_update(agent, repo)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((repo / "skills/new-skill/SKILL.md").read_text(), "skill")
            self.assertEqual((repo / "extensions/tool.ts").read_text(), "export {}")
            self.assertFalse((repo / "skills/new-skill/.env").exists())
            self.assertFalse((repo / "skills/new-skill/node_modules").exists())

            (agent / "skills" / "latest-skill").mkdir()
            (agent / "skills" / "latest-skill" / "SKILL.md").write_text("latest")
            (agent / "skills" / "new-skill" / "SKILL.md").write_text("updated")
            result = self.run_update(agent, repo)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((repo / "skills/latest-skill/SKILL.md").read_text(), "latest")
            self.assertEqual((repo / "skills/new-skill/SKILL.md").read_text(), "updated")

    def test_vendors_configured_packages_and_explicit_resources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = root / "agent"
            repo = root / "repo"
            configured_skill = root / "agents" / "grill-me"
            package = agent / "npm" / "node_modules" / "demo-package"
            (agent / "skills" / "personal").mkdir(parents=True)
            (agent / "skills" / "personal" / "SKILL.md").write_text("personal")
            (agent / "skills" / "personal" / "package.json").write_text(json.dumps({
                "name": "personal-skill", "version": "1.0.0"
            }))
            (agent / "extensions").mkdir(parents=True)
            (agent / "extensions" / "local.ts").write_text("export {}")
            configured_skill.mkdir(parents=True)
            (configured_skill / "SKILL.md").write_text("configured")
            for directory in ("extensions", "skills/demo-skill", "prompts", "themes"):
                (package / directory).mkdir(parents=True, exist_ok=True)
            (package / "extensions" / "index.js").write_text("export default () => {}")
            (package / "skills/demo-skill/SKILL.md").write_text("package skill")
            (package / "prompts/package.md").write_text("package prompt")
            (package / "themes/dark.json").write_text("{}")
            (package / ".env").write_text("API_KEY=do-not-copy")
            (package / "package.json").write_text(json.dumps({
                "name": "demo-package",
                "version": "1.2.3",
                "dependencies": {"left-pad": "1.3.0"},
                "pi": {
                    "extensions": ["./extensions"],
                    "skills": ["./skills"],
                    "prompts": ["./prompts"],
                    "themes": ["./themes"],
                },
            }))
            (agent / "settings.json").write_text(json.dumps({
                "defaultThinkingLevel": "high",
                "skills": [str(configured_skill)],
                "packages": ["npm:demo-package"],
            }))

            result = self.run_update(agent, repo)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((repo / "skills/grill-me/SKILL.md").read_text(), "configured")
            self.assertEqual((repo / "vendor/demo-package/skills/demo-skill/SKILL.md").read_text(), "package skill")
            self.assertFalse((repo / "vendor/demo-package/.env").exists())
            self.assertTrue((repo / "package.json").exists())
            manifest = json.loads((repo / "package.json").read_text())
            self.assertEqual(manifest["dependencies"]["demo-package"], "file:vendor/demo-package")
            self.assertIn("./vendor/demo-package/extensions", manifest["pi"]["extensions"])
            self.assertIn("./vendor/demo-package/prompts", manifest["pi"]["prompts"])
            self.assertIn("skills/personal", manifest["workspaces"])
            self.assertNotIn(str(root), json.dumps(manifest))
            self.assertIn("- Skills: 3", (repo / "SOURCES.md").read_text())
            self.assertIn("- Extension resource paths: 2", (repo / "SOURCES.md").read_text())
            config = json.loads((repo / "config/settings.json").read_text())
            self.assertEqual(config, {"defaultThinkingLevel": "high"})

    def test_setup_merges_safe_preferences_without_touching_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = root / "agent"
            repo = root / "repo"
            (repo / "config").mkdir(parents=True)
            (repo / "config" / "settings.json").write_text(json.dumps({"defaultThinkingLevel": "high"}))
            agent.mkdir()
            (agent / "settings.json").write_text(json.dumps({"defaultThinkingLevel": "low", "custom": True}))
            auth = agent / "auth.json"
            auth.write_text('{"private":"do-not-touch"}')
            env = os.environ | {
                "PI_CODING_AGENT_DIR": str(agent),
                "PI_AGENT_COLLECTION_DIR": str(repo),
            }

            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve().parents[1] / "setup-config.py")],
                env=env, text=True, capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            settings = json.loads((agent / "settings.json").read_text())
            self.assertTrue(settings["custom"])
            self.assertEqual(settings["defaultThinkingLevel"], "high")
            self.assertEqual(auth.read_text(), '{"private":"do-not-touch"}')
            self.assertTrue(list(agent.glob("settings.json.bak-*")))

    def test_refuses_likely_hard_coded_key_before_copying_anything(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            agent = root / "agent"
            repo = root / "repo"
            (agent / "skills" / "unsafe").mkdir(parents=True)
            secret = "x" * 40
            (agent / "skills" / "unsafe" / "SKILL.md").write_text(
                f'api_key = "{secret}"\n'
            )
            (agent / "extensions").mkdir()

            result = self.run_update(agent, repo)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("likely credential", result.stderr.lower())
            self.assertFalse((repo / "skills").exists())
            self.assertNotIn(secret, result.stdout + result.stderr)

    def test_refuses_collection_inside_pi_source_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            agent = Path(temp) / "agent"
            (agent / "skills").mkdir(parents=True)
            (agent / "extensions").mkdir()
            (agent / "skills" / "safe" / "SKILL.md").parent.mkdir()
            (agent / "skills" / "safe" / "SKILL.md").write_text("safe")

            result = self.run_update(agent, agent)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("overlap", result.stderr.lower())
            self.assertEqual((agent / "skills/safe/SKILL.md").read_text(), "safe")


if __name__ == "__main__":
    unittest.main()
