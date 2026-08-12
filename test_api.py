"""GenomeSPOT Python API 冒烟测试（新增文件，不改动任何源码）。

完整预测流程：
    .fna + .faa
        |
        v
    measure_genome_features(faa_path, fna_path)      # feature extraction
        |
        v
    GenomeSPOT.predict_from_genome(features, models) # model prediction
        |
        v
    predictions (dict)

运行方式（必须使用 genome_spot 环境，sklearn==1.2.2）：
    cd /home/liujiacheng/GenomeSPOT/genomespot
    /home/liujiacheng/miniconda3/envs/genomespot/bin/python test_api.py
"""

from genome_spot.bioinformatics.genome import measure_genome_features
from genome_spot.genome_spot import GenomeSPOT

MODEL_DIR = "./models"


def predict_genome(fna: str, faa: str, models_dir: str = MODEL_DIR) -> dict:
    """Run the full GenomeSPOT prediction pipeline on one genome.

    Args:
        fna: Path to a genome's contigs in FASTA format (.gz allowed)
        faa: Path to a genome's proteins in FASTA format (.gz allowed)
        models_dir: Path to directory containing models and instructions.json

    Returns:
        predictions: nested dict of each target's predicted value,
            error, is_novel, warning, and units.
    """
    # Step 1: feature extraction
    genome_features = measure_genome_features(faa_path=faa, fna_path=fna)

    # Step 2: prediction from genome features
    predictor = GenomeSPOT()
    predictions = predictor.predict_from_genome(genome_features, models_dir)

    return predictions


def _fmt(value, width=12):
    return str(value) if value is not None else "None"


if __name__ == "__main__":
    FNA = "/tmp/cs_validate/GCA_018156225.1_genomic.fna.gz"
    FAA = "/tmp/cs_validate/GCA_018156225.1_protein.faa.gz"

    print("=" * 70)
    print("GenomeSPOT Python API smoke test")
    print("=" * 70)
    print("fna:", FNA)
    print("faa:", FAA)
    print("models dir:", MODEL_DIR)
    print()

    result = predict_genome(FNA, FAA)

    print("-" * 70)
    print("Predictions")
    print("-" * 70)
    for target in sorted(result):
        r = result[target]
        print(f"{target:22s} value={_fmt(r['value']):>12s}  "
              f"error={_fmt(r['error']):>12s}  units={r['units']!s:10s}  "
              f"is_novel={_fmt(r['is_novel']):>6s}  warning={_fmt(r['warning'])}")

    print()
    required = ["temperature_optimum", "ph_optimum", "salinity_optimum", "oxygen"]
    missing = [t for t in required if t not in result]
    if missing:
        print("ERROR: 缺少以下预测:", missing)
        raise SystemExit(1)

    print("OK: temperature / ph / salinity / oxygen 预测均正常输出。")
