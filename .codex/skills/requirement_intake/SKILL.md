---
name: requirement_intake
description: 在生成页面之前先补问关键参数，只要参数不完整就不能直接输出 HTML。
---

# Requirement Intake

## 目标

先把模糊需求补齐，再把结构化结果交给后续 skill。

## 必须收集的参数

- 页面名称
- 页面目标
- 目标用户
- 字段
- 操作
- 风格约束
- hft-sdk 接口约束

## 规则

1. 不允许直接生成页面
2. 缺什么问什么
3. 尽量让用户按标签格式回复
4. 参数完整后才允许流转到下一个 skill
