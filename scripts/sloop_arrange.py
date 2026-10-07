"""
sloop_arrange.py — 读取 arrangement.json，写入 4 轨（含鼓轨）、设 BPM/SWG、存 section。

用法:
    python sloop_arrange.py <section> <bpm> <swing>

arrangement.json 结构:
{
  "tracks": [
    {
      "type": "synth",
      "engine": "ANALOG",
      "preset": 9,
      "params": {"LEN": 64, "DIV": 1, "ATK": 20, "REL": 60, "FLT": 80},
      "steps": [
        {"i": 0, "notes": [72], "time": 0, "vel": 100},
        {"i": 1, "notes": [], "time": 1},
        ...
      ]
    },
    {
      "type": "drum",
      "params": {"LEN": 32, "DIV": 1},
      "steps": [
        {"i": 0, "lanes": [0, 4]},
        {"i": 4, "lanes": [2, 4]},
        ...
      ]
    }
  ]
}

注意：播放由设备 PLAY 键触发，脚本结束后会提示用户按 PLAY。
"""

import json
import sys
import time
from sloop_link import (
    SloopLink, ENGINES, DIVS, TIME_NOTE, TIME_TIE, TIME_REST,
    P_LEN, P_DIV, P_SWG, P_GATE, P_ATK, P_DEC, P_SUS, P_REL, P_FLT,
    G_BPM, G_SWING,
    LANE_BY_NAME,
)

PARAM_IDS = {
    'LVL': 0, 'ATK': 1, 'DEC': 2, 'SUS': 3, 'REL': 4, 'FLT': 5,
    'LEN': 29, 'DIV': 30, 'SWG': 31, 'GATE': 32,
    'PAT': 46, 'RATE': 47, 'DEPTH': 48, 'CHORD': 49,
}

NOTE_MAP = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
            'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8,
            'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def name_to_midi(name):
    if not name:
        return None
    name = name.strip()
    if len(name) < 2:
        return None
    try:
        octave = int(name[-1])
    except ValueError:
        return None
    pitch_name = name[:-1]
    if pitch_name not in NOTE_MAP:
        return None
    return (octave + 1) * 12 + NOTE_MAP[pitch_name]


def build_synth_track(link, idx, track_data):
    link.select_track(idx)
    time.sleep(0.15)
    engine_name = track_data.get('engine', 'ANALOG')
    engine = ENGINES.get(engine_name, 0)
    preset = track_data.get('preset', 0)
    link.preset(engine, preset)
    time.sleep(0.3)
    params = track_data.get('params', {})
    for key, value in params.items():
        if key in PARAM_IDS:
            link.track_param(idx, PARAM_IDS[key], value)
            time.sleep(0.05)
    steps = track_data.get('steps', [])
    for step in steps:
        i = step['i']
        notes = step.get('notes', [])
        midi_notes = []
        for n in notes:
            if isinstance(n, str):
                v = name_to_midi(n)
                if v is not None:
                    midi_notes.append(v)
            elif isinstance(n, int):
                midi_notes.append(n)
        time_mode = step.get('time', TIME_NOTE)
        vel = step.get('vel', 100)
        flags = step.get('flags', 0)
        link.write_step(idx, i, midi_notes, time_mode, vel, flags)
        time.sleep(0.12)


def build_drum_track(link, idx, track_data):
    link.select_track(idx)
    time.sleep(0.15)
    params = track_data.get('params', {})
    # 鼓组 KIT 通过 P_E0(50) 设置
    if 'KIT' in params:
        kit = params['KIT']
        if isinstance(kit, str):
            from sloop_link import KITS
            kit = KITS.get(kit, 0)
        link.track_param(idx, 50, kit)
        time.sleep(0.2)
    for key, value in params.items():
        if key in ('LEN', 'DIV'):
            link.track_param(idx, PARAM_IDS[key], value)
            time.sleep(0.05)
    steps = track_data.get('steps', [])
    for step in steps:
        i = step['i']
        lanes = step.get('lanes', [])
        # 支持音名形式
        if not lanes and 'notes' in step:
            for n in step['notes']:
                if isinstance(n, str) and n.upper() in LANE_BY_NAME:
                    lanes.append(LANE_BY_NAME[n.upper()])
        levels = step.get('levels')
        ratchets = step.get('ratchets')
        link.write_drum_step(i, lanes, levels, ratchets)
        time.sleep(0.12)


def main():
    if len(sys.argv) < 4:
        print('用法: python sloop_arrange.py <section> <bpm> <swing>')
        sys.exit(1)
    section = int(sys.argv[1])
    bpm = int(sys.argv[2])
    swing = int(sys.argv[3])

    with open('arrangement.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    tracks = data.get('tracks', [])
    if len(tracks) < 4:
        print(f'警告: arrangement.json 只有 {len(tracks)} 轨，SLOOP 需要 4 轨')

    link = SloopLink().open()
    try:
        print(f'设备: {link.info()}')
        link.set_global(G_BPM, bpm)
        link.set_global(G_SWING, swing)
        time.sleep(0.1)

        for idx, track_data in enumerate(tracks[:4]):
            ttype = track_data.get('type', 'synth')
            print(f'写入轨 {idx} ({ttype})...')
            if ttype == 'drum' or idx == 3:
                build_drum_track(link, idx, track_data)
            else:
                build_synth_track(link, idx, track_data)

        print(f'保存到 section {section}...')
        link.save_section(section)
        time.sleep(0.5)
        print('完成。请按设备 PLAY 键播放。')
    finally:
        link.close()


if __name__ == '__main__':
    main()