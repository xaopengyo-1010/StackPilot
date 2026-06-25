import build


def test_build_command_creates_release_tui_exe_with_configs():
    command = build.build_command()

    assert "--name=StackPilot_TUI" in command
    assert str(build.SRC_DIR) in command
    assert command[-1] == str(build.ENTRY_SCRIPT)

    add_data_index = command.index("--add-data")
    assert command[add_data_index + 1] == build.add_data_arg(build.CONFIG_DIR, "configs")
