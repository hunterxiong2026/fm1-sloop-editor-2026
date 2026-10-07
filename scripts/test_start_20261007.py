# -*- coding: utf-8 -*-
"""测试 SLOOP 是否响应 MIDI 传输消息（Start 0xFA）直接播放"""
import sys, ctypes, time
import ctypes.wintypes as w
sys.path.insert(0, r'C:\Users\hunte\Doubao\chats\2026-10-06\new-chat\felucca_direct')
import felucca_link as fl
from felucca_link import FeluccaLink

mm = ctypes.windll.winmm
mm.midiOutShortMsg.argtypes = [w.HANDLE, w.DWORD]
mm.midiOutShortMsg.restype = w.UINT

outs, ins, out, inn = fl.find_felucca()
print('out devs:', outs)
print('in  devs:', ins)

link = FeluccaLink()
link.open()

def short(msg, name):
    rc = mm.midiOutShortMsg(link.hout, msg)
    print(f'{name}: midiOutShortMsg({hex(msg)}) rc={rc}')

try:
    # 1) 读全局 SYNC 参数（id=13）看当前同步模式
    r = link.req(fl.CMD['GET'], [1, 13], timeout=1.5)
    print('GET G_SYNC(13):', r)
    if r:
        a = r[1]
        # 回复 [scope, id, lo, hi]?
        if len(a) >= 4:
            val = (a[2] + (a[3] << 7)) - 8192
            print('  scope=%d id=%d  v14lo=%d v14hi=%d -> SYNC=%d' % (a[0], a[1], a[2], a[3], val))

    # 2) 发 MIDI Start
    short(0xFA, 'START')

    # 3) 发 MIDI Continue（若设备在暂停态）
    # short(0xFB, 'CONTINUE')

    # 保持连接短暂观察是否有 SysEx 推送
    for _ in range(10):
        fr = link.recv(timeout=0.3)
        if fr:
            print('  rx:', fr.hex())
finally:
    link.close()
print('DONE')
