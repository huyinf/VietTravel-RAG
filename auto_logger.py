#!/usr/bin/env python3
"""
Auto Logger for CtrlColor
=========================

Automatically captures all logs when running any Python command.
Usage: python auto_logger.py <your_command>

Examples:
  python auto_logger.py test.py
  python auto_logger.py quick_test.py
  python auto_logger.py run_full_tests.py --scenario basic
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class AutoLogger:
    """Automatic command logging system"""

    def __init__(self, log_dir="./command_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.process = None
        self.log_file = None

    def generate_log_filename(self, command):
        """Generate a unique log filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean command for filename
        cmd_clean = command[0].replace(".py", "").replace("/", "_").replace("\\", "_")
        if len(command) > 1:
            cmd_clean += f"_{'_'.join(command[1:3])}"  # Add first 2 args

        return f"{timestamp}_{cmd_clean}.log"

    def run_with_logging(self, command):
        """Run command and capture all output to log file"""
        log_filename = self.generate_log_filename(command)
        log_path = self.log_dir / log_filename

        print(f"Running: {' '.join(command)}")
        print(f"Logging to: {log_path}")
        print("=" * 60)

        # Create log file with header
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("CtrlColor Command Log\n")
            f.write(f"{'=' * 50}\n")
            f.write(f"Command: {' '.join(command)}\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write(f"Working Directory: {os.getcwd()}\n")
            f.write(f"Python: {sys.executable}\n")
            f.write(f"{'=' * 50}\n\n")

        try:
            # Start the process
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                universal_newlines=True,
                bufsize=1,  # Line buffered
            )

            # Real-time output and logging
            with open(log_path, "a", encoding="utf-8") as log_file:
                self.log_file = log_file

                while True:
                    output = self.process.stdout.readline()
                    if output == "" and self.process.poll() is not None:
                        break

                    if output:
                        # Print to console
                        print(output.strip())

                        # Write to log file with timestamp
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        log_file.write(f"[{timestamp}] {output}")
                        log_file.flush()

                # Get return code
                return_code = self.process.poll()

                # Write footer
                end_time = datetime.now().isoformat()
                log_file.write(f"\n{'=' * 50}\n")
                log_file.write(f"Finished: {end_time}\n")
                log_file.write(f"Return Code: {return_code}\n")
                log_file.write(f"{'=' * 50}\n")

                print("=" * 60)
                if return_code == 0:
                    print("Command completed successfully")
                else:
                    print(f"Command failed with return code: {return_code}")
                print(f"Full log saved to: {log_path}")

                return return_code

        except KeyboardInterrupt:
            print("\nInterrupted by user")
            if self.process:
                self.process.terminate()
                self.process.wait()

            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n{'=' * 50}\n")
                log_file.write(f"INTERRUPTED: {datetime.now().isoformat()}\n")
                log_file.write(f"{'=' * 50}\n")

            return 130  # Standard exit code for Ctrl+C

        except Exception as e:
            print(f"Error running command: {e}")

            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"\n{'=' * 50}\n")
                log_file.write(f"ERROR: {e}\n")
                log_file.write(f"Time: {datetime.now().isoformat()}\n")
                log_file.write(f"{'=' * 50}\n")

            return 1


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Auto Logger for CtrlColor")
        print("=" * 30)
        print("Usage: python auto_logger.py <command> [args...]")
        print("")
        print("Examples:")
        print("  python auto_logger.py test.py")
        print("  python auto_logger.py quick_test.py")
        print("  python auto_logger.py run_full_tests.py --scenario basic")
        print("  python auto_logger.py python test.py")
        print("")
        print("All output will be captured to ./command_logs/")
        return 1

    # Parse command
    command = sys.argv[1:]

    # If first argument doesn't start with 'python' and ends with '.py', prepend 'python'
    if command[0].endswith(".py") and not command[0].startswith("python"):
        command = ["python"] + command

    # Create logger and run
    logger = AutoLogger()
    return logger.run_with_logging(command)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
