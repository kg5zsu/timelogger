import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(
        description="timelogger — TUI dashboard and CSV export"
    )
    parser.add_argument(
        "--db",
        default=os.path.expanduser(
            os.environ.get(
                "TIMELOGGER_DB",
                "~/.local/share/timelogger/usage.db",
            )
        ),
        help="Path to usage.db",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)",
    )
    parser.add_argument(
        "--export",
        nargs="?",
        const="timelogger-export.csv",
        help="Export to CSV file and exit",
    )
    parser.add_argument(
        "--export-mode",
        choices=["raw", "category", "app"],
        default="raw",
        help="Export mode: raw, category, app (default: raw)",
    )

    args = parser.parse_args()

    if args.export:
        from .export import export_csv

        path = export_csv(
            args.export, db_path=args.db, days=args.days,
            mode=args.export_mode
        )
        print(f"Exported to {path}")
        sys.exit(0)

    from .app import TimeloggerApp

    app = TimeloggerApp(db_path=args.db)
    app.run()


if __name__ == "__main__":
    main()
