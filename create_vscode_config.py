import json
import os

if __name__ == '__main__':
    """创建vscode配置，方便web版vscode调试"""
    launcherCfg = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Debug",
                "type": "python",
                "request": "launch",
                "cwd": "${workspaceFolder}/scripts",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                },
                "program": "${workspaceFolder}/scripts/debug_server.py",
                "console": "integratedTerminal"
            }
        ]
    }

    os.makedirs('.vscode', exist_ok=True)
    with open('.vscode/launch.json', 'w', encoding='utf-8') as f:
        json.dump(launcherCfg, f, ensure_ascii=False, indent=2)
