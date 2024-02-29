import argparse
import os
from colorama import Fore

def parse_arguments():
    parser = argparse.ArgumentParser(description='Starts the API.')
    parser.add_argument('--dev', action='store_true', help='Run in development mode.')
    parser.add_argument('--prod', action='store_true', help='Run in production mode.')
    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    if args.dev:
        port = 1339
        reload_option = "--reload"
        workers_option = ""
    elif args.prod:
        port = 1338
        reload_option = ""
        workers_option = "--workers 8"
    else:
        raise SystemExit(f"{Fore.RED}ERROR: {Fore.RESET}You didn't select a mode.")

    os.system(f"uvicorn api.main:app --host 0.0.0.0 --port {port} {reload_option} {workers_option}")

if __name__ == "__main__":
    main()