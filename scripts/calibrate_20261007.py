# -*- coding: utf-8 -*-
"""SLOOP 真机校准（用已验证的 felucca_link 库）：打印完整原始帧 + 逐步解码
1. STEP_GET（read_step）  2. DRUM_STEP（read_drum_step）
3. TRACK_DUMP（p 数组）   4. INFO trailer
"""
import sys, time
sys.path.insert(0, r'C:\Users\hunte\Doubao\chats\2026-10-06\new-chat\felucca_direct')
import felucca_link as fl
from felucca_link import FeluccaLink, CMD, parse_info

outs, ins, out, inn = fl.find_felucca()
out = (1, 'Felucca'); inn = (0, 'Felucca')
fl.find_felucca = lambda: (outs, ins, out, inn)
link = FeluccaLink(); link.open()

def show(name, r):
    rc, args = r
    # 完整帧 = F0 + HDR + cmd + args + F7
    frame = bytes([0xF0] + fl.HDR + [rc] + args + [0xF7])
    print(f'=== {name} ===')
    print(f'  完整帧 hex : {frame.hex()}')
    print(f'  完整帧 list: {list(frame)}')
    print(f'  body args [{len(args)}B]: {args}')
    return args

try:
    # 4) INFO
    r = link.req(CMD['INFO'], timeout=3.0)
    if r: args = show('INFO', r)
    else: print('INFO: NO REPLY')

    # 1) read_step tr0 step0
    link.req(CMD['TRACK'], [0], timeout=1.0)
    time.sleep(0.05)
    r = link.req(CMD['STEP_GET'], [0], timeout=1.5)
    if r: show('STEP_GET tr0 step0', r)
    else: print('STEP_GET: NO REPLY')
    # 再读 tr0 step1（TIE 步）和 step24（八分 NOTE）对比
    for s in (1, 24):
        r = link.req(CMD['STEP_GET'], [s], timeout=1.5)
        if r: show(f'STEP_GET tr0 step{s}', r)

    # 2) read_drum_step tr3 step0
    link.req(CMD['TRACK'], [3], timeout=1.0)
    time.sleep(0.05)
    r = link.req(33, [0], timeout=1.5)   # 33 = DRUM_STEP
    if r: show('DRUM_STEP tr3 step0', r)
    else: print('DRUM_STEP: NO REPLY')

    # 3) track_dump tr0
    r = link.req(CMD['TRACK_DUMP'], [0], timeout=3.0)
    if r: show('TRACK_DUMP tr0', r)
    else: print('TRACK_DUMP: NO REPLY')
finally:
    link.close()
print('DONE')
