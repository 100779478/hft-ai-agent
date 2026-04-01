---
name: html_generation
description: 根据结构化页面需求和 hft-sdk contract 生成 HTML 页面。当已经有 intake 完成块与 contract 块时使用；负责直接生成完整 HTML，不要重新回到逐项补问。
---

# HTML Generation

## 目标

根据结构化参数和 contract 生成可预览、可下载的 HTML 页面。

## 输入

- `[INTAKE_COMPLETE]`
- `[HFT_SDK_CONTRACT]`

## 规则

1. 不能绕过前置 skill，但如果前置 skill 已输出结构化块，就必须直接生成，不要再次补问。
2. 页面风格尽量贴近客户端约束或用户显式指定的视觉基准。
3. 如果存在“默认假设”，直接带着假设生成，不要再次要求用户重复确认。
4. 输出要保留 preview / download 能力。
5. 当用户明确要求“用 markdown 展示 HTML”时，优先输出完整 `html` fenced code block。

## 输出要求

1. 先给完整 HTML。
2. HTML 必须可直接保存为单文件运行。
3. 如有必要，可在 HTML 后补一小段默认假设说明，但不要重新进入问答模式。
