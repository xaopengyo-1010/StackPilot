from stackpilot.scanner import scan_system


def test_scanner_uses_windows_hardware_snapshot(monkeypatch):
    from stackpilot import detector

    monkeypatch.setattr(
        detector,
        "detect_windows_hardware_snapshot",
        lambda: {
            "ComputerSystem": {
                "Manufacturer": "Lenovo",
                "Model": "Yoga Pro 7",
                "SystemSKUNumber": "83AU",
                "TotalPhysicalMemory": 34359738368,
            },
            "BaseBoard": {"Manufacturer": "LENOVO", "Product": "LNVNB161216"},
            "BIOS": {"Manufacturer": "LENOVO", "SMBIOSBIOSVersion": "M1CN41WW"},
            "Processors": [
                {
                    "Name": "AMD Ryzen 7 7840HS",
                    "Architecture": 9,
                    "NumberOfCores": 8,
                    "NumberOfLogicalProcessors": 16,
                    "MaxClockSpeed": 3801,
                }
            ],
            "PhysicalMemory": [{"Capacity": 34359738368, "Speed": 6400, "DeviceLocator": "Onboard"}],
            "DiskDrives": [{"Model": "WD SN740", "Size": 1000202273280, "MediaType": "SSD"}],
            "LogicalDisks": [{"DeviceID": "D:", "FileSystem": "NTFS", "Size": 500095492096, "FreeSpace": 322122547200}],
            "VideoControllers": [{"Name": "AMD Radeon 780M Graphics", "AdapterRAM": 536870912}],
            "OperatingSystem": {"Caption": "Microsoft Windows 11 Home", "Version": "10.0.26100", "OSArchitecture": "64-bit"},
        },
    )
    monkeypatch.setattr(detector, "detect_nvidia_driver", lambda: None)
    monkeypatch.setattr(detector, "detect_wsl", lambda: False)
    monkeypatch.setattr(detector, "get_command_version", lambda command, args: None)

    profile = scan_system()

    assert profile.computer_model is not None
    assert profile.computer_model.model == "Yoga Pro 7"
    assert profile.baseboard is not None
    assert profile.baseboard.product == "LNVNB161216"
    assert profile.bios is not None
    assert profile.bios.version == "M1CN41WW"
    assert profile.cpu is not None
    assert profile.cpu.logical_cores == 16
    assert profile.memory is not None
    assert profile.memory.total_gb == 32
    assert profile.disks[0].model == "WD SN740"
    assert profile.disk_volumes[0].name == "D:"
    assert profile.gpus[0].name == "AMD Radeon 780M Graphics"
    assert profile.cpu_name == "AMD Ryzen 7 7840HS"
    assert profile.ram_gb == 32
