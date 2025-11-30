#!/usr/bin/env python3
import argparse
import os
import random
import socket
import subprocess
import sys
import time
import hashlib
import signal
from pathlib import Path

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.panel import Panel
from rich import box
from pyfiglet import figlet_format
from InquirerPy import inquirer

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT_DIR / "config" / "labs.yaml"

console = Console()

current_compose_file = None
current_project_name = None


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def pick_flag(flag_pool):
    flag = random.choice(flag_pool)
    flag_hash = hashlib.sha256(flag.encode()).hexdigest()
    return flag, flag_hash


def check_port_available(port: int) -> bool:
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", port))
        s.close()
        return True
    except OSError:
        return False


def choose_port(default_port: int, override_port: int | None) -> int:
    if override_port is not None:
        if check_port_available(override_port):
            return override_port
        console.print(f"[yellow]Port {override_port} is in use.[/yellow]")

    if check_port_available(default_port):
        return default_port
    console.print(f"[yellow]Default port {default_port} is in use.[/yellow]")

    while True:
        new_port = int(Prompt.ask("Enter a different port"))
        if check_port_available(new_port):
            return new_port
        console.print(f"[yellow]Port {new_port} also in use.[/yellow]")


def wait_for_port(port: int, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        if not check_port_available(port):
            return True
        time.sleep(1)
    return False


def teardown_lab():
    global current_compose_file, current_project_name

    if not current_compose_file:
        return

    console.print("[cyan]Tearing down lab and wiping data...[/cyan]")
    try:
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(current_compose_file),
                "-p",
                current_project_name,
                "down",
                "-v",
            ],
            check=False,
        )
    finally:
        current_compose_file = None
        current_project_name = None


def sigint_handler(sig, frame):
    console.print("\n[red]Interrupted. Cleaning up lab...[/red]")
    teardown_lab()
    sys.exit(1)


signal.signal(signal.SIGINT, sigint_handler)


def run_one_lab(cfg, args):
    """Run a single lab from selection to teardown. Returns when finished."""
    global current_compose_file, current_project_name

    # --- 1) Select OWASP LLM category ---
    vuln_keys = list(cfg.keys())
    vuln_choice = inquirer.select(
        message="Select OWASP LLM vulnerability:",
        choices=[f"{key} - {cfg[key].get('name', '')}" for key in vuln_keys],
    ).execute()

    selected_vuln = vuln_choice.split(" ", 1)[0]
    vuln_cfg = cfg[selected_vuln]
    labs = vuln_cfg["labs"]

    # --- 2) Select lab ---
    lab_keys = list(labs.keys())
    lab_choice = inquirer.select(
        message="Select lab:",
        choices=[f"{x} - {labs[x].get('title', '')}" for x in lab_keys],
    ).execute()

    selected_lab_id = lab_choice.split(" ", 1)[0]
    lab_cfg = labs[selected_lab_id]

    # --- 3) Select difficulty ---
    difficulty_keys = list(lab_cfg["difficulty"].keys())
    difficulty = inquirer.select(
        message="Select difficulty:",
        choices=difficulty_keys,
    ).execute()

    diff_cfg = lab_cfg["difficulty"][difficulty]

    # --- 4) Port selection ---
    default_port = lab_cfg["default_port"]
    host_port = choose_port(default_port, args.port)

    # --- 5) Random flag ---
    chosen_flag, flag_hash = pick_flag(diff_cfg["flag_pool"])

    # --- 6) Compose/Dockerfile paths ---
    compose_file = ROOT_DIR / diff_cfg["compose_file"]
    dockerfile = ROOT_DIR / diff_cfg["dockerfile"]

    if not compose_file.exists():
        console.print(f"[red]Compose file not found:[/red] {compose_file}")
        sys.exit(1)
    if not dockerfile.exists():
        console.print(f"[red]Dockerfile not found:[/red] {dockerfile}")
        sys.exit(1)

    current_compose_file = compose_file
    current_project_name = f"{selected_vuln.lower()}_{selected_lab_id.lower()}_{difficulty}"

    env = os.environ.copy()
    env["HOST_PORT"] = str(host_port)
    env["DIFFICULTY"] = difficulty
    env["FLAG_SHA256"] = flag_hash
    env["FLAG_PLAIN"] = chosen_flag

    # --- 7) Spin up Docker with progress ---
    docker_cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_file),
        "-p",
        current_project_name,
        "up",
        "--build",
        "-d",
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Spinning up Docker lab...", start=True)

        try:
            subprocess.run(docker_cmd, check=True, env=env, cwd=ROOT_DIR)
        except subprocess.CalledProcessError as e:
            progress.update(task, description="Docker startup failed.")
            console.print(f"[red]Docker error:[/red] {e}")
            teardown_lab()
            return  # Return to menu instead of killing script

        progress.update(task, description="Waiting for lab to become ready...")

        if not wait_for_port(host_port):
            progress.update(task, description="Lab failed to start.")
            console.print("[red]Lab did not start properly.[/red]")
            teardown_lab()
            return  # Back to menu

    url = f"http://localhost:{host_port}"

    console.print(
        Panel.fit(
            f"[bold green]Lab is ready![/bold green]\n\n"
            f"OWASP LLM: [cyan]{selected_vuln}[/cyan]\n"
            f"Lab: [cyan]{selected_lab_id}[/cyan]\n"
            f"Difficulty: [cyan]{difficulty}[/cyan]\n\n"
            f"Access the lab at:\n[bold]{url}[/bold]\n\n"
            f"Once you obtain the flag, paste it below.",
            border_style="green",
            box=box.ROUNDED,
        )
    )

    # --- 8) Flag loop ---
    while True:
        flag_input = Prompt.ask("\nPaste your flag")

        with Progress(
            SpinnerColumn(),
            TextColumn("Validating flag..."),
            transient=True,
        ) as p:
            t = p.add_task("", start=True)
            time.sleep(1.2)

        if hashlib.sha256(flag_input.encode()).hexdigest() == flag_hash:
            console.print(
                Panel.fit(
                    "[bold green]VICTORY![/bold green]\nFlag is correct.",
                    border_style="green",
                    box=box.DOUBLE,
                )
            )
            break
        else:
            console.print("[bold red]Incorrect flag. Try again.[/bold red]")

    # --- 9) Teardown & return to menu ---
    teardown_lab()
    console.print("[bold]Lab cleaned up.[/bold]\n")


def main():
    parser = argparse.ArgumentParser(description="LLM OWASP Labs Controller")
    parser.add_argument("-p", "--port", type=int, help="Override default host port")
    args = parser.parse_args()

    cfg = load_config()

    banner = figlet_format("LLM OWASP LABS")
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    console.print("[bold]Welcome to the LLM OWASP practice range.[/bold]\n")

    while True:
        # Run one full lab from selection → victory → teardown
        run_one_lab(cfg, args)

        # After teardown, ask if the user wants another round
        again = inquirer.select(
            message="What would you like to do next?",
            choices=[
                "Start another lab",
                "Exit",
            ],
        ).execute()

        if again == "Exit":
            console.print("[bold]Goodbye. See you in the next engagement.[/bold]")
            break
        # else loop continues and shows the menu again


if __name__ == "__main__":
    main()
