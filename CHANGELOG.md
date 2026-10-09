# Changelog

本项目所有显著变更均记录于此。
格式基于 [Keep a Changelog](https://keepachangelog.com/)，
版本号遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

### 计划
- [ ] DIV 枚举扩展到 9 个（1/2、1BAR、2BAR）
- [ ] KIT 37-41（USR1-4、USR3+4）名称校准
- [ ] FM6 引擎预设名读取（NAMES [9]）
- [ ] Parameter locks / Micro timing / Fills 的 SysEx 写入
- [ ] 多 section 链式编排（A→B→C→D）
- [ ] macOS 支持（CoreMIDI）

---

## [1.1.0] - 2026-10-09

### 新增
- **适配 SLOOP 2.4.1 固件**
- **FM6 引擎**（六算子 FM / DX7 兼容）：`ENGINES['FM6'] = 9`，引擎总数 9 → 10
- **新轨道参数**：
  - `FILT=50`（每轨滤波器，2.4 新增）
  - `STRUM=51`（和弦拨弦，-60..60）
  - `VLEAD=52`（voice leading，0..1）
  - `KIT=53`（鼓组参数，替代 2.3 的 50）
  - 引擎编辑参数 54-60（原 51-57 整体后移 3 位）
- 轨道参数总数 **58 → 61**
- 鼓组总数 **37 → 42**（新增 USR1-4、USR3+4，名称待校准）

### 修复（2.4.1 实测校准）
- **`P_KIT` 从 50 迁到 53**：2.3 文档的 `P_E0=50`（当前预设号）在 2.4.1 中已改为 `FILT`，
  鼓组参数迁到 53。这是本次校准最重要的修正。
- **winmm 回调签名**：正确的 5 参数
  `(hMidiIn, wMsg, dwInstance, dwParam1, dwParam2)`。
- **输入累积切帧**：设备会连续推多帧（如选轨后的 TRACK 通知 + 真正回复），
  必须按 `F7` 切完整帧。
- **`request()` 跳过非匹配帧**：避免把推送帧（rc != cmd）当成回复。
- **`close()` 不调用 `midiInReset`**：有 pending buffer 时会与回调线程死锁。
- **`send()` 用带 NUL 的 buffer**：与 felucca_link 保持一致。
- **MIDIHDR 结构体**：`dwUser`/`reserved` 用 `c_ulonglong`（8 字节）。
- **INFO trailer**：实测 `[4, 9]`（2.3 为 `[4, 6]`）。

### 变更
- `SKILL.md` version: 1.0.0 → 1.1.0
- `sloop_link.py` 固件版本注释更新为 2.4.1
- 直连"四坑"重新整理，新增"其他关键坑"章节
- 文档全面更新：引擎表、参数表、KIT 表、INFO 解析

### 已知限制
- 仅支持 Windows
- 无自动播放命令
- **DIV 枚举未扩展**：2.4 新增 1/2、1BAR、2BAR（当前脚本仍 6 值）
- **KIT 37-41**（USR1-4、USR3+4）名称未校验
- SLOOP 固件为 Beta，有变砖风险

---

## [1.0.0] - 2026-10-07

### 新增
- **SLOOP 2.3 直连方案**（ctypes + winmm.dll，协议族同 Felucca）
- `scripts/sloop_link.py`：直连核心库
- `scripts/sloop_cli.py`：命令行工具（12 个子命令）
- `scripts/sloop_arrange.py`：单槽一键编曲
- `SKILL.md` / `README.md` / `CHANGELOG.md` / `LICENSE`
- `reference/sloop-sysex-map.md`：参数表、预设名、鼓组枚举、lane 映射
- `examples/sloop-recipes.md`：编曲配方

### 与 Felucca 的差异（2.3 时）
- 命令 33 = DRUM_STEP（Felucca 是 SONG）
- 写步无 chance 字节
- 9 引擎（无 DRUM/FM6/NOISE/SLICE），鼓走第 4 轨专用
- 无自动播放命令
- 58 轨道参数 + 32 全局参数

---

## 版本号规则

从 `1.0.0` 起，严格遵循 [Semantic Versioning](https://semver.org/)：

| 变更类型 | 版本号变化 | 示例 |
|---|---|---|
| **破坏性变更** | `MAJOR` | 协议不兼容、脚本接口重构 |
| **新增功能** | `MINOR` | 新引擎、新参数、新脚本 |
| **修复/校准** | `PATCH` | 解析校准、bug fix、文档纠正 |

### 每次改进的流程
1. **改代码/文档**
2. **在 `CHANGELOG.md` 的 `[Unreleased]` 段新增条目**
3. **发版时把 `[Unreleased]` 改名为 `[X.Y.Z] - YYYY-MM-DD`**
4. **同步更新 `SKILL.md` 的 `version` 字段和 `README.md` 顶部的 badge**