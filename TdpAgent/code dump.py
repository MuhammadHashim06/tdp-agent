import os

BASE_DIR = "app"
OUTPUT_FILE = "code_dump.txt"

def dump_code(base_dir, output_file):
    with open(output_file, "w", encoding="utf-8") as out:
        for root, dirs, files in os.walk(base_dir):
            for file in sorted(files):
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, base_dir)

                    out.write(f"\n{'='*80}\n")
                    out.write(f"{base_dir}/{relative_path}:\n\n")

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"[ERROR READING FILE: {e}]")

                    out.write("\n")

    print(f"Code successfully dumped into {output_file}")

if __name__ == "__main__":
    dump_code(BASE_DIR, OUTPUT_FILE)
