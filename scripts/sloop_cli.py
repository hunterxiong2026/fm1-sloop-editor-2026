"""
sloop_cli.py — FM-1 / SLOOP 2.4.1 命令行工具

用法:
    python sloop_cli.py info
    python sloop_cli.py desc <scope> <id>
    python sloop_cli.py names <engine>
    python sloop_cli.py preset <tr> <engine> <preset>
    python sloop_cli.py kit <kit_num>
    python sloop_cli.py readstep <tr> <step>
    python sloop_cli.py drumread <step>
    python sloop_cli.py readparam <tr> <pid>
    python sloop_cli.py setparam <tr> <pid> <value>
    python sloop_cli.py dump <tr>
    python sloop_cli.py save <section>
    python sloop_cli.py restore <tr>
"""

import sys
from sloop_link import (
    SloopLink, ENGINES, ENGINE_NAMES, KITS, DRUM_LANES, LANE_BY_NAME,
    TIME_REST, TIME_NOTE,
)


def cmd_info(link):
    print(link.info())


def cmd_desc(link, scope, pid):
    print(link.desc(int(scope), int(pid)))


def cmd_names(link, engine):
    e = int(engine)
    names = link.names(e)
    print(f'引擎 {ENGINE_NAMES.get(e, e)} 预设名（{len(names)} 个）：')
    for i, n in enumerate(names):
        print(f'  {i:2d} = {n}')


def cmd_preset(link, tr, engine, preset):
    tr, engine, preset = int(tr), int(engine), int(preset)
    link.select_track(tr)
    import time; time.sleep(0.2)
    link.preset(engine, preset)
    print(f'轨{tr} 已切到 {ENGINE_NAMES.get(engine, engine)} 预设 {preset}')


def cmd_kit(link, kit_num):
    k = int(kit_num)
    link.set_kit(k)
    name = next((n for n, v in KITS.items() if v == k), '?')
    print(f'鼓组已切到 {k} ({name})')


def cmd_readstep(link, tr, step):
    print(link.read_step(int(tr), int(step)))


def cmd_drumread(link, step):
    print(link.read_drum_step(int(step)))


def cmd_readparam(link, tr, pid):
    print(link.track_param(int(tr), int(pid)))


def cmd_setparam(link, tr, pid, value):
    link.track_param(int(tr), int(pid), int(value))
    print(f'轨{tr} 参数{pid} 已设为 {value}')


def cmd_dump(link, tr):
    print(link.track_dump(int(tr)))


def cmd_save(link, section):
    link.save_section(int(section))
    print(f'已保存到 section {section}')


def cmd_restore(link, tr):
    t = int(tr)
    for i in range(64):
        link.write_step(t, i, [], TIME_REST, 0)
    print(f'轨 {t} 已清空')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    link = SloopLink().open()
    try:
        if cmd == 'info':
            cmd_info(link)
        elif cmd == 'desc':
            cmd_desc(link, sys.argv[2], sys.argv[3])
        elif cmd == 'names':
            cmd_names(link, sys.argv[2])
        elif cmd == 'preset':
            cmd_preset(link, sys.argv[2], sys.argv[3], sys.argv[4])
        elif cmd == 'kit':
            cmd_kit(link, sys.argv[2])
        elif cmd == 'readstep':
            cmd_readstep(link, sys.argv[2], sys.argv[3])
        elif cmd == 'drumread':
            cmd_drumread(link, sys.argv[2])
        elif cmd == 'readparam':
            cmd_readparam(link, sys.argv[2], sys.argv[3])
        elif cmd == 'setparam':
            cmd_setparam(link, sys.argv[2], sys.argv[3], sys.argv[4])
        elif cmd == 'dump':
            cmd_dump(link, sys.argv[2])
        elif cmd == 'save':
            cmd_save(link, sys.argv[2])
        elif cmd == 'restore':
            cmd_restore(link, sys.argv[2])
        else:
            print(f'未知命令: {cmd}')
            print(__doc__)
    finally:
        link.close()


if __name__ == '__main__':
    main()