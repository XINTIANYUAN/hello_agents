#!/usr/bin/env python3
"""启动 Task5 本地服务，并报告 Redis、Qdrant 和 n8n 的健康状态。

在项目根目录使用 Python 3.10 或更高版本运行：

    python3 code/chapter5/start-services.py
    python3 code/chapter5/start-services.py --status

依赖版本见同目录 runtime-versions.json。项目专用 Node/n8n 安装示例：

    mkdir -p .task5-runtime/cache
    touch .task5-runtime/npmrc
    export npm_config_cache="$PWD/.task5-runtime/cache"
    export npm_config_userconfig="$PWD/.task5-runtime/npmrc"
    npm install --prefix .task5-runtime/node --registry https://registry.npmjs.org node@24.22.3
    export PATH="$PWD/.task5-runtime/node/node_modules/node/bin:$PATH"
    npm install --prefix .task5-runtime/app --registry https://registry.npmjs.org --omit=dev n8n@2.49.7

本次安装使用 npm 11.20.0，未传入 --ignore-scripts。npm 的 allowScripts
机制列出 14 个待批准的生命周期脚本；SQLite、isolated-vm 等相关模块已实际
加载验证。复制环境时，请根据具体错误检查安装日志和原生模块的可加载性。

运行前准备下列本机配置和二进制：

* Redis 7.4.11 安装在 ~/.local/redis-7.4.11/bin。
* Qdrant 1.20.2 二进制在 .task5-runtime/qdrant/qdrant。
* Redis 配置在 .task5-local/redis.conf，使用本机 6385 端口。
* Qdrant 配置在 .task5-runtime/qdrant/config.yaml，使用本机 6335 端口。
* n8n 环境变量字典在 .task5-local/n8n.env.json，使用本机 5685 端口。

初始化流程负责准备上述配置、n8n owner 和凭证。此脚本复用已有配置，服务
日志写入 .task5-local/start-services-*.log。模型服务由本机 Ollama 提供。
"""

import argparse
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import time
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".task5-local"
RUNTIME = ROOT / ".task5-runtime"
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def redis_password(config):
    """只把 requirepass 用于本机健康检查，配置值保留在内存中。"""
    if not config.is_file():
        return None
    password = None
    for line in config.read_text(encoding="utf-8").splitlines():
        parts = shlex.split(line, comments=True)
        if parts and parts[0] == "requirepass":
            if len(parts) != 2:
                raise ValueError("Redis requirepass 配置格式错误")
            password = parts[1]
    return password


def healthy(service, password):
    try:
        if service["name"] == "redis":
            with socket.create_connection(("127.0.0.1", service["port"]), timeout=1) as connection:
                with connection.makefile("rwb", buffering=0) as stream:
                    if password:
                        encoded = password.encode("utf-8")
                        auth_command = (
                            b"*2\r\n$4\r\nAUTH\r\n$"
                            + str(len(encoded)).encode()
                            + b"\r\n"
                            + encoded
                            + b"\r\n"
                        )
                        stream.write(auth_command)
                        if stream.readline(1024) != b"+OK\r\n":
                            return False
                    stream.write(b"*1\r\n$4\r\nPING\r\n")
                    return stream.readline(1024) == b"+PONG\r\n"
        with HTTP.open(service["health_url"], timeout=1) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def port_in_use(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def n8n_environment():
    try:
        values = json.loads((LOCAL / "n8n.env.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ValueError("请先准备有效的 .task5-local/n8n.env.json") from None
    if not isinstance(values, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in values.items()
    ):
        raise ValueError("n8n.env.json 应为环境变量名称到字符串值的 JSON 字典")
    environment = os.environ.copy()
    environment.update(values)
    environment.update({
        "N8N_USER_FOLDER": str(LOCAL / "n8n"),
        "N8N_LISTEN_ADDRESS": "127.0.0.1",
        "N8N_HOST": "localhost",
        "N8N_PORT": "5685",
        "PATH": (
            str(RUNTIME / "node/node_modules/node/bin")
            + os.pathsep
            + environment.get("PATH", "")
        ),
    })
    return environment


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--status", action="store_true", help="只检查当前服务健康状态")
    parser.add_argument("--timeout", type=int, default=90, help="启动后的最大等待秒数，默认 90")
    arguments = parser.parse_args()
    if arguments.timeout <= 0:
        parser.error("--timeout 必须大于 0")

    redis_config = LOCAL / "redis.conf"
    qdrant_config = RUNTIME / "qdrant/config.yaml"
    node = RUNTIME / "node/node_modules/node/bin/node"
    n8n = RUNTIME / "app/node_modules/n8n/bin/n8n"
    redis = Path.home() / ".local/redis-7.4.11/bin/redis-server"
    qdrant = RUNTIME / "qdrant/qdrant"
    services = [
        {
            "name": "redis",
            "port": 6385,
            "command": [str(redis), str(redis_config), "--daemonize", "no"],
            "required": [redis, redis_config],
        },
        {
            "name": "qdrant",
            "port": 6335,
            "command": [str(qdrant), "--config-path", str(qdrant_config)],
            "required": [qdrant, qdrant_config],
            "health_url": "http://127.0.0.1:6335/readyz",
        },
        {
            "name": "n8n",
            "port": 5685,
            "command": [str(node), str(n8n), "start"],
            "required": [node, n8n],
            "health_url": "http://127.0.0.1:5685/healthz/readiness",
        },
    ]
    try:
        password = redis_password(redis_config)
    except (OSError, ValueError):
        print(json.dumps(
            {"ready": False, "error": "无法读取 Redis 健康检查配置"},
            ensure_ascii=False,
        ))
        return 1

    results = []
    processes = {}
    for service in services:
        name = service["name"]
        url = f"http://127.0.0.1:{service['port']}"
        if name == "redis":
            url = "redis://127.0.0.1:6385"
        result = {"name": name, "url": url, "healthy": healthy(service, password)}
        results.append(result)
        if result["healthy"] or arguments.status:
            result["action"] = "reused" if result["healthy"] else "checked"
            continue
        result["action"] = "failed"
        if port_in_use(service["port"]):
            result["error"] = "端口已有监听服务，但本任务的健康检查失败"
            continue
        missing = []
        for path in service["required"]:
            if not path.is_file():
                missing.append(str(path))
        if missing:
            result["error"] = "缺少启动文件"
            result["missing"] = missing
            continue
        try:
            environment = n8n_environment() if name == "n8n" else os.environ.copy()
            LOCAL.mkdir(parents=True, exist_ok=True)
            if name == "n8n":
                (LOCAL / "n8n").mkdir(parents=True, exist_ok=True)
            log = LOCAL / f"start-services-{name}.log"
            descriptor = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            working_directory = LOCAL / "qdrant" if name == "qdrant" else ROOT
            working_directory.mkdir(parents=True, exist_ok=True)
            with os.fdopen(descriptor, "ab") as output:
                process = subprocess.Popen(
                    service["command"],
                    cwd=working_directory,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
            processes[name] = process
            result.update(
                action="started",
                pid=process.pid,
                log=str(log.relative_to(ROOT)),
            )
        except ValueError as error:
            result["error"] = str(error)
        except OSError:
            result["error"] = "服务进程启动失败，请检查可执行文件和本地日志"

    deadline = time.monotonic() + arguments.timeout
    pending = {name for name in processes}
    while pending and time.monotonic() < deadline:
        for service, result in zip(services, results):
            name = service["name"]
            if name not in pending:
                continue
            result["healthy"] = healthy(service, password)
            if result["healthy"]:
                pending.remove(name)
            elif processes[name].poll() is not None:
                result.update(action="failed", error="进程已退出，请查看本地服务日志")
                pending.remove(name)
        if pending:
            time.sleep(1)
    for result in results:
        if result["name"] in pending:
            result["error"] = "等待健康检查超时，后续可使用 --status 再检查"
    report = {"ready": all(result["healthy"] for result in results), "services": results}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
