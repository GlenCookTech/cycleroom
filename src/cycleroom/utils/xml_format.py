import xml.dom.minidom
import argparse

def pretty_print_xml(xml_file):
    """Reads an XML file and outputs a formatted, easy-to-read version."""
    try:
        with open(xml_file, "r", encoding="utf-8") as file:
            xml_content = file.read()

        # Parse and pretty-print XML
        parsed_xml = xml.dom.minidom.parseString(xml_content)
        formatted_xml = parsed_xml.toprettyxml(indent="  ")

        # Output formatted XML
        print(formatted_xml)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format and pretty-print an XML file.")
    parser.add_argument("xml_file", help="Path to the XML file to be formatted")
    args = parser.parse_args()

    pretty_print_xml(args.xml_file)
