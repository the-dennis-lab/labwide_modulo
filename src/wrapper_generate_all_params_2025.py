def main():
    """Main function to handle command line arguments and start batch processing."""
    if len(sys.argv) < 2:
        print("Usage: python batch_process_wrapper.py <parent_folder_path> [output_folder_path] [timeout_seconds]")
        print("\nArguments:")
        print("  parent_folder_path   Path to folder containing subfolders to process")
        print("  output_folder_path   Optional. Base path for output folders")
        print("  timeout_seconds      Optional. Timeout per subfolder (default: 300)")
        print("\nExample:")
        print("  python batch_process_wrapper.py /data/experiments")
        print("  python batch_process_wrapper.py /data/experiments /data/results")
        print("  python batch_process_wrapper.py /data/experiments /data/results 600")
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
    batch_process(parent_folder, output_folder, timeout)#!/usr/bin/env python3
"""
Batch Processing Wrapper for Animal Tracking Data

This script runs the generate_all_params_2025.py script on every subfolder
within a specified parent folder.

Usage:
    python batch_process_wrapper.py <parent_folder_path> [output_folder_path]

Arguments:
    parent_folder_path: Path to the parent folder containing subfolders to process
    output_folder_path: Optional. Base path for output folders. If not specified,
                       results will be saved in each respective subfolder.

Example:
    python batch_process_wrapper.py /data/experiments /data/results
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

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
                    logger.info(f"Script: {output_line}")  # Log it too
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

    logger.info(f"Found {len(subfolders)} subfolders to process")

    # Process each subfolder
    successful_count = 0
    failed_count = 0

    for i, subfolder in enumerate(subfolders, 1):
        subfolder_name = os.path.basename(subfolder)
        logger.info(f"Processing subfolder {i}/{len(subfolders)}: {subfolder_name}")

        success = run_processing_script(script_path, subfolder, output_folder, timeout)

        if success:
            successful_count += 1
        else:
            failed_count += 1

        logger.info(f"Progress: {i}/{len(subfolders)} completed")

    # Summary
    logger.info("=" * 50)
    logger.info("BATCH PROCESSING SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Total subfolders processed: {len(subfolders)}")
    logger.info(f"Successful: {successful_count}")
    logger.info(f"Failed: {failed_count}")

    if failed_count > 0:
        logger.warning("Some subfolders failed to process. Check the log for details.")
    else:
        logger.info("All subfolders processed successfully!")


def main():
    """Main function to handle command line arguments and start batch processing."""
    if len(sys.argv) < 2:
        print("Usage: python batch_process_wrapper.py <parent_folder_path> [output_folder_path]")
        print("\nArguments:")
        print("  parent_folder_path   Path to folder containing subfolders to process")
        print("  output_folder_path   Optional. Base path for output folders")
        print("\nExample:")
        print("  python batch_process_wrapper.py /data/experiments")
        print("  python batch_process_wrapper.py /data/experiments /data/results")
        sys.exit(1)

    # Get arguments
    parent_folder = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else None

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

    # Start processing
    batch_process(parent_folder, output_folder)


if __name__ == "__main__":
    main()
