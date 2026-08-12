# GenomeSPOT MCP Server 使用说明

本目录为 **GenomeSPOT 预测能力** 封装为 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) Server 的集成。

- **功能**：从细菌/古菌基因组（`.fna` + `.faa`）预测温度、pH、盐度、氧耐受等生长条件。
- **模型**：官方 GenomeSPOT v1.0.0 模型（`models/` 目录，要求 scikit-learn==1.2.2）。
- **方式**：本地 `stdio` 模式，供 VS Code / Claude Desktop / Cursor 等 MCP 客户端调用。

---

## 1. 文件清单

| 文件 | 说明 |
|---|---|
| `test_api.py` | Python API 封装：`predict_genome(fna, faa)`（feature 提取 + 模型预测） |
| `genomespot_mcp_server.py` | MCP Server（stdio），暴露工具 `predict_genome` |
| `.vscode/mcp.json` | VS Code 工作区级 MCP 配置（自动发现） |
| `README_MCP.md` | 本文档 |

> 未修改任何 GenomeSPOT 原始源码（`genome_spot/`、`models/`、`tests/`、`data/` 等均保持原样）。

## 2. 前置条件

- Python 环境：**必须使用 `genomespot` conda 环境**
  （Python 3.10.20，`scikit-learn==1.2.2`，`mcp` SDK ≥ 2.0 已安装）。
- 预测输入：配对的文件
  - `.fna`：基因组 contigs（支持 `.gz`）
  - `.faa`：蛋白序列（支持 `.gz`）
- 模型目录：`./models`（相对项目根目录）

## 3. 快速开始

### 3.1 直接启动 Server（stdio）

```bash
cd /home/liujiacheng/GenomeSPOT/genomespot
/home/liujiacheng/miniconda3/envs/genomespot/bin/python genomespot_mcp_server.py
```

启动后进程阻塞等待 stdin 上的 MCP JSON-RPC 请求（正常现象）。

### 3.2 通过 Python API 直接调用（不经过 MCP）

```bash
/home/liujiacheng/miniconda3/envs/genomespot/bin/python test_api.py
```

### 3.3 MCP 协议自测（连接 + 工具调用）

```bash
cd /tmp && /home/liujiacheng/miniconda3/envs/genomespot/bin/python /tmp/mcp_conn_check.py
```

该脚本会依次执行 `initialize → list_tools → call_tool(predict_genome)`。

## 4. 客户端配置

### VS Code（`.vscode/mcp.json`，已配置）

```json
{
  "servers": {
    "genomespot": {
      "type": "stdio",
      "command": "/home/liujiacheng/miniconda3/envs/genomespot/bin/python",
      "args": ["/home/liujiacheng/GenomeSPOT/genomespot/genomespot_mcp_server.py"],
      "cwd": "/home/liujiacheng/GenomeSPOT/genomespot"
    }
  }
}
```

VS Code 打开项目后会自动发现；若未生效，命令面板执行
`MCP: List Servers` / `MCP: Reload Server` 或 `Developer: Reload Window`。

### Claude Desktop / Cursor 等

在 MCP 客户端配置中加入同一份 `command / args / cwd` 即可。

## 5. 工具参考：`predict_genome`

| 项目 | 说明 |
|---|---|
| 输入 | `fna`（str，基因组文件路径）、`faa`（str，蛋白文件路径） |
| 输出 | JSON：`temperature_optimum/min/max`、`ph_optimum/min/max`、`salinity_optimum/min/max`、`oxygen`，各含 `value / error / is_novel / units / warning` |
| 耗时 | 单基因组约 5–10 秒（feature 提取为主） |

**内部流程**

```
.fna + .faa
   → measure_genome_features(faa, fna)          # 2210 原始特征
   → GenomeSPOT.predict_from_genome(features)   # 10 项预测
   → 返回 JSON
```

**示例返回值（键值）**

```json
{
  "temperature_optimum": {"value": 32.87, "error": 5.80, "is_novel": false, "units": "C", "warning": null},
  "ph_optimum":         {"value": 7.12,  "error": 0.92, "is_novel": false, "units": "pH", "warning": null},
  "salinity_optimum":   {"value": 2.42,  "error": 2.05, "is_novel": false, "units": "% w/v NaCl", "warning": null},
  "oxygen":             {"value": "tolerant", "error": 0.941, "is_novel": false, "units": "probability", "warning": null}
}
```

## 6. 验证示例

在已下载的验证基因组上运行（`Carboxylicivirga sediminis JR1`，GCA_018156225.1）：

```bash
/home/liujiacheng/miniconda3/envs/genomespot/bin/python - <<'PY'
from genome_spot.bioinformatics.genome import measure_genome_features
from genome_spot.genome_spot import GenomeSPOT
fna, faa = "/tmp/cs_validate/GCA_018156225.1_genomic.fna.gz", "/tmp/cs_validate/GCA_018156225.1_protein.faa.gz"
feats = measure_genome_features(faa, fna)
pred = GenomeSPOT().predict_from_genome(feats, "./models")
for t in sorted(pred):
    r = pred[t]
    print(f"{t:22s} {str(r['value']):>10s}  ±{r['error']}  {r['units']}")
PY
```

**预期结果（已通过官方模型实测）**：

| 条件 | 预测 | 单位 |
|---|---|---|
| temperature_optimum | 32.87 | °C |
| ph_optimum | 7.12 | pH |
| salinity_optimum | 2.42 | % w/v NaCl |
| oxygen | tolerant (p=0.94) | probability |

（10 项预测中 9 项连续值与 BacDive 实测偏差均在模型误差估计内，氧分类一致。）

## 7. 常见问题（Troubleshooting）

| 现象 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError: No module named 'numpy'` | 用了 base 环境 `python`（无依赖） | 改用 `/home/liujiacheng/miniconda3/envs/genomespot/bin/python` |
| 模型加载失败 / sklearn 版本错误 | `scikit-learn` 版本 ≠ 1.2.2 | 确认在 `genomespot` 环境内运行 |
| MCP 客户端报 `AttributeError: ... serverInfo/isError/inputSchema` | 客户端使用了旧版 MCP SDK 属性名（2.0 为 snake_case） | 升级客户端 SDK 至 ≥2.0 |
| 预测结果全为 `NaN` / `warning="genome missing features"` | 输入 `.faa` 与 `.fna` 不配对或蛋白数过少 | 检查文件，重新用 prodigal 预测蛋白 |
| VS Code 未发现 server | 未加载工作区配置 | `MCP: Reload Server` 或重载窗口 |
