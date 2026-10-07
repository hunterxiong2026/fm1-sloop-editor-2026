# SLOOP 2.3 SysEx 参数映射

> 来源：2026-10-07 实机验证 · 固件 FELUCCA SLOOP 2.3

## 帧格式
```
F0 7D 46 4C <cmd & 0x7F> <args...> F7
```

## v14 编码
```
v14enc(v) = v + 8192 → [lo & 0x7F, (lo >> 7) & 0x7F]
v14dec(lo, hi) = (lo + (hi << 7)) - 8192
```

## 命令枚举

| 命令 | 值 | SLOOP 说明 |
|---|---|---|
| INFO | 1 | 设备信息 |
| GET / SET | 2 / 3 | SET: `[scope, id, v14lo, v14hi]` |
| DESC | 5 | `[scope, id]` |
| STEP_GET / STEP_SET | 6 / 7 | 步读/写（先 TRACK [tr]） |
| PRESET | 8 | `[engine, preset_in_engine]` |
| PROJECT | 9 | 槽 0-3 = song sections A-D |
| NAMES | 10 | `[engine]` → 预设名（权威） |
| TRACK | 27 | `[]` 查询 / `[tr]` 选择 |
| TRACK_MIX | 28 | `[tr, v14(level), mute]` |
| TRACK_DUMP | 29 | `[tr]` → 全参数 dump |
| TRACK_STEP | 30 | 写步 `[tr, i, n, notes4, time, flags, vel]` |
| TRACK_PARAM | 31 | 读 `[tr, id]` / 写 `[tr, id, v14lo, v14hi]` |
| **DRUM_STEP** | **33** | 鼓轨：读 `[i]` / 写 `[i, on3B, lv5B, rt5B]` |

## INFO 回复结构（实测校准）

```
version(\0串) nengines(1B) pcount(1B) gcount(1B) nstep(1B) pe0(1B)
engines×nengines(\0串) trailer[ntrk(1B), flag(1B)]
```

实测：`version='FELUCCA SLOOP 2.3'`, nengines=9, pcount=58, gcount=32,
nstep=64, pe0=50, **trailer=[4, 6]**。

- `ntrk = trailer[0]` = 4
- `flag = trailer[1]` = 6（独立 flag 字节，无 chainRows/uiCaps）

## TRACK_STEP 读步回复（12B，实测校准）

```
请求：TRACK[tr] → STEP_GET[i]
回复：f0 7d 46 4c 06 <body> f7
body = [i, n, notes4, time, flags, vel, lvl, hi, rat]
       b0 b1 b2-b5    b6   b7     b8   b9   b10 b11
```

**实测示例**：
```
f0 7d 46 4c 06 00 01 3c 00 00 00 00 00 64 00 00 00 f7
body = [0, 1, 60, 0,0,0, 0, 0, 100, 0, 0, 0]
       i  n  notes     time flags vel lvl hi rat
```

**后 3B 解码**：
```
lvl = b[9] | ((b[10] & 1) << 7)
rat = b[11] | (((b[10] >> 1) & 1) << 7)
```
写步不带 ext 时 lvl/rat 回 0。TIE 步示例：`body=[1,1,0,0,0,0,1,0,100,0,0,0]`（time=1）。

## DRUM_STEP 读步回复（14B，实测校准）

```
请求：TRACK[3] → DRUM_STEP[i]
回复：f0 7d 46 4c 21 <body> f7
body = [i(1B), on(3B), lv(5B), rt(5B)]
```

**实测示例**：
```
f0 7d 46 4c 21 00 11 20 00 00 00 00 00 00 00 00 00 00 00 f7
body = [0, 17, 32, 0,0,0,0,0, 0,0,0,0,0]
       i  on3B        lv5B       rt5B
```
`on = 17 + 32×128 = 4113` = lanes 0(KICK) + 4(CHH) + 12(RIDE)。

## TRACK_DUMP 回复（119B，实测校准）

```
body = [tr, engine, preset, p[0].lo, p[0].hi, p[1].lo, p[1].hi, ...]
       b0  b1      b2       b3       b4       b5       b6
```
- 头 3B = `[tr, engine, preset]` **单字节**
- `p` = **58 × (lo, hi) v14 对**，必须 `v14dec(lo, hi)` 解码
- 实测：`body = [0, 0, 9, 104,64, 6,64, 70,64, ...]` → `p[0]=v14dec(104,64)=104=LVL`

## 轨道参数（58 个）

| ID | 名称 | 说明 |
|---|---|---|
| 0 | LVL | 轨道电平 |
| 1 | ATK | Attack |
| 2 | DEC | Decay |
| 3 | SUS | Sustain |
| 4 | REL | Release |
| 5 | FLT | 滤波器 |
| 6 | PIT | 音高 |
| 7 | SHP | 形状 |
| 8 | TRIM | 修剪 |
| 9-12 | LFO1 RATE/WAVE/PHS/FADE | LFO1 |
| 13-16 | LFO2 PIT/FLT/SHP/AMP | LFO2 |
| 17-24 | ARP MODE/RATE/OCT/GATE/SWG/PROB/HOLD/ORD | 琶音 |
| 25-28 | SCL ROOT/SCL/QNT/TRN | 音阶 |
| 29 | LEN | 步长 |
| 30 | DIV | 分度 |
| 31 | SWG | 摇摆 |
| 32 | GATE | 门限 |
| 33-36 | DST/CHO/DLY/REV | 发送效果 |
| 37-40 | VCE/GLD/PAN/MUTE | 声音/滑音/声像/静音 |
| 41-45 | GLMOD/PRIO/ALLOC/DTUNE/SLCR | 高级 |
| 46 | PAT | Pattern（1-16, def=1） |
| 47 | RATE | 速率 |
| 48 | DEPTH | 深度 |
| 49 | CHORD | 和弦 |
| 50 | P_E0 | 当前预设号；鼓轨 = KIT |
| 51-57 | 引擎编辑参数 | ANALOG: DTN MIX NOIS CUT RES DRV KTR |

## 全局参数（32 个）

| ID | 名称 | 说明 |
|---|---|---|
| 0 | BPM | 40-240 |
| 1 | SWING | 摇摆 |
| 2 | CLICK | 节拍器 |
| 3 | TUNE | 调音 |
| 4 | TIME | 分度 |
| 5-9 | DLY FDBK/COLR/MIX/SIZE/DAMP | 延迟 |
| 10-11 | CRT/CDP | 滤波 |
| 12-14 | MIDI/SYNC/ROUT | MIDI |
| 15-19 | CPU/SLOT/NAME/LOAD/SAVE | 系统 |
| 20 | ENG | 当前轨引擎 |
| 21-23 | SET/CLRSQ/INIT | 设置 |
| 24-31 | CH/LVL/REV/DUST/DUCK/FILT/ROLL/NEW | 混音与主效果 |

## 引擎（9 个）

| 值 | 名称 | 说明 |
|---|---|---|
| 0 | ANALOG | 虚拟模拟 |
| 1 | DIGITAL | 数字 FM |
| 2 | PHASE | 相位失真 |
| 3 | LOFI | 芯片音乐 |
| 4 | SAMPLE | 采样器 |
| 5 | VOICE | 共振峰 |
| 6 | TRIO | 三振荡器 |
| 7 | WHEEL | 音轮风琴 |
| 8 | GRAIN | 颗粒 |

**注意**：无 DRUM/FM6/NOISE/SLICE；鼓走第 4 轨专用。

## 预设名（NAMES 实测，权威）

### ANALOG (0)
```
0=808 BOOM       1=808 DIRTY     2=SUB BASS      3=808 SLIDE
4=ACID 303       5=PLUGG BASS    6=REESE         7=WOBBLE
8=FUNK BASS      9=G-FUNK LD     10=TRAP PLUCK   11=SYN BRASS
12=SUPERSAW      13=WARM PAD     14=DARK STR     15=ATMOS PAD
```

### DIGITAL (1)
```
0=RHODES   1=DX RHODES  2=WURLI     3=CLAV      4=M1 PIANO
5=AFRO KEYS 6=TRAP BELL  7=MUSIC BOX 8=MARIMBA   9=KALIMBA
10=PLUGG BELL 11=GLASS PAD 12=FM BASS
```

### PHASE (2)
```
0=CZ BASS  1=SOFT KEYS  2=CZ STRING  3=RESO PLUCK  4=CZ BRASS
```

### LOFI (3)
```
0=GAME LEAD  1=GB BASS  2=8BIT ARP  3=CHIP
```

### SAMPLE (4)
```
0=GRAND PNO  1=UP BASS  2=VIBES  3=HORN STAB  4=STRING STB
5=LOFI FLUTE  6=SCRATCH  7=GM KIT  8=DUSTY PNO  9=LOFI KEYS
10=DEEP BASS
```

### VOICE (5)
```
0=CHOIR AAH  1=SOUL OOH  2=TALKBOX  3=WOW BASS  4=VOWL
```

### TRIO (6)
```
0=FAT BASS  1=MIN STAB  2=MIN7 STAB  3=RAVE STAB  4=DUB CHORD
5=SAW PAD  6=SYNC LEAD  7=HOOVER
```

### WHEEL (7)
```
0=SOUL ORGAN  1=GOSPEL  2=JAZZ ORGAN  3=DIRTY B3  4=HOUSE ORGN
```

### GRAIN (8)
```
0=LOFI CLOUD  1=VIBE HAZE  2=FLUTE DUST
```

## 鼓轨 lane → GM 音

| lane | 名称 | GM |
|---|---|---|
| 0 | KICK | 36 |
| 1 | KICK2 | 35 |
| 2 | SNARE | 38 |
| 3 | CLAP | 39 |
| 4 | CHH | 42 |
| 5 | OPEN HAT | 46 |
| 6 | PEDAL | 44 |
| 7 | RIM | 37 |
| 8 | SNARE2 | 40 |
| 9 | LOW TOM | 43 |
| 10 | HI TOM | 48 |
| 11 | CRASH | 49 |
| 12 | RIDE | 51 |
| 13 | SHAKER | 70 |
| 14 | CONGA | 63 |
| 15 | COWBELL | 56 |

## 鼓组 KIT（37 组）

```
0=ACOUSTIC  1=DEEP  2=TIGHT  3=BRIGHT  4=DUST
5=808  6=909  7=606  8=80S  9=VINTAGE
10=TRAP  11=DRILL  12=BOOMBAP  13=LO-FI  14=PHONK
15=HOUSE  16=D.HOUSE  17=TECHNO  18=MINIMAL  19=ELECTRO
20=DISCO  21=GARAGE  22=JUNGLE  23=DUBSTEP  24=DEMBOW
25=AMAPIANO  26=AFRO  27=LATIN  28=TRIBAL  29=SYNTHWV
30=CHIP  31=ARCADE  32=GLITCH  33=INDUSTR  34=HYPER
35=AMBIENT  36=JAZZ
```

## 鼓步编码

```
写：[i, ...g7(on,3), ...g7(lv,5), ...g7(rt,5)]
读：[i, on3B, lv5B, rt5B]（14B）

on = 16bit lane 掩码（lane l = bit l）
lv = Σ(lvl[l]&3) * 4^l；lvl 枚举：0=NORM 1=GHOST 2=SOFT 3=HARD
rt = Σ(rat[l]&3) * 4^l（ratchet 1-4 次）
g7(x,n) = 每 7bit 一段取低 n 字节
```

**示例**：KICK + SNARE + CHH
```
on = (1<<0)|(1<<2)|(1<<4) = 21
```

## DIV/TIME 枚举（SLOOP 只有 6 个）

```
0=1/4  1=1/8  2=1/16  3=1/32  4=8T  5=16T
```

## TIE 语义

- `time=1` 延续**最近一个 NOTE 起始步**的音符
- 整段全 TIE 无 NOTE 起始 = 静音
- 写长音 = 首步 `time=0` + 后续步 `time=1`

## 关键坑（实测校准）

1. **命令号不要重复带**：`link.request(CMD_TRACK, [0])` 不是 `[27, 0]`
2. **写步无 chance**：SLOOP 布局 `[tr,i,n,notes,time,flags,vel]`
3. **TIE 需 NOTE 起始**
4. **无 SONG 命令**：33=DRUM_STEP
5. **mock 预设表不可信**：以 NAMES 为准
6. **PRESET = [engine, 引擎内预设号]**：换音色后写步需 0.2s 间隔
7. **TRACK_DUMP 的 p 是 v14 对**（不是"已解码值"）：`v14dec(p[2i+1], p[2i+2])`
8. **winmm 回调必须 5 参数**：`(hMidiIn, wMsg, dwInstance, dwParam1, dwParam2)`。
   4 参数会让 `dwParam1` 收到 `dwInstance=NULL`，所有请求收不到回复。
9. **INFO trailer = [ntrk, flag]**：4 = ntrk；6 是独立 flag 字节，不是 ntrk。