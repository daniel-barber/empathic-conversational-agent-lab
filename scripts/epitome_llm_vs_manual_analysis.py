#!/usr/bin/env python3
import sys
from pathlib import Path
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt


def load_excel(path: Path) -> pd.DataFrame:
    if not path.exists():
        print(f"❌ ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    return pd.read_excel(path)


def compute_agreement(man, llm):
    acc = accuracy_score(man, llm)
    kappa = cohen_kappa_score(man, llm)
    cm = confusion_matrix(man, llm)
    return acc, kappa, cm


def main():
    # 1) Paths
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    manual_path = DATA_DIR / "empatheticdialogues_epitome_manual_annotation_pairs_100.xlsx"
    llm_path    = DATA_DIR / "empatheticdialogues_epitome_llm_evaluation_100.xlsx"

    # 2) Load
    manual = load_excel(manual_path)
    llm    = load_excel(llm_path)

    # 3) Join on index (or conv_id if you prefer)
    df = manual.join(llm, lsuffix="_manual", rsuffix="_llm")

    # 4) Define categories manually
    categories = [
        {
            "name": "Emotional_Reactions",
            "score_manual": "Emotional_Reactions_manual",
            "score_llm":    "Emotional_Reactions_llm",
            "rationale_manual": "Rationale_ER_manual",
            "rationale_llm":    "Rationale_ER_llm",
        },
        {
            "name": "Interpretations",
            "score_manual": "Interpretations_manual",
            "score_llm":    "Interpretations_llm",
            "rationale_manual": "Rationale_IN_manual",
            "rationale_llm":    "Rationale_IN_llm",
        },
        {
            "name": "Explorations",
            "score_manual": "Explorations_manual",
            "score_llm":    "Explorations_llm",
            "rationale_manual": "Rationale_EX_manual",
            "rationale_llm":    "Rationale_EX_llm",
        },
    ]

    results = []
    for cat in categories:
        sm = cat["score_manual"]
        sl = cat["score_llm"]
        if sm not in df.columns or sl not in df.columns:
            print(f"❌ ERROR: Missing columns for {cat['name']}: {sm} or {sl}", file=sys.stderr)
            sys.exit(1)

        acc, kappa, cm = compute_agreement(df[sm], df[sl])
        results.append({
            "category": cat["name"],
            "agreement": acc,
            "cohen_kappa": kappa
        })
        print(f"\n--- {cat['name']} ---")
        print("Confusion matrix:")
        print(cm)

    # 5) Summary table
    results_df = pd.DataFrame(results)
    print("\n=== Summary ===")
    print(results_df.to_string(index=False))

    # 6) Plot
    fig, ax = plt.subplots()
    results_df.plot.bar(x="category", y=["agreement", "cohen_kappa"], ax=ax)
    ax.set_ylim(0, 1)
    ax.set_title("Agreement & Cohen’s Kappa per EPITOME Category")
    ax.set_ylabel("Score")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()

    # # 7) Rationale exact-match
    # for cat in categories:
    #     rm = cat["rationale_manual"]
    #     rl = cat["rationale_llm"]
    #     if rm in df.columns and rl in df.columns:
    #         man_r = df[rm].fillna("").str.strip().str.lower()
    #         llm_r = df[rl].fillna("").str.strip().str.lower()
    #         match_rate = (man_r == llm_r).mean()
    #         print(f"Rationale exact match for {cat['name']}: {match_rate:.2%}")
    #     else:
    #         print(f"⚠️  Skipping rationale match for {cat['name']} (columns missing)")

    # 8) Save summary
    out_path = DATA_DIR / "epitome_llm_vs_manual_agreement_summary.xlsx"
    results_df.to_excel(out_path, index=False)
    print(f"\n✅ Wrote summary to: {out_path}")


if __name__ == "__main__":
    main()
