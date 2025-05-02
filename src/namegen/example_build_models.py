"""
This example builds names based on the US name data set.

You can find the dataset at data.gov: https://catalog.data.gov/dataset/baby-names-from-social-security-card-applications-national-data

Run the file by giving the input directory with the -i flag. The input directory should have all of the .txt files from the data.gov download.
You can also give an output path for the resultant model JSON using the -o flag.
Additional options include start-year, end-year, and gender.
"""

import argparse
import pandas as pd
from pathlib import Path

from namegen import build_weighted_markov_chain, save_markov_model_to_json


def load_name_data(
    name_dir: Path, start_year: int = None, end_year: int = None, gender: str = None
) -> pd.DataFrame:
    """
    Loads all yobXXXX.txt files in the given directory into a single DataFrame,
    optionally filtered by year and gender.

    Returns:
        DataFrame with columns: 'Name', 'Gender', 'Count', 'Year'
    """
    all_data = []

    for file in sorted(name_dir.glob("yob*.txt")):
        year = int(file.stem[3:])  # extract year from 'yobXXXX'
        df = pd.read_csv(file, names=["Name", "Gender", "Count"])
        df["Year"] = year
        all_data.append(df)

    combined = pd.concat(all_data, ignore_index=True)

    if start_year is not None:
        combined = combined[combined["Year"] >= start_year]

    if end_year is not None:
        combined = combined[combined["Year"] <= end_year]

    if gender is not None:
        gender = gender.upper()
        if gender not in {"M", "F"}:
            raise ValueError("Gender must be 'M' or 'F'")
        combined = combined[combined["Gender"] == gender]

    return combined


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="names",
        help="Path to directory containing yobXXXX.txt files",
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Full output path for model JSON file"
    )
    parser.add_argument(
        "--output-name",
        type=str,
        help="Name of the output file (e.g., 'model.json'), placed in current directory if -o not provided",
    )
    parser.add_argument(
        "-n",
        "--order",
        type=int,
        default=3,
        help="N-gram order for Markov model (default=3)",
    )
    parser.add_argument(
        "--start-year", type=int, help="Start year for filtering names (inclusive)"
    )
    parser.add_argument(
        "--end-year", type=int, help="End year for filtering names (inclusive)"
    )
    parser.add_argument("--gender", type=str, help="Gender to filter by: M or F")

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        raise FileNotFoundError(f"Input path '{input_path}' does not exist.")

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    elif args.output_name:
        output_path = Path.cwd() / args.output_name
    else:
        output_path = Path.cwd() / "name_model.json"

    print(f"Loading name data from: {input_path}")
    name_df = load_name_data(
        name_dir=input_path,
        start_year=args.start_year,
        end_year=args.end_year,
        gender=args.gender,
    )

    print(f"Total names loaded: {len(name_df)}")
    if name_df.empty:
        raise ValueError("Filtered DataFrame is empty. Check year range and gender.")

    print(f"Building Markov model with n-gram order {args.order}...")
    model = build_weighted_markov_chain(name_df[["Name", "Count"]], n=args.order)

    print(f"Saving model to: {output_path}")
    save_markov_model_to_json(model, output_path)

    print("Done! Model saved successfully.")


if __name__ == "__main__":
    main()
