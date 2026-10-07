\# SLOOP 编曲配方



\## 已验收的 4 轨编曲（2026-10-07）



\### track0 旋律

\- 引擎：ANALOG，预设 9 = G-FUNK LD（亮 lead）

\- 长音铺底建议改 13 = WARM PAD

\- LEN=64, DIV=1 (1/8)

\- 4 小节时值递减：全音符（NOTE + TIE×8）→ 二分×2 → 四分×4 → 八分×8



\### track1 和弦

\- 引擎：ANALOG，预设 9

\- LEN=32, DIV=1

\- Cmaj7 - Am7 - Fmaj7 - G7，每小节 4 音 NOTE + TIE



\### track2 贝斯

\- 引擎：ANALOG，\*\*预设 6 = REESE\*\*（听感通过）

\- LEN=32, DIV=1

\- 四分行走（每 2 步 NOTE + TIE）



> SUB BASS=2 / 808 BOOM=0 听感偏轻，不推荐做走路贝斯。



\### track3 鼓

\- KIT=5 (808)

\- LEN=32, DIV=1

\- DRUM\_STEP 写 lane0 KICK / lane2 SNARE / lane4 CHH / lane12 RIDE



\### 全局

\- BPM=88, SWG=40

\- PROJECT 保存 section 0（A）

\- 播放 = 设备 PLAY 键



\## 常用预设速查



| 用途 | 引擎 | 预设 | 备注 |

|---|---|---|---|

| 亮 Lead | ANALOG | 9 = G-FUNK LD | |

| 长音铺底 | ANALOG | 13 = WARM PAD | 听感柔 |

| 氛围垫 | ANALOG | 15 = ATMOS PAD | |

| 走路贝斯 | ANALOG | 6 = REESE | 已验证 |

| Acid | ANALOG | 4 = ACID 303 | |

| Supersaw | ANALOG | 12 = SUPERSAW | |

| 电钢 | DIGITAL | 0 = RHODES | |

| DX 电钢 | DIGITAL | 1 = DX RHODES | |

| 钟琴 | DIGITAL | 6 = TRAP BELL | |

| 8-bit Lead | LOFI | 0 = GAME LEAD | |

| GM 鼓组 | SAMPLE | 7 = GM KIT | |



\## 鼓组速查



| 风格 | KIT |

|---|---|

| Hip-hop | 12 = BOOMBAP / 13 = LO-FI |

| Trap | 10 = TRAP / 11 = DRILL |

| House | 15 = HOUSE / 16 = D.HOUSE |

| Techno | 17 = TECHNO / 18 = MINIMAL |

| 808 | 5 = 808 |

| 909 | 6 = 909 |

| Jazz | 36 = JAZZ |



\## 关键坑



\- \*\*播放靠设备 PLAY 键\*\*，无自动播放命令

\- \*\*写步无 chance 字节\*\*，与 Felucca 不同

\- \*\*TIE 需 NOTE 起始\*\*，整段 TIE = 静音

\- \*\*换音色后写步需 0.2s 间隔\*\*

\- \*\*预设号以 NAMES 读回为准\*\*，不要用 mock 表

