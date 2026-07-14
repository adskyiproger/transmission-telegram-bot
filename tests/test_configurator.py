from pathlib import Path

import yaml

from models.BotConfigurator import BotConfigurator


def test_validate_requires_token_and_super_user(tmp_path: Path):
    config_file = tmp_path / "torrentino.yaml"
    config_file.write_text("bot: {}\n", encoding="utf-8")
    original = BotConfigurator.config_file
    try:
        BotConfigurator.config_file = str(config_file)
        assert BotConfigurator().validate() is False
    finally:
        BotConfigurator.config_file = original


def test_safe_round_trip_preserves_unicode(tmp_path: Path):
    config_file = tmp_path / "torrentino.yaml"
    config_file.write_text(
        yaml.safe_dump({"bot": {"token": "token", "super_user": 7}}),
        encoding="utf-8",
    )
    original = BotConfigurator.config_file
    try:
        BotConfigurator.config_file = str(config_file)
        configurator = BotConfigurator()
        configurator.set("bot.label", "Київ")
        assert (
            yaml.safe_load(config_file.read_text(encoding="utf-8"))["bot"]["label"]
            == "Київ"
        )
    finally:
        BotConfigurator.config_file = original


def test_runtime_secrets_are_not_persisted(tmp_path: Path):
    config_file = tmp_path / "torrentino.yaml"
    config_file.write_text("bot: {}\n", encoding="utf-8")
    original_file = BotConfigurator.config_file
    original_overrides = BotConfigurator._runtime_overrides
    try:
        BotConfigurator.config_file = str(config_file)
        BotConfigurator._runtime_overrides = {"bot.token": "runtime-secret"}
        assert BotConfigurator().get("bot.token") == "runtime-secret"
        assert "runtime-secret" not in config_file.read_text(encoding="utf-8")
    finally:
        BotConfigurator.config_file = original_file
        BotConfigurator._runtime_overrides = original_overrides
