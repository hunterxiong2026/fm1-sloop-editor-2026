\# 官方固件编曲配方



\## DX7 经典音色



\### 电钢琴（E.Piano）

\- Algorithm: 5

\- Feedback: 6

\- Operator 1 (Carrier): Output 99, Coarse 1

\- Operator 2 (Modulator): Output 75, Coarse 14

\- 包络：Attack 快，Decay 中，Sustain 低



\### 钟声（Bell）

\- Algorithm: 5

\- Feedback: 7

\- Operator 1: Output 99, Coarse 1

\- Operator 2: Output 85, Coarse 7

\- 包络：Attack 0，Decay 长，Sustain 0



\### 铜管（Brass）

\- Algorithm: 18

\- Feedback: 5

\- Operator 1-2: Output 90–99

\- 包络：Attack 中，Decay 中，Sustain 高



\## Pattern 链式播放配置



\### 4 小节循环

```

Pattern 1 → Pattern 2 → Pattern 3 → Pattern 4 → Repeat

```



\### 主部+副部

```

Pattern 1 (A段) → Pattern 2 (B段) → Pattern 1

```



\### 12 小节布鲁斯

```

Pattern 1 (I) → Pattern 2 (IV) → Pattern 1 → Pattern 3 (V) → Pattern 2 (IV) → Pattern 1

```



\## 参数速查



| 参数 | pp | qq | 范围 |

|---|---|---|---|

| Algorithm | 01 | 02 | 0–31 |

| Feedback | 01 | 03 | 0–7 |

| LFO Speed | 01 | 05 | 0–99 |

| Op1 Attack | 00 | 69 | 0–99 |

| Op1 Output | 00 | 79 | 0–99 |

| Op2 Attack | 00 | 54 | 0–99 |

| Op2 Output | 00 | 64 | 0–99 |



\## 与 Felucca Skill 的差异



| 维度 | felucca-editor | fm1-official-editor |

|---|---|---|

| 协议 | 自定义 `F0 7D 46 4C ...` | DX7 标准 `F0 43 1n pp qq vv F7` |

| 核心能力 | 多轨编曲、13 引擎、64 步音序器 | FM 音色编辑、Pattern 链式播放 |

| 音色库 | DX7 + 自定义 | DX7 标准 |

| 链式播放 | SONG 命令（op=1/op=2） | Chain Mode（Pattern 属性） |

| 参数数量 | 91+27 | 155（DX7 标准） |

| 读回能力 | 支持（STEP\_GET 等） | 未公开命令（V14/V15 可用） |

