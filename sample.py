import hfclib
import os


def main():
    # Asks user for file path
    hfclib.debug_mode = True

    file_path = input("Enter the path to the HFC file: ")

    if not os.path.exists(file_path):
        print("File not found.")
        return

    try:
        hfc = hfclib.parseHfc(file_path)
        print(hfc)
        list_hfc = hfclib.parseList(hfc)
        print(list_hfc)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
else:
    pass
