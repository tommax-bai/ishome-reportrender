"""出站边缘：把渲染好的册写进**私有对象存储**（阿里云 OSS 私有桶，用户裁决 2026-08-30 晚）。

**为什么是对象存储而不是自家服务器出一个地址**：册要在业主手机上打开，而生成侧那台机器上
跑着别的生产服务——多开一个公网面就是多一份风险。私有桶的签名链接由 OSS 域名直接对外、
自带有效期，本项目一个公网端口都不用开。这条同架构方案里"图/视频走 CDN→OSS 直出不过网关"。

**本模块只写不签**。签名是"给谁看、看多久"的事，属业务侧（project-svc）——生成侧不知用户是谁
（图 v0.2 §0）。两边靠**确定性对象键**接头：键由 `report_id` 推得，见 contracts
`registries/object_keys.md`。这也是"这份报告出没出册"不必另立台账的原因——问存储即知。

依赖方向（import-linter 锁定）：本模块只依赖运行库（oss2），不感知上层。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import oss2

REPORT_BOOK_KEY_TEMPLATE = "reports/{report_id}/book.html"
"""册的对象键模板。**唯一真源在 contracts `registries/object_keys.md`**，本行是逐字副本。

要有副本是因为写的一侧（本仓）与签的一侧（project-svc）是两个语言两个仓，谁也不能 import 谁；
两处逐字一致由各自的守门测试盯住，对不上就是接不上头——不是风格问题。
"""

BOOK_CONTENT_TYPE = "text/html; charset=utf-8"
"""册是自包含 HTML，浏览器直接打开。签名链接不改这个头，故写入时就得写对。"""

_ENDPOINT_ENV = "ISHOME_OSS_ENDPOINT"
_BUCKET_ENV = "ISHOME_OSS_BUCKET_PRIVATE"
_ACCESS_KEY_ID_ENV = "ISHOME_OSS_ACCESS_KEY_ID"
_ACCESS_KEY_SECRET_ENV = "ISHOME_OSS_ACCESS_KEY_SECRET"


class BookStoreError(Exception):
    """写册失败——响亮失败。册写不进去就是这份报告没出来，不许当成功回报。"""

    def __init__(self, details: list[str]) -> None:
        super().__init__("；".join(details))
        self.details = details


def book_key_of(report_id: str) -> str:
    """册的对象键。确定性派生：同一份报告重跑覆盖同一个对象，天然幂等。"""
    if not report_id or "/" in report_id:
        raise BookStoreError([f"report_id 不成立：`{report_id}`——它要当对象键的一段用"])
    return REPORT_BOOK_KEY_TEMPLATE.format(report_id=report_id)


@dataclass(frozen=True)
class OssSettings:
    """私有桶连接口径。四个值全部来自环境，代码里不留任何默认桶名或端点。"""

    endpoint: str
    bucket: str
    access_key_id: str
    access_key_secret: str

    @staticmethod
    def from_env() -> OssSettings:
        """从环境读取；**缺一即启动就失败**，不等到第一份报告渲完才发现存不进去。"""
        values = {
            name: os.environ.get(name, "").strip()
            for name in (_ENDPOINT_ENV, _BUCKET_ENV, _ACCESS_KEY_ID_ENV, _ACCESS_KEY_SECRET_ENV)
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise BookStoreError(
                [
                    f"私有对象存储没配全，缺：{'、'.join(missing)}——凭证放"
                    " ~/.ishome/oss-local.env（本机）或 /opt/ishome/env/oss.env（服务器），不入库"
                ]
            )
        return OssSettings(
            endpoint=values[_ENDPOINT_ENV],
            bucket=values[_BUCKET_ENV],
            access_key_id=values[_ACCESS_KEY_ID_ENV],
            access_key_secret=values[_ACCESS_KEY_SECRET_ENV],
        )


class OssBookStore:
    """阿里云 OSS 私有桶的册写入口。签名不在这里——本层只写不签（见模块文档）。"""

    def __init__(self, settings: OssSettings) -> None:
        auth = oss2.Auth(settings.access_key_id, settings.access_key_secret)
        self._bucket = oss2.Bucket(auth, settings.endpoint, settings.bucket)
        self._bucket_name = settings.bucket

    @property
    def bucket_name(self) -> str:
        return self._bucket_name

    def put_book(self, report_id: str, html: str) -> str:
        """写一册，返回对象键。写失败即上抛——不吞、不返回一个指向空气的键。"""
        key = book_key_of(report_id)
        try:
            self._bucket.put_object(
                key,
                html.encode("utf-8"),
                headers={"Content-Type": BOOK_CONTENT_TYPE},
            )
        except oss2.exceptions.OssError as e:
            raise BookStoreError([f"册写不进私有桶 `{self._bucket_name}`（键 {key}）：{e}"]) from e
        return key
