# Versions and licenses

The target is Ubuntu 26.04 LTS, initially verified on amd64. Apt versions are explicit
in profiles/ubuntu-26.04/apt.lock. Ubuntu dependency licenses remain available under
/usr/share/doc/PACKAGE/copyright on the target. The installer records exact versions;
it does not run an unbounded upgrade or install from a floating latest tag.

| Software | Pin | License and choice |
|---|---|---|
| Chezmoi | 2.70.5 | MIT |
| uv | 0.11.3 | MIT / Apache-2.0 |
| Claude Code | 2.1.261 | Anthropic proprietary terms, deliberately included at owner request |
| Codex CLI | 0.153.4 | Apache-2.0 |
| OpenCode | 1.18.27 | MIT; installed with restrictive initial permissions, never launched as an agent by the installer |
| VS Code | 1.136.1-1788413865 | Microsoft binary distribution terms; deliberate existing editor choice |
| JetBrainsMono Nerd Font | 3.4.0 archive | SIL OFL-1.1, retained in installed font directory |
| Nordic | bb5e31ec1488b1fd5641aa10f65f36d8714b5dba | GPL-3.0; Voyager's actual GTK theme |
| Nordzy icons | 829c47bda534d3c9f3c7d46c73a6fe9d946eca41 | GPL-3.0; dark icon theme |
| Tactile | v37, 6f3c1f8868f2bcb36c520c81a37ca929406b08cd | GPL-3.0-or-later |
| tmux plugins | Exact Voyager commits in plugins.json | MIT except SessionX GPL-3.0; toggle-popup license metadata is unclassified. Upstream notices retained |

## VS Code extensions match the Mac inventory

Linux installation uses ID and version, not a copied Mac binary. Publisher-specific
licenses are deliberate existing-tool choices. Missing license metadata is explicitly
shown below, not assumed to mean MIT. WSL and its umbrella extension pack are excluded.

| Extension | Version | Publisher license metadata |
|---|---|---|
| ms-azuretools.vscode-docker | 2.0.0 | SEE LICENSE IN LICENSE.md |
| ms-vscode-remote.remote-ssh-edit | 0.87.0 | SEE LICENSE IN LICENSE.txt |
| ms-toolsai.vscode-jupyter-cell-tags | 0.1.9 | See publisher license |
| ms-vscode.remote-explorer | 0.5.0 | SEE LICENSE IN LICENSE.txt |
| ms-toolsai.jupyter-keymap | 1.1.2 | MIT |
| ms-vscode.makefile-tools | 0.12.17 | SEE LICENSE IN LICENSE.txt |
| astro-build.houston | 0.1.2 | MIT |
| github.remotehub | 0.64.0 | SEE LICENSE IN LICENSE |
| ms-vscode.remote-server | 1.5.3 | SEE LICENSE IN LICENSE.txt |
| ms-vscode.remote-repositories | 0.42.0 | SEE LICENSE IN LICENSE |
| ms-toolsai.vscode-jupyter-slideshow | 0.1.6 | See publisher license |
| tomoki1207.pdf | 1.2.2 | See publisher license |
| ms-toolsai.jupyter | 2025.9.1 | MIT |
| ms-toolsai.jupyter-renderers | 1.3.0 | MIT |
| analytic-signal.preview-tiff | 1.0.1 | See publisher license |
| esbenp.prettier-vscode | 12.4.0 | MIT |
| ms-python.python | 2026.4.0 | MIT |
| catppuccin.catppuccin-vsc-icons | 1.26.0 | MIT |
| mhutchie.git-graph | 1.30.0 | SEE LICENSE IN 'LICENSE' |
| ms-vscode.cpptools-extension-pack | 1.5.1 | SEE LICENSE IN LICENSE.txt |
| ms-vscode.cpptools-themes | 2.0.0 | SEE LICENSE IN LICENSE.txt |
| vscjava.vscode-java-debug | 0.59.0 | SEE LICENSE IN LICENSE.txt |
| vscjava.vscode-maven | 0.45.3 | MIT |
| ms-vscode.cmake-tools | 1.23.52 | MIT |
| mechatroner.rainbow-csv | 3.24.1 | MIT |
| catppuccin.catppuccin-vsc | 3.19.0 | MIT |
| ms-python.debugpy | 2026.6.0 | MIT |
| ms-vscode-remote.remote-ssh | 0.128.0 | SEE LICENSE IN LICENSE.txt |
| ms-python.black-formatter | 2026.6.0 | MIT |
| vscjava.vscode-java-pack | 0.31.1 | MIT |
| ms-python.vscode-python-envs | 1.36.0 | See publisher license |
| vscjava.vscode-java-dependency | 0.27.6 | MIT |
| vscjava.vscode-java-test | 0.46.0 | See publisher license |
| vscjava.vscode-gradle | 3.18.0 | SEE LICENSE IN LICENSE.md |
| redhat.vscode-yaml | 1.24.0 | MIT |
| dbaeumer.vscode-eslint | 3.0.34 | MIT |
| ms-vscode-remote.remote-containers | 0.466.0 | SEE LICENSE IN LICENSE.txt |
| github.vscode-github-actions | 0.32.3 | MIT |
| bradlc.vscode-tailwindcss | 0.16.0 | MIT |
| ms-python.vscode-pylance | 2026.3.1 | SEE LICENSE IN LICENSE.txt |
| ms-kubernetes-tools.vscode-kubernetes-tools | 1.4.1 | Apache-2.0 |
| davidanson.vscode-markdownlint | 0.62.1 | MIT |
| continue.continue | 2.0.0 | Apache-2.0 |
| ms-azuretools.vscode-containers | 2.5.0 | SEE LICENSE IN LICENSE.md |
| ms-vscode.cpp-devtools | 0.6.18 | SEE LICENSE IN LICENSE.txt |
| eamodio.gitlens | 19.1.0 | SEE LICENSE IN LICENSE |
| charliermarsh.ruff | 2026.76.0 | MIT |
| ms-vscode.cpptools | 1.34.2 | SEE LICENSE IN LICENSE.txt |
| arcticicestudio.nord-visual-studio-code | 0.19.0 | MIT |
| redhat.java | 1.56.0 | EPL-2.0 |
