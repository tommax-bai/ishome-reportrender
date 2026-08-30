# 真跑 · 报告册进私有桶、业主拿到能打开的链接 · 2026-08-30 晚

> 目的：**免费闭环的出口那一半**——报告册从本地磁盘上的一个文件，变成业主点得开的一条链接。
> 用户裁决当晚：目标＝尽快让真人用上；私有产物放阿里云 OSS 私有桶；先做"报告能打开"这一半。
> 纪律：本文所有数与状态**逐字取自真跑**；失败路径与安全口径一并留档。

## 一、跑法与进程组

**五个进程，缺一即整条线断在不同的地方**（拓扑 v1.3 已记；本轮之前是四个）：

```
LiteLLM :4000（常驻）
genpipe-http :8104            (ishome-aipipe)
genpipe-workflow-worker       (ishome-aipipe，队列 genpipe-workflows)
reportgen-worker              (ishome-reportgen，队列 reportgen-activities)
reportrender-worker           (ishome-reportrender，队列 reportrender-activities)   ← 本轮新增
project-svc :8103             (ishome-backend)
```

```bash
# 出册 worker（本轮新增的那个）
set -a; source ~/.ishome/oss-local.env; set +a
export ISHOME_CONTRACTS_REGISTRIES_DIR=~/codes/ishome-contracts/registries
uv run --directory ~/codes/ishome-reportrender reportrender-worker

# 派发
curl -X POST http://127.0.0.1:8103/api/v1/reports -H 'Content-Type: application/json' -d @dispatch.json
# 取链接
curl http://127.0.0.1:8103/api/v1/reports/{report_id}/link
```

`./gradlew` 默认 JVM 是 Java 8，起 project-svc 前 `export JAVA_HOME=/opt/homebrew/opt/openjdk@21`（既有坑）。

## 二、结果：一次通过

`report_id` `01M19CYGNH2MD1DP4G508CKPG3`，域 `lighting`，`entitlement` PAID，
画像里带了一条户型特征（`balcony_service`，取自户型图解析线的真跑依据）。

| 项 | 逐字 |
|---|---|
| 派发 | `HTTP 202` |
| workflow | `COMPLETED`，`verdict = ok`，`failed_stage = null`，`violations = []` |
| 四阶段派发次序 | `report-unit-compose` → `report-page-assemble` → `report-book-check`（`reportgen-activities`）→ **`report-book-render`（`reportrender-activities`）** |
| 重写轮数 | `lighting: 2`（用满上限，但过了） |
| 册的键 | `reports/01M19CYGNH2MD1DP4G508CKPG3/book.html` |
| 册大小 | 5 614 字节，6 张卡 |
| 取链接 | `HTTP 200`，带 `expiresAt` |
| 签名链接取册 | `HTTP 200`，`Content-Type: text/html; charset=utf-8` |

**户型特征真的进了正文**：其中一张卡逐字写着"你家阳台画了洗衣机和柜体虚线框，说明它不是晾衣服
的地方，而是要天天动手干活的家政区"——这是获客线追记五那条链路（图→特征→规则→报告）
第一次出现在**业主能打开的成品**里，不再只是推导素材。

## 三、三条安全口径，都是实测不是声称

1. **桶确实私有**：无签名直取 `HTTP 403`，`AccessDenied ... because of bucket acl`。
   这是"公开与私有严格分轨"（获客线红线二）在存储层的实测证据，不是配置声称。
2. **没出册的报告取链接 → `HTTP 404`**，不是签一条指向空气的地址。
   签名是纯本地计算，对着不存在的对象照样签得出形态完好的链接，所以**先判在不在再签**。
3. **链接有效期七天**，且当前**没有"认人"这一步**——所以成立的说法是
   **"拿到链接的人就能打开，且会过期"**，不是"只有他能打开"。
   触发条件写死＝开始接外部真实用户时改短、每次现签，那时后半句才成立。

## 四、起不来时的三条失败路径（都实测过，各自一句人话）

出册 worker **缺配置就起不来**，不带着半套配置上线等第一份报告去踩：

| 缺什么 | 说什么 |
|---|---|
| 词表目录 | `没有 ISHOME_CONTRACTS_REGISTRIES_DIR：出册要 contracts 注册表里的锁定文案与落点项名词表…` |
| 词表目录指错 | `/tmp 下缺：locked_texts.json、anchor_items.json——不是 contracts 的 registries 目录？` |
| 桶凭证 | `私有对象存储没配全，缺：ISHOME_OSS_ACCESS_KEY_SECRET——凭证放 ~/.ishome/oss-local.env…` |

第三条**点名缺的是哪一个**，不是笼统说"配置不全"。这三条起初有一条冒的是调用栈，
已改成一句话——**起不来的原因要一眼读得懂**，缺配置在部署现场是最常见的一种起不来。

## 五、踩到并已处置的一坑

**编排多一步，就得多一个 worker，否则整条线卡在重试直到超时——而两侧单测全绿**。
加完出册那一步后没同步补集成测试的桩件，pytest 挂了十几分钟才发现；补上桩件后 9 条集成测试
2.3 秒全过。这条与"路由写了 ≠ 端点可达"是同一族：**编排的改动只能由真派发一次来断言**。

## 六、留档

- `dispatch.json`：本轮派发请求体逐字；
- `book-01M19CYGNH2MD1DP4G508CKPG3.html`：**从签名链接上取回来的那一份**（不是本地渲的那一份）——
  留它是为了将来能回答"业主当时看到的到底是什么"，那份在桶里会被同 id 的重跑覆盖。

## 七、还没做的

**链接还没自动送到业主手里**：现在是我们拿着 `report_id` 去问一次。送进会话属**上传入口接线**
那一批（会话侧至今没有通向业务侧的出站客户端），触发条件即那条线开工时。
自测阶段手动交付不违反"无人工介入"——判据是人力会不会随用户量增长，几个测试对象不算。
