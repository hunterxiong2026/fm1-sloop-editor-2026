# -*- coding: utf-8 -*-
"""SLOOP 播放测试 v2：SYNC=外部时钟 + Start + 时钟流"""
import sys, ctypes, time
import ctypes.wintypes as w
sys.path.insert(0, r'C:\Users\hunte\Doubao\chats\2026-10-06\new-chat\felucca_direct')
import felucca_link as fl
from felucca_link import FeluccaLink

mm = ctypes.windll.winmm
mm.midiOutShortMsg.argtypes = [w.HANDLE, w.DWORD]
mm.midiOutShortMsg.restype = w.UINT

link = FeluccaLink()
link.open()

def short(msg, name):
    rc = mm.midiOutShortMsg(link.hout, msg)
    print(f'{name}: {hex(msg)} rc={rc}')

def read_sync():
    r = link.req(fl.CMD['GET'], [1, 13], timeout=1.5)
    if r and len(r[1]) >= 4:
        a = r[1]
        return (a[2] + (a[3] << 7)) - 8192
    return None

def v14enc(v):
    x = v + 8192
    return [x & 0x7F, (x >> 7) & 0x7F]

try:
    print('SYNC before:', read_sync())
    # 切 SYNC=1（外部 MIDI 时钟）
    v = v14enc(1)
    link.send(fl.CMD['SET'], [1, 13] + v)
    time.sleep(0.2)
    print('SYNC after :', read_sync())

    # Start + 时钟流（120BPM → 48 时钟/秒，共 2 秒）
    short(0xFA, 'START')
    t0 = time.time()
    n = 0
    while time.time() - t0 < 2.0:
        mm.midiOutShortMsg(link.hout, 0xF8)
        n += 1
        time.sleep(0.020)   # ~50Hz
    print(f'  sent {n} clock ticks (0xF8)')

    # 观察推送
    for _ in range(10):
        fr = link.recv(timeout=0.3)
        if fr:
            print('  rx:', fr.hex())
finally:
    link.close()
print('DONE')
