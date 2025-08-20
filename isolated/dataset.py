import os

# Map group name -> list of filenames
groups = {
    "runc no systemd-cgroup": [
        "runc_no_flag_1/no_flag.txt",
        "runc_no_flag_2/no_flag.txt",
    ],
    "runc with systemd-cgroup": [
        "runc_with_flag.txt",
        "runc_with_flag2.txt",
        "runc_with_flag3.txt",
    ],
    "gvisor no systemd-cgroup": [
        "gvisor_no_flag1.txt",
        "gvisor_no_flag2.txt",
    ],
    "gvisor with systemd-cgroup": [
        "gvisor_with_flag1.txt",
        "gvisor_with_flag2.txt",
    ],
}

groups = {
    "systemd-cgroups ON":  ["weird/runc_local_120_withflag.txt"],
    "systemd-cgroups OFF": ["weird/runc_local_120_noflag.txt"]
}

groups = {
    "local 100 containers systemd-cgroups ON":   ["local_runs/withflag_local_100"],
    "local 100 containers systemd-cgroups OFF":  ["local_runs/noflag_local_100"],
    "local 300 containers systemd-cgroups ON":   ["local_runs/withflag_local_300"],
    "local 300 containers systemd-cgroups OFF":  ["local_runs/noflag_local_300"],
}

groups = {
    l: [f"automated_logs/{l}"] for l in os.listdir("automated_logs")
}
print(groups)

groups = [
    ('systemd_on_100.log', ['automated_logs/local_flag_on_100.log']),
    ('systemd_off_100.log', ['automated_logs/local_flag_off_100.log']),

    ('systemd_on_300.log', ['automated_logs/local_flag_on_300.log']),
    ('systemd_off_300.log', ['automated_logs/local_flag_off_300.log']),

    ('systemd_on_500.log', ['automated_logs/local_flag_on_500.log']),
    ('systemd_off_500.log', ['automated_logs/local_flag_off_500.log']),

    ('systemd_on_700.log', ['automated_logs/local_flag_on_700.log']),
    ('systemd_off_700.log', ['automated_logs/local_flag_off_700.log']),

    ('systemd_on_1000.log', ['automated_logs/local_flag_on_1000.log']),
    ('systemd_off_1000.log', ['automated_logs/local_flag_off_1000.log']),
]

groups = [
    ('systemd_on_100',   ['no_CO/systemd_on_100.json']),
    ('systemd_off_100',  ['no_CO/systemd_off_100.json']),

    ('systemd_on_300',   ['no_CO/systemd_on_300.json']),
    ('systemd_off_300',  ['no_CO/systemd_off_300.json']),

    ('systemd_on_500',   ['no_CO/systemd_on_500.json']),
    ('systemd_off_500',  ['no_CO/systemd_off_500.json']),

    ('systemd_on_700',   ['no_CO/systemd_on_700.json']),
    ('systemd_off_700',  ['no_CO/systemd_off_700.json']),

    ('systemd_on_1000',  ['no_CO/systemd_on_1000.json']),
    ('systemd_off_1000', ['no_CO/systemd_off_1000.json']),
]

#groups = sorted(groups.items(), key=lambda k : k[0])

groups = [
    ("gvisor cgroupfs": ["final/"]),
    ("gvisor systemd":  ["final/"]),
]
