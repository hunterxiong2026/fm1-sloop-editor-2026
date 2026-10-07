---
name: fm1-sloop-editor
version: 1.0.0
author: hunterxiong2026
license: MIT
description: "通过直连 SysEx（ctypes + winmm）操作 M-VAVE FM-1 的 SLOOP 2.3 固件，实现 4 轨编曲、鼓组写入、预设切换与项目槽位管理。播放由设备 PLAY 键触发。"
keywords:
  - fm1
  - sloop
  - m-vave
  - sysex
  - winmm
  - ctypes
  - synthesizer
  - groovebox
  - drum-machine
categories:
  - music
  - automation
  - hardware-integration
triggers:
  - "用 SLOOP 编一段"
  - "调整 SLOOP 音色"
  - "写一段鼓点"
  - "换 SLOOP 预设"
  - "存到 section A/B/C/D"
requirements:
  - name: m-vave-fm1
    type: hardware
    optional: false
  - name: sloop-firmware
    type: firmware
    version: "2.3"
    optional: false
  - name: python
    type: runtime
    version: "3.10+"
    optional: false
  - name: windows
    type: platform
    optional: false
platforms:
  - windows
---

# SLOOP Editor Skill

## 概述
通过直连 SysEx 协议操控 FM-1 上的 SLOOP 2.3 固件。协议族与 Felucca 相同
（帧头 `F0 7D 46 4C ...`），但命令号与写步布局有差异。SLOOP 是 4 轨 Groovebox
（3 合成器轨 + 1 专用鼓机轨），播放由设备 PLAY 键触发。

## 何时使用
- 用户要求写一段编曲（旋律/和弦/贝斯/鼓）
- 用户要求修改音色参数（滤波器、包络、LFO、琶音等）
- 用户要求切换预设或鼓组
- 用户要求存/读 section A-D

## 前置条件
1. **独立 venv**：`scripts/venv/`，绝不装任何包进系统
2. **FM-1 空闲**：直连前必须关闭浏览器/任何 Web MIDI 会话（设备输入独占）
3. **设备名**：MIDI 设备名为 `Felucca`（输出 idx=1 / 输入 idx=0）
4. **固件版本**：FELUCCA SLOOP 2.3（9 引擎 / 64 步 / 4 轨）

## 脚本清单

| 脚本 | 作用 |
|---|---|
| `sloop_link.py` | 直连核心库（设备枚举 / open / send / INFO·DESC·STEP·DRUM_STEP 解析） |
| `sloop_cli.py` | 命令行工具：`info` `desc` `names` `readstep` `drumread` `preset` `kit` `readparam` `setparam` `dump` `save` `restore` |
| `sloop_arrange.py` | 单槽一键：读 JSON → 写 4 轨（含鼓轨）→ 设 BPM/SWG → 存 section → 提示 PLAY |

## 协议核心

### 帧格式
```
F0 7D 46 4C <cmd & 0x7F> <args...> F7
```
HDR = `7D 46 4C`。设备回复同帧头。

### v14 编码（参数值）
```
v14enc(v) = v + 8192 → [lo & 0x7F, (lo >> 7) & 0x7F]
v14dec(lo, hi) = (lo + (hi << 7)) - 8192
```

### 命令枚举
| 命令 | 值 | SLOOP 说明 |
|---|---|---|
| INFO | 1 | 设备信息 |
| GET / SET | 2 / 3 | SET: `[scope, id, v14lo, v14hi]` |
| DESC | 5 | `[scope, id]`；scope 0=轨道 1=全局 |
| STEP_GET / STEP_SET | 6 / 7 | 步读/写（作用于当前选中轨，先 TRACK [tr]） |
| PRESET | 8 | `[engine, preset_in_engine]`（引擎内序号） |
| PROJECT | 9 | op 0=load 1=save 2=query；**槽 0-3 = song sections A-D** |
| NAMES | 10 | `[engine]` → 读该引擎全部预设名（权威来源） |
| TRACK | 27 | `[]` = 查询全部轨；`[tr]` = 选择 |
| TRACK_MIX | 28 | `[tr, v14(level), mute]` |
| TRACK_DUMP | 29 | `[tr]` → 全参数 dump |
| TRACK_STEP | 30 | 写步 `[tr, i, n, notes4, time, flags, vel]`（**无 chance**） |
| TRACK_PARAM | 31 | 读 `[tr, id]` / 写 `[tr, id, v14lo, v14hi]` |
| **DRUM_STEP** | **33** | **鼓轨专用**：读 `[i]` / 写 `[i, on(3B), lv(5B), rt(5B)]`（先 TRACK [3]） |
| BK_* | 34-36 | v6 备份/恢复（未用） |

**⚠️ 与 Felucca 的关键差异**：SLOOP 命令 33 = DRUM_STEP，**没有 SONG 播放命令**。
`SONG [0]/[2]` 会被当成 DRUM_STEP 读步（回复看似"状态"实为鼓步数据）。

### TRACK_STEP 写步布局（合成器轨）
```
写步：[tr, i, n, note0..3, time, flags, vel]
读步(STEP_GET 6)：[i]  ← 只带步索引！先发 TRACK [tr] 选轨
回复：[i, n, note0..3, time, flags, vel, lvl, hi, rat]（12B）
```
- `tr`=轨道 0-3；`i`=步索引 0-63；`n`=音符数 0-4
- `time`：0=NOTE 1=TIE 2=REST
- `flags`：1=accent 2=slide
- `vel`=力度 0-127
- **无 chance 字节**（Felucca 版多带 4 字节会让 n/notes/time 全错位）
- **后 3B 解码**（2026-10-07 实测）：
  ```
  lvl = b[9] | ((b[10] & 1) << 7)
  rat = b[11] | (((b[10] >> 1) & 1) << 7)
  ```
  写步不带 ext 时 lvl/rat 回 0。

### TIE 语义（关键）
- `time=1` 延续**最近一个 NOTE 起始步**的音符
- 整段全 TIE 无 NOTE 起始 = 静音
- 写长音 = 首步 `time=0` + 后续步 `time=1`

### DRUM_STEP 写鼓步（v5）
```
写：[i, ...g7(on,3), ...g7(lv,5), ...g7(rt,5)]
读：[i]
回复（14B）：[i, on(3B), lv(5B), rt(5B)]
```
- `on` = 16bit lane 掩码（lane l = bit l）
- `lv` = Σ(lvl[l]&3) * 4^l；lvl 枚举：0=NORM 1=GHOST 2=SOFT 3=HARD
- `rt` = Σ(rat[l]&3) * 4^l（ratchet 1-4 次）
- `g7(x,n)` = 每 7bit 一段取低 n 字节

**实测读回**：
```
f0 7d 46 4c 21 00 11 20 00 00 00 00 00 00 00 00 00 00 00 f7
body = [0, 17, 32, 0,0,0,0,0, 0,0,0,0,0]
       i  on3B        lv5B       rt5B
```
`on = 17 + 32×128 = 4113` = lanes 0(KICK) + 4(CHH) + 12(RIDE)

### 鼓轨 lane → GM 音
```
0=KICK(36)   1=KICK2(35)  2=SNARE(38)  3=CLAP(39)
4=CHH(42)    5=OPEN HAT(46) 6=PEDAL(44) 7=RIM(37)
8=SNARE2(40) 9=LOW TOM(43) 10=HI TOM(48) 11=CRASH(49)
12=RIDE(51)  13=SHAKER(70) 14=CONGA(63)  15=COWBELL(56)
```

## 参数 ID

### 轨道参数（TRACK_PARAM，58 个）
```
LVL=0  ATK=1  DEC=2  SUS=3  REL=4  FLT=5  PIT=6  SHP=7  TRIM=8
LFO1: RATE=9 WAVE=10 PHS=11 FADE=12
LFO2: PIT=13 FLT=14 SHP=15 AMP=16
ARP:  MODE=17 RATE=18 OCT=19 GATE=20 SWG=21 PROB=22 HOLD=23 ORD=24
SCL:  ROOT=25 SCL=26 QNT=27 TRN=28
LEN=29  DIV=30  SWG=31  GATE=32
DST=33  CHO=34  DLY=35  REV=36
VCE=37  GLD=38  PAN=39  MUTE=40
GLMOD=41  PRIO=42  ALLOC=43  DTUNE=44  SLCR=45
PAT=46(1-16,def=1)  RATE=47  DEPTH=48  CHORD=49
P_E0=50（当前预设号；鼓轨 = KIT 鼓组号）
引擎编辑参数 51-57（ANALOG: DTN MIX NOIS CUT RES DRV KTR）
```

### 全局参数（SET scope=1，32 个）
```
BPM=0(40-240)  SWING=1  CLICK=2  TUNE=3  TIME=4
DLY: FDBK=5 COLR=6 MIX=7 SIZE=8 DAMP=9
CRT=10  CDP=11  MIDI=12  SYNC=13  ROUT=14
CPU=15  SLOT=16  NAME=17  LOAD=18  SAVE=19
ENG=20（当前轨引擎选择）  SET=21  CLRSQ=22  INIT=23
CH=24  LVL=25  REV=26  DUST=27  DUCK=28  FILT=29  ROLL=30  NEW=31
```

### 枚举
```
DIV/TIME（SLOOP 只有 6 个）: 0=1/4  1=1/8  2=1/16  3=1/32  4=8T  5=16T
ENG: ANALOG=0 DIGITAL=1 PHASE=2 LOFI=3 SAMPLE=4
     VOICE=5 TRIO=6 WHEEL=7 GRAIN=8
     （无 DRUM/FM6/NOISE/SLICE；鼓走第 4 轨专用）
```

### 预设名（NAMES 实测，权威）
完整表格见 `reference/sloop-sysex-map.md`。注意 **mock 预设表顺序不可信**，
以 `NAMES [engine]` 读回的为准。例如真实 ANALOG WARM PAD = **13**，不是 mock 里的 9。

**ANALOG 常用**：
```
0=808 BOOM  2=SUB BASS  4=ACID 303  6=REESE  9=G-FUNK LD
12=SUPERSAW  13=WARM PAD  15=ATMOS PAD
```

### 鼓组 KIT（37 组，TRACK_PARAM [3, 50, v14(kit)]）
```
0=ACOUSTIC 1=DEEP 2=TIGHT 3=BRIGHT 4=DUST 5=808 6=909 7=606
8=80S 9=VINTAGE 10=TRAP 11=DRILL 12=BOOMBAP 13=LO-FI 14=PHONK
15=HOUSE 16=D.HOUSE 17=TECHNO 18=MINIMAL 19=ELECTRO 20=DISCO
21=GARAGE 22=JUNGLE 23=DUBSTEP 24=DEMBOW 25=AMAPIANO 26=AFRO
27=LATIN 28=TRIBAL 29=SYNTHWV 30=CHIP 31=ARCADE 32=GLITCH
33=INDUSTR 34=HYPER 35=AMBIENT 36=JAZZ
```

## 操控流程

### 单轨写入
```
python sloop_arrange.py <section> <bpm> <swing>
# 读 arrangement.json → 写 4 轨（含鼓轨）→ 存 section → 提示按 PLAY
```

### 命令行速查
```
python sloop_cli.py info                       # 设备信息
python sloop_cli.py names <engine>             # 读引擎预设名
python sloop_cli.py preset <tr> <engine> <p>   # 切预设
python sloop_cli.py kit <kit_num>              # 切鼓组
python sloop_cli.py readstep <tr> <step>       # 读合成器步
python sloop_cli.py drumread <step>            # 读鼓步
python sloop_cli.py readparam <tr> <pid>       # 读轨道参数
python sloop_cli.py setparam <tr> <pid> <val>  # 写轨道参数
python sloop_cli.py dump <tr>                  # 读该轨全参数
python sloop_cli.py save <section>             # 存 section
```

### 播放验收
- **SLOOP 无自动播放命令**。写入并保存后，提示用户**按设备 PLAY 键**。
- 以实际听声为准。

## INFO 解析要点（实测校准）

```
version(\0串) nengines(1B) pcount(1B) gcount(1B) nstep(1B) pe0(1B)
engines×nengines(\0串) trailer[ntrk(1B), flag(1B)]
```
- SLOOP 的 trailer = **`[ntrk, flag]`**，无 chainRows/uiCaps
- `ntrk = trailer[0]`（实测 = 4）
- `flag = trailer[1]`（实测 = 6，独立 flag 字节）
- 实测 trailer：`[4, 6]`
- 版本串是变长 \0 结尾，不是固定 4 字节

## TRACK_DUMP 解析要点（实测校准）

```
回复 119B：body = [tr, engine, preset, p[0].lo, p[0].hi, p[1].lo, p[1].hi, ...]
```
- 头 3B = `[tr, engine, preset]` **单字节**
- `p` = **58 × (lo, hi) v14 对**，必须 `v14dec(lo, hi)` 解码
- 例：`p[0] = v14dec(104, 64) = 104` = LVL

## 直连四坑（勿重踩）
1. **MIDIHDR 的 `dwUser`/`reserved` 字段必须是 8 字节指针**（误写 4 字节 → SysEx 发送永不 DONE）
2. **`MIM_LONGDATA = 0x3C4`**（误写 0x3C6 → 回复被静默丢弃）
3. **winmm 所有函数需显式声明 argtypes**（否则 x64 指针截断）
4. **winmm 回调必须是 5 参数**（`hMidiIn, wMsg, dwInstance, dwParam1, dwParam2`）。
   4 参数定义会让 `hdr_ptr` 收到 `dwInstance=NULL`，导致所有请求收不到回复。

## 用户硬约束
1. **独立 venv，绝不装任何包进系统**
2. 播放验收以实际听声为准（SLOOP 需用户按 PLAY）
3. 修改音色/编曲后直接改文件与设备，不需要输出提示词正文
4. 回复先给一句话总结

## 参考
- `reference/sloop-sysex-map.md`：参数表、预设名、鼓组枚举、lane 映射
- `reference/calibration-2026-10-07.md`：原始帧校准记录
- `examples/sloop-recipes.md`：编曲配方（含 4 轨验收编曲）

## 已知限制
- 仅支持 Windows（依赖 winmm.dll）
- **无自动播放命令**，播放靠设备 PLAY 键
- 贝斯轨音色听感需实测（REESE=6 已验证，SUB BASS=2 偏轻）
- SLOOP 固件为 Beta，刷入有变砖风险