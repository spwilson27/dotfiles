import unittest

from lib.models import SetupEntry
from lib.planner import filter_entries, normalize_tags


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.entries = [
            SetupEntry(
                name="common",
                provider="shell",
                target=("echo common",),
                os_targets=("linux",),
                tags=("all",),
            ),
            SetupEntry(
                name="dev-only",
                provider="shell",
                target=("echo dev",),
                os_targets=("linux-ubuntu",),
                tags=("dev",),
            ),
        ]

    def test_normalize_tags_defaults_to_all(self) -> None:
        self.assertEqual({"all"}, normalize_tags(None))
        self.assertEqual({"all"}, normalize_tags([]))
        self.assertEqual({"all"}, normalize_tags(["", "  "]))

    def test_normalize_tags_supports_repeated_or_comma_separated_values(self) -> None:
        self.assertEqual({"all", "dev"}, normalize_tags(["all,dev"]))
        self.assertEqual({"all", "dev"}, normalize_tags(["all", "dev"]))

    def test_filter_entries_respects_os_and_tag_rules(self) -> None:
        selected = filter_entries(self.entries, selected_os="linux-ubuntu", tags={"all"})
        self.assertEqual(["common"], [item.name for item in selected])

        selected = filter_entries(self.entries, selected_os="linux-ubuntu", tags={"dev"})
        self.assertEqual(["dev-only"], [item.name for item in selected])

        selected = filter_entries(self.entries, selected_os="linux-ubuntu", tags={"all", "dev"})
        self.assertEqual(["common", "dev-only"], [item.name for item in selected])
