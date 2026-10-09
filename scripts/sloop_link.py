"""
sloop_link.py — FM-1 / SLOOP 直连 SysEx 核心库（已按 2.4.1 实测校准）

零第三方依赖，仅用 ctypes 直调 Windows winmm.dll。
协议帧：F0 7D 46 4C <cmd & 0x7F> <args...> F7
固件：FELUCCA SLOOP 2.4.1（实测：10 引擎 / 64 步 / 4 轨 / 61 轨道参数）
      （2.3 文档为 9 引擎 / 58 参数，已过时）

⚠️ 与 Felucca 的关键差异：
  - 命令 33 = DRUM_STEP（Felucca 是 SONG）
  - 写步无 chance 字节
  - 鼓轨用专用 DRUM_STEP 命令
  - INFO trailer = [ntrk, flag]（2.4.1 实测 [4, 9]；4=ntrk，9 为独立 flag）
"""

import ctypes
import time
from ctypes import wintypes

# ---------- winmm 常量 ----------
CALLBACK_FUNCTION = 0x00030000
MIM_LONGDATA = 0x3C4        # ⚠️ 不是 0x3C6
MHDR_DONE = 0x00000001

# ---------- 命令枚举 ----------
CMD_INFO = 1
CMD_GET = 2
CMD_SET = 3
CMD_DESC = 5
CMD_STEP_GET = 6
CMD_STEP_SET = 7
CMD_PRESET = 8
CMD_PROJECT = 9
CMD_NAMES = 10
CMD_TRACK = 27
CMD_TRACK_MIX = 28
CMD_TRACK_DUMP = 29
CMD_TRACK_STEP = 30
CMD_TRACK_PARAM = 31
CMD_DRUM_STEP = 33       # ⚠️ SLOOP：鼓轨专用（Felucca 是 SONG）
CMD_BK = 34

HDR = [0x7D, 0x46, 0x4C]

# ---------- 轨道参数 ID（2.4.1 实测 61 个：0-60） ----------
P_LVL, P_ATK, P_DEC, P_SUS, P_REL = 0, 1, 2, 3, 4
P_FLT, P_PIT, P_SHP, P_TRIM = 5, 6, 7, 8
P_LFO1_RATE, P_LFO1_WAVE, P_LFO1_PHS, P_LFO1_FADE = 9, 10, 11, 12
P_LFO2_PIT, P_LFO2_FLT, P_LFO2_SHP, P_LFO2_AMP = 13, 14, 15, 16
P_ARP_MODE, P_ARP_RATE, P_ARP_OCT, P_ARP_GATE = 17, 18, 19, 20
P_ARP_SWG, P_ARP_PROB, P_ARP_HOLD, P_ARP_ORD = 21, 22, 23, 24
P_SCL_ROOT, P_SCL, P_QNT, P_TRN = 25, 26, 27, 28
P_LEN, P_DIV, P_SWG, P_GATE = 29, 30, 31, 32
P_DST, P_CHO, P_DLY, P_REV = 33, 34, 35, 36
P_VCE, P_GLD, P_PAN, P_MUTE = 37, 38, 39, 40
P_GLMOD, P_PRIO, P_ALLOC, P_DTUNE, P_SLCR = 41, 42, 43, 44, 45
P_PAT, P_RATE, P_DEPTH, P_CHORD = 46, 47, 48, 49
# ⚠️ 2.4.1 实测（desc 全量扫描）：50-60 与 2.3 文档完全不同！
P_FILT   = 50    # 2.4.1 实测 label=FILT（2.3 文档误作"预设号 P_E0"）
P_STRUM  = 51    # 实测 label=STRUM（-60..60）
P_VLEAD  = 52    # 实测 label=VLEAD（0..1）
P_KIT    = 53    # ⚠️ 鼓组参数！实测 label=KIT（0..41，42 组）；鼓轨当前值=5=808
# 引擎编辑参数（实测 54-60，2.3 文档的 51-57 整体后移 3 位）
P_E_DTN, P_E_MIX, P_E_NOIS, P_E_CUT = 54, 55, 56, 57
P_E_RES, P_E_DRV, P_E_KTR = 58, 59, 60

# ---------- 全局参数 ID（32 个） ----------
G_BPM, G_SWING, G_CLICK, G_TUNE, G_TIME = 0, 1, 2, 3, 4
G_DLY_FDBK, G_DLY_COLR, G_DLY_MIX, G_DLY_SIZE, G_DLY_DAMP = 5, 6, 7, 8, 9
G_CRT, G_CDP, G_MIDI, G_SYNC, G_ROUT = 10, 11, 12, 13, 14
G_CPU, G_SLOT, G_NAME, G_LOAD, G_SAVE = 15, 16, 17, 18, 19
G_ENG, G_SET, G_CLRSQ, G_INIT = 20, 21, 22, 23
G_CH, G_LVL, G_REV, G_DUST, G_DUCK = 24, 25, 26, 27, 28
G_FILT, G_ROLL, G_NEW = 29, 30, 31

# ---------- 枚举 ----------
# ⚠️ 2.4.1 实测 10 引擎（含 FM6）；2.3 文档只有 9 个
ENGINES = {
    'ANALOG': 0, 'DIGITAL': 1, 'PHASE': 2, 'LOFI': 3, 'SAMPLE': 4,
    'VOICE': 5, 'TRIO': 6, 'WHEEL': 7, 'GRAIN': 8, 'FM6': 9,
}
ENGINE_NAMES = {v: k for k, v in ENGINES.items()}

DIVS = {'1/4': 0, '1/8': 1, '1/16': 2, '1/32': 3, '8T': 4, '16T': 5}
DIV_NAMES = {v: k for k, v in DIVS.items()}

TIME_NOTE, TIME_TIE, TIME_REST = 0, 1, 2

DRUM_LANES = {
    0:  ('KICK',    36),
    1:  ('KICK2',   35),
    2:  ('SNARE',   38),
    3:  ('CLAP',    39),
    4:  ('CHH',     42),
    5:  ('OPENHAT', 46),
    6:  ('PEDAL',   44),
    7:  ('RIM',     37),
    8:  ('SNARE2',  40),
    9:  ('LOWTOM',  43),
    10: ('HITOM',   48),
    11: ('CRASH',   49),
    12: ('RIDE',    51),
    13: ('SHAKER',  70),
    14: ('CONGA',   63),
    15: ('COWBELL', 56),
}
LANE_BY_NAME = {name: idx for idx, (name, _) in DRUM_LANES.items()}

# ⚠️ 2.4.1 实测 KIT 参数范围 0..41（42 组），下表为 2.3 文档的 37 组（0-36），
# 37-41 名称未知，待 NAMES/DESC 补充
KITS = {
    'ACOUSTIC': 0, 'DEEP': 1, 'TIGHT': 2, 'BRIGHT': 3, 'DUST': 4,
    '808': 5, '909': 6, '606': 7, '80S': 8, 'VINTAGE': 9,
    'TRAP': 10, 'DRILL': 11, 'BOOMBAP': 12, 'LO-FI': 13, 'PHONK': 14,
    'HOUSE': 15, 'D.HOUSE': 16, 'TECHNO': 17, 'MINIMAL': 18, 'ELECTRO': 19,
    'DISCO': 20, 'GARAGE': 21, 'JUNGLE': 22, 'DUBSTEP': 23, 'DEMBOW': 24,
    'AMAPIANO': 25, 'AFRO': 26, 'LATIN': 27, 'TRIBAL': 28, 'SYNTHWV': 29,
    'CHIP': 30, 'ARCADE': 31, 'GLITCH': 32, 'INDUSTR': 33, 'HYPER': 34,
    'AMBIENT': 35, 'JAZZ': 36,
}

DRUM_LEVELS = {'NORM': 0, 'GHOST': 1, 'SOFT': 2, 'HARD': 3}

# ---------- winmm 结构体 ----------
class MIDIHDR(ctypes.Structure):
    """⚠️ 与 felucca_link.py 逐字段一致（实测这是唯一能稳定收全帧的声明）。
    lpData 用 c_void_p、dwUser/reserved 用 c_ulonglong，共 88B。"""
    _fields_ = [
        ("lpData", ctypes.c_void_p),
        ("dwBufferLength", wintypes.DWORD),
        ("dwBytesRecorded", wintypes.DWORD),
        ("dwUser", ctypes.c_ulonglong),
        ("dwFlags", wintypes.DWORD),
        ("lpNext", ctypes.c_void_p),
        ("reserved", ctypes.c_ulonglong),
        ("dwOffset", wintypes.DWORD),
        ("dwReserved", ctypes.c_void_p * 4),
    ]

class MIDIINCAPS(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD), ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * 32),
        ("dwSupport", wintypes.DWORD),
    ]

class MIDIOUTCAPS(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD), ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * 32),
        ("wTechnology", wintypes.WORD),
        ("wVoices", wintypes.WORD), ("wNotes", wintypes.WORD),
        ("wChannelMask", wintypes.WORD),
        ("dwSupport", wintypes.DWORD),
    ]

# ---------- winmm 绑定 ----------
winmm = ctypes.WinDLL('winmm')

winmm.midiInGetNumDevs.restype = wintypes.UINT
winmm.midiInGetDevCapsW.argtypes = [wintypes.UINT, ctypes.POINTER(MIDIINCAPS), wintypes.UINT]
winmm.midiInGetDevCapsW.restype = wintypes.UINT
winmm.midiInOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.UINT,
                             ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]
winmm.midiInOpen.restype = wintypes.UINT
winmm.midiInClose.argtypes = [wintypes.HANDLE]
winmm.midiInStart.argtypes = [wintypes.HANDLE]
winmm.midiInStop.argtypes = [wintypes.HANDLE]
winmm.midiInReset.argtypes = [wintypes.HANDLE]
winmm.midiInPrepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiInPrepareHeader.restype = wintypes.UINT
winmm.midiInAddBuffer.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiInAddBuffer.restype = wintypes.UINT
winmm.midiInUnprepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]

winmm.midiOutGetNumDevs.restype = wintypes.UINT
winmm.midiOutGetDevCapsW.argtypes = [wintypes.UINT, ctypes.POINTER(MIDIOUTCAPS), wintypes.UINT]
winmm.midiOutGetDevCapsW.restype = wintypes.UINT
winmm.midiOutOpen.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.UINT,
                              ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]
winmm.midiOutOpen.restype = wintypes.UINT
winmm.midiOutClose.argtypes = [wintypes.HANDLE]
winmm.midiOutPrepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiOutPrepareHeader.restype = wintypes.UINT
winmm.midiOutLongMsg.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]
winmm.midiOutLongMsg.restype = wintypes.UINT
winmm.midiOutUnprepareHeader.argtypes = [wintypes.HANDLE, ctypes.POINTER(MIDIHDR), wintypes.UINT]

# ---------- 设备枚举 ----------
def list_inputs():
    n = winmm.midiInGetNumDevs()
    out = []
    for i in range(n):
        caps = MIDIINCAPS()
        if winmm.midiInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            out.append((i, caps.szPname))
    return out

def list_outputs():
    n = winmm.midiOutGetNumDevs()
    out = []
    for i in range(n):
        caps = MIDIOUTCAPS()
        if winmm.midiOutGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            out.append((i, caps.szPname))
    return out

def find_felucca():
    in_idx = next((i for i, name in list_inputs() if 'felucca' in name.lower()), None)
    out_idx = next((i for i, name in list_outputs() if 'felucca' in name.lower()), None)
    return in_idx, out_idx

# ---------- 编码 ----------
def v14enc(v):
    x = v + 8192
    return [x & 0x7F, (x >> 7) & 0x7F]

def v14dec(lo, hi):
    return (lo + (hi << 7)) - 8192

def g7(x, n):
    out = []
    for _ in range(n):
        out.append(x & 0x7F)
        x >>= 7
    return out

def ung7(arr):
    x = 0
    for i, b in enumerate(arr):
        x |= (b & 0x7F) << (7 * i)
    return x

def build_frame(cmd, args):
    return bytes([0xF0] + HDR + [(cmd & 0x7F)] + list(args) + [0xF7])

def drum_pack(lanes, levels=None, ratchets=None):
    on = 0
    for l in lanes:
        on |= (1 << l)
    lv = 0
    if levels:
        for l, v in levels.items():
            lv |= (v & 3) << (2 * l)
    rt = 0
    if ratchets:
        for l, v in ratchets.items():
            rt |= ((v - 1) & 3) << (2 * l)
    return g7(on, 3), g7(lv, 5), g7(rt, 5)

def drum_unpack(on3, lv5, rt5):
    on = ung7(on3)
    lv = ung7(lv5)
    rt = ung7(rt5)
    lanes = [l for l in range(16) if (on >> l) & 1]
    levels = {l: (lv >> (2 * l)) & 3 for l in lanes}
    ratchets = {l: ((rt >> (2 * l)) & 3) + 1 for l in lanes}
    return lanes, levels, ratchets

# ---------- 连接 ----------
class SloopLink:
    def __init__(self):
        self.h_in = None
        self.h_out = None
        self._rx_queue = []
        self._rx_acc = bytearray()   # 累积未切帧的输入字节（按 F7 切完整帧）
        self._in_buf = None
        self._in_hdr = None
        self._cb_ref = None

    def open(self):
        in_idx, out_idx = find_felucca()
        if in_idx is None or out_idx is None:
            raise RuntimeError('未找到 Felucca MIDI 设备。请确认 FM-1 已连接，且浏览器/Web MIDI 已关闭。')

        # ---- 输入 ----
        h = wintypes.HANDLE()
        self._in_buf = ctypes.create_string_buffer(8192)
        # ⚠️ 位置式构造，逐字段与 felucca_link.py 一致（实测稳定收全帧的关键）
        self._in_hdr = MIDIHDR(ctypes.addressof(self._in_buf), 8192, 0, 0, 0, 0, 0, 0,
                               (ctypes.c_void_p * 4)())

        # ⚠️ winmm 回调必须是 5 参数
        # void CALLBACK MidiInProc(HMIDIIN, UINT, DWORD_PTR, DWORD_PTR, DWORD_PTR)
        CB = ctypes.WINFUNCTYPE(None,
                                wintypes.HANDLE,     # hMidiIn
                                wintypes.UINT,       # wMsg
                                ctypes.c_void_p,     # dwInstance
                                ctypes.c_void_p,     # dwParam1 (MIDIHDR*)
                                ctypes.c_void_p)     # dwParam2

        def _cb(hMidiIn, wMsg, dwInstance, dwParam1, dwParam2):
            if wMsg == MIM_LONGDATA:
                hdr_ptr = ctypes.cast(dwParam1, ctypes.POINTER(MIDIHDR))
                hdr = hdr_ptr.contents
                if hdr.dwBytesRecorded > 0:
                    data = ctypes.string_at(hdr.lpData, hdr.dwBytesRecorded)
                    # ⚠️ 必须累积并按 F7 切完整帧：设备会连续推多帧
                    # （如选轨后的 TRACK 通知 rc=27 + 真正的回复帧）
                    self._rx_acc += data
                    while True:
                        i = self._rx_acc.find(bytes([0xF7]))
                        if i < 0:
                            break
                        frame = bytes(self._rx_acc[:i + 1])
                        del self._rx_acc[:i + 1]
                        self._rx_queue.append(frame)
                winmm.midiInAddBuffer(self.h_in, hdr_ptr, ctypes.sizeof(MIDIHDR))
        self._cb_ref = CB(_cb)

        rc = winmm.midiInOpen(ctypes.byref(h), in_idx,
                              ctypes.cast(self._cb_ref, ctypes.c_void_p), None, CALLBACK_FUNCTION)
        if rc != 0:
            raise RuntimeError(f'midiInOpen 失败: {rc}')
        self.h_in = h
        winmm.midiInPrepareHeader(self.h_in, ctypes.byref(self._in_hdr), ctypes.sizeof(MIDIHDR))
        winmm.midiInAddBuffer(self.h_in, ctypes.byref(self._in_hdr), ctypes.sizeof(MIDIHDR))
        winmm.midiInStart(self.h_in)

        # ---- 输出 ----
        h = wintypes.HANDLE()
        rc = winmm.midiOutOpen(ctypes.byref(h), out_idx, None, None, 0)
        if rc != 0:
            winmm.midiInClose(self.h_in)
            raise RuntimeError(f'midiOutOpen 失败: {rc}')
        self.h_out = h
        return self

    def close(self):
        """⚠️ 不要调用 midiInReset：在有 pending buffer 时会与回调线程死锁（实测必现）。
        与 felucca_link.py 一致：Stop → UnprepareHeader → Close。"""
        if self.h_in:
            try:
                winmm.midiInStop(self.h_in)
            except Exception:
                pass
            try:
                winmm.midiInUnprepareHeader(self.h_in, ctypes.byref(self._in_hdr), ctypes.sizeof(MIDIHDR))
            except Exception:
                pass
            winmm.midiInClose(self.h_in)
            self.h_in = None
        if self.h_out:
            winmm.midiOutClose(self.h_out)
            self.h_out = None

    def send(self, frame: bytes):
        buf = ctypes.create_string_buffer(frame)  # ⚠️ 带 NUL，与 felucca_link 一致
        hdr = MIDIHDR(ctypes.addressof(buf), len(frame), 0, 0, 0, 0, 0, 0,
                      (ctypes.c_void_p * 4)())
        winmm.midiOutPrepareHeader(self.h_out, ctypes.byref(hdr), ctypes.sizeof(MIDIHDR))
        winmm.midiOutLongMsg(self.h_out, ctypes.byref(hdr), ctypes.sizeof(MIDIHDR))
        for _ in range(400):
            if hdr.dwFlags & MHDR_DONE:
                break
            time.sleep(0.005)
        winmm.midiOutUnprepareHeader(self.h_out, ctypes.byref(hdr), ctypes.sizeof(MIDIHDR))

    def send_cmd(self, cmd, args):
        self.send(build_frame(cmd, args))

    def _poll_rx(self, timeout=1.0):
        end = time.time() + timeout
        while time.time() < end:
            if self._rx_queue:
                return self._rx_queue.pop(0)
            time.sleep(0.01)
        return None

    def request(self, cmd, args, timeout=2.0):
        """发命令并等 rc==cmd 的完整回复帧。跳过其它推送帧（如选轨后的 TRACK 通知 rc=27）。"""
        self._rx_queue.clear()
        self.send_cmd(cmd, args)
        end = time.time() + timeout
        while time.time() < end:
            fr = self._poll_rx(max(0.02, min(0.2, end - time.time())))
            if fr is None:
                continue
            if len(fr) < 6 or fr[0] != 0xF0 or fr[-1] != 0xF7 or fr[1:4] != bytes(HDR):
                continue
            if fr[4] == (cmd & 0x7F):
                return fr
        return None

    # ---- 高层 API ----
    def info(self):
        """解析 INFO 回复。SLOOP 2.4.1 实测：
        version='FELUCCA SLOOP 2.4.1', nengines=10, pcount=61, gcount=32,
        nstep=64, pe0=53, ntrk=4, trailer=[4, 9]

        trailer = [ntrk, flag]；trailer[0]=ntrk；trailer[1] 是独立 flag 字节。
        （2.3 文档的 trailer=[4,6] 中 6 也是 flag，不是 ntrk。）
        """
        r = self.request(CMD_INFO, [])
        if not r or len(r) < 6:
            return None
        body = list(r[5:-1])
        try:
            z = body.index(0x00)
        except ValueError:
            return {'raw': body}
        version = bytes(body[:z]).decode('ascii', errors='replace')
        p = body[z+1:]
        out = {'version': version}
        if len(p) >= 5:
            out['nengines'] = p[0]
            out['pcount']   = p[1]
            out['gcount']   = p[2]
            out['nstep']    = p[3]
            out['pe0']      = p[4]
        rest = p[5:]
        i = 0
        want = out.get('nengines', 0)
        for _ in range(want):
            try:
                zz = rest.index(0x00, i)
            except ValueError:
                break
            i = zz + 1
        trailer = rest[i:]
        out['trailer_raw'] = list(trailer)
        if len(trailer) >= 1:
            out['ntrk'] = trailer[0]
        if len(trailer) >= 2:
            out['flag'] = trailer[1]
        return out

    def desc(self, scope, pid):
        r = self.request(CMD_DESC, [scope, pid])
        if not r or len(r) < 11:
            return None
        b = list(r[5:-1])
        if len(b) < 11:
            return None
        scope_, id_, fmt = b[0], b[1], b[2]
        mn = v14dec(b[3], b[4])
        mx = v14dec(b[5], b[6])
        dv = v14dec(b[7], b[8])
        i = 9
        try:
            z1 = b.index(0x00, i)
            label = bytes(b[i:z1]).decode('ascii', 'replace')
            i = z1 + 1
            z2 = b.index(0x00, i)
            unit = bytes(b[i:z2]).decode('ascii', 'replace')
        except ValueError:
            label, unit = '', ''
        return {'scope': scope_, 'id': id_, 'fmt': fmt,
                'min': mn, 'max': mx, 'def': dv,
                'label': label, 'unit': unit}

    def names(self, engine):
        r = self.request(CMD_NAMES, [engine], timeout=3.0)
        if not r:
            return []
        body = list(r[5:-1])
        out = []
        i = 0
        while i < len(body):
            try:
                z = body.index(0x00, i)
            except ValueError:
                break
            s = bytes(body[i:z]).decode('ascii', 'replace')
            if s:
                out.append(s)
            i = z + 1
        return out

    def select_track(self, track):
        self.send_cmd(CMD_TRACK, [track])

    def query_tracks(self):
        return self.request(CMD_TRACK, [], timeout=2.0)

    def preset(self, engine, preset):
        self.send_cmd(CMD_PRESET, [engine, preset])

    def set_kit(self, kit_num):
        """⚠️ 2.4.1 实测鼓组参数 = id 53 (KIT)，不是文档的 P_E0=50！
        实测：tr3 id=53 当前值=5(808)；写 36(JAZZ) 读回=36；id=50 是 FILT 与鼓组无关。"""
        self.select_track(3)
        time.sleep(0.1)
        self.track_param(3, P_KIT, kit_num)

    def save_section(self, section):
        self.send_cmd(CMD_PROJECT, [1, section])

    def load_section(self, section):
        self.send_cmd(CMD_PROJECT, [0, section])

    def query_section(self, section):
        r = self.request(CMD_PROJECT, [2, section])
        if not r or len(r) < 8:
            return None
        b = list(r[5:-1])
        return {'op': b[0], 'slot': b[1], 'used': b[2]}

    def track_param(self, track, pid, value=None):
        if value is None:
            r = self.request(CMD_TRACK_PARAM, [track, pid])
            if not r or len(r) < 8:
                return None
            b = list(r[5:-1])
            return v14dec(b[2], b[3])
        self.send_cmd(CMD_TRACK_PARAM, [track, pid] + v14enc(value))

    def set_global(self, pid, value):
        self.send_cmd(CMD_SET, [1, pid] + v14enc(value))

    def track_dump(self, track):
        """
        读轨道全参数。回复 119B：
          body = [tr, engine, preset, p[0].lo, p[0].hi, p[1].lo, p[1].hi, ...]
        头 3B = [tr, engine, preset] 单字节；
        p = 58 × (lo,hi) v14 对，必须 v14dec(lo,hi)。
        """
        r = self.request(CMD_TRACK_DUMP, [track], timeout=3.0)
        if not r:
            return None
        body = list(r[5:-1])
        if len(body) < 3:
            return None
        tr, engine, preset = body[0], body[1], body[2]
        p_raw = body[3:]
        p = []
        for i in range(0, len(p_raw) - 1, 2):
            p.append(v14dec(p_raw[i], p_raw[i+1]))
        return {'track': tr, 'engine': engine, 'preset': preset, 'p': p}

    # ---- 合成器轨写步 ----
    def write_step(self, track, step, notes, time_mode=TIME_NOTE,
                   velocity=100, flags=0):
        n = min(len(notes), 4)
        nb = [0] * 4
        for i, p in enumerate(notes[:4]):
            nb[i] = int(p)
        args = [track, step, n] + nb + [time_mode, flags, velocity]
        self.send_cmd(CMD_TRACK_STEP, args)

    def read_step(self, track, step):
        """
        读合成器步。回复 12B：
          body = [i, n, notes4, time, flags, vel, lvl, hi, rat]
        ⚠️ 2.4.1 实测（12 组 flags×vel 组合）：合成器轨的 lvl(b[9])/hi(b[10])/rat(b[11])
        恒为 0，协议写步无入口可产生非零值 → bit7 扩展解码（lvl=b[9]|((b[10]&1)<<7) 等）
        未经高值样本验证，遇非零样本时按此推断解析，并建议再实测确认。
        flags 正确落在 b[7]（1=accent 2=slide），vel 在 b[8]。
        """
        self.select_track(track)
        time.sleep(0.08)
        r = self.request(CMD_STEP_GET, [step])
        if not r or len(r) < 6:
            return None
        b = list(r[5:-1])
        if len(b) < 9:
            return None
        lvl = 0
        rat = 0
        if len(b) >= 12:
            lvl = b[9] | ((b[10] & 1) << 7)
            rat = b[11] | (((b[10] >> 1) & 1) << 7)
        return {
            'i': b[0], 'n': b[1],
            'notes': b[2:6],
            'time': b[6], 'flags': b[7], 'vel': b[8],
            'lvl': lvl, 'rat': rat,
            'raw': b,
        }

    # ---- 鼓轨写步 ----
    def write_drum_step(self, step, lanes, levels=None, ratchets=None):
        on3, lv5, rt5 = drum_pack(lanes, levels, ratchets)
        args = [step] + on3 + lv5 + rt5
        self.send_cmd(CMD_DRUM_STEP, args)

    def read_drum_step(self, step):
        """
        读鼓步。回复 14B：
          body = [i, on3B, lv5B, rt5B]
        实测：on = 17 + 32×128 = 4113 = KICK(bit0)+CHH(bit4)+RIDE(bit12)
        """
        self.select_track(3)
        time.sleep(0.08)
        r = self.request(CMD_DRUM_STEP, [step])
        if not r or len(r) < 6:
            return None
        b = list(r[5:-1])
        if len(b) < 14:
            return None
        lanes, levels, ratchets = drum_unpack(b[1:4], b[4:9], b[9:14])
        return {
            'i': b[0],
            'lanes': lanes,
            'levels': levels,
            'ratchets': ratchets,
            'raw': b,
        }