#!/usr/bin/env python3
"""
Enhanced Batch Processing Wrapper for Animal Tracking Data

This script runs the generate_all_params_2025.py script on every subfolder
within a specified parent folder, with options to skip existing CSV files.

Usage:
    python wrapper_generate_all_params_2025.py <parent_folder_path> [output_folder_path] [timeout_seconds]

Arguments:
    parent_folder_path: Path to the parent folder containing subfolders to process
    output_folder_path: Optional. Base path for output folders. If not specified,
                       results will be saved in each respective subfolder.
    timeout_seconds: Optional. Timeout per subfolder (default: 300)

Example:
    python wrapper_generate_all_params_2025.py /data/experiments /data/results 600
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Tuple
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('batch_processing.log')
    ]
)
logger = logging.getLogger(__name__)


def find_processing_script() -> Optional[str]:
    """
    Find the generate_all_params_2025.py script in the same directory as this wrapper script.

    Returns:
        Path to the processing script if found, None otherwise
    """
    # Get the directory where this wrapper script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Look for the processing script in the same directory
    processing_script = os.path.join(script_dir, "generate_all_params_2025.py")

    if os.path.isfile(processing_script):
        return processing_script

    # Fallback to other common locations if not found in same directory
    possible_locations = [
        "generate_all_params_2025.py",  # Current working directory
        "../generate_all_params_2025.py",  # Parent directory
        "scripts/generate_all_params_2025.py",  # Scripts subdirectory
    ]

    for location in possible_locations:
        if os.path.isfile(location):
            return os.path.abspath(location)

    return None


def check_existing_csv_files(subfolder_path: str) -> List[str]:
    """
    Check if CSV files with 'ccf_all_params_file.csv' pattern already exist in the subfolder.

    Args:
        subfolder_path: Path to the subfolder to check

    Returns:
        List of existing CSV files matching the pattern
    """
    pattern = os.path.join(subfolder_path, "*ccf_all_params_file.csv")
    existing_files = glob.glob(pattern)
    return existing_files


def get_subfolders(parent_folder: str) -> list:
    """
    Get all subfolders within the parent folder.

    Args:
        parent_folder: Path to the parent folder

    Returns:
        List of subfolder paths
    """
    subfolders = []

    try:
        for item in os.listdir(parent_folder):
            item_path = os.path.join(parent_folder, item)
            if os.path.isdir(item_path):
                subfolders.append(item_path)

        # Sort subfolders for consistent processing order
        subfolders.sort()

    except PermissionError:
        logger.error(f"Permission denied accessing folder: {parent_folder}")
    except FileNotFoundError:
        logger.error(f"Folder not found: {parent_folder}")

    return subfolders


def categorize_subfolders(subfolders: List[str]) -> Tuple[List[str], List[Tuple[str, List[str]]]]:
    """
    Categorize subfolders into those without existing CSV files and those with existing files.

    Args:
        subfolders: List of subfolder paths

    Returns:
        Tuple of (folders_without_csv, folders_with_csv_and_files)
    """
    folders_without_csv = []
    folders_with_csv = []

    for subfolder in subfolders:
        existing_files = check_existing_csv_files(subfolder)
        if existing_files:
            folders_with_csv.append((subfolder, existing_files))
        else:
            folders_without_csv.append(subfolder)

    return folders_without_csv, folders_with_csv


def show_processing_summary(parent_folder: str, output_folder: Optional[str],
                          folders_without_csv: List[str],
                          folders_with_csv: List[Tuple[str, List[str]]]) -> None:
    """
    Display a summary of what will be processed and where outputs will be saved.

    Args:
        parent_folder: Input parent folder
        output_folder: Output folder (if specified)
        folders_without_csv: Folders without existing CSV files
        folders_with_csv: Folders with existing CSV files
    """
    print("\n" + "="*80)
    print("BATCH PROCESSING SUMMARY")
    print("="*80)
    print(f"INPUT FOLDER: {parent_folder}")

    if output_folder:
        print(f"OUTPUT FOLDER: {output_folder}")
        print("   Results will be saved in subfolders within the output directory")
    else:
        print(f"OUTPUT FOLDER: Same as input folder")
        print("   Results will be saved directly in each respective subfolder")

    print(f"\nFOLDER ANALYSIS:")
    print(f"   Total subfolders found: {len(folders_without_csv) + len(folders_with_csv)}")
    print(f"   Folders without existing CSV: {len(folders_without_csv)}")
    print(f"   Folders with existing CSV: {len(folders_with_csv)}")

    if folders_without_csv:
        print(f"\nFOLDERS TO PROCESS (no existing CSV):")
        for i, folder in enumerate(folders_without_csv[:10], 1):  # Show first 10
            folder_name = os.path.basename(folder)
            if output_folder:
                output_path = os.path.join(output_folder, folder_name)
            else:
                output_path = folder
            print(f"   {i:2d}. {folder_name} -> {output_path}")

        if len(folders_without_csv) > 10:
            print(f"   ... and {len(folders_without_csv) - 10} more folders")

    if folders_with_csv:
        print(f"\nFOLDERS WITH EXISTING CSV FILES:")
        for i, (folder, files) in enumerate(folders_with_csv[:10], 1):  # Show first 10
            folder_name = os.path.basename(folder)
            file_names = [os.path.basename(f) for f in files]
            print(f"   {i:2d}. {folder_name}")
            for file_name in file_names:
                print(f"       {file_name}")

        if len(folders_with_csv) > 10:
            print(f"   ... and {len(folders_with_csv) - 10} more folders with existing files")

    print("="*80)


def ask_user_preference(folders_with_csv: List[Tuple[str, List[str]]]) -> str:
    """
    Ask user what to do with folders that already have CSV files.

    Args:
        folders_with_csv: List of folders with existing CSV files

    Returns:
        User's choice: 'skip', 'recreate', or 'ask_each'
    """
    if not folders_with_csv:
        return 'skip'  # No folders with existing CSV, so doesn't matter

    print(f"\nDECISION NEEDED:")
    print(f"Found {len(folders_with_csv)} folders that already contain CSV files.")
    print("\nWhat would you like to do?")
    print("1. SKIP - Skip all folders with existing CSV files")
    print("2. RECREATE - Recreate CSV files for all folders (overwrite existing)")
    print("3. ASK EACH - Ask for each folder individually")
    print("4. CANCEL - Cancel the entire operation")

    while True:
        choice = input("\nEnter your choice (1/2/3/4): ").strip()

        if choice == '1':
            return 'skip'
        elif choice == '2':
            return 'recreate'
        elif choice == '3':
            return 'ask_each'
        elif choice == '4':
            print("Operation cancelled by user.")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


def should_process_folder(folder_path: str, existing_files: List[str], preference: str) -> bool:
    """
    Determine if a folder should be processed based on user preference.

    Args:
        folder_path: Path to the folder
        existing_files: List of existing CSV files in the folder
        preference: User preference ('skip', 'recreate', 'ask_each')

    Returns:
        True if folder should be processed, False otherwise
    """
    if preference == 'skip':
        return False
    elif preference == 'recreate':
        return True
    elif preference == 'ask_each':
        folder_name = os.path.basename(folder_path)
        print(f"\nFolder: {folder_name}")
        print("   Existing CSV files:")
        for file in existing_files:
            print(f"   {os.path.basename(file)}")

        while True:
            choice = input("   Process this folder? (y/n/q to quit): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no']:
                return False
            elif choice in ['q', 'quit']:
                print("Operation cancelled by user.")
                sys.exit(0)
            else:
                print("   Please enter 'y' for yes, 'n' for no, or 'q' to quit.")

    return False


def run_processing_script(script_path: str, subfolder_path: str, output_folder: Optional[str] = None, timeout: int = 300) -> bool:
    """
    Run the processing script on a single subfolder with real-time output.

    Args:
        script_path: Path to the generate_all_params_2025.py script
        subfolder_path: Path to the subfolder to process
        output_folder: Optional output folder path
        timeout: Timeout in seconds (default: 5 minutes)

    Returns:
        True if processing was successful, False otherwise
    """
    try:
        # Prepare command
        cmd = [sys.executable, script_path, subfolder_path]

        # Add output folder if specified
        if output_folder:
            # Create subfolder-specific output directory
            subfolder_name = os.path.basename(subfolder_path)
            specific_output = os.path.join(output_folder, subfolder_name)
            os.makedirs(specific_output, exist_ok=True)
            cmd.append(specific_output)

        logger.info(f"Running command: {' '.join(cmd)}")
        logger.info(f"Timeout set to {timeout} seconds")

        # Run the script with real-time output streaming
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Stream output in real-time
        output_lines = []
        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_line = output.strip()
                    print(f"    {output_line}")  # Print to console with indentation
                    #logger.info(f"Script: {output_line}")  # Log it too
                    output_lines.append(output_line)

            # Wait for process to complete with timeout
            return_code = process.wait(timeout=timeout)

            if return_code == 0:
                logger.info(f"Successfully processed: {subfolder_path}")
                return True
            else:
                logger.error(f"Script failed with return code {return_code}: {subfolder_path}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ({timeout}s) expired for {subfolder_path}")
            process.kill()  # Kill the process
            process.wait()  # Wait for cleanup
            return False

    except Exception as e:
        logger.error(f"Unexpected error processing {subfolder_path}: {e}")
        return False


def batch_process(parent_folder: str, output_folder: Optional[str] = None, timeout: int = 300) -> None:
    """
    Main batch processing function.

    Args:
        parent_folder: Path to the parent folder containing subfolders to process
        output_folder: Optional base output folder path
        timeout: Timeout per subfolder in seconds (default: 5 minutes)
    """
    # Validate parent folder
    if not os.path.isdir(parent_folder):
        logger.error(f"Parent folder does not exist: {parent_folder}")
        return

    # Find the processing script
    script_path = find_processing_script()
    if not script_path:
        logger.error("Could not find generate_all_params_2025.py script")
        logger.error("Please ensure the script is in the current directory or update the script path")
        return

    logger.info(f"Found processing script at: {script_path}")

    # Create output folder if specified
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"Output will be saved to: {output_folder}")

    # Get all subfolders
    subfolders = get_subfolders(parent_folder)

    if not subfolders:
        logger.warning(f"No subfolders found in: {parent_folder}")
        return

    # Categorize folders by existing CSV files
    folders_without_csv, folders_with_csv = categorize_subfolders(subfolders)

    # Show processing summary
    show_processing_summary(parent_folder, output_folder, folders_without_csv, folders_with_csv)

    # Ask user preference for folders with existing CSV files
    user_preference = ask_user_preference(folders_with_csv)

    # Build final list of folders to process
    folders_to_process = folders_without_csv.copy()

    for folder, existing_files in folders_with_csv:
        if should_process_folder(folder, existing_files, user_preference):
            folders_to_process.append(folder)

    if not folders_to_process:
        print("\nNo folders to process based on your selections.")
        return

    print(f"\nSTARTING PROCESSING")
    print(f"Will process {len(folders_to_process)} out of {len(subfolders)} total folders")

    # Confirm before starting
    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Operation cancelled.")
        return

    # Process each selected subfolder
    successful_count = 0
    failed_count = 0

    for i, subfolder in enumerate(folders_to_process, 1):
        subfolder_name = os.path.basename(subfolder)
        logger.info(f"Processing subfolder {i}/{len(folders_to_process)}: {subfolder_name}")

        success = run_processing_script(script_path, subfolder, output_folder, timeout)

        if success:
            successful_count += 1
        else:
            failed_count += 1

        logger.info(f"Progress: {i}/{len(folders_to_process)} completed")

    # Summary
    print("\n" + "="*50)
    print("FINAL PROCESSING SUMMARY")
    print("="*50)
    print(f"Total subfolders found: {len(subfolders)}")
    print(f"Total subfolders processed: {len(folders_to_process)}")
    print(f"Successful: {successful_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped: {len(subfolders) - len(folders_to_process)}")

    if failed_count > 0:
        logger.warning("Some subfolders failed to process. Check the log for details.")
    else:
        logger.info("All selected subfolders processed successfully!")


def main():
    """Main function to handle command line arguments and start batch processing."""
    if len(sys.argv) < 2:
        print("Usage: python wrapper_generate_all_params_2025.py <parent_folder_path> [output_folder_path] [timeout_seconds]")
        print("\nArguments:")
        print("  parent_folder_path   Path to folder containing subfolders to process")
        print("  output_folder_path   Optional. Base path for output folders")
        print("  timeout_seconds      Optional. Timeout per subfolder (default: 300)")
        print("\nExample:")
        print("  python wrapper_generate_all_params_2025.py /data/experiments")
        print("  python wrapper_generate_all_params_2025.py /data/experiments /data/results")
        print("  python wrapper_generate_all_params_2025.py /data/experiments /data/results 600")
        sys.exit(1)

    # Get arguments
    parent_folder = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else None
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 300

    # Convert to absolute paths
    parent_folder = os.path.abspath(parent_folder)
    if output_folder:
        output_folder = os.path.abspath(output_folder)

    # Log start
    logger.info("Starting batch processing")
    logger.info(f"Parent folder: {parent_folder}")
    if output_folder:
        logger.info(f"Output folder: {output_folder}")
    else:
        logger.info("Output folder: Results will be saved in each respective subfolder")
    logger.info(f"Timeout per subfolder: {timeout} seconds")

    # Start processing
    batch_process(parent_folder, output_folder, timeout)


if __name__ == "__main__":
    main()
