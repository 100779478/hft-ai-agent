---
name: workbench-layout
description: 通用工作台布局与 HTML 参考页驱动 skill。适用于本项目所有高密度桌面工作台页面；当页面已经有明确接口或数据契约时，使用本 skill 统一处理一屏布局、内部滚动、深色交易客户端视觉语言、参考 HTML 对齐、交互密度控制，以及单文件 HTML 原型生成约束。
---

# Workbench Layout

将本 skill 视为当前项目唯一的工作台视觉与参考页入口。
不要再单独寻找旧的 `html-design-builder` 说明；本 skill 已吸收其有效规则。

## 核心职责

- 负责工作台页面的视觉语言、布局密度、滚动策略和交互骨架。
- 负责把本地参考 HTML 作为首要事实来源，而不是自由发挥新风格。
- 负责把页面产出收敛为可直接运行的单文件 HTML 原型。
- 不负责发明接口字段、业务能力或文档中不存在的操作。

## 参考源规则

优先把当前目录下这些文件视为唯一参考源：

- `shell-workbench.html`
- `page-table-standard.html`
- `page-market-standard.html`
- `page-operation-standard.html`
- `page-strategy-standard.html`
- `page-settings-standard.html`
- `page-dialog-standard.html`
- `page-message-standard.html`
- `page-whitelist-standard.html`
- `page-approval-standard.html`
- `page-board-standard.html`
- `trade-risk-precheck.html`
- `assets/tokens.css`
- `assets/app.css`
- `assets/components.css`

生成页面前必须先读取：

1. 如目标页面属于工作台子页，先读 `shell-workbench.html`
2. 读取唯一主参考页
3. 按需最多补充 2 个辅助参考页，只用于弹窗、消息、设置等局部模式
4. 读取 `assets/tokens.css`
5. 读取 `assets/app.css`
6. 读取 `assets/components.css`

如果参考页与自然语言需求冲突，在以下方面优先服从参考页：

- 视觉语言
- 布局骨架
- 信息密度
- 控件尺寸
- 间距比例
- 状态标签语义
- 工具栏和表格组织方式

只要本地参考文件可用，就不要重新发明一套新的 SaaS 风格。

## 页面类型映射

- 工作台模块首页：`shell-workbench.html`
- 表格列表页：`page-table-standard.html`
- 行情联动页：`page-market-standard.html`
- 审批或录入页：`page-operation-standard.html`
- 策略监控页：`page-strategy-standard.html`
- 设置页：`page-settings-standard.html`
- 弹窗或二次确认：`page-dialog-standard.html`
- 消息中心或告警中心：`page-message-standard.html`
- 白名单维护页：`page-whitelist-standard.html`
- 审批详情页：`page-approval-standard.html`
- 行情看板页：`page-board-standard.html`
- 交易前风控校验页：`trade-risk-precheck.html`

## 一屏布局规则

- 默认按桌面工作台一屏展示设计，优先让主要信息在首屏完成查看和操作。
- 页面根容器优先使用 `height: 100vh` 或等价结构。
- 页面外层优先 `overflow: hidden`，不要让整个 `body` 无限向下滚动。
- 表格区、详情区、日志区、侧栏等密集区域超出时，各自使用内部滚动。
- 使用 flex 或 grid 时，给滚动子区域设置 `min-height: 0` 和必要的 `min-width: 0`。
- 工具栏、筛选栏、状态栏保持固定占位，由主内容区承接剩余空间。

## 视觉与交互硬约束

- 页面必须保持深色、高密度、表格优先、工具栏优先的桌面交易客户端气质。
- 页面必须是可演示交互原型，不是静态截图。
- 除非用户明确要求，否则按桌面宽度设计，不做移动端优先。
- 除非用户明确提供，否则不要使用外部框架、CDN、外部字体或外部资源。
- 最终只输出一个内嵌 CSS 与 JS 的完整 HTML 文件。
- 页面结果必须明显锚定本地参考页，不能退化成通用后台。

默认应覆盖这些可演示交互：

- 表格行选中
- 筛选区交互或联动
- 标签切换
- 弹窗打开与关闭
- 正常、加载、空态、异常之间的状态切换

适用时至少覆盖以下三种状态：

- 正常
- 空态
- 加载
- 异常
- 只读
- 无权限
- 断连

状态颜色语义必须与参考页保持一致，尤其不要随意改变这些交易语义：

- Bid / Ofr
- 运行中 / 暂停 / 停止
- 预警 / 拦截 / 风控阻断

## 禁止事项

- 不要改成浅色 SaaS 后台。
- 不要用大卡片替代高密度主表格。
- 不要显著增加留白。
- 不要把工作流页面做成纯静态看板。
- 不要删除参考页中已有的顶部工具栏、右侧快捷区、状态区等核心骨架。
- 不要使用泛化、失真的业务字段名。
- 不要输出解释文字替代 HTML。
- 不要跳过 `assets/*.css` 然后凭感觉临摹样式。

## 需求改写

如果用户只给自然语言需求，先读取 [references/prompt-template-v2.md](references/prompt-template-v2.md)，再把需求改写成结构化 prompt。

优先收集或推断：

- 页面名称
- 页面类型
- 业务模块
- 页面定位
- 主要区域
- 关键字段
- 必要状态
- 关键交互
- 主参考页
- 辅助参考页

优先做明确假设，不要保留过多模糊自由度。

## 默认执行方式

- 如存在多种合理布局，优先选择最保守、最接近参考页的方案。
- 如请求命中常见场景，优先直接复用对应参考页骨架，而不是临时造新模式。
- 如用户要求“首版就能演示”，默认需要带真实可点的状态切换和局部交互。
