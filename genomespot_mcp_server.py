"""GenomeSPOT MCP Server (stdio 模式).

暴露工具:
    predict_genome(fna, faa)
        输入: 基因组 contigs (.fna) 与蛋白序列 (.faa) 文件路径
        输出: temperature / ph / salinity / oxygen 的预测值、error、is_novel、units、warning

内部流程（复用已通过验证的 test_api.py）:
    .fna + .faa
        -> test_api.predict_genome()   [measure_genome_features() + GenomeSPOT.predict_from_genome()]
        -> JSON 字符串返回

运行方式 (必须使用 genome_spot 环境, sklearn==1.2.2):
    cd /home/liujiacheng/GenomeSPOT/genomespot
    /home/liujiacheng/miniconda3/envs/genomespot/bin/python genomespot_mcp_server.py
"""

import json
import sys
from pathlib import Path
from typing import Any

# 将项目根目录加入 sys.path，保证可 import genome_spot 与 test_api
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.mcpserver import MCPServer  # MCP Python SDK >= 2.0

from test_api import predict_genome as _predict_genome_api  # 复用已验证的预测封装

# 与 test_api.py 保持一致
MODEL_DIR = "./models"

server = MCPServer(
    name="genomespot",
    title="GenomeSPOT",
    description=(
        "Predict oxygen, temperature, salinity, and pH preferences of "
        "bacteria and archaea from a genome, using the official GenomeSPOT models."
    ),
    version="0.1.0",
)


def _predictions_to_dict(predictions: dict) -> dict:
    """把 GenomeSPOT 预测 dict 整理成仅含关键字段的 dict."""
    result: dict[str, Any] = {}
    for target in sorted(predictions):
        r = predictions[target]
        result[target] = {
            "value": r.get("value"),
            "error": r.get("error"),
            "is_novel": r.get("is_novel"),
            "units": r.get("units"),
            "warning": r.get("warning"),
        }
    return result


@server.tool()
def predict_genome(fna: str, faa: str) -> str:
    """从基因组序列预测生长条件 (temperature / ph / salinity / oxygen)。

    Args:
        fna: 基因组 contigs 的 FASTA 文件路径 (.fna, 支持 .gz)
        faa: 蛋白序列的 FASTA 文件路径 (.faa, 支持 .gz)

    Returns:
        JSON 字符串，包含每个 target 的 value / error / is_novel / units / warning
    """
    predictions = _predict_genome_api(fna, faa, models_dir=MODEL_DIR)
    return json.dumps(_predictions_to_dict(predictions), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 本地 stdio 模式
    server.run(transport="stdio")
