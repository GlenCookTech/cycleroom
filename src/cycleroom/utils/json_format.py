import json
import argparse

def pretty_print_json(json_file):
    """Reads a JSON file and outputs a formatted, easy-to-read version."""
    try:
        with open(json_file, "r", encoding="utf-8") as file:
            json_content = json.load(file)

        # Pretty-print JSON with indentation
        formatted_json = json.dumps(json_content, indent=4, sort_keys=True)

        # Output formatted JSON
        logger.info(formatted_json)

    except Exception as e:
        logger.info(f"❌ Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format and pretty-print a JSON file.")
    parser.add_argument("json_file", help="Path to the JSON file to be formatted")
    args = parser.parse_args()

    pretty_print_json(args.json_file)
