#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import dotenv


def main():
    parser = argparse.ArgumentParser(description="Backfill Hevy workouts to Intervals.icu")
    parser.add_argument("--max-page", type=int, default=100, help="Max number of pages to sync (default: 100)")
    parser.add_argument("--page-size", type=int, default=10, help="Hevy page size, max 10 (default: 10)")
    args = parser.parse_args()

    dotenv.load_dotenv()

    LAMBDA_DIR = Path(__file__).parent / "lambda"
    sys.path.insert(0, str(LAMBDA_DIR))
    import utils  # type: ignore

    utils.local_sync_all(max_page=args.max_page, page_size=args.page_size)


if __name__ == "__main__":
    main()
