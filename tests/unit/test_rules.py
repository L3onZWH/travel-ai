"""Unit tests for agent/rules.py."""
from __future__ import annotations

from agent.rules import RulesEngine


class TestLoad:
    def test_load_returns_empty_when_file_missing(self, tmp_path):
        engine = RulesEngine(rules_path=tmp_path / "nonexistent.md")
        assert engine.load() == ""

    def test_load_returns_file_content(self, tmp_path):
        rule_file = tmp_path / "rule.md"
        rule_file.write_text("# 规则\n- 保持简洁", encoding="utf-8")
        engine = RulesEngine(rules_path=rule_file)
        assert "保持简洁" in engine.load()

    def test_load_soul_returns_empty_when_missing(self, tmp_path):
        engine = RulesEngine(soul_path=tmp_path / "soul.md")
        assert engine.load_soul() == ""

    def test_load_soul_returns_content(self, tmp_path):
        soul = tmp_path / "soul.md"
        soul.write_text("喜欢简短回复", encoding="utf-8")
        engine = RulesEngine(soul_path=soul)
        assert "简短回复" in engine.load_soul()


class TestAsSystemBlock:
    def test_empty_block_when_both_missing(self, tmp_path):
        engine = RulesEngine(
            rules_path=tmp_path / "rule.md",
            soul_path=tmp_path / "soul.md",
        )
        assert engine.as_system_block() == ""

    def test_block_contains_rule_section(self, tmp_path):
        rule_file = tmp_path / "rule.md"
        rule_file.write_text("每次回答需含费用估算", encoding="utf-8")
        engine = RulesEngine(rules_path=rule_file, soul_path=tmp_path / "soul.md")
        block = engine.as_system_block()
        assert "行为规则" in block
        assert "费用估算" in block

    def test_block_contains_soul_section(self, tmp_path):
        soul = tmp_path / "soul.md"
        soul.write_text("言简意赅", encoding="utf-8")
        engine = RulesEngine(rules_path=tmp_path / "rule.md", soul_path=soul)
        block = engine.as_system_block()
        assert "用户偏好" in block
        assert "言简意赅" in block

    def test_block_ends_with_separator(self, tmp_path):
        rule_file = tmp_path / "rule.md"
        rule_file.write_text("some rule", encoding="utf-8")
        engine = RulesEngine(rules_path=rule_file, soul_path=tmp_path / "soul.md")
        block = engine.as_system_block()
        assert block.endswith("---")
