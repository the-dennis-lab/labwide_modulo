import os
import subprocess
import sys

def run_script_in_subfolders(main_directory, output_directory=None):
    # Iterate over all subdirectories in the main directory
    for root, dirs, files in os.walk(main_directory):
        for subdir in dirs:
            subdir_path = os.path.join(root, subdir)
            # Prepare the command to run script_a
            command = ['python', 'ccf_adjusted_params.py', subdir_path]
            if output_directory:
                command.append(output_directory)
            # Run the command
            subprocess.run(command)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python wrapper_script.py <main_directory> [output_directory]")
        sys.exit(1)

    main_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else None

    run_script_in_subfolders(main_directory, output_directory)
