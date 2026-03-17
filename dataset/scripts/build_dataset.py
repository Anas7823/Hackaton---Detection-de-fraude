from __future__ import annotations

from build_ground_truth import GROUND_TRUTH_PATH, build_rows_from_manifest, write_ground_truth


def main() -> None:
    rows = build_rows_from_manifest()
    write_ground_truth(rows, GROUND_TRUTH_PATH)

    print("Dataset reconstruit.")
    print("Matérialisation locale: inactive")
    print(f"Ground truth final: {GROUND_TRUTH_PATH}")
    print(f"Lignes totales: {len(rows)}")


if __name__ == "__main__":
    main()
