# pokedat.py
import sys
import os
import json
import argparse
import multiprocessing
import time
import logging
import traceback
from typing import Callable, Optional

from concurrent.futures import ThreadPoolExecutor, as_completed
from text_config import TextConfig
from utilities import get_strings, get_bytes
from tbl_handler import TblHandler


# Configure logging with consistent formatting
class VerbosityFilter(logging.Filter):
    def __init__(self, name=''):
        super().__init__(name)
        self.allow_generated_messages = False
        
    def filter(self, record):
        # Skip messages about files being generated
        if not self.allow_generated_messages and any(x in record.msg for x in ["generated at", "writing", "reading"]):
            return False
        return True

# Configure logging
logging.basicConfig(
    format='[%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO
)

# Create a logger for this module with custom filter
logger = logging.getLogger(__name__)
verbosity_filter = VerbosityFilter()
logger.addFilter(verbosity_filter)

class PokeDatCLI:
    """Command-line interface for the PokeDAT utility."""
    
    @staticmethod
    def display_help() -> None:
        """Displays the program's help message."""
        logger.info("\n=== PokeDAT Switch | by Steins;Traduções ===\n")
        logger.info("Usage:")
        logger.info("  pokedat.exe <command> <input> [output] --version=<version> [--format=<format>]\n")
        logger.info("Commands:")
        logger.info("  read       <file or folder> [output_folder]  -  Extracts texts")
        logger.info("  write      <input_file or folder> <output_folder>  -  Generates .dat files\n")
        logger.info("Supported versions: LGPE, SWSH, LA, SV, LZA")
        logger.info("Supported formats: json, txt\n")
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """Parse and validate command line arguments."""
        parser = argparse.ArgumentParser(
            description="PokeDAT Switch | by Steins;Traduções",
            usage="pokedat.py {read,write} input [output] --version={LGPE,SWSH,LA,SV,LZA} [--format={json,txt}] [-h]\n")
        parser.add_argument("command", choices=["read", "write"], help="Command to execute")
        parser.add_argument("input", help="Input file or folder")
        parser.add_argument("output", nargs="?", help="Output folder (optional for 'read')")
        parser.add_argument("--version", required=True, choices=["LGPE", "SWSH", "LA", "SV", "LZA"],
                            help="Game version (e.g., LGPE, SWSH, LA, SV, LZA)")
        parser.add_argument("--format", choices=["json", "txt"], default="json",
                            help="Output/input format (default: json)")
        return parser.parse_args()


class DatReader:
    """Handles reading and extracting content from DAT files."""
    
    def __init__(self, config: TextConfig):
        self.config = config
    
    def read_dat_file(self, file_path: str) -> list[str] | None:
        """Read a .dat file and extract strings."""
        try:
            with open(file_path, 'rb', buffering=1024 * 1024) as f:
                data = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None

        lines = get_strings(data, self.config)
        if lines is None:
            logger.error(f"Error extracting strings from {file_path}")
        return lines
    def process_file(self, file_path: str, input_root: str, output_folder: Optional[str] = None) -> None:
        """Process a .dat file and extract its texts to JSON format."""
        lines = self.read_dat_file(file_path)
        if not lines:
            return

        # Attempt to load the corresponding .tbl
        labels = []
        try:
            tbl_handler = TblHandler(file_path)
            labels = tbl_handler.get_labels()
        except Exception as e:
            logger.warning(f"Warning: {str(e)}")

        if output_folder:
            # Prepare JSON data
            json_data = []
            for idx, line in enumerate(lines):
                entry = {
                    "id": labels[idx]["id"] if idx < len(labels) else f"UNKNOWN_{idx}",
                    "hash": hex(labels[idx]["hash"]) if idx < len(labels) else "N/A",
                    "text": line
                }
                json_data.append(entry)

            # Define the JSON file path
            relative = os.path.relpath(file_path, start=input_root)
            relative_no_ext, _ = os.path.splitext(relative)
            json_path = os.path.join(output_folder, f"{relative_no_ext}.json")
            os.makedirs(os.path.dirname(json_path), exist_ok=True)

            try:
                # Write JSON with UTF-8 encoding
                with open(json_path, 'w', encoding='utf-8') as f_json:
                    json.dump(json_data, f_json, ensure_ascii=False, indent=4)
                # Silent success
            except Exception as e:
                logger.error(f"Error writing JSON to {json_path}: {e}")
        else:
            # Display extracted texts
            logger.info(f"--- {os.path.basename(file_path)} ---")
            for line in lines:
                logger.info(f"{line}")
    def process_file_txt(self, file_path: str, input_root: str, output_folder: Optional[str] = None) -> None:
        lines = self.read_dat_file(file_path)
        if not lines:
            return

        if output_folder:
            relative = os.path.relpath(file_path, start=input_root)
            relative_no_ext, _ = os.path.splitext(relative)
            txt_path = os.path.join(output_folder, f"{relative_no_ext}.txt")
            os.makedirs(os.path.dirname(txt_path), exist_ok=True)

            try:
                with open(txt_path, 'w', encoding='utf-8') as f_txt:
                    for line in lines:
                        f_txt.write(f"{line}\n")
                logger.info(f"TXT generated at {txt_path}")
            except Exception as e:
                logger.error(f"Error writing TXT to {txt_path}: {e}")
        else:
            logger.info(f"--- {os.path.basename(file_path)} ---")
            for line in lines:
                logger.info(f"{line}")
    def process_directory(self, input_folder: str, output_folder: Optional[str] = None,
                        max_workers: Optional[int] = None,
                        process_func: Optional[Callable[[str, str, Optional[str]], None]] = None) -> None:

        if process_func is None:
            process_func = self.process_file

        if not os.path.isdir(input_folder):
            logger.error(f"Folder not found: {input_folder}")
            sys.exit(1)

        files = [os.path.join(root, name)
                for root, _, filenames in os.walk(input_folder)
                for name in filenames if name.endswith('.dat')]

        if not files:
            logger.warning(f"No .dat files found in {input_folder} or subfolders")
            return

        # Dynamically adjust max_workers
        max_workers = min(max_workers or (multiprocessing.cpu_count() * 2), len(files))

        logger.info(f"Starting processing of {len(files)} files with {max_workers} workers")
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_func, file, input_folder, output_folder): file for file in files}
            for idx, future in enumerate(as_completed(futures), start=1):
                try:
                    future.result()
                    # Show status with relative path
                    rel_path = os.path.relpath(futures[future], start=input_folder)
                    logger.info(f"[{idx}/{len(files)}] Processed: {rel_path}")
                except Exception as e:
                    logger.error(f"Error during processing {futures[future]}: {e}")

        elapsed_time = time.perf_counter() - start_time
        files_per_second = len(files) / elapsed_time if elapsed_time > 0 else 0
        logger.info(f"Completed {len(files)} files in {elapsed_time:.2f} seconds ({files_per_second:.2f} files/sec)")


class DatWriter:
    """Handles writing content to DAT files."""
    
    def __init__(self, config: TextConfig):
        self.config = config
        self.success_count = 0
        self.error_count = 0
        self.error_files = []
    
    def process_file_json(self, json_path: str, input_root: str, output_folder: str) -> bool:
        """Process a JSON file and generate the corresponding .dat file."""
        output_path = None
        try:
            with open(json_path, 'r', encoding='utf-8', buffering=1024*1024) as f:
                json_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"\033[91m✗ JSON PARSE ERROR in {json_path}:\n    Line {e.lineno}, Column {e.colno}: {e.msg}\033[0m")
            return False
        except Exception as e:
            logger.error(f"\033[91m✗ ERROR reading JSON {json_path}: {e}\033[0m")
            return False

        try:
            lines = []
            for idx, entry in enumerate(json_data):
                if not isinstance(entry, dict):
                    logger.error(f"\033[91m✗ ERROR in {json_path}:\n    Entry #{idx} is not a valid object (expected dict, got {type(entry).__name__})\033[0m")
                    return False
                if "text" not in entry:
                    logger.error(f"\033[91m✗ ERROR in {json_path}:\n    Entry #{idx} missing 'text' field. Available fields: {list(entry.keys())}\033[0m")
                    return False
                lines.append(entry["text"])
            
            flags = [0] * len(lines)
            try:
                data = get_bytes(lines, flags, self.config)
            except Exception as e:
                logger.error(f"\033[91m✗ ERROR converting text to bytes in {json_path}:\n    {type(e).__name__}: {e}\n    Total entries: {len(lines)}\033[0m")
                return False

            relative = os.path.relpath(json_path, start=input_root)
            relative_no_ext, _ = os.path.splitext(relative)
            output_path = os.path.join(output_folder, f"{relative_no_ext}.dat")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'wb', buffering=1024*1024) as f:
                f.write(data)
            logger.info(f"File {os.path.basename(output_path)} generated at {output_path}")
            return True
        except KeyError as e:
            location = f" to {output_path}" if output_path else f" in {json_path}"
            logger.error(f"\033[91m✗ KEY ERROR writing .dat{location}:\n    Missing key: {e}\033[0m")
            return False
        except Exception as e:
            location = f" to {output_path}" if output_path else f" from {json_path}"
            tb = traceback.format_exc()
            logger.error(f"\033[91m✗ ERROR writing .dat{location}:\n    {type(e).__name__}: {e}\n\nTraceback:\n{tb}\033[0m")
            return False
    
    def process_file_txt(self, txt_path: str, input_root: str, output_folder: str) -> bool:
        """Process a TXT file and generate the corresponding .dat file."""
        output_path = None
        try:
            with open(txt_path, 'r', encoding='utf-8', buffering=1024*1024) as f:
                lines = [line.strip() for line in f if line.strip()]
        except UnicodeDecodeError as e:
            logger.error(f"\033[91m✗ ENCODING ERROR in {txt_path}:\n    Position {e.start}-{e.end}: {e.reason}\033[0m")
            return False
        except Exception as e:
            logger.error(f"\033[91m✗ ERROR reading TXT {txt_path}:\n    {type(e).__name__}: {e}\033[0m")
            return False

        try:
            flags = [0] * len(lines)
            try:
                data = get_bytes(lines, flags, self.config)
            except Exception as e:
                logger.error(f"\033[91m✗ ERROR converting text to bytes in {txt_path}:\n    {type(e).__name__}: {e}\n    Total lines: {len(lines)}\033[0m")
                return False

            relative = os.path.relpath(txt_path, start=input_root)
            relative_no_ext, _ = os.path.splitext(relative)
            output_path = os.path.join(output_folder, f"{relative_no_ext}.dat")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'wb', buffering=1024*1024) as f:
                f.write(data)
            logger.info(f"File {os.path.basename(output_path)} generated at {output_path}")
            return True
        except Exception as e:
            location = f" to {output_path}" if output_path else f" from {txt_path}"
            tb = traceback.format_exc()
            logger.error(f"\033[91m✗ ERROR writing .dat{location}:\n    {type(e).__name__}: {e}\n\nTraceback:\n{tb}\033[0m")
            return False
    
    def process_directory(self, input_folder: str, output_folder: str,
                        max_workers: Optional[int] = None, file_pattern="*.json",
                        process_func: Optional[Callable[[str, str, str], bool]] = None) -> None:
        """Process all input files in a directory with multithreading."""
        if process_func is None:
            process_func = self.process_file_json

        if not os.path.isdir(input_folder):
            logger.error(f"Input folder not found: {input_folder}")
            sys.exit(1)

        files = [os.path.join(root, name)
                for root, _, filenames in os.walk(input_folder)
                for name in filenames if name.endswith(file_pattern[1:])]

        if not files:
            logger.warning(f"No {file_pattern} files found in {input_folder} or subfolders")
            return

        # Reset counters
        self.success_count = 0
        self.error_count = 0
        self.error_files = []

        # Dynamically adjust max_workers
        max_workers = min(max_workers or (multiprocessing.cpu_count() * 2), len(files))

        logger.info(f"Starting processing of {len(files)} files with {max_workers} workers")
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_func, file, input_folder, output_folder): file for file in files}
            for idx, future in enumerate(as_completed(futures), start=1):
                file_path = futures[future]
                rel_path = os.path.relpath(file_path, start=input_folder)
                try:
                    success = future.result()
                    if success:
                        self.success_count += 1
                        logger.info(f"[{idx}/{len(files)}] ✓ Processed: {rel_path}")
                    else:
                        # Error details already logged in process_file_* methods
                        self.error_count += 1
                        self.error_files.append(rel_path)
                except Exception as e:
                    # Unexpected exception not caught by process_file_* methods
                    self.error_count += 1
                    self.error_files.append(rel_path)
                    logger.error(f"\033[91m[{idx}/{len(files)}] ✗ UNEXPECTED ERROR processing {rel_path}:\n    {type(e).__name__}: {e}\033[0m")

        elapsed_time = time.perf_counter() - start_time
        files_per_second = len(files) / elapsed_time if elapsed_time > 0 else 0
        
        # Display summary
        logger.info("\n" + "="*60)
        logger.info("COMPILATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total files: {len(files)}")
        logger.info(f"\033[92m✓ Successful: {self.success_count}\033[0m")
        if self.error_count > 0:
            logger.error(f"\033[91m✗ Failed: {self.error_count}\033[0m")
            logger.error("\nFailed files:")
            for error_file in self.error_files:
                logger.error(f"\033[91m  - {error_file}\033[0m")
        else:
            logger.info("\033[92m✓ All files compiled successfully!\033[0m")
        logger.info(f"\nTime: {elapsed_time:.2f} seconds ({files_per_second:.2f} files/sec)")
        logger.info("="*60 + "\n")


def run_read(args: argparse.Namespace, config: TextConfig) -> None:
    reader = DatReader(config)
    read_format_map = {
        "json": reader.process_file,
        "txt": reader.process_file_txt,
    }
    process_func = read_format_map[args.format]

    if os.path.isdir(args.input):
        reader.process_directory(args.input, args.output, process_func=process_func)
    else:
        input_root = os.path.dirname(args.input)
        process_func(args.input, input_root, args.output)


def run_write(args: argparse.Namespace, config: TextConfig) -> None:
    if not args.output:
        logger.error("Missing output path for 'write' command.")
        sys.exit(1)

    writer = DatWriter(config)
    write_format_map = {
        "json": ("*.json", writer.process_file_json),
        "txt": ("*.txt", writer.process_file_txt),
    }
    file_pattern, process_func = write_format_map[args.format]

    if os.path.isdir(args.input):
        writer.process_directory(args.input, args.output,
                            file_pattern=file_pattern, process_func=process_func)
    else:
        input_root = os.path.dirname(args.input)
        process_func(args.input, input_root, args.output)


def main() -> None:
    """Main entry point for the application."""
    args = PokeDatCLI.parse_args()
    config = TextConfig(args.version)

    if args.command == "read":
        run_read(args, config)
    elif args.command == "write":
        run_write(args, config)


if __name__ == "__main__":
    main()