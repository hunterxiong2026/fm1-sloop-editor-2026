# Changelog

本项目所有显著变更均记录于此。
格式基于 [Keep a Changelog](https://keepachangelog.com/)，
版本号遵循 [Semantic Versioning](https://semver.org/)。

## [Unreleased]

### 计划
- [ ] 贝斯轨音色听感迭代（更多预设验证）
- [ ] 多 section 链式编排（A→B→C→D）
- [ ] 鼓组 lane 力度/ratchet 细粒度 API
- [ ] `sloop_arrange.py` 支持双 section 一键写入
- [ ] macOS 支持（CoreMIDI）

---

## [1.0.0] - 2026-10-07

### 新增
- **SLOOP 2.3 直连方案**（ctypes + winmm.dll，协议族同 Felucca）
- `scripts/sloop_link.py`：直连核心库
  - 设备枚举（`Felucca` 输入/输出端口）
  - 帧收发（`F0 7D 46 4C <cmd> <args...> F7`）
  - v14 编解码、DRUM_STEP 的 g7 编解码
  - INFO / DESC / NAMES / STEP / TRACK_PARAM / TRACK_MIX / TRACK_DUMP / DRUM_STEP / PROJECT / PRESET
  - 鼓轨 lane → GM 音映射、37 套鼓组枚举
- `scripts/sloop_cli.py`：命令行工具（12 个子命令）
  `info` `desc` `names` `preset` `kit` `readstep` `drumread`
  `readparam` `setparam` `dump` `save` `restore`
- `scripts/sloop_arrange.py`：单槽一键编曲（读 JSON → 写 4 轨含鼓轨 → 存 section → 提示 PLAY）
- `SKILL.md`：入口文档，含完整协议、参数 ID、关键坑
- `reference/sloop-sysex-map.md`：参数表、预设名、鼓组枚举、lane 映射
- `examples/sloop-recipes.md`：编曲配方（含 4 轨验收编曲）

### 真机校准（发布前完成）
- **winmm 回调签名**：正确的 5 参数
  `(hMidiIn, wMsg, dwInstance, dwParam1, dwParam2)`。
  4 参数定义会让 `dwParam1` 收到 `dwInstance=NULL`，导致所有 request 收不到回复。
- **INFO trailer 解析**：SLOOP 的 trailer = `[ntrk, flag]`（实测 `[4, 6]`），
  无 chainRows/uiCaps 字段。
- **TRACK_STEP 读步回复**：确认 12B 布局
  `[i, n, notes4, time, flags, vel, lvl, hi, rat]`，后 3B 解码：
  ```
  lvl = b[9] | ((b[10] & 1) << 7)
  rat = b[11] | (((b[10] >> 1) & 1) << 7)
  ```
- **DRUM_STEP 读步回复**：确认 14B 布局 `[i, on3B, lv5B, rt5B]`。
- **TRACK_DUMP 解析**：头 3B = `[tr, engine, preset]` 单字节，
  `p` = **58 × (lo, hi) v14 对**，必须 `v14dec(lo, hi)` 解码。

### 与 Felucca 的差异
- **命令 33** = DRUM_STEP（Felucca 是 SONG）
- **写步无 chance 字节**：`[tr, i, n, notes4, time, flags, vel]`
- **9 引擎**（无 DRUM/FM6/NOISE/SLICE），鼓走第 4 轨专用
- **无自动播放命令**，播放靠设备 PLAY 键
- **58 轨道参数 + 32 全局参数**（Felucca 是 91 + 27）
- **DIV 枚举 6 个**（Felucca 8 个）

### 已知限制
- 仅支持 Windows（依赖 winmm.dll）
- 无自动播放命令，播放靠设备 PLAY 键
- 贝斯轨音色听感需实测（REESE=6 已验证，SUB BASS=2 偏轻）
- SLOOP 固件为 Beta，刷入有变砖风险

---

## 版本号规则

从 `1.0.0` 起，严格遵循 [Semantic Versioning](https://semver.org/)：

| 变更类型 | 版本号变化 | 示例 |
|---|---|---|
| **破坏性变更** | `MAJOR` | 协议不兼容、脚本接口重构 |
| **新增功能** | `MINOR` | 新脚本、新命令、新配方 |
| **修复/校准** | `PATCH` | 解析校准、bug fix、文档纠正 |

### 每次改进的流程
1. **改代码/文档**
2. **在 `CHANGELOG.md` 的 `[Unreleased]` 段新增条目**
3. **发版时把 `[Unreleased]` 改名为 `[X.Y.Z] - YYYY-MM-DD`**
4. **同步更新 `SKILL.md` 的 `version` 字段和 `README.md` 顶部的 badge**