import pytest

from rpgmaker2godot.utils.messages import (
    display_program_banner,
    display_title,
)


def test_display_title_renders_message_inside_a_panel(
    capsys,
) -> None:
    display_title("Hello")

    captured = capsys.readouterr()

    assert "Hello" in captured.out
    # Panel border characters are present.
    # Rich falls back to square corners when the output is not a TTY.
    assert "┌" in captured.out
    assert "└" in captured.out


def test_display_program_banner_shows_name_version_and_summary(
    capsys,
) -> None:
    display_program_banner()

    captured = capsys.readouterr()

    assert "rpgmaker2godot v0.1.0" in captured.out
    assert (
        "Convert RPG Maker MV/MZ tilesets to Godot resources."
        in captured.out
    )


def test_banner_hides_build_number_when_absent(
    capsys,
    monkeypatch,
) -> None:
    from rpgmaker2godot.utils import messages

    monkeypatch.setattr(messages, "BUILD_NUMBER", 0)

    display_program_banner()

    captured = capsys.readouterr()

    assert "rpgmaker2godot v0.1.0" in captured.out
    assert "build" not in captured.out


def test_banner_appends_build_number_after_version(
    capsys,
    monkeypatch,
) -> None:
    from rpgmaker2godot.utils import messages

    monkeypatch.setattr(messages, "BUILD_NUMBER", 35)

    display_program_banner()

    captured = capsys.readouterr()

    assert "rpgmaker2godot v0.1.0 build 35" in captured.out