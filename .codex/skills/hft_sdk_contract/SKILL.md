---
name: hft_sdk_contract
description: 把补齐后的 HTML 页面需求整理为 hft-sdk 可消费的页面契约。当已经拿到 requirement_intake 的结构化交接块时使用；负责生成稳定 contract，不要把用户重新打回补问阶段。
---

# HFT SDK Contract

## 目标

把自然语言需求转换为结构化 contract。

## 输入约束

1. 优先消费 `[INTAKE_COMPLETE]` 结构化块。
2. 如果输入已包含等价的完整结构化内容，也视为有效输入。
3. 不要因为轻微缺省或默认值问题把用户退回上一阶段；优先沿用“默认假设”。

## 输出重点

- endpoint
- method
- request_fields
- actions
- response_shape
- integration_notes

## 规则

1. 产物必须能被后续 HTML skill 直接使用。
2. 遇到非关键空缺时，优先补默认 contract，而不是重新追问用户。
3. 只有出现明显冲突或关键接口无法确定时，才明确指出阻塞点。
4. 输出时使用统一结构块，便于后续 skill 直接消费。

## 输出格式

```text
[HFT_SDK_CONTRACT]
endpoint：
method：
request_fields：
actions：
response_shape：
integration_notes：
[/HFT_SDK_CONTRACT]
```
