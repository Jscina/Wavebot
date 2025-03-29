"""
Script to calibrate servo motors.

Usage:
  - Directly set a servo angle once:
      ./calibrate_servos.py --channel EYE_LEFT_X --angle 120 \
                            --log-file servo_cal.log
  - Interactive mode (if --channel or --angle not given):
      ./calibrate_servos.py
  - List channels:
      ./calibrate_servos.py --list-channels
"""

import sys
import argparse
import logging
from typing import Optional
from wavebot import set_servo_angle, Channel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servo calibration script.")

    parser.add_argument(
        "--channel", type=str, help="Name of servo channel (e.g. EYE_LEFT_X)."
    )
    parser.add_argument("--angle", type=float, help="Desired angle (e.g. 120.0).")
    parser.add_argument(
        "--log-file", type=str, help="File path for logging (optional)."
    )
    parser.add_argument(
        "--list-channels", action="store_true", help="List available servo channels."
    )

    return parser.parse_args()


def configure_logging(log_file: Optional[str]) -> logging.Logger:
    """Configure logging to console or file."""
    logger = logging.getLogger("servo_calibration")
    logger.setLevel(logging.INFO)

    logger.handlers.clear()

    if log_file:
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    else:
        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def list_channels() -> None:
    """Print available servo channels."""
    print("Available Channels:")
    for ch in Channel:
        print(f"  {ch.name} (value={ch.value})")
    print()


def interactive_mode(logger: logging.Logger) -> None:
    """
    Repeatedly prompt user for a channel name + angle until 'quit'.
    """
    print(
        "Interactive Servo Calibration\n"
        "Type 'list' to see channels, or 'quit' to exit.\n"
        "Format: <channel_name> <angle>\n"
        "Example: EYE_LEFT_X 110\n"
    )

    while True:
        user_input = input("Enter command: ").strip()
        if not user_input:
            continue

        if user_input.lower() in ("quit", "q"):
            print("Exiting interactive mode.")
            break

        if user_input.lower() == "list":
            list_channels()
            continue

        parts = user_input.split()
        if len(parts) != 2:
            print("Invalid input. Use 'list', 'quit', or <channel> <angle>.\n")
            continue

        channel_str, angle_str = parts
        try:
            channel = Channel[channel_str.upper()]
        except KeyError:
            print(f"Unknown channel '{channel_str}'.\n")
            continue

        try:
            angle = float(angle_str)
        except ValueError:
            print(f"Invalid angle '{angle_str}'. Must be numeric.\n")
            continue

        logger.info("Setting channel=%s to angle=%.2f", channel.name, angle)
        set_servo_angle(channel, angle)


def main() -> None:
    args = parse_args()
    logger = configure_logging(args.log_file)

    if args.list_channels:
        list_channels()
        sys.exit(0)

    if args.channel and args.angle is not None:
        try:
            channel = Channel[args.channel.upper()]
        except KeyError:
            print(f"Error: '{args.channel}' is not a valid channel name.\n")
            list_channels()
            sys.exit(1)

        logger.info("Setting channel=%s to angle=%.2f", channel.name, args.angle)
        set_servo_angle(channel, args.angle)
        print(f"Set {channel.name} to {args.angle} degrees.")
        print("Done.")
        sys.exit(0)

    interactive_mode(logger)


if __name__ == "__main__":
    main()
