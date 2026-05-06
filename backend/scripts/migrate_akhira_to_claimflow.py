import os
import shutil

source_dir = r"C:\Users\guest123\Downloads\Praharshitha_koduri\Akhira"
dest_dir = r"C:\Users\guest123\ClaimFlow\backend"

files_to_copy = [
    "guardrails.py",
    "pipeline.py",
    "retrieval.py",
    "generator.py",
    "intent.py",
    "insurance_kb.json"
]

def migrate_files():
    # Ensure destination directory exists
    os.makedirs(dest_dir, exist_ok=True)

    copied_files = []

    for file_name in files_to_copy:
        src_file = os.path.join(source_dir, file_name)
        
        if not os.path.exists(src_file):
            print(f"Warning: Source file not found - {src_file}")
            continue

        dest_file = os.path.join(dest_dir, file_name)
        
        # Check if file exists in destination, prepend prefix if it does
        if os.path.exists(dest_file):
            new_file_name = f"akhira_{file_name}"
            dest_file = os.path.join(dest_dir, new_file_name)
            
        shutil.copy2(src_file, dest_file)
        copied_files.append((file_name, dest_file))

    print("\nMigration Summary:")
    print("-" * 50)
    if not copied_files:
        print("No files were copied.")
    else:
        for original_name, final_dest in copied_files:
            print(f"Copied: {original_name}")
            print(f"    To: {final_dest}")
    print("-" * 50)

if __name__ == "__main__":
    migrate_files()
