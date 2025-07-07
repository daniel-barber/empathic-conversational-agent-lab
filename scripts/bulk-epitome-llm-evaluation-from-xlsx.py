import pandas as pd
from backend.services.epitome_evaluation import call_epitome_model
import sys
import pathlib

# Add project root to sys.path for module imports like backend.*
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

INPUT_PATH = "data/empatheticdialogues_epitome_llm_evaluation_100.xlsx"
OUTPUT_PATH = "data/empatheticdialogues_epitome_llm_evaluation_100.xlsx"  # Overwrite original


def batch_evaluate_xlsx(input_path: str, output_path: str):
    df = pd.read_excel(input_path, engine="openpyxl")

    for idx, row in df.iterrows():
        seeker = row['seeker_text']
        responder = row['response_text']
        if pd.isna(seeker) or pd.isna(responder):
            continue
        result = call_epitome_model(seeker, responder)
        df.at[idx, 'Emotional_Reactions'] = result['emotional_reactions']['score']
        df.at[idx, 'Rationale_ER'] = result['emotional_reactions']['rationale']
        df.at[idx, 'Interpretations'] = result['interpretations']['score']
        df.at[idx, 'Rationale_IN'] = result['interpretations']['rationale']
        df.at[idx, 'Explorations'] = result['explorations']['score']
        df.at[idx, 'Rationale_EX'] = result['explorations']['rationale']
        print(f"[{idx + 1}/{len(df)}] Evaluated conv_id={row['conv_id']}")

    df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"Batch evaluation complete. Results written to {output_path}")


if __name__ == "__main__":
    batch_evaluate_xlsx(INPUT_PATH, OUTPUT_PATH)
