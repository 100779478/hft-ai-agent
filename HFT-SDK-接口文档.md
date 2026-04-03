# HFT-SDK-View 接口文档
请根据本文档生成对应的 html 页面,http接口地址为: http://172.24.17.44:9005/hft-sdk ,
sse 地址为: http://172.24.17.44:9005/hft-sdk/sse/stream?clientId={clientId} ,
每个接口生成的 html 表单请赋默认值。

## 1. 后台服务器接口地址信息

| 配置项       | 值 | 说明 |
|-----------|-----|------|
| HTTP 接口地址 | http://172.24.17.44:9005/hft-sdk | 本地开发环境访问地址 |
| 服务器端口     | 9005 | 应用服务器监听端口 |
| 上下文路径     | /hft-sdk | API访问基础路径 |

## 2. SSE服务器连接地址信息

| 配置项       | 值                                                                    | 说明                                     |
|-----------|----------------------------------------------------------------------|----------------------------------------|
| 服务器地址     | http://172.24.17.44:9005/hft-sdk/sse/stream?clientId={clientId}         | SSE连接地址,html代码自动生成随机clientId,无需暴露到页面 |
| SSE连接端点   | /sse/stream                                                          |
| html 监听方式 | 使用 eventSource.addEventListener('eventName', function (data){}) 监听方式 |
| 请求方法      | GET                                                                  | HTTP请求方法                               |
| 内容类型      | text/event-stream                                                    | SSE专用内容类型                              |
| 请求参数      | clientId (String)                                                    | 客户端唯一标识                                |

## 3. Controller接口文档参数

### 3.1 策略相关接口

#### 3.1.1 更新策略状态
- **接口路径**: `/client/update-rule-status`
- **请求方法**: POST
- **请求参数**: `RuleStatusInfo`对象
  | 字段名 | 类型 | 说明 |
  |-------|-----|------|
  | ruleID | Integer | 策略ID |
  | optType | String | 操作类型 |
- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: `RULE_STATUS`,`RULE_PROP`,`RULE_POSITION`,`RULE_INDICATOR`,`RULE_OPT_LOG`

#### 3.1.2 更新策略参数
- **接口路径**: `/client/update-rule-params`
- **请求方法**: POST
- **请求参数**: `RuluParams`对象
  | 字段名 | 类型 | 说明 |
  |-------|-----|------|
  | ruleID | Integer | 策略ID |
  | key | String | 参数键 |
  | value | String | 参数值 |
- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: `RULE_STATUS`,`RULE_PROP`,`RULE_POSITION`,`RULE_INDICATOR`,`RULE_OPT_LOG`

### 3.2 订单操作接口

#### 3.2.1 银行间FAK订单
- **接口路径**: `/client/fak-order`
- **请求方法**: POST
- **请求参数**: `VFAKOrder`对象

| 字段名 | 类型 | 说明 | 默认值      |
|-------|----|----------|------|
| customerID | String | 报单用户 | zx01     |
| securityID | String | 证券代码/合约代码 | 240210   |
| direction | char | 买卖方向 (0- 买入  1-卖出) | 1        |
| price | double | 委托价格 | 101.1234 |
| ymt | double | 到期收益率 |
| volume | int | 委托数量/交易量 | 100 |
| deliveryType | int | 结算方式 | 0 |
| clearingMethod | int | 清算类型/清算方式 | 13 |
| settlType | int | 结算速度 | 1 |
| quoteId | String | 报价编号 |
| mdTime | String | 行情时间 | 20260312-10:11:20.300 |
| accountId | String | 账户ID/资金账号 | zx01_simcfets |
| portfolioId | int | 投资组合ID |
| instructionID | String | 指令ID/交易指令编号 |
| reserver3 | String | 预留字段,HFT会原数据返回 | fak test |
| text | String | 报单说明/备注信息 | fak test |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: `RULE_ORDER`,`ORDER_FAILED`


#### 3.2.2 银行间双边报单
- **接口路径**: `/client/bilateral-order`
- **请求方法**: POST
  **请求参数**: `VBilateralOrder`对象

| 字段名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| customerID | String | 报单用户 | zx01 |
| securityID | String | 证券代码/合约代码 | 050004 |
| bidPrice | double | 买价/买入报价价格 | 102.26 |
| bidYTM | double | 买入到期收益率 | 0.87 |
| bidStrikeYeild | double | 买入行权收益率 | 0.0000 |
| bidVolume | int | 买入数量/买盘量 | 1 |
| bidDeliveryType | int | 买入结算方式 | 0 |
| bidClearingMethod | int | 买入清算方式 | 0 |
| bidSettlType | int | 买入结算类型 | 0 |
| askPrice | double | 卖价/卖出报价价格 | 102.26 |
| askYTM | double | 卖出到期收益率 | 0.87 |
| askStrikeYeild | double | 卖出行权收益率 | 0.0000 |
| askVolume | int | 卖出数量/卖盘量 | 1 |
| askDeliveryType | int | 卖出结算方式 | 0 |
| askClearingMethod | int | 卖出清算方式 | 0 |
| askSettlType | int | 卖出结算类型 | 0 |
| maxFloor | int | 最大显示量/最大成交量 | 0 |
| accountID | String | 账户ID/交易账户 | zx01_simcfets |
| routingType | int | 路由类型/发送对象 | 0 |
| traderID | String | 交易员ID | testlhhjdealer |
| traderName | String | 交易员姓名 | testlhhjdealer |
| text | String | 报单说明/备注信息 |  |
| validUntilTime | String | 报价有效时间 | 2026-03-05 10:00:00 |
| portfolioId | int | 投资组合ID |  |
| instructionID | String | 指令ID/交易指令编号 |  |
| reserver3 | String | 预留字段,HFT会原数据返回 |  |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: `RULE_ORDER`,`ORDER_FAILED`

#### 3.2.3 银行间Xbond报单
- **接口路径**: `/client/xbond-order`
- **请求方法**: POST
  **请求参数**: `VXbondOrder`对象

| 字段名 | 类型 | 说明 | 默认值 |
|-------|-----|------|------|
| customerID | String | 报单用户 | zx01 |
| securityID | String | 证券代码/债券代码 | 240210 |
| orderPriceType | char | 报单价格条件/订单价格类型 | 2 |
| direction | char | 买卖方向 (0- 买入  1-卖出) | 1 |
| price | double | 委托价格 | 101.1234 | 
| ymt | double | 到期收益率 | 2.205 |
| volume | int | 委托数量/交易量 | 100 |
| matchType | int | 报价方式/匹配类型 | 9 |
| clearingMethod | int | 清算方式 | 13 |
| settlType | int | 结算类型 | 2 |
| accountId | String | 账户ID/资金账号 | zx01_simcfets |
| reserver3 | String | 预留字段,HFT会原数据返回 | xbond test |
| text | String | 报单说明/备注信息 | xbond test | 
| portfolioId | int | 投资组合ID |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: `RULE_ORDER`,`ORDER_FAILED`

#### 3.2.4 报单撤单
- **接口路径**: `/client/cancel-order/{orderInnerId}`
- **请求方法**: POST
- **请求参数**: `orderInnerId` (路径参数，String) - 订单内部编号
- **返回值**: `Response<String>` - 成功响应

#### 3.2.5 双边报单撤单
- **接口路径**: `/client/cancel-b-order/{orderInnerId}`
- **请求方法**: POST
- **请求参数**: `orderInnerId` (路径参数，String) - 订单内部编号
- **返回值**: `Response<String>` - 成功响应

### 3.3 行情操作接口

#### 3.3.1 场内深度行情接口
- **接口路径**: `/market-data/inner-market-data`
- **请求方法**: POST
- **请求参数**: `VDepthMarketDataReq`对象
-
| 字段名 | 类型 | 说明 | 默认值 |
|-------|------|------|--------|
| tradingDay | String | 交易日 | "20260318" |
| preSettlementPrice | double | 昨结算 | 0.0 |
| preClosePrice | double | 昨收盘 | 0.894 |
| preOpenInterest | double | 昨持仓量 | 0.0 |
| preDelta | double | 昨虚实度 | 0.0 |
| historyHigh | double | 合约最高 | 0.0 |
| historyLow | double | 合约最低 | 0.0 |
| tradingPhaseCode | String | 交易状态代码 | "" |
| openPrice | double | 今开盘 | 0.0 |
| highestPrice | double | 最高价 | 0.0 |
| lowestPrice | double | 最低价 | 0.0 |
| closePrice | double | 今收盘 | 0.0 |
| upperLimitPrice | double | 涨停板价 | 0.0 |
| lowerLimitPrice | double | 跌停板价 | 0.0 |
| clearPrice | double | 本次结算价 | 0.0 |
| currDelta | double | 今虚实度 | 0.0 |
| lastPrice | double | 最新价 | 0.0 |
| volume | long | 数量 | 0 |
| turnover | double | 成交金额 | 0.0 |
| openInterest | double | 持仓量 | 0.0 |
| netChg | double | 涨跌 | 0.0 |
| markup | double | 涨跌幅 | 0.0 |
| swing | double | 振幅 | 0.0 |
| avgPrice | double | 平均价 | 0.0 |
| iOPV | double | IOPV | 0.0 |
| bidPrice1 | double | 申买价一 | 0.895 |
| bidVolume1 | long | 申买量一 | 100 |
| askPrice1 | double | 申卖价一 | 0.895 |
| askVolume1 | long | 申卖量一 | 100 |
| bidPrice2 | double | 申买价二 | 0.0 |
| bidVolume2 | long | 申买量二 | 400 |
| bidPrice3 | double | 申买价三 | 0.0 |
| bidVolume3 | long | 申买量三 | 0 |
| askPrice2 | double | 申卖价二 | 0.0 |
| askVolume2 | long | 申卖量二 | 0 |
| askPrice3 | double | 申卖价三 | 0.0 |
| askVolume3 | long | 申卖量三 | 0 |
| bidPrice4 | double | 申买价四 | 0.0 |
| bidVolume4 | long | 申买量四 | 0 |
| bidPrice5 | double | 申买价五 | 0.0 |
| bidVolume5 | long | 申买量五 | 0 |
| askPrice4 | double | 申卖价四 | 0.0 |
| askVolume4 | long | 申卖量四 | 0 |
| askPrice5 | double | 申卖价五 | 0.0 |
| askVolume5 | long | 申卖量五 | 0 |
| bidPrice6 | double | 申买价六 | 0.0 |
| bidVolume6 | long | 申买量六 | 0 |
| bidPrice7 | double | 申买价七 | 0.0 |
| bidVolume7 | long | 申买量七 | 0 |
| bidPrice8 | double | 申买价八 | 0.0 |
| bidVolume8 | long | 申买量八 | 0 |
| bidPrice9 | double | 申买价九 | 0.0 |
| bidVolume9 | long | 申买量九 | 0 |
| bidPrice10 | double | 申买价十 | 0.0 |
| bidVolume10 | long | 申买量十 | 0 |
| askPrice6 | double | 申卖价六 | 0.0 |
| askVolume6 | long | 申卖量六 | 0 |
| askPrice7 | double | 申卖价七 | 0.0 |
| askVolume7 | long | 申卖量七 | 0 |
| askPrice8 | double | 申卖价八 | 0.0 |
| askVolume8 | long | 申卖量八 | 0 |
| askPrice9 | double | 申卖价九 | 0.0 |
| askVolume9 | long | 申卖量九 | 0 |
| askPrice10 | double | 申卖价十 | 0.0 |
| askVolume10 | long | 申卖量十 | 0 |
| sequenceNo | int | 序号 | 0 |
| marketName | String | 市场中文名 | "" |
| instrumentID | String | 合约代码 | "159003.SZ" |
| instrumentName | String | 合约名称 | "" |
| commodityType | char | 商品类型 | ' ' |
| updateTime | String | 最后修改时间 | "9:15:00" |
| updateMillisec | int | 最后修改毫秒 | 0 |
| exchangeID | String | 交易所代码 | "SZSE" |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: 无

#### 3.3.2 交易所固收行情
- **接口路径**: `/market-data/fix-market-data`
- **请求方法**: POST
- **请求参数**: `VFixDepthMarketDataReq`对象 , 具体参数值参考 "交易所固收行情参数值.md"

| 字段名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| tradingDay | String | 交易日 | 20260320 |
| preSettlementPrice | double | 昨结算 | 0 |
| preClosePrice | double | 昨收盘 | 0 |
| preOpenInterest | double | 昨持仓量 | 0 |
| preDelta | double | 昨虚实度 | 1 |
| historyHigh | double | 合约最高 | 0 |
| historyLow | double | 合约最低 | 0 |
| tradingPhaseCode | String | 交易状态代码 |  |
| openPrice | double | 今开盘 | 0 |
| highestPrice | double | 最高价 | 0 |
| lowestPrice | double | 最低价 | 0 |
| closePrice | double | 今收盘 | 0 |
| upperLimitPrice | double | 涨停板价 | 0 |
| lowerLimitPrice | double | 跌停板价 | 0 |
| clearPrice | double | 本次结算价 | 0 |
| currDelta | double | 今虚实度 | 1 |
| bidPrice1 | double | 申买价一 | 99.974 |
| bidVolume1 | long | 申买量一 | 30000 |
| askPrice1 | double | 申卖价一 | 99.975 |
| askVolume1 | long | 申卖量一 | 10000 |
| bidPrice2 | double | 申买价二 | 99.973 |
| bidVolume2 | long | 申买量二 | 20000 |
| bidPrice3 | double | 申买价三 | 99.972 |
| bidVolume3 | long | 申买量三 | 10000 |
| askPrice2 | double | 申卖价二 | 99.975 |
| askVolume2 | long | 申卖量二 | 10000 |
| askPrice3 | double | 申卖价三 | 99.976 |
| askVolume3 | long | 申卖量三 | 10000 |
| bidPrice4 | double | 申买价四 | 99.965 |
| bidVolume4 | long | 申买量四 | 80000 |
| bidPrice5 | double | 申买价五 | 99.964 |
| bidVolume5 | long | 申买量五 | 10000 |
| askPrice4 | double | 申卖价四 | 99.979 |
| askVolume4 | long | 申卖量四 | 80000 |
| askPrice5 | double | 申卖价五 | 100.047 |
| askVolume5 | long | 申卖量五 | 10000 |
| bidPrice6 | double | 申买价六 | 99.961 |
| bidVolume6 | long | 申买量六 | 100000 |
| bidPrice7 | double | 申买价七 | 99.96 |
| bidVolume7 | long | 申买量七 | 10000 |
| bidPrice8 | double | 申买价八 | 99.907 |
| bidVolume8 | long | 申买量八 | 10000 |
| bidPrice9 | double | 申买价九 | 99.872 |
| bidVolume9 | long | 申买量九 | 10000 |
| bidPrice10 | double | 申买价十 | 99.867 |
| bidVolume10 | long | 申买量十 | 10000 |
| askPrice6 | double | 申卖价六 | 100.067 |
| askVolume6 | long | 申卖量六 | 10000 |
| askPrice7 | double | 申卖价七 | 100.072 |
| askVolume7 | long | 申卖量七 | 10000 |
| askPrice8 | double | 申卖价八 | 100.754 |
| askVolume8 | long | 申卖量八 | 10000 |
| askPrice9 | double | 申卖价九 | 100.767 |
| askVolume9 | long | 申卖量九 | 10000 |
| askPrice10 | double | 申卖价十 | 101.916 |
| askVolume10 | long | 申卖量十 | 10000 |
| bidYTM1 | double | 申买一到期收益率 | 1.645 |
| bidMDTime1 | String | 买一行情发生时间 | 13:48:01 |
| bidQuoteID1 | String | 申买一报价编号 | 419807 |
| bidTraderID1 | String | 申买一报价方 | 中金公司 |
| bidFullPrice1 | double | 全价申买价一 | 101.167 |
| bidYTM2 | double | 申买二到期收益率 | 1.6493 |
| bidMDTime2 | String | 买二行情发生时间 | 13:40:25 |
| bidQuoteID2 | String | 申买二报价编号 | 403826 |
| bidTraderID2 | String | 申买二报价方 | 国泰海通 |
| bidFullPrice2 | double | 全价申买价二 | 101.166 |
| bidYTM3 | double | 申买三到期收益率 | 1.6536 |
| bidMDTime3 | String | 买三行情发生时间 | 13:49:22 |
| bidQuoteID3 | String | 申买三报价编号 | 422594 |
| bidTraderID3 | String | 申买三报价方 | 东方证券 |
| bidFullPrice3 | double | 全价申买价三 | 101.165 |
| bidYTM4 | double | 申买四到期收益率 | 1.6838 |
| bidMDTime4 | String | 买四行情发生时间 | 13:49:30 |
| bidQuoteID4 | String | 申买四报价编号 | 422976 |
| bidTraderID4 | String | 申买四报价方 | 招商证券 |
| bidFullPrice4 | double | 全价申买价四 | 101.158 |
| bidYTM5 | double | 申买五到期收益率 | 1.6881 |
| bidMDTime5 | String | 买五行情发生时间 | 9:17:50 |
| bidQuoteID5 | String | 申买五报价编号 | 51614 |
| bidTraderID5 | String | 申买五报价方 | 银河证券 |
| bidFullPrice5 | double | 全价申买价五 | 101.157 |
| bidYTM6 | double | 申买六到期收益率 | 1.701 |
| bidMDTime6 | String | 买六行情发生时间 | 9:02:54 |
| bidQuoteID6 | String | 申买六报价编号 | 9429 |
| bidTraderID6 | String | 申买六报价方 | 中信证券 |
| bidFullPrice6 | double | 全价申买价六 | 101.154 |
| bidYTM7 | double | 申买七到期收益率 | 1.7053 |
| bidMDTime7 | String | 买七行情发生时间 | 13:00:14 |
| bidQuoteID7 | String | 申买七报价编号 | 352362 |
| bidTraderID7 | String | 申买七报价方 | 国泰海通 |
| bidFullPrice7 | double | 全价申买价七 | 101.153 |
| bidYTM8 | double | 申买八到期收益率 | 1.934 |
| bidMDTime8 | String | 买八行情发生时间 | 9:05:10 |
| bidQuoteID8 | String | 申买八报价编号 | 16203 |
| bidTraderID8 | String | 申买八报价方 | 国信证券 |
| bidFullPrice8 | double | 全价申买价八 | 101.1 |
| bidYTM9 | double | 申买九到期收益率 | 2.0852 |
| bidMDTime9 | String | 买九行情发生时间 | 9:01:21 |
| bidQuoteID9 | String | 申买九报价编号 | 4510 |
| bidTraderID9 | String | 申买九报价方 | 东方证券 |
| bidFullPrice9 | double | 全价申买价九 | 101.065 |
| bidYTM10 | double | 申买十到期收益率 | 2.1068 |
| bidMDTime10 | String | 买十行情发生时间 | 9:00:11 |
| bidQuoteID10 | String | 申买十报价编号 | 580 |
| bidTraderID10 | String | 申买十报价方 | 中信建投 |
| bidFullPrice10 | double | 全价申买价十 | 101.06 |
| askYTM1 | double | 申卖一到期收益率 | 1.6407 |
| askMDTime1 | String | 卖一行情发生时间 | 13:59:47 |
| askQuoteID1 | String | 申卖一报价编号 | 441171 |
| askTraderID1 | String | 申卖一报价方 | 中金公司 |
| askFullPrice1 | double | 全价申卖价一 | 101.168 |
| askYTM2 | double | 申卖二到期收益率 | 1.6407 |
| askMDTime2 | String | 卖二行情发生时间 | 14:00:13 |
| askQuoteID2 | String | 申卖二报价编号 | 441749 |
| askTraderID2 | String | 申卖二报价方 | 东方证券 |
| askFullPrice2 | double | 全价申卖价二 | 101.168 |
| askYTM3 | double | 申卖三到期收益率 | 1.6364 |
| askMDTime3 | String | 卖三行情发生时间 | 13:59:08 |
| askQuoteID3 | String | 申卖三报价编号 | 440207 |
| askTraderID3 | String | 申卖三报价方 | 国泰海通 |
| askFullPrice3 | double | 全价申卖价三 | 101.169 |
| askYTM4 | double | 申卖四到期收益率 | 1.6234 |
| askMDTime4 | String | 卖四行情发生时间 | 13:57:26 |
| askQuoteID4 | String | 申卖四报价编号 | 437499 |
| askTraderID4 | String | 申卖四报价方 | 招商证券 |
| askFullPrice4 | double | 全价申卖价四 | 101.172 |
| askYTM5 | double | 申卖五到期收益率 | 1.3305 |
| askMDTime5 | String | 卖五行情发生时间 | 10:56:32 |
| askQuoteID5 | String | 申卖五报价编号 | 292874 |
| askTraderID5 | String | 申卖五报价方 | 国信证券 |
| askFullPrice5 | double | 全价申卖价五 | 101.24 |
| askYTM6 | double | 申卖六到期收益率 | 1.2444 |
| askMDTime6 | String | 卖六行情发生时间 | 9:00:10 |
| askQuoteID6 | String | 申卖六报价编号 | 508 |
| askTraderID6 | String | 申卖六报价方 | 中信建投 |
| askFullPrice6 | double | 全价申卖价六 | 101.26 |
| askYTM7 | double | 申卖七到期收益率 | 1.2229 |
| askMDTime7 | String | 卖七行情发生时间 | 9:01:22 |
| askQuoteID7 | String | 申卖七报价编号 | 4518 |
| askTraderID7 | String | 申卖七报价方 | 东方证券 |
| askFullPrice7 | double | 全价申卖价七 | 101.265 |
| askYTM8 | double | 申卖八到期收益率 | -1.6921 |
| askMDTime8 | String | 卖八行情发生时间 | 9:04:08 |
| askQuoteID8 | String | 申卖八报价编号 | 13115 |
| askTraderID8 | String | 申卖八报价方 | 银河证券 |
| askFullPrice8 | double | 全价申卖价八 | 101.947 |
| askYTM9 | double | 申卖九到期收益率 | -1.7473 |
| askMDTime9 | String | 卖九行情发生时间 | 9:01:10 |
| askQuoteID9 | String | 申卖九报价编号 | 3865 |
| askTraderID9 | String | 申卖九报价方 | 中信证券 |
| askFullPrice9 | double | 全价申卖价九 | 101.96 |
| askYTM10 | double | 申卖十到期收益率 | -6.5699 |
| askMDTime10 | String | 卖十行情发生时间 | 13:00:21 |
| askQuoteID10 | String | 申卖十报价编号 | 352600 |
| askTraderID10 | String | 申卖十报价方 | 国泰海通 |
| askFullPrice10 | double | 全价申卖价十 | 103.109 |
| sequenceNo | int | 序号 | 0 |
| marketName | String | 市场中文名 |  |
| instrumentID | String | 合约代码 | 243153.SH |
| instrumentName | String | 合约名称 | 25京东SK |
| commodityType | char | 商品类型 | E |
| updateTime | String | 最后修改时间 | 14:36:06 |
| updateMillisec | int | 最后修改毫秒 | 0 |
| exchangeID | String | 交易所代码 | SSEFIX |
| accruedInterestAmt | double | 应计利息 | 1.1932 |
| bidClearingMethod1 | int | 买一结算方式 | 0 |
| bidMinQty1 | long | 申买一最低成交量 | 0 |
| bidClearingMethod2 | int | 买二结算方式 | 0 |
| bidMinQty2 | long | 申买二最低成交量 | 0 |
| bidClearingMethod3 | int | 买三结算方式 | 0 |
| bidMinQty3 | long | 申买三最低成交量 | 0 |
| bidClearingMethod4 | int | 买四结算方式 | 0 |
| bidMinQty4 | long | 申买四最低成交量 | 0 |
| bidClearingMethod5 | int | 买五结算方式 | 0 |
| bidMinQty5 | long | 申买五最低成交量 | 0 |
| bidClearingMethod6 | int | 买六结算方式 | 0 |
| bidMinQty6 | long | 申买六最低成交量 | 0 |
| bidClearingMethod7 | int | 买七结算方式 | 0 |
| bidMinQty7 | long | 申买七最低成交量 | 0 |
| bidClearingMethod8 | int | 买八结算方式 | 0 |
| bidMinQty8 | long | 申买八最低成交量 | 0 |
| bidClearingMethod9 | int | 买九结算方式 | 0 |
| bidMinQty9 | long | 申买九最低成交量 | 0 |
| bidClearingMethod10 | int | 买十结算方式 | 0 |
| bidMinQty10 | long | 申买十最低成交量 | 0 |
| askClearingMethod1 | int | 卖一结算方式 | 0 |
| askMinQty1 | long | 申卖一最低成交量 | 0 |
| askClearingMethod2 | int | 卖二结算方式 | 0 |
| askMinQty2 | long | 申卖二最低成交量 | 0 |
| askClearingMethod3 | int | 卖三结算方式 | 0 |
| askMinQty3 | long | 申卖三最低成交量 | 0 |
| askClearingMethod4 | int | 卖四结算方式 | 0 |
| askMinQty4 | long | 申卖四最低成交量 | 0 |
| askClearingMethod5 | int | 卖五结算方式 | 0 |
| askMinQty5 | long | 申卖五最低成交量 | 0 |
| askClearingMethod6 | int | 卖六结算方式 | 0 |
| askMinQty6 | long | 申卖六最低成交量 | 0 |
| askClearingMethod7 | int | 卖七结算方式 | 0 |
| askMinQty7 | long | 申卖七最低成交量 | 0 |
| askClearingMethod8 | int | 卖八结算方式 | 0 |
| askMinQty8 | long | 申卖八最低成交量 | 0 |
| askClearingMethod9 | int | 卖九结算方式 | 0 |
| askMinQty9 | long | 申卖九最低成交量 | 0 |
| askClearingMethod10 | int | 卖十结算方式 | 0 |
| askMinQty10 | long | 申卖十最低成交量 | 0 |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: 无

#### 3.3.3 Cfest深度行情接口
- **接口路径**: `/market-data/cfest-market-data`
- **请求方法**: POST
- **请求参数**: `VCfetsDepthMarketDataReq`对象

| 字段名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| tradingDay | String | 交易日 | 20260320 |
| bondID | String | 债券代码 | 1605726 |
| bondName | String | 债券名称 | 16北京债09 |
| mDBookType | int | 行情类型 | 2 |
| mDSubBookType | int | 行情分类 | 123 |
| openPrice | double | 开盘价 | 0 |
| lastPrice | double | 最新成交价 | 0 |
| volume | long | 可成交总量,单位万元 | 0 |
| legSettlType | int | 清算速度 | 2 |
| bidPrice1 | double | 申买价1 | 101.3136 |
| bidYTM1 | double | 申买到期收益率1 | 1.0148 |
| bidVolume1 | long | 申买量1,单位万元 | 1000 |
| bidMDTime1 | String | 买1行情发生时间 | 20260320-13:22:51.392 |
| bidQuoteID1 | String | 申买价1报价编号 | 260320020410015000 |
| bidDeliveryType1 | int | 申买价1结算方式 | 0 |
| bidTradeVolume1 | long | 订单总量,申买量1,单位万元 | 0 |
| bidTradingAcctNumber1 | String | 申买价1交易账户 | 410225 |
| askPrice1 | double | 申卖价1 | 101.3136 |
| askYTM1 | double | 申卖到期收益1 | 1.0148 |
| askVolume1 | long | 申卖量1,单位万元 | 1000 |
| askMDTime1 | String | 卖1行情发生时间 | 20260320-13:22:51.392 |
| askQuoteID1 | String | 申卖价1报价编号 | 260320020410015000 |
| askDeliveryType1 | int | 申卖价1结算方式 | 0 |
| askTradeVolume1 | long | 订单总量,申卖量1,单位万元 | 0 |
| askTradingAcctNumber1 | String | 申卖价1交易账户 | 410225 |
| bidPrice2 | double | 申买价2 |  |
| bidYTM2 | double | 申买到期收益率2 | 0 |
| bidVolume2 | long | 申买量2,单位万元 | 0 |
| bidMDTime2 | String | 买2行情发生时间 |  |
| bidQuoteID2 | String | 申买价2报价编号 |  |
| bidDeliveryType2 | int | 申买价2结算方式 | 0 |
| bidTradeVolume2 | long | 订单总量,申买量2,单位万元 | 0 |
| bidTradingAcctNumber2 | String | 申买价2交易账户 |  |
| askPrice2 | double | 申卖价2 |  |
| askYTM2 | double | 申卖到期收益率2 | 0 |
| askVolume2 | long | 申卖量2,单位万元 | 0 |
| askMDTime2 | String | 卖2行情发生时间 |  |
| askQuoteID2 | String | 申卖价2报价编号 |  |
| askDeliveryType2 | int | 申卖价2结算方式 | 0 |
| askTradeVolume2 | long | 订单总量,申卖量2,单位万元 | 0 |
| askTradingAcctNumber2 | String | 申卖价2交易账户 |  |
| bidPrice3 | double | 申买价3 |  |
| bidYTM3 | double | 申买到期收益率3 | 0 |
| bidVolume3 | long | 申买量3,单位万元 | 0 |
| bidMDTime3 | String | 买3行情发生时间 |  |
| bidQuoteID3 | String | 申买价3报价编号 |  |
| bidDeliveryType3 | int | 申买价3结算方式 | 0 |
| bidTradeVolume3 | long | 订单总量,申买量3,单位万元 | 0 |
| bidTradingAcctNumber3 | String | 申买价3交易账户 |  |
| askPrice3 | double | 申卖价3 |  |
| askYTM3 | double | 申卖到期收益率3 | 0 |
| askVolume3 | long | 申卖量3,单位万元 | 0 |
| askMDTime3 | String | 卖3行情发生时间 |  |
| askQuoteID3 | String | 申卖价3报价编号 |  |
| askDeliveryType3 | int | 申卖价3结算方式 | 0 |
| askTradeVolume3 | long | 订单总量,申卖量3,单位万元 | 0 |
| askTradingAcctNumber3 | String | 申卖价3交易账户 |  |
| bidPrice4 | double | 申买价4 |  |
| bidYTM4 | double | 申买到期收益率4 | 0 |
| bidVolume4 | long | 申买量4,单位万元 | 0 |
| bidMDTime4 | String | 买4行情发生时间 |  |
| bidQuoteID4 | String | 申买价4报价编号 |  |
| bidDeliveryType4 | int | 申买价4结算方式 | 0 |
| bidTradeVolume4 | long | 订单总量,申买量4,单位万元 | 0 |
| bidTradingAcctNumber4 | String | 申买价4交易账户 |  |
| askPrice4 | double | 申卖价4 |  |
| askYTM4 | double | 申卖到期收益率4 | 0 |
| askVolume4 | long | 申卖量4,单位万元 | 0 |
| askMDTime4 | String | 卖4行情发生时间 |  |
| askQuoteID4 | String | 申卖价4报价编号 |  |
| askDeliveryType4 | int | 申卖价4结算方式 | 0 |
| askTradeVolume4 | long | 订单总量,申卖量4,单位万元 | 0 |
| askTradingAcctNumber4 | String | 申卖价4交易账户 |  |
| bidPrice5 | double | 申买价5 |  |
| bidYTM5 | double | 申买到期收益率5 | 0 |
| bidVolume5 | long | 申买量5,单位万元 | 0 |
| bidMDTime5 | String | 买5行情发生时间 |  |
| bidQuoteID5 | String | 申买价5报价编号 |  |
| bidDeliveryType5 | int | 申买价5结算方式 | 0 |
| bidTradeVolume5 | long | 订单总量,申买量5,单位万元 | 0 |
| bidTradingAcctNumber5 | String | 申买价5交易账户 |  |
| askPrice5 | double | 申卖价5 |  |
| askYTM5 | double | 申卖到期收益率5 | 0 |
| askVolume5 | long | 申卖量5,单位万元 | 0 |
| askMDTime5 | String | 卖5行情发生时间 |  |
| askQuoteID5 | String | 申卖价5报价编号 |  |
| askDeliveryType5 | int | 申卖价5结算方式 | 0 |
| askTradeVolume5 | long | 订单总量,申卖量5,单位万元 | 0 |
| askTradingAcctNumber5 | String | 申卖价5交易账户 |  |
| bidPrice6 | double | 申买价6 |  |
| bidYTM6 | double | 申买到期收益率6 | 0 |
| bidVolume6 | long | 申买量6,单位万元 | 0 |
| bidMDTime6 | String | 买6行情发生时间 |  |
| bidQuoteID6 | String | 申买价6报价编号 |  |
| bidDeliveryType6 | int | 申买价6结算方式 | 0 |
| bidTradeVolume6 | long | 订单总量,申买量6,单位万元 | 0 |
| bidTradingAcctNumber6 | String | 申买价6交易账户 |  |
| askPrice6 | double | 申卖价6 |  |
| askYTM6 | double | 申卖到期收益6 | 0 |
| askVolume6 | long | 申卖量6,单位万元 | 0 |
| askMDTime6 | String | 卖6行情发生时间 |  |
| askQuoteID6 | String | 申卖价6报价编号 |  |
| askDeliveryType6 | int | 申卖价6结算方式 | 0 |
| askTradeVolume6 | long | 订单总量,申卖量6,单位万元 | 0 |
| askTradingAcctNumber6 | String | 申卖价6交易账户 |  |
| bidPrice7 | double | 申买价7 |  |
| bidYTM7 | double | 申买到期收益率7 | 0 |
| bidVolume7 | long | 申买量7,单位万元 | 0 |
| bidMDTime7 | String | 买7行情发生时间 |  |
| bidQuoteID7 | String | 申买价7报价编号 |  |
| bidDeliveryType7 | int | 申买价7结算方式 | 0 |
| bidTradeVolume7 | long | 订单总量,申买量7,单位万元 | 0 |
| bidTradingAcctNumber7 | String | 申买价7交易账户 |  |
| askPrice7 | double | 申卖价7 |  |
| askYTM7 | double | 申卖到期收益率7 | 0 |
| askVolume7 | long | 申卖量7,单位万元 | 0 |
| askMDTime7 | String | 卖7行情发生时间 |  |
| askQuoteID7 | String | 申卖价7报价编号 |  |
| askDeliveryType7 | int | 申卖价7结算方式 | 0 |
| askTradeVolume7 | long | 订单总量,申卖量7,单位万元 | 0 |
| askTradingAcctNumber7 | String | 申卖价7交易账户 |  |
| bidPrice8 | double | 申买价8 |  |
| bidYTM8 | double | 申买到期收益率8 | 0 |
| bidVolume8 | long | 申买量8,单位万元 | 0 |
| bidMDTime8 | String | 买8行情发生时间 |  |
| bidQuoteID8 | String | 申买价8报价编号 |  |
| bidDeliveryType8 | int | 申买价8结算方式 | 0 |
| bidTradeVolume8 | long | 订单总量,申买量8,单位万元 | 0 |
| bidTradingAcctNumber8 | String | 申买价8交易账户 |  |
| askPrice8 | double | 申卖价8 |  |
| askYTM8 | double | 申卖到期收益率8 | 0 |
| askVolume8 | long | 申卖量8,单位万元 | 0 |
| askMDTime8 | String | 卖8行情发生时间 |  |
| askQuoteID8 | String | 申卖价8报价编号 |  |
| askDeliveryType8 | int | 申卖价8结算方式 | 0 |
| askTradeVolume8 | long | 订单总量,申卖量8,单位万元 | 0 |
| askTradingAcctNumber8 | String | 申卖价8交易账户 |  |
| bidPrice9 | double | 申买价9 |  |
| bidYTM9 | double | 申买到期收益率9 | 0 |
| bidVolume9 | long | 申买量9,单位万元 | 0 |
| bidMDTime9 | String | 买9行情发生时间 |  |
| bidQuoteID9 | String | 申买价9报价编号 |  |
| bidDeliveryType9 | int | 申买价9结算方式 | 0 |
| bidTradeVolume9 | long | 订单总量,申买量9,单位万元 | 0 |
| bidTradingAcctNumber9 | String | 申买价9交易账户 |  |
| askPrice9 | double | 申卖价9 |  |
| askYTM9 | double | 申卖到期收益率9 | 0 |
| askVolume9 | long | 申卖量9,单位万元 | 0 |
| askMDTime9 | String | 卖9行情发生时间 |  |
| askQuoteID9 | String | 申卖价9报价编号 |  |
| askDeliveryType9 | int | 申卖价9结算方式 | 0 |
| askTradeVolume9 | long | 订单总量,申卖量9,单位万元 | 0 |
| askTradingAcctNumber9 | String | 申卖价9交易账户 |  |
| bidPrice10 | double | 申买价10 |  |
| bidYTM10 | double | 申买到期收益率10 | 0 |
| bidVolume10 | long | 申买量10,单位万元 | 0 |
| bidMDTime10 | String | 买10行情发生时间 |  |
| bidQuoteID10 | String | 申买价10报价编号 |  |
| bidDeliveryType10 | int | 申买价10结算方式 | 0 |
| bidTradeVolume10 | long | 订单总量,申买量10,单位万元 | 0 |
| bidTradingAcctNumber10 | String | 申买价10交易账户 |  |
| askPrice10 | double | 申卖价10 |  |
| askYTM10 | double | 申卖到期收益率10 | 0 |
| askVolume10 | long | 申卖量10,单位万元 | 0 |
| askMDTime10 | String | 卖10行情发生时间 |  |
| askQuoteID10 | String | 申卖价10报价编号 |  |
| askDeliveryType10 | int | 申卖价10结算方式 | 0 |
| askTradeVolume10 | long | 订单总量,申卖量10,单位万元 | 0 |
| askTradingAcctNumber10 | String | 申卖价10交易账户 |  |
| transactTime | String | 行情生成时间 | 0.557540706 |
| marketIndicator | int | 市场 | 1 |
| realTimeUndertakeFlag | int | 实时承接标识 | 0 |
| subjectPartyType | int | 本方主体类型 | -99 |
| bidClearingMethod1 | int | 申买1清算类型 | 13 |
| bidClearingMethod2 | int | 申买2清算类型 | 0 |
| bidClearingMethod3 | int | 申买3清算类型 | 0 |
| bidClearingMethod4 | int | 申买4清算类型 | 0 |
| bidClearingMethod5 | int | 申买5清算类型 | 0 |
| bidClearingMethod6 | int | 申买6清算类型 | 0 |
| bidClearingMethod7 | int | 申买7清算类型 | 0 |
| bidClearingMethod8 | int | 申买8清算类型 | 0 |
| bidClearingMethod9 | int | 申买9清算类型 | 0 |
| bidClearingMethod10 | int | 申买10清算类型 | 0 |
| askClearingMethod1 | int | 申卖1清算类型 | 13 |
| askClearingMethod2 | int | 申卖2清算类型 | 0 |
| askClearingMethod3 | int | 申卖3清算类型 | 0 |
| askClearingMethod4 | int | 申卖4清算类型 | 0 |
| askClearingMethod5 | int | 申卖5清算类型 | 0 |
| askClearingMethod6 | int | 申卖6清算类型 | 0 |
| askClearingMethod7 | int | 申卖7清算类型 | 0 |
| askClearingMethod8 | int | 申卖8清算类型 | 0 |
| askClearingMethod9 | int | 申卖9清算类型 | 0 |
| askClearingMethod10 | int | 申卖10清算类型 | 0 |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: 无

#### 3.3.4 经纪商报价接口
- **接口路径**: `/market-data/broker-best-quote`
- **请求方法**: POST
- **请求参数**: `VBrokerBestQuoteReq`对象

| 字段名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| bondID | String | 交易品种代码 | 194998.SH |
| exchangeCode | int | 交易所代号 | 1 |
| bondName | String | 债券名称 | 22南新04 |
| brokerShortName | int | 经纪商 | 6 |
| quoteTime | String | 报价时间 | 20241202-09:05:27 |
| bidYield | double | 买收益率 | 2.500012 |
| bidNetPrice | double | 买净价 | 102.015916 |
| ofrYield | double | 卖收益率 |  |
| ofrNetPrice | double | 卖净价 |  |
| t0BidVolume | long | T+0买报价数量（所有） | 0 |
| t0BidBargain1Volume | long | T+0买报价*数量 | 0 |
| t0BidBargain2Volume | long | T+0买报价**数量 | 0 |
| t0BidOCOVolume | long | T+0买报价OCO数量 | 0 |
| t0BidPackVolume | long | T+0买报价打包数量 | 0 |
| t0BidStrikeVolume | long | T+0买报价行权数量 | 0 |
| t0BidIndicativeCount | int | T+0买意向报价数 | 0 |
| t0BidQuoteCount | int | T+0买报价数 | 0 |
| t0OfrVolume | long | T+0卖报价数量（所有） | 0 |
| t0OfrBargain1Volume | long | T+0卖报价*数量 | 0 |
| t0OfrBargain2Volume | long | T+0卖报价**数量 | 0 |
| t0OfrOCOVolume | long | T+0卖报价OCO数量 | 0 |
| t0OfrPackVolume | long | T+0卖报价打包数量 | 0 |
| t0OfrStrikeVolume | long | T+0卖报价行权数量 | 0 |
| t0OfrIndicativeCount | int | T+0卖意向报价数 | 0 |
| t0OfrQuoteCount | int | T+0卖报价数 | 0 |
| t1BidVolume | long | T+1买报价数量（所有） | 0 |
| t1BidBargain1Volume | long | T+1买报价*数量 | 0 |
| t1BidBargain2Volume | long | T+1买报价**数量 | 0 |
| t1BidOCOVolume | long | T+1买报价OCO数量 | 0 |
| t1BidPackVolume | long | T+1买报价打包数量 | 0 |
| t1BidStrikeVolume | long | T+1买报价行权数量 | 0 |
| t1BidIndicativeCount | int | T+1买意向报价数 | 0 |
| t1BidQuoteCount | int | T+1买报价数 | 0 |
| t1OfrVolume | long | T+1卖报价数量（所有） | 0 |
| t1OfrBargain1Volume | long | T+1卖报价*数量 | 0 |
| t1OfrBargain2Volume | long | T+1卖报价**数量 | 0 |
| t1OfrOCOVolume | long | T+1卖报价OCO数量 | 0 |
| t1OfrPackVolume | long | T+1卖报价打包数量 | 0 |
| t1OfrStrikeVolume | long | T+1卖报价行权数量 | 0 |
| t1OfrIndicativeCount | int | T+1卖意向报价数 | 0 |
| t1OfrQuoteCount | int | T+1卖报价数 | 0 |
| fWDBidVolume | long | 远期买报价数量（所有） | 0 |
| fWDBidBargain1Volume | long | 远期买报价*数量 | 0 |
| fWDBidBargain2Volume | long | 远期买报价**数量 | 0 |
| fWDBidOCOVolume | long | 远期买报价OCO数量 | 0 |
| fWDBidPackVolume | long | 远期买报价打包数量 | 0 |
| fWDBidStrikeVolume | long | 远期买报价行权数量 | 0 |
| fWDBidIndicativeCount | int | 远期买意向报价数 | 0 |
| fWDBidQuoteCount | int | 远期买报价数 | 0 |
| fWDOfrVolume | long | 远期卖报价数量（所有） | 0 |
| fWDOfrBargain1Volume | long | 远期卖报价*数量 | 0 |
| fWDOfrBargain2Volume | long | 远期卖报价**数量 | 0 |
| fWDOfrOCOVolume | long | 远期卖报价OCO数量 | 0 |
| fWDOfrPackVolume | long | 远期卖报价打包数量 | 0 |
| fWDOfrStrikeVolume | long | 远期卖报价行权数量 | 0 |
| fWDOfrIndicativeCount | int | 远期卖意向报价数 | 0 |
| fWDOfrQuoteCount | int | 远期卖报价数 | 0 |
| isBidOutlier | int | 是否Bid毛刺 | 1 |
| isOfrOutlier | int | 是否Ofr毛刺 | 0 |
| bidComment | String | 报价说明 | --(*) |
| ofrComment | String | 报价说明 | Strike |
| reserver1 | String | 系统保留字段1 | None |
| reserver2 | String | 系统保留字段2 | 68695320 |
| reserver3 | String | 系统保留字段3 | bid_done |
| reserver4 | String | 系统保留字段4 | ofr_done |
| reserver5 | String | 系统保留字段5 | 2.5 |
| bidStrikeYield | double | 买行权收益率 |  |
| ofrStrikeYield | double | 卖行权收益率 |  |
| bidFullPrice | double | 买全价 | 104.426875 |
| ofrFullPrice | double | 卖全价 |  |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: 无

#### 3.3.5 经纪商成交接口
- **接口路径**: `/market-data/broker-deal`
- **请求方法**: POST
- **请求参数**: `VBrokerDealReq`对象

| 字段名 | 类型 | 说明 | 默认值 |
| :--- | :--- | :--- | :--- |
| bondID | String | 交易品种代码 | 112517268 |
| exchangeCode | int | 交易所代码 | 31 |
| bondName | String | 债券名称 | 25光大银行CD268 |
| direction | char | 买入卖出 | X |
| amount | double | 成交面额 | 0 |
| quoteID | String | 交易行情ID | e1468178382000103432 |
| legSettlType | int | 清算速度 | 1 |
| settlDate | String | 结算日期 |  |
| netPrice | double | 成交净价 |  |
| fullPrice | double | 成交全价 |  |
| yield | double | 收益率 | 1.6 |
| strikeFlag | int | 是否行权收益率 | 0 |
| execType | char | 成交状态 | 0 |
| transactTime | String | 业务发生时间 | 20260203-09:36:43 |
| brokerShortName | int | 经纪商 | 1 |
| reserver1 | String | 系统保留字段1 | YTM |
| reserver2 | String | 系统保留字段2 |  |
| reserver3 | String | 系统保留字段3 |  |
| reserver4 | String | 系统保留字段4 |  |
| reserver5 | String | 系统保留字段5 |  |
| strikeYield | double | 行权收益率 |  |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: 无

#### 3.3.6 市场状态接口
- **接口路径**: `/market-data/market-status`
- **请求方法**: POST
- **请求参数**: `VMarketStatusReq`对象

| 字段名 | 类型 | 说明 | 默认值 |
|-------|------|------|--------|
| marketIndicator | int | 市场 | |
| tradeMethod | int | 交易方式 | |
| tradSesStatus | int | 交易时间段状态 | |
| tradSesTime | String | 时间 | |

- **返回值**: `Response<String>` - 成功响应
- **需监听消息eventName**: 无

## 4. 响应格式

所有接口返回`Response<T>`对象，结构如下：

| 字段名 | 类型 | 说明 |
|-------|--|------|
| code | String | 响应状态码 (0表示成功) |
| message | String | 响应消息 |
| data | T | 响应数据 |

## 5. 示例请求

### 5.1 连接客户端示例
```json
POST /hft-sdk/client/connect
Content-Type: application/json

{
"ip": "172.24.16.12",
"port": 30801
}
```

### 5.2 FAK订单示例
```json
POST /hft-sdk/client/fak-order
Content-Type: application/json

{
"securityID": "100001",
"direction": "B",
"price": 100.5,
"ymt": 3.2,
"volume": 1000,
"deliveryType": 1,
"clearingMethod": 1,
"settlType": 1,
"quoteId": "Q12345",
"mdTime": "20260303100000",
"accountId": "ACC001",
"orderInnerId": "ORD12345",
"portfolioId": "PORT001",
"instructionID": "INST12345"
}
```

### 5.3 SSE连接示例
```
GET /hft-sdk/sse/stream?clientId=client123
Accept: text/event-stream
```
