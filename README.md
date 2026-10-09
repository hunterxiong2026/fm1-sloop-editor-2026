# SLOOP Editor Skill

> 用自然语言控制 M-VAVE FM-1（SLOOP 2.4.1 固件），完成 4 轨编曲、鼓组写入与项目槽位管理。

[![Version](https://img.shields.io/badge/version-1.1.0-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 这是什么

一个 DeepSeek Harness（DSH）Skill，通过**直连 SysEx**（ctypes + winmm.dll）操控
FM-1 上的 SLOOP 2.4.1 固件。SLOOP 是 4 轨 Groovebox：

- **轨道 0-2**：3 个合成器轨（**10 引擎**可选，含 **FM6**）
- **轨道 3**：专用鼓机轨（16 lane / **42 套鼓组**）

**与 felucca-editor 的区别**：
- **Felucca**：13 引擎、64 步、SONG 播放链（自动播放）
- **SLOOP**：10 引擎 + 专用鼓机、64 步、**播放靠设备 PLAY 键**

---

## 目录结构

```
fm1-sloop-editor/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── LICENSE
├── reference/
│   └── sloop-sysex-map.md
├── scripts/
│   ├── sloop_link.py
│   ├── sloop_cli.py
│   └── sloop_arrange.py
└── examples/
    └── sloop-recipes.md
```

---

## 安装

### 1. 放置 Skill

把 `fm1-sloop-editor/` 放进 `~/.dsh/skills/` 或项目 `.dsh/skills/`。

### 2. 创建独立 venv

```bash
cd scripts
python -m venv venv
venv\Scripts\activate
```

### 3. 硬件准备

- FM-1 刷入 **SLOOP 2.4.1**（从 SLOOP 官方安装器刷入）
- USB 连接电脑
- **关闭浏览器 / 任何 Web MIDI 会话**

---

## 使用

### 首次验证

```bash
python scripts/sloop_cli.py info
```

应输出：
```
version='FELUCCA SLOOP 2.4.1', nengines=10, pcount=61, gcount=32,
nstep=64, pe0=53, ntrk=4, trailer=[4, 9]
```

### 日常指令示例

| 你的话 | Skill 的动作 |
|---|---|
| 写一段 4 轨 8 小节编曲 | `sloop_arrange.py 0 88 40` |
| 把轨 1 换成 WARM PAD | `sloop_cli.py preset 1 0 13` |
| 换成 808 鼓组 | `sloop_cli.py kit 5` |
| 读一下轨 2 的 LEN | `sloop_cli.py readparam 2 29` |
| 换到 FM6 引擎弹 DX7 音色 | `sloop_cli.py preset 0 9 <patch>` |

### 命令行速查

```bash
# 设备信息
python sloop_cli.py info

# 预设名（权威）
python sloop_cli.py names 0            # ANALOG
python sloop_cli.py names 9            # FM6

# 切预设 / 鼓组
python sloop_cli.py preset <tr> <engine> <preset>
python sloop_cli.py kit <kit_num>

# 读写步进
python sloop_cli.py readstep <tr> <step>
python sloop_cli.py drumread <step>
python sloop_cli.py readparam <tr> <pid>
python sloop_cli.py setparam <tr> <pid> <value>

# 一键编曲
python sloop_arrange.py <section> <bpm> <swing>
```

---

## 版本号规则

从 `1.0.0` 起，严格遵循 [Semantic Versioning](https://semver.org/)：

| 变更类型 | 版本号变化 | 示例 |
|---|---|---|
| **破坏性变更** | `MAJOR` | 协议不兼容、脚本接口重构 |
| **新增功能** | `MINOR` | 新引擎、新参数、新脚本 |
| **修复/校准** | `PATCH` | 解析校准、bug fix、文档纠正 |

### 当前版本：`1.1.0`

- **适配 SLOOP 2.4.1**
- 引擎 9 → **10**（新增 FM6 六算子 FM）
- 轨道参数 58 → **61**
- **KIT 参数从 50 迁到 53**（重要修正）
- 新增 FILT/STRUM/VLEAD 参数
- 新增 winmm 回调 5 参数修正、输入累积切帧、`midiInReset` 死锁规避

---

## 已知限制

- **仅支持 Windows**（依赖 winmm.dll）
- **无自动播放命令**，播放靠设备 PLAY 键
- **DIV 枚举未扩展**：2.4 新增 1/2、1BAR、2BAR（当前脚本仍 6 值）
- **KIT 37-41**（USR1-4、USR3+4）名称未校验
- **SLOOP 固件为 Beta**，刷入有变砖风险

---

## 用户硬约束

1. 独立 venv，绝不装任何包进系统
2. 播放验收以实际听声为准（需用户按 PLAY）
3. 修改音色/编曲后直接改文件与设备，不输出提示词正文
4. 回复先给一句话总结

---

## 许可

MIT License，详见 [LICENSE](LICENSE)。

## 免责声明

SLOOP 固件仍处于 Beta 阶段，刷入与使用存在变砖风险，请自行承担。
本 Skill 为第三方工具，与 M-VAVE 官方无关。