# HFT SDK View Summary

Use this file as a compact summary before reading the full SDK document.

## Base addresses

- HTTP base URL: `http://172.24.17.44:9005/hft-sdk`
- SSE URL: `http://172.24.17.44:9005/hft-sdk/sse/stream?clientId={clientId}`

## Common response shape

All documented interfaces return `Response<T>` with:

- `code`
- `message`
- `data`

## Common endpoint groups

- Strategy actions
  Example paths include `/client/update-rule-status` and `/client/update-rule-params`
- Order actions
  Example paths include `/client/fak-order`, `/client/bilateral-order`, `/client/xbond-order`, and cancel endpoints
- Market data
  Example paths include `/market-data/inner-market-data`, `/market-data/fix-market-data`, `/market-data/broker-best-quote`, `/market-data/broker-deal`, `/market-data/market-status`

## Generation guidance

- Prefer documented default values as the HTML form defaults.
- Generate the first page version with real HTTP and SSE bindings instead of a static preview.
- When a requested field is not documented, omit it from the page and tell the user it was not found in the interface document.
- When the requested page capability is not documented, stop and report that the current system does not support it.
- Keep the HTML page aligned with HFT desktop density rather than building a generic API playground.