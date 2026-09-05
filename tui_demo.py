"""Textual front end for the Ubuntu workstation bootstrapper.

The interface is preview-only by default.  Passing ``--apply`` explicitly
enables the real apply path in ``bootstrap.sh``.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Static

SCRIPT_DIR = Path(__file__).resolve().parent

CAPABILITIES = {
    "personal": (
        "Personal configuration",
        "Shell, tmux, Ghostty, Starship, and editor preferences",
        True,
    ),
    "workspace-foundation": (
        "Workspace foundation",
        "Project layout and a small set of durable working principles",
        True,
    ),
    "core-tools": (
        "Core command-line tools",
        "Git, curl, build essentials, and bootstrap requirements",
        True,
    ),
    "optional": (
        "Optional tools",
        "Extra utilities you can add without changing the base profile",
        False,
    ),
}


class BootstrapPreview(App):
    """Small, review-first UI over the existing bootstrap shell script."""

    CSS = """
    Screen {
        background: #080d18;
        color: #d8dee9;
    }

    #topbar {
        height: 3;
        color: #88c0d0;
        text-style: bold;
        padding: 1 2;
    }

    #workspace {
        height: 1fr;
        layout: horizontal;
        align: center top;
        padding: 0 2 1 2;
    }

    #rail {
        width: 24;
        height: 1fr;
        border: round #22324a;
        background: #101b2d;
        padding: 2 2;
    }

    #rail-kicker {
        color: #88c0d0;
        text-style: bold;
        margin-bottom: 1;
    }

    #rail-title {
        color: #eceff4;
        text-style: bold;
    }

    #rail-version {
        color: #7d8799;
        margin-bottom: 2;
    }

    .rail-step {
        color: #7d8799;
        height: 2;
        padding: 0 1;
        margin-bottom: 1;
    }

    .rail-step.active {
        color: #88c0d0;
        background: #1a2b43;
        text-style: bold;
    }

    #rail-copy {
        color: #8f98ab;
        margin-top: 8;
    }

    #main {
        width: 1fr;
        height: 1fr;
        max-width: 105;
        padding: 1 5;
    }

    .eyebrow {
        color: #88c0d0;
        text-style: bold;
        margin-bottom: 1;
    }

    #step-label, #review-step-label {
        color: #81a1c1;
        text-style: bold;
    }

    #title, #review-title {
        color: #eceff4;
        text-style: bold;
        margin: 1 0 0 0;
    }

    #subtitle, #review-subtitle {
        color: #8fbcbb;
        margin: 0 0 2 0;
    }

    #question-row {
        height: 2;
        layout: horizontal;
        align: left middle;
        margin-bottom: 1;
    }

    #question {
        color: #d8dee9;
        text-style: bold;
    }

    #selection-count {
        color: #8f98ab;
        margin-left: 2;
    }

    .capability-row {
        height: 4;
        background: #101b2d;
        border: round #22324a;
        padding: 0 1;
        margin-bottom: 1;
    }

    Button.capability-toggle {
        width: 1fr;
        height: 2;
        padding: 0 1;
        background: #141f31;
        color: #8b98aa;
        border: none;
        content-align: left middle;
        text-align: left;
        text-style: bold;
    }

    Button.capability-toggle.selected {
        color: #eceff4;
    }

    Button.capability-toggle:hover {
        background: #19283d;
    }

    Button.capability-toggle:focus {
        background: #203753;
        border-left: thick #88c0d0;
        outline: none;
    }

    .capability-description {
        color: #7d8799;
        padding: 0 2;
        height: 1;
    }

    #selection-detail {
        color: #8f98ab;
        margin: 1 0 2 0;
    }

    #safety, #review-safety {
        color: #a3be8c;
        background: #15251f;
        border-left: thick #a3be8c;
        height: 2;
        padding: 0 2;
        margin: 0 0 2 0;
    }

    #status, #review-status {
        color: #8fbcbb;
        margin: 0 0 1 0;
    }

    #review-view {
        display: none;
    }

    #review-list, #backend-output {
        color: #d8dee9;
        background: #141f31;
        border-left: thick #5e81ac;
        padding: 1 2;
        margin: 1 0 2 0;
    }

    #review-list {
        height: 6;
    }

    #backend-output {
        max-height: 10;
        overflow-y: auto;
    }

    #review-actions {
        height: 3;
        layout: horizontal;
        align: left middle;
    }

    #back {
        width: 14;
        margin-right: 1;
    }

    #apply {
        width: 22;
    }

    Button.primary {
        background: #5e81ac;
        color: #eceff4;
    }

    Footer {
        background: #080d18;
        color: #d8dee9;
    }
    """

    BINDINGS: ClassVar = [
        ("q", "quit", "Quit"),
        ("r", "reset", "Reset"),
    ]

    def __init__(
        self,
        *,
        apply_mode: bool = False,
        no_packages: bool = False,
        destination: str | None = None,
        workspace: str | None = None,
    ) -> None:
        super().__init__()
        self.apply_mode = apply_mode
        self.no_packages = no_packages
        self.destination = destination
        self.workspace = workspace
        self.selections = {key: details[2] for key, details in CAPABILITIES.items()}

    def compose(self) -> ComposeResult:
        mode_label = "APPLY ENABLED" if self.apply_mode else "PREVIEW MODE"
        action_label = "Accept and apply" if self.apply_mode else "Run preview"
        safety_text = (
            "APPLY ENABLED  ·  Accept will run the installer on this machine"
            if self.apply_mode
            else "SAFE BY DEFAULT  ·  Preview mode  ·  nothing changes on this screen"
        )

        yield Static(
            f"WORKSTATION BOOTSTRAP   ·   UBUNTU 26.04 LTS   ·   {mode_label}",
            id="topbar",
        )
        with Container(id="workspace"):
            with Vertical(id="rail"):
                yield Static("SETUP", id="rail-kicker")
                yield Static("Ubuntu workstation", id="rail-title")
                yield Static("v0.1 · preview only", id="rail-version")
                yield Static(
                    "1  Profile", id="rail-profile", classes="rail-step active"
                )
                yield Static("2  Components", id="rail-components", classes="rail-step")
                yield Static("3  Review", id="rail-review", classes="rail-step")
                yield Static("4  Apply", id="rail-apply", classes="rail-step")
                yield Static(
                    "First choose the outcome. Then review every concrete change before applying it.",
                    id="rail-copy",
                )

            with Container(id="main"):
                with Vertical(id="profile-view"):
                    yield Static("STEP 1 OF 4", id="step-label")
                    yield Static("Prepare your Ubuntu workstation", id="title")
                    yield Static(
                        "Choose what you would like to set up today.",
                        id="subtitle",
                    )
                    with Horizontal(id="question-row"):
                        yield Static("What would you like to set up?", id="question")
                        yield Static("3 selected", id="selection-count")
                    yield Static("CAPABILITIES", classes="eyebrow")
                    for key, (_, description, _) in CAPABILITIES.items():
                        with Vertical(classes="capability-row"):
                            yield Button(
                                self._capability_label(key),
                                id=key,
                                classes="capability-toggle selected"
                                if self.selections[key]
                                else "capability-toggle",
                            )
                            yield Static(
                                description,
                                classes="capability-description",
                            )
                    yield Static(
                        "3 base capabilities will be included in the next review step.",
                        id="selection-detail",
                    )
                    yield Static(safety_text, id="safety")
                    yield Static(
                        "STATUS  ·  Preview only  ·  No files or packages will be changed"
                        if not self.apply_mode
                        else "STATUS  ·  Apply enabled  ·  Review before changing this machine",
                        id="status",
                    )
                    yield Button("Review changes", variant="primary", id="review")

                with Vertical(id="review-view"):
                    yield Static("STEP 3 OF 4", id="review-step-label")
                    yield Static("Review before applying", id="review-title")
                    yield Static(
                        "Confirm the selected layers before anything is changed.",
                        id="review-subtitle",
                    )
                    yield Static("SELECTED CAPABILITIES", classes="eyebrow")
                    yield Static(self._review_text(), id="review-list")
                    yield Static("WHAT WILL HAPPEN", classes="eyebrow")
                    yield Static(
                        "The installer will run in preview mode and report its plan without changing files."
                        if not self.apply_mode
                        else "The installer will apply the selected profile after you confirm this button.",
                        id="review-detail",
                    )
                    yield Static(
                        "SAFE BY DEFAULT  ·  Preview only  ·  no files or packages will be changed"
                        if not self.apply_mode
                        else "APPLY ENABLED  ·  This will change the selected destination",
                        id="review-safety",
                    )
                    yield Static("READY · Nothing has been run yet", id="review-status")
                    yield Static("BACKEND OUTPUT", classes="eyebrow")
                    yield Static("No backend run yet.", id="backend-output")
                    with Horizontal(id="review-actions"):
                        yield Button("Back", id="back")
                        yield Button(action_label, variant="primary", id="apply")

        yield Footer()

    def on_mount(self) -> None:
        self._refresh_selection_summary()

    def _capability_label(self, key: str) -> str:
        title = CAPABILITIES[key][0]
        marker = "✓" if self.selections[key] else "○"
        return f"{marker}  {title}"

    def _review_text(self) -> str:
        selected = [
            f"✓  {CAPABILITIES[key][0]}" for key in CAPABILITIES if self.selections[key]
        ]
        return "\n".join(selected) if selected else "○  Nothing selected"

    def _refresh_selection_summary(self) -> None:
        count = sum(self.selections.values())
        base_count = sum(
            self.selections[key] for key in CAPABILITIES if key != "optional"
        )
        optional_text = "on" if self.selections["optional"] else "off"
        self.query_one("#selection-count", Static).update(f"{count} selected")
        self.query_one("#selection-detail", Static).update(
            f"{base_count} base capabilities selected  ·  Optional tools: {optional_text}"
        )
        if self.query_one("#review-view").display:
            self.query_one("#review-list", Static).update(self._review_text())

    def _set_step(self, current: str) -> None:
        for key in ("profile", "components", "review", "apply"):
            self.query_one(f"#rail-{key}").remove_class("active")
        self.query_one(f"#rail-{current}").add_class("active")

    def _show_review(self) -> None:
        self.query_one("#profile-view").display = False
        self.query_one("#review-view").display = True
        self.query_one("#review-list", Static).update(self._review_text())
        self._set_step("review")

    def _show_profile(self) -> None:
        self.query_one("#review-view").display = False
        self.query_one("#profile-view").display = True
        self._set_step("profile")

    def _backend_command(self) -> list[str]:
        command = [
            str(SCRIPT_DIR / "bootstrap.sh"),
            "--apply" if self.apply_mode else "--preview",
        ]
        if self.apply_mode:
            command.append("--noninteractive")
        if not self.selections["personal"]:
            command.append("--no-config")
        if not self.selections["workspace-foundation"]:
            command.append("--no-workspace")
        if self.no_packages or not self.selections["core-tools"]:
            command.append("--no-packages")
        if self.selections["optional"]:
            command.append("--with-optional")
        if self.destination:
            command.extend(["--destination", self.destination])
        if self.workspace:
            command.extend(["--workspace", self.workspace])
        return command

    @work(thread=True, exclusive=True)
    def _execute_backend(self, command: list[str]) -> None:
        try:
            result = subprocess.run(
                command,
                cwd=SCRIPT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=300,
                check=False,
            )
            output = result.stdout or "(backend produced no output)"
            self.call_from_thread(
                self._backend_finished,
                result.returncode,
                output,
            )
        except subprocess.TimeoutExpired:
            self.call_from_thread(
                self._backend_finished,
                124,
                "Backend stopped after the 300-second safety limit.",
            )
        except OSError as error:
            self.call_from_thread(
                self._backend_finished,
                127,
                f"Could not start backend: {error}",
            )

    def _backend_finished(self, returncode: int, output: str) -> None:
        self.query_one("#backend-output", Static).update(output.strip())
        apply_button = self.query_one("#apply", Button)
        apply_button.disabled = False
        if returncode == 0:
            self.query_one("#review-status", Static).update(
                "SUCCESS · backend completed"
            )
            self._set_step("apply")
            self.notify("Backend completed successfully", severity="information")
        else:
            self.query_one("#review-status", Static).update(
                f"FAILED · backend exited with status {returncode}"
            )
            self.notify("Backend failed · see the output above", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id in CAPABILITIES:
            self.selections[button_id] = not self.selections[button_id]
            event.button.label = self._capability_label(button_id)
            event.button.set_class(self.selections[button_id], "selected")
            self._refresh_selection_summary()
            return

        if button_id == "review":
            self._show_review()
            return

        if button_id == "back":
            self._show_profile()
            return

        if button_id == "apply":
            command = self._backend_command()
            event.button.disabled = True
            self.query_one("#review-status", Static).update(
                "RUNNING · backend command started"
            )
            self.query_one("#backend-output", Static).update(
                "Running " + " ".join(command) + "\n"
            )
            self._execute_backend(command)

    def action_reset(self) -> None:
        self.selections = {key: details[2] for key, details in CAPABILITIES.items()}
        for key in CAPABILITIES:
            button = self.query_one(f"#{key}", Button)
            button.label = self._capability_label(key)
            button.set_class(self.selections[key], "selected")
        self._show_profile()
        self._refresh_selection_summary()
        self.notify("Selection reset", severity="information")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Textual front end for the Ubuntu workstation bootstrapper"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Enable the real apply backend; default is preview-only",
    )
    parser.add_argument(
        "--no-packages",
        action="store_true",
        help="Pass --no-packages to the bootstrap backend",
    )
    parser.add_argument("--destination", help="Pass a destination home to the backend")
    parser.add_argument("--workspace", help="Pass a workspace root to the backend")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    BootstrapPreview(
        apply_mode=args.apply,
        no_packages=args.no_packages,
        destination=args.destination,
        workspace=args.workspace,
    ).run()
