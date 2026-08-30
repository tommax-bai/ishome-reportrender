"""worker 进程装配：连接 Temporal（namespace `genpipe`），监听 `reportrender-activities`。

**组合根在此**：私有桶连接、锁定文案、落点项名词表三样都在这里装好并当场校验——
装不上就起不来，绝不带着半套配置上线等第一份报告去踩（"缺配置要在起不来的时候就知道"）。

genpipe workflow 按 activity 归属把任务派到本仓专属队列；重试/心跳/取消/背压沿用 Temporal
activity 原生语义，不引入服务间 HTTP 调用（对齐文档 §3.1）。

**词表从 contracts 注册表目录读，本仓不留副本**：锁定文案与落点项名各自的真源是
contracts `registries/locked_texts.json` 与 `registries/anchor_items.json`；本层再存一份
就是同一条词表两处各写一遍，源侧长出新词而这边忘了改、整册当场渲不出来（README 已有此口径，
这里是它在服务形态下的落法）。目录由 `ISHOME_CONTRACTS_REGISTRIES_DIR` 给。
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from temporalio.client import Client
from temporalio.worker import Worker

from reportrender.activities import ReportBookRenderer, activity_registry
from reportrender.anchor_text import ItemLabels
from reportrender.book_store import OssBookStore, OssSettings
from reportrender.models import parse_anchor_items, parse_locked_texts

GENPIPE_NAMESPACE = "genpipe"
REPORTRENDER_TASK_QUEUE = "reportrender-activities"
"""contracts `registries/task_queues.md` 逐字一致（只增不改）。"""

REGISTRIES_DIR_ENV = "ISHOME_CONTRACTS_REGISTRIES_DIR"
LOCKED_TEXTS_FILE = "locked_texts.json"
ANCHOR_ITEMS_FILE = "anchor_items.json"


def _load_registries() -> tuple[dict[str, str], ItemLabels]:
    """读 contracts 注册表里的两份词表。缺目录或缺文件即启动失败，说清缺哪一个。"""
    raw_dir = os.environ.get(REGISTRIES_DIR_ENV, "").strip()
    if not raw_dir:
        raise SystemExit(
            f"没有 {REGISTRIES_DIR_ENV}：出册要 contracts 注册表里的锁定文案与落点项名词表，"
            "指到 ishome-contracts 的 registries/ 目录"
        )
    directory = Path(raw_dir)
    missing = [
        name for name in (LOCKED_TEXTS_FILE, ANCHOR_ITEMS_FILE) if not (directory / name).is_file()
    ]
    if missing:
        raise SystemExit(
            f"{directory} 下缺：{'、'.join(missing)}——不是 contracts 的 registries 目录？"
        )

    def load(name: str) -> Any:
        with (directory / name).open(encoding="utf-8") as f:
            return json.load(f)

    return parse_locked_texts(load(LOCKED_TEXTS_FILE)), parse_anchor_items(load(ANCHOR_ITEMS_FILE))


async def run_worker(temporal_address: str) -> None:
    locked_texts, item_labels = _load_registries()
    store = OssBookStore(OssSettings.from_env())
    renderer = ReportBookRenderer(store, locked_texts, item_labels)
    client = await Client.connect(temporal_address, namespace=GENPIPE_NAMESPACE)
    worker = Worker(
        client,
        task_queue=REPORTRENDER_TASK_QUEUE,
        activities=list(activity_registry(renderer).values()),
    )
    await worker.run()


def main() -> None:
    asyncio.run(run_worker(os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")))


if __name__ == "__main__":
    main()
