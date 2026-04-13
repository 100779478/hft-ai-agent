# HFT SDK 视图摘要

在阅读完整接口文档前，可先查看本文件，快速了解 HFT SDK 的核心接口视图和页面生成约束。

## 完整文档入口

- 完整接口文档：[hft-sdk-api-reference.md](/D:/hft-ai-agent/.codex/skills/hft-sdk-contract/references/hft-sdk-api-reference.md)

## 基础地址

- HTTP 基础地址：`http://172.24.17.44:9005/hft-sdk`
- SSE 地址：`http://172.24.17.44:9005/hft-sdk/sse/stream?clientId={clientId}`

## 通用返回结构

文档中的接口统一返回 `Response<T>`，主要字段包括：

- `code`
- `message`
- `data`

## 常见接口分组

- 策略操作
  典型路径如 `/client/update-rule-status`、`/client/update-rule-params`
- 下单操作
  典型路径如 `/client/fak-order`、`/client/bilateral-order`、`/client/xbond-order` 以及各类撤单接口
- 行情数据
  典型路径如 `/market-data/inner-market-data`、`/market-data/fix-market-data`、`/market-data/broker-best-quote`、`/market-data/broker-deal`、`/market-data/market-status`

## 页面生成约束

- 优先使用文档中的默认值，作为 HTML 表单默认值。
- 首版页面应直接生成带真实 HTTP 和 SSE 绑定能力的页面，而不是只做静态预览。
- 如果用户要求的字段没有在文档中出现，应在页面中省略，并明确告知用户该字段未在接口文档中找到。
- 如果用户要求的页面能力没有在文档中出现，应停止生成，并明确说明当前系统不支持该能力。
- 页面视觉与交互密度应贴近 HFT 桌面交易工作台，而不是做成通用 API 调试页。
