# test_pipeline.py (project root)
from app.core.analyzer import extract_breakdown
from app.core.scorer import score_breakdown
from app.core.pattern_engine import detect_patterns
from app.core.idea_generator import generate_ideas
import json, os, glob
from tqdm import tqdm

paths = sorted(glob.glob("data/sample_ads/*.png"))[:3]  # test with 3 first

def main():
    print(f"Starting analysis on {len(paths)} images...")
    breakdowns = [extract_breakdown(p, os.path.basename(p).split(".")[0]) for p in tqdm(paths, desc="Extracting Breakdowns")]

    print("Scoring Breakdowns...")
    scores     = [score_breakdown(b) for b in tqdm(breakdowns, desc="Scoring", leave=False)]

    print("Detecting Patterns...")
    patterns   = detect_patterns(breakdowns, scores, "Lenskart")

    print("Generating Ideas...")
    ideas      = generate_ideas(patterns, "Lenskart")

    print("\n--- DONE ---")
    print(json.dumps({"scores": scores, "patterns": patterns, "ideas": ideas}, indent=2))

if __name__ == "__main__":
    main()