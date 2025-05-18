import os
import shutil

# Set this to your "exercises" folder path
EXERCISES_DIR = "/Users/ashto/Desktop/Grin and Gain Files/exercise_db_gng/exercises"

def flatten_exercise_images(directory):
    for subfolder in os.listdir(directory):
        subfolder_path = os.path.join(directory, subfolder)

        # Ensure it's a directory (an exercise folder)
        if os.path.isdir(subfolder_path):
            for filename in os.listdir(subfolder_path):
                file_path = os.path.join(subfolder_path, filename)

                if os.path.isfile(file_path) and filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    # New name: FolderName-Index.jpg
                    new_filename = f"{subfolder}-{filename}"
                    destination_path = os.path.join(directory, new_filename)

                    # Move and rename
                    shutil.move(file_path, destination_path)
                    print(f"Moved: {file_path} → {destination_path}")

            # Optionally remove the now-empty subfolder
            os.rmdir(subfolder_path)
            print(f"Removed folder: {subfolder_path}")

# 🔁 Run the function
flatten_exercise_images(EXERCISES_DIR)
