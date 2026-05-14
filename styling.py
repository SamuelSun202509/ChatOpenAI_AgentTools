"""Bosch corporate-design styling for the Streamlit chatbot.

Everything that defines the *visual identity* lives in this single module:

  * `BOSCH_CSS`              — full global stylesheet (8px grid, palette, typography)
  * `BOSCH_LOGO_SVG`         — official Bosch logo SVG (verbatim, never recreate)
  * `BOSCH_SUPERGRAPHIC_URI` — official supergraphic gradient (data-URI SVG)
  * `inject_bosch_style()`   — call once near the top of `app.py`
  * `render_bosch_header()`  — supergraphic ribbon + white header bar with logo
  * `render_user_bubble()`   — user chat message
  * `render_assistant_bubble()` — assistant chat message
  * `render_sources()`       — `📚 References (N)` expander
  * `render_unauthorized_card()` — Bosch-red "🔒 Unauthorized" card

Design rules enforced here come from the Bosch brand-style guide:
  - No shadows, no decorative gradients (only the official supergraphic).
  - Bosch Red (`#e0000a`) is reserved for the logo wordmark and a single
    critical signal (the Unauthorized card). Primary CTAs use Bosch Blue.
  - All spacing is a multiple of 8px.
  - Typography: Bosch Office Sans → Helvetica Neue → Arial (license-aware
    fallback chain; the font file itself is not shipped here).
"""

from __future__ import annotations

import streamlit as st


# ============================================================
# Official Bosch supergraphic gradient (SVG data URI, do NOT replace).
# Source: bosch-brand-style-guide skill — verbatim.
# ============================================================
BOSCH_SUPERGRAPHIC_URI = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbDpzcGFjZT0icHJlc2VydmU"
    "iIHdpZHRoPSI3MjAiIGhlaWdodD0iMzAwIiB2aWV3Qm94PSIwIDAgNzIwIDMwMCI+PHN0eWxlPi5zdDd7ZmlsbDojOTQxYjFlfTwvc3R5b"
    "GU+PGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTEuNTUgLTMuMykiPjxsaW5lYXJHcmFkaWVudCBpZD0iU1ZHSURfMV8iIHgxPSIxMTguOTg"
    "iIHgyPSI4NDIuMDgiIHkxPSItMzIuNjYzIiB5Mj0iLTMyLjY2MyIgZ3JhZGllbnRUcmFuc2Zvcm09Im1hdHJpeCgxIDAgMCAtMSAtMTE4L"
    "jk4IDEyMC41NCkiIGdyYWRpZW50VW5pdHM9InVzZXJTcGFjZU9uVXNlIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiM5NTIzMzE"
    "iLz48c3RvcCBvZmZzZXQ9Ii4wMzYiIHN0b3AtY29sb3I9IiM5MjFDMUQiLz48c3RvcCBvZmZzZXQ9Ii4wODUiIHN0b3AtY29sb3I9IiNCM"
    "DI3MzkiLz48c3RvcCBvZmZzZXQ9Ii4xMjQiIHN0b3AtY29sb3I9IiNBRDFGMjQiLz48c3RvcCBvZmZzZXQ9Ii4xNTEiIHN0b3AtY29sb3I"
    "9IiNDNzIwMjYiLz48c3RvcCBvZmZzZXQ9Ii4xNyIgc3RvcC1jb2xvcj0iI0Q0MjAyNyIvPjxzdG9wIG9mZnNldD0iLjE3NiIgc3RvcC1jb"
    "2xvcj0iI0NDMjQzMSIvPjxzdG9wIG9mZnNldD0iLjE4OSIgc3RvcC1jb2xvcj0iI0I3MkI0QyIvPjxzdG9wIG9mZnNldD0iLjIwNyIgc3R"
    "vcC1jb2xvcj0iIzk1MzM3MSIvPjxzdG9wIG9mZnNldD0iLjIxNCIgc3RvcC1jb2xvcj0iIzg4MzU3RiIvPjxzdG9wIG9mZnNldD0iLjI0N"
    "CIgc3RvcC1jb2xvcj0iIzg1MzY4MSIvPjxzdG9wIG9mZnNldD0iLjI2NCIgc3RvcC1jb2xvcj0iIzZGMzY4QiIvPjxzdG9wIG9mZnNldD0"
    "iLjI5MSIgc3RvcC1jb2xvcj0iIzM5NDI4RiIvPjxzdG9wIG9mZnNldD0iLjMyNCIgc3RvcC1jb2xvcj0iIzIzM0Q3RCIvPjxzdG9wIG9mZ"
    "nNldD0iLjQxOCIgc3RvcC1jb2xvcj0iIzMyMkM2RiIvPjxzdG9wIG9mZnNldD0iLjQ5NCIgc3RvcC1jb2xvcj0iIzJBMzg4NSIvPjxzdG9"
    "wIG9mZnNldD0iLjU1OCIgc3RvcC1jb2xvcj0iIzFENjJBMSIvPjxzdG9wIG9mZnNldD0iLjU3IiBzdG9wLWNvbG9yPSIjMjc2Q0E1Ii8+P"
    "HN0b3Agb2Zmc2V0PSIuNjEiIHN0b3AtY29sb3I9IiM0MzhFQjMiLz48c3RvcCBvZmZzZXQ9Ii42NCIgc3RvcC1jb2xvcj0iIzU1QTVCQyI"
    "vPjxzdG9wIG9mZnNldD0iLjY1NiIgc3RvcC1jb2xvcj0iIzVDQUZCRiIvPjxzdG9wIG9mZnNldD0iLjY3OCIgc3RvcC1jb2xvcj0iIzU2Q"
    "UJCRCIvPjxzdG9wIG9mZnNldD0iLjcwNiIgc3RvcC1jb2xvcj0iIzQzOUZCOCIvPjxzdG9wIG9mZnNldD0iLjczNyIgc3RvcC1jb2xvcj0"
    "iIzE4OEVBRiIvPjxzdG9wIG9mZnNldD0iLjc0MyIgc3RvcC1jb2xvcj0iIzAzOEJBRSIvPjxzdG9wIG9mZnNldD0iLjc5IiBzdG9wLWNvb"
    "G9yPSIjMDY5MjkyIi8+PHN0b3Agb2Zmc2V0PSIuODg3IiBzdG9wLWNvbG9yPSIjMDVBMTRCIi8+PHN0b3Agb2Zmc2V0PSIxIiBzdG9wLWN"
    "vbG9yPSIjMDM5MjdFIi8+PC9saW5lYXJHcmFkaWVudD48cGF0aCBkPSJNMCAwaDcyMy4xdjMwNi40SDB6IiBzdHlsZT0iZmlsbDp1cmwoI"
    "1NWR0lEXzFfKSIvPjxsaW5lYXJHcmFkaWVudCBpZD0iU1ZHSURfMl8iIHgxPSIzMjUuMDgiIHgyPSIyMzUuOTgiIHkxPSItMTA5LjI2IiB"
    "5Mj0iLTEwOS4yNiIgZ3JhZGllbnRUcmFuc2Zvcm09Im1hdHJpeCgxIDAgMCAtMSAtMTE4Ljk4IDEyMC41NCkiIGdyYWRpZW50VW5pdHM9I"
    "nVzZXJTcGFjZU9uVXNlIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiM4OTM2ODAiLz48c3RvcCBvZmZzZXQ9Ii4zMzUiIHN0b3A"
    "tY29sb3I9IiM4OTM2ODAiLz48c3RvcCBvZmZzZXQ9Ii41MDIiIHN0b3AtY29sb3I9IiM4RDMxNkQiLz48c3RvcCBvZmZzZXQ9Ii44NCIgc"
    "3RvcC1jb2xvcj0iIzkwMjk0RCIvPjxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvcj0iIzkwMjU0MSIvPjwvbGluZWFyR3JhZGllbnQ+PHB"
    "hdGggZD0iTTE3NS4xIDE1My4yIDExNyAzMDYuNGg4OS4xeiIgc3R5bGU9ImZpbGw6dXJsKCNTVkdJRF8yXykiLz48bGluZWFyR3JhZGllb"
    "nQgaWQ9IlNWR0lEXzNfIiB4MT0iNDc4LjkzIiB4Mj0iNDQ2LjU1IiB5MT0iMTIwLjI0IiB5Mj0iLTgyLjI4NCIgZ3JhZGllbnRUcmFuc2Z"
    "vcm09Im1hdHJpeCgxIDAgMCAtMSAtMTE4Ljk4IDEyMC41NCkiIGdyYWRpZW50VW5pdHM9InVzZXJTcGFjZU9uVXNlIj48c3RvcCBvZmZzZ"
    "XQ9IjAiIHN0b3AtY29sb3I9IiMzMjJDNkYiLz48c3RvcCBvZmZzZXQ9Ii4yNDMiIHN0b3AtY29sb3I9IiMzMjJDNkYiLz48c3RvcCBvZmZ"
    "zZXQ9Ii40NiIgc3RvcC1jb2xvcj0iIzMwMkY3MiIvPjxzdG9wIG9mZnNldD0iLjcxNiIgc3RvcC1jb2xvcj0iIzJBM0E3RSIvPjxzdG9wI"
    "G9mZnNldD0iLjk5IiBzdG9wLWNvbG9yPSIjMTU0QTkzIi8+PHN0b3Agb2Zmc2V0PSIxIiBzdG9wLWNvbG9yPSIjMTM0Qjk0Ii8+PC9saW5"
    "lYXJHcmFkaWVudD48cGF0aCBkPSJtMjg4LjQgMTUzLjIgMjIuMyAxNTMuMmg0Ny40VjBoLTQ1LjJ6IiBzdHlsZT0iZmlsbDp1cmwoI1NWR"
    "0lEXzNfKSIvPjxsaW5lYXJHcmFkaWVudCBpZD0iU1ZHSURfNF8iIHgxPSIyOTQuMDgiIHgyPSIzNzIuODgiIHkxPSItMzIuNjYzIiB5Mj0"
    "iLTMyLjY2MyIgZ3JhZGllbnRUcmFuc2Zvcm09Im1hdHJpeCgxIDAgMCAtMSAtMTE4Ljk4IDEyMC41NCkiIGdyYWRpZW50VW5pdHM9InVzZ"
    "XJTcGFjZU9uVXNlIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiM2RjM3OEQiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I"
    "9IiMzQTQyOTEiLz48L2xpbmVhckdyYWRpZW50PjxwYXRoIGQ9Im0xNzUuMSAxNTMuMiAzMSAxNTMuMiA0Ny44LTE1My4yTDIwOS40IDB6I"
    "iBzdHlsZT0iZmlsbDp1cmwoI1NWR0lEXzRfKSIvPjxsaW5lYXJHcmFkaWVudCBpZD0iU1ZHSURfNV8iIHgxPSI0MzEuODgiIHgyPSIzMjU"
    "uMDgiIHkxPSItMzIuNjYzIiB5Mj0iLTMyLjY2MyIgZ3JhZGllbnRUcmFuc2Zvcm09Im1hdHJpeCgxIDAgMCAtMSAtMTE4Ljk4IDEyMC41N"
    "CkiIGdyYWRpZW50VW5pdHM9InVzZXJTcGFjZU9uVXNlIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiMyMzNEN0QiLz48c3RvcCB"
    "vZmZzZXQ9Ii4yNDkiIHN0b3AtY29sb3I9IiMyOTNEN0QiLz48c3RvcCBvZmZzZXQ9Ii41NDUiIHN0b3AtY29sb3I9IiMzQTNDODAiLz48c"
    "3RvcCBvZmZzZXQ9Ii44NjIiIHN0b3AtY29sb3I9IiM1MTNCODQiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiM1RDNBODYiLz4"
    "8L2xpbmVhckdyYWRpZW50PjxwYXRoIGQ9Im0yNTMuOSAxNTMuMi00Ny44IDE1My4yaDEwNC42bC0yMi4zLTE1My4yTDMxMi45IDBIMjA5L"
    "jR6IiBzdHlsZT0iZmlsbDp1cmwoI1NWR0lEXzVfKSIvPjxwYXRoIGQ9Ik0xMTYuMSAwSDU1Ljd2OTQuOGwzNC4yIDU4LjQtMzQuMiA1OC4"
    "0djk0LjhIMTE3TDk1LjIgMTUzLjJ6IiBzdHlsZT0iZmlsbDojYWYyMDI0Ii8+PGxpbmVhckdyYWRpZW50IGlkPSJTVkdJRF82XyIgeDE9I"
    "jMyOS4xMSIgeDI9IjIzMi42NyIgeTE9IjQzLjkzNyIgeTI9IjQzLjkzNyIgZ3JhZGllbnRUcmFuc2Zvcm09Im1hdHJpeCgxIDAgMCAtMSA"
    "tMTE4Ljk4IDEyMC41NCkiIGdyYWRpZW50VW5pdHM9InVzZXJTcGFjZU9uVXNlIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiM4O"
    "TM2ODAiLz48c3RvcCBvZmZzZXQ9Ii4zMzUiIHN0b3AtY29sb3I9IiM4OTM2ODAiLz48c3RvcCBvZmZzZXQ9Ii41MDIiIHN0b3AtY29sb3I"
    "9IiM4RDMxNkQiLz48c3RvcCBvZmZzZXQ9Ii44NCIgc3RvcC1jb2xvcj0iIzkwMjk0RCIvPjxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvc"
    "j0iIzkwMjU0MSIvPjwvbGluZWFyR3JhZGllbnQ+PHBhdGggZD0iTTE3NS4xIDE1My4yIDIwOS40IDBoLTkzLjN6IiBzdHlsZT0iZmlsbDp"
    "1cmwoI1NWR0lEXzZfKSIvPjxwYXRoIGZpbGw9IiM5NDFiMWUiIGQ9Ik01NS43IDk0LjhWMEgweiIgY2xhc3M9InN0NyIvPjxwYXRoIGQ9I"
    "m01NS43IDIxMS42IDM0LjItNTguNC0zNC4yLTU4LjR6IiBzdHlsZT0iZmlsbDojYjEyNzM5Ii8+PHBhdGggZmlsbD0iIzk0MWIxZSIgZD0"
    "iTTU1LjcgMjExLjYgMCAzMDYuNGg1NS43eiIgY2xhc3M9InN0NyIvPjxwYXRoIGQ9Ik01NS43IDk0LjggMCAwdjMwNi40bDU1LjctOTQuO"
    "HoiIHN0eWxlPSJmaWxsOiM5NTI0MzIiLz48cGF0aCBkPSJNMTE2LjEgMCA5NS4yIDE1My4yIDExNyAzMDYuNGw1OC4xLTE1My4yeiIgc3R"
    "5bGU9ImZpbGw6I2Q0MjAyNyIvPjxsaW5lYXJHcmFkaWVudCBpZD0iU1ZHSURfN18iIHgxPSI3NDguOTYiIHgyPSI3NDguOTYiIHkxPSIxM"
    "jAuNDQiIHkyPSItMTg2LjA2IiBncmFkaWVudFRyYW5zZm9ybT0ibWF0cml4KDEgMCAwIC0xIC0xMTguOTggMTIwLjU0KSIgZ3JhZGllbnR"
    "Vbml0cz0idXNlclNwYWNlT25Vc2UiPjxzdG9wIG9mZnNldD0iMCIgc3RvcC1jb2xvcj0iIzk0QkU1NSIvPjxzdG9wIG9mZnNldD0iLjA0N"
    "CIgc3RvcC1jb2xvcj0iIzkzQkQ1OCIvPjxzdG9wIG9mZnNldD0iLjM4OSIgc3RvcC1jb2xvcj0iIzhCQkM2QSIvPjxzdG9wIG9mZnNldD0"
    "iLjcxNSIgc3RvcC1jb2xvcj0iIzg2QkM3NSIvPjxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvcj0iIzg0QkM3OSIvPjwvbGluZWFyR3Jhd"
    "GllbnQ+PHBhdGggZD0iTTY0MS42IDI1OS42YzEuNy0yNS40IDEwLTU0LjYgMTguOC04NS42IDEuNC01IDIuOC0xMCA0LjItMTUuMXEtMi4"
    "xLTguMjUtNC4yLTE2LjJjLTguOC0zMy4zLTE3LTY0LjctMTguOC05Mi0xLjQtMjEuMiAxLjQtMzcgOC45LTUwLjZoLTQ1LjljLTcuNSAxO"
    "C4zLTEwLjMgMjkuMS04LjkgNTAuMyAxLjcgMjcuMyAxMCA1OC43IDE4LjggOTIgMTMgNDkuMyAyOCAxMDYuMiAyMy4yIDE2NC4yaDEyLjl"
    "jLTcuNi0xMi44LTEwLjQtMjcuMy05LTQ3IiBzdHlsZT0iZmlsbDp1cmwoI1NWR0lEXzdfKSIvPjxsaW5lYXJHcmFkaWVudCBpZD0iU1ZHS"
    "URfOF8iIHgxPSI2NTMuNzYiIHgyPSI3MzMuNDkiIHkxPSIxMTcuMjkiIHkyPSItMTg0LjQ1IiBncmFkaWVudFRyYW5zZm9ybT0ibWF0cml"
    "4KDEgMCAwIC0xIC0xMTguOTggMTIwLjU0KSIgZ3JhZGllbnRVbml0cz0idXNlclNwYWNlT25Vc2UiPjxzdG9wIG9mZnNldD0iMCIgc3Rvc"
    "C1jb2xvcj0iIzA4QTI0QiIvPjxzdG9wIG9mZnNldD0iLjE2OCIgc3RvcC1jb2xvcj0iIzBBQTE0RSIvPjxzdG9wIG9mZnNldD0iLjQwNSI"
    "gc3RvcC1jb2xvcj0iIzBCOUU1NyIvPjxzdG9wIG9mZnNldD0iLjY4MyIgc3RvcC1jb2xvcj0iIzA5OUE2NyIvPjxzdG9wIG9mZnNldD0iL"
    "jk5IiBzdG9wLWNvbG9yPSIjMDQ5NDdEIi8+PHN0b3Agb2Zmc2V0PSIxIiBzdG9wLWNvbG9yPSIjMDQ5MzdFIi8+PC9saW5lYXJHcmFkaWV"
    "udD48cGF0aCBkPSJNNjE0LjUgMTQyLjNjLTguOC0zMy4zLTE3LTY0LjctMTguOC05Mi0xLjQtMjEuMiAxLjQtMzIgOC45LTUwLjNoLTM1L"
    "jRjNS43IDUzLjktMy44IDEwNi43LTEzLjYgMTY2LjgtNS43IDM1LTExLjcgNzEuMy0xMy4yIDEwMC42LTEuMSAyMS4xLjQgMzIuOCAxLjg"
    "gMzloOTMuNWM0LjgtNTcuOS0xMC4zLTExNC44LTIzLjItMTY0LjEiIHN0eWxlPSJmaWxsOnVybCgjU1ZHSURfOF8pIi8+PHBhdGggZD0iT"
    "TY2NC42IDE1OC45Yy0xLjQgNS4xLTIuOCAxMC4xLTQuMiAxNS4xLTguOCAzMS0xNyA2MC4yLTE4LjggODUuNi0xLjQgMTkuNyAxLjQgMzQ"
    "uMiA5IDQ2LjloMzNjNC4yLTUxLjgtNy4yLTEwMi4zLTE5LTE0Ny42IiBzdHlsZT0iZmlsbDojMWM5YTQ4Ii8+PGxpbmVhckdyYWRpZW50I"
    "GlkPSJTVkdJRF85XyIgeDE9IjgxMi44MyIgeDI9IjgxMi44MyIgeTE9IjEyMC41NCIgeTI9Ii0xODUuOTYiIGdyYWRpZW50VHJhbnNmb3J"
    "tPSJtYXRyaXgoMSAwIDAgLTEgLTExOC45OCAxMjAuNTQpIiBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHN0b3Agb2Zmc2V0P"
    "SIwIiBzdG9wLWNvbG9yPSIjNjlBMDYwIi8+PHN0b3Agb2Zmc2V0PSIuMDQiIHN0b3AtY29sb3I9IiM2MzlENUMiLz48c3RvcCBvZmZzZXQ"
    "9Ii4yMTkiIHN0b3AtY29sb3I9IiM0Qzk0NEYiLz48c3RvcCBvZmZzZXQ9Ii40MTgiIHN0b3AtY29sb3I9IiMzNzhFNDciLz48c3RvcCBvZ"
    "mZzZXQ9Ii42NTEiIHN0b3AtY29sb3I9IiMyOThCNDQiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiMyMzhBNDMiLz48L2xpbmV"
    "hckdyYWRpZW50PjxwYXRoIGQ9Ik02ODAuNSAwYzEwLjcgNTUuMy0yLjUgMTEwLjQtMTUuOSAxNTguOSAxMS43IDQ1LjMgMjMuMiA5NS44I"
    "DE4LjkgMTQ3LjZoMzkuNlYweiIgc3R5bGU9ImZpbGw6dXJsKCNTVkdJRF85XykiLz48bGluZWFyR3JhZGllbnQgaWQ9IlNWR0lEXzEwXyI"
    "geDE9IjY1Mi40NSIgeDI9IjY1Mi40NSIgeTE9IjEyMC41NCIgeTI9Ii0xODUuODYiIGdyYWRpZW50VHJhbnNmb3JtPSJtYXRyaXgoMSAwI"
    "DAgLTEgLTExOC45OCAxMjAuNTQpIiBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHN0b3Agb2Zmc2V0PSIwIiBzdG9wLWNvbG9"
    "yPSIjMDVCNURDIi8+PHN0b3Agb2Zmc2V0PSIuMjIiIHN0b3AtY29sb3I9IiMwNEIwRDciLz48c3RvcCBvZmZzZXQ9Ii41MzciIHN0b3AtY"
    "29sb3I9IiMwNUE0QzkiLz48c3RvcCBvZmZzZXQ9Ii45MTIiIHN0b3AtY29sb3I9IiMwNTkxQjQiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3A"
    "tY29sb3I9IiMwNThDQUUiLz48L2xpbmVhckdyYWRpZW50PjxwYXRoIGQ9Ik01NDIuMyAyNjcuNGMxLjUtMjkuNCA3LjUtNjUuNiAxMy4yL"
    "TEwMC42QzU2NS4zIDEwNi43IDU3NC44IDU0IDU2OS4xIDBoLTcwLjhjLTEuNCAxMS40LTIuOSAxOS4yLTEuOCA0MS44IDEuNSAzMS42IDc"
    "uNSA3MC41IDEzLjIgMTA4LjIgOC40IDU1LjQgMTYuNiAxMDguOCAxNS4xIDE1Ni40SDU0NGMtMS4zLTYuMi0yLjgtMTcuOS0xLjctMzkiI"
    "HN0eWxlPSJmaWxsOnVybCgjU1ZHSURfMTBfKSIvPjxwYXRoIGQ9Ik0zNzUuNyAxNTMuMiAzNTguMSAwdjMwNi40eiIgc3R5bGU9ImZpbGw"
    "6IzJhMzg4NiIvPjxsaW5lYXJHcmFkaWVudCBpZD0iU1ZHSURfMTFfIiB4MT0iNzUxLjA1IiB4Mj0iNzk2LjcxIiB5MT0iLTQuMzI4IiB5M"
    "j0iNzcuMTM2IiBncmFkaWVudFRyYW5zZm9ybT0ibWF0cml4KDEgMCAwIC0xIC0xMTguOTggMTIwLjU0KSIgZ3JhZGllbnRVbml0cz0idXN"
    "lclNwYWNlT25Vc2UiPjxzdG9wIG9mZnNldD0iMCIgc3RvcC1jb2xvcj0iIzYyQjE2RSIvPjxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvc"
    "j0iIzg3Qjk1NyIvPjwvbGluZWFyR3JhZGllbnQ+PHBhdGggZD0iTTY0MS42IDUwLjZjMS43IDI3LjMgMTAgNTguNyAxOC44IDkycTIuMSA"
    "3Ljk1IDQuMiAxNi4yQzY3OC4xIDExMC40IDY5MS4yIDU1LjMgNjgwLjUgMGgtMzBjLTcuNSAxMy42LTEwLjMgMjkuNC04LjkgNTAuNiIgc"
    "3R5bGU9ImZpbGw6dXJsKCNTVkdJRF8xMV8pIi8+PGxpbmVhckdyYWRpZW50IGlkPSJTVkdJRF8xMl8iIHgxPSI1NTAuNCIgeDI9IjYzMS4"
    "1OSIgeTE9IjExMy43MSIgeTI9Ii0xODkuMjgiIGdyYWRpZW50VHJhbnNmb3JtPSJtYXRyaXgoMSAwIDAgLTEgLTExOC45OCAxMjAuNTQpI"
    "iBncmFkaWVudFVuaXRzPSJ1c2VXU3BhY2VPblVzZSI+PHN0b3Agb2Zmc2V0PSIwIiBzdG9wLWNvbG9yPSIjMDY5QUQ0Ii8+PHN0b3Agb2Z"
    "mc2V0PSIuMzUyIiBzdG9wLWNvbG9yPSIjMzBBMENFIi8+PHN0b3Agb2Zmc2V0PSIxIiBzdG9wLWNvbG9yPSIjNUJCMEMwIi8+PC9saW5lY"
    "XJHcmFkaWVudD48cGF0aCBkPSJNNTA5LjggMTUwYy01LjctMzcuNy0xMS43LTc2LjYtMTMuMi0xMDguMi0xLjEtMjIuNy40LTMwLjQgMS4"
    "4LTQxLjhoLTQxLjVjMS41IDQwLjEtMS41IDg1LjMtNyAxNjAuOC0zLjEgNDMuNS04IDExMC41LTcgMTQ1LjdINTI1YzEuNC00Ny43LTYuO"
    "C0xMDEuMS0xNS4yLTE1Ni41IiBzdHlsZT0iZmlsbDp1cmwoI1NWR0lEXzEyXykiLz48bGluZWFyR3JhZGllbnQgaWQ9IlNWR0lEXzEzXyI"
    "geDE9IjUwNS4zMyIgeDI9IjUwNS4zMyIgeTE9IjEyMC41NCIgeTI9Ii0xODUuODYiIGdyYWRpZW50VHJhbnNmb3JtPSJtYXRyaXgoMSAwI"
    "DAgLTEgLTExOC45OCAxMjAuNTQpIiBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHN0b3Agb2Zmc2V0PSIwIiBzdG9wLWNvbG9"
    "yPSIjMUU0NThFIi8+PHN0b3Agb2Zmc2V0PSIuMjQxIiBzdG9wLWNvbG9yPSIjMUY0Rjk2Ii8+PHN0b3Agb2Zmc2V0PSIuNzI5IiBzdG9wL"
    "WNvbG9yPSIjMkI2QUFCIi8+PHN0b3Agb2Zmc2V0PSIxIiBzdG9wLWNvbG9yPSIjMzM3QkI5Ii8+PC9saW5lYXJHcmFkaWVudD48cGF0aCB"
    "kPSJNMzU4LjEgMzA2LjRoNTYuNVYwaC01Ni41bDE3LjYgMTUzLjJ6IiBzdHlsZT0iZmlsbDp1cmwoI1NWR0lEXzEzXykiLz48bGluZWFyR"
    "3JhZGllbnQgaWQ9IlNWR0lEXzE0XyIgeDE9IjU1NC45MiIgeDI9IjU1NC45MiIgeTE9Ii0xODUuODYiIHkyPSIxMjAuNTQiIGdyYWRpZW5"
    "0VHJhbnNmb3JtPSJtYXRyaXgoMSAwIDAgLTEgLTExOC45OCAxMjAuNTQpIiBncmFkaWVudFVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHN0b"
    "3Agb2Zmc2V0PSIwIiBzdG9wLWNvbG9yPSIjM0Y5QUM5Ii8+PHN0b3Agb2Zmc2V0PSIxIiBzdG9wLWNvbG9yPSIjMjA2MkEyIi8+PC9saW5"
    "lYXJHcmFkaWVudD48cGF0aCBkPSJNNDQ5LjkgMTYwLjhjNS41LTc1LjUgOC41LTEyMC42IDctMTYwLjhoLTQyLjJsLS4xIDMwNi40aDI4L"
    "jNjLTEtMzUuMSAzLjgtMTAyLjEgNy0xNDUuNiIgc3R5bGU9ImZpbGw6dXJsKCNTVkdJRF8xNF8pIi8+PC9nPjwvc3ZnPg=="
)


# ============================================================
# Official Bosch logo SVG (do NOT recreate — use this exact markup).
# Source: bosch-brand-style-guide skill — verbatim.
# ============================================================
BOSCH_LOGO_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 433 97" aria-hidden="true" focusable="false">
  <g fill="none">
    <g fill="#ed0007" fill-rule="evenodd">
      <path d="M185.2,46.88a13.77,13.77,0,0,0,8.8-13c0-11.7-8.3-17.5-19.7-17.5H144.4V80h32.5c10,0,19.8-7,19.8-17.7C196.7,49.58,185.2,47,185.2,46.88ZM160,29.58h11.6a5.66,5.66,0,0,1,6,5.31q0,.34,0,.69a5.93,5.93,0,0,1-6,5.81H159.9Zm11.7,37.1H160.1V54.18h11.3c5.7,0,8.4,2.5,8.4,6.2C179.8,65,176.4,66.68,171.7,66.68Z"></path>
      <path d="M231.1,14.78c-18.4,0-29.2,14.7-29.2,33.3s10.8,33.3,29.2,33.3,29.2-14.6,29.2-33.3S249.6,14.78,231.1,14.78Zm0,51.4c-9,0-13.5-8.1-13.5-18.1s4.5-18,13.5-18,13.6,8.1,13.6,18C244.7,58.18,240.1,66.18,231.1,66.18Z"></path>
      <path d="M294.2,41.38l-2.2-.5c-5.4-1.1-9.7-2.5-9.7-6.4,0-4.2,4.1-5.9,7.7-5.9a17.86,17.86,0,0,1,13,5.9l9.9-9.8c-4.5-5.1-11.8-10-23.2-10-13.4,0-23.6,7.5-23.6,20,0,11.4,8.2,17,18.2,19.1l2.2.5c8.3,1.7,11.4,3,11.4,7,0,3.8-3.4,6.3-8.6,6.3-6.2,0-11.8-2.7-16.1-8.2l-10.1,10c5.6,6.7,12.7,11.9,26.4,11.9,11.9,0,24.6-6.8,24.6-20.7C314.3,46.08,303.3,43.28,294.2,41.38Z"></path>
      <path d="M349.7,66.18c-7,0-14.3-5.8-14.3-18.5,0-11.3,6.8-17.6,13.9-17.6,5.6,0,8.9,2.6,11.5,7.1l12.8-8.5c-6.4-9.7-14-13.8-24.5-13.8-19.2,0-29.6,14.9-29.6,32.9,0,18.9,11.5,33.7,29.4,33.7,12.6,0,18.6-4.4,25.1-13.8L361.1,59C358.5,63.18,355.7,66.18,349.7,66.18Z"></path>
      <polygon points="416.3 16.38 416.3 39.78 397 39.78 397 16.38 380.3 16.38 380.3 79.98 397 79.98 397 54.88 416.3 54.88 416.3 79.98 433 79.98 433 16.38 416.3 16.38"></polygon>
    </g>
    <g fill="#000000">
      <path d="M48.2.18a48.2,48.2,0,1,0,48.2,48.2A48.2,48.2,0,0,0,48.2.18Zm0,91.9a43.7,43.7,0,1,1,43.7-43.7,43.71,43.71,0,0,1-43.7,43.7Z"></path>
      <path d="M68.1,18.28H64.8v16.5H31.7V18.28H28.3a36.06,36.06,0,0,0,0,60.2h3.4V62H64.8v16.5h3.3a36.05,36.05,0,0,0,0-60.2ZM27.1,72A31.59,31.59,0,0,1,24.47,27.4a32.51,32.51,0,0,1,2.63-2.62Zm37.7-14.6H31.7V39.28H64.8Zm4.5,14.5v-10h0V34.78h0v-10a31.65,31.65,0,0,1,2.39,44.71A33.68,33.68,0,0,1,69.3,71.88Z"></path>
    </g>
  </g>
</svg>"""


# ============================================================
# Global stylesheet — Bosch palette, 8px grid, typography,
# Streamlit-component overrides via `data-testid` selectors.
# ============================================================
BOSCH_CSS = f"""
<style>
:root {{
  --bosch-red: #e0000a;
  --bosch-purple: #54003c;
  --bosch-blue: #007bc0;
  --bosch-blue-dark: #005691;
  --bosch-blue-tint: #e6f3fb;
  --bosch-green: #6dbf24;
  --color-text: #000000;
  --color-text-muted: #525252;
  --color-background: #ffffff;
  --color-background-alt: #f2f2f2;
  --color-border: #cccccc;
  --font-primary: "Bosch Office Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --space-unit: 8px;
}}

html, body, [class*="st-"], .stMarkdown, .stTextInput, .stRadio, .stSelectbox,
button, input, textarea {{
  font-family: var(--font-primary) !important;
  color: var(--color-text);
}}

.stApp {{
  background-color: var(--color-background);
}}

/* Push everything down so the supergraphic ribbon has room at viewport top.
   Streamlit's main container has its own padding; we keep a comfortable
   gap below the ribbon. */
.stApp > header {{
  background-color: var(--color-background);
  border-bottom: 1px solid var(--color-border);
}}

/* ====== Top supergraphic ribbon ====== */
.bosch-supergraphic {{
  width: 100vw;
  position: fixed;
  top: 0;
  left: 0;
  height: 6px;
  background-image: url("{BOSCH_SUPERGRAPHIC_URI}");
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  z-index: 999999;
  pointer-events: none;
}}

/* Streamlit's own toolbar sits at top:0 by default; nudge it down by 6px
   so the supergraphic stays visible. */
[data-testid="stHeader"] {{
  top: 6px !important;
}}
.stApp {{
  padding-top: 6px;
}}

/* ====== Bosch header bar (logo + page title + signed-in) ====== */
.bosch-header-bar {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: calc(var(--space-unit) * 3);
  padding: calc(var(--space-unit) * 2) calc(var(--space-unit) * 3);
  background-color: var(--color-background);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: calc(var(--space-unit) * 3);
}}

.bosch-header-bar__brand {{
  display: flex;
  align-items: center;
  gap: calc(var(--space-unit) * 3);
  min-width: 0;
}}

.bosch-header-bar__logo {{
  display: flex;
  align-items: center;
  flex-shrink: 0;
  text-decoration: none;
}}

.bosch-header-bar__logo svg {{
  height: 24px;
  width: auto;
}}

.bosch-header-bar__title {{
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: 0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}

.bosch-header-bar__meta {{
  font-size: 13px;
  color: var(--color-text-muted);
  text-align: right;
  line-height: 1.4;
  flex-shrink: 0;
}}

.bosch-header-bar__meta strong {{
  color: var(--color-text);
  font-weight: 700;
}}

@media (max-width: 640px) {{
  .bosch-header-bar {{
    flex-direction: column;
    align-items: flex-start;
    gap: calc(var(--space-unit) * 1);
  }}
  .bosch-header-bar__meta {{
    text-align: left;
  }}
}}

/* ====== Chat bubbles ====== */
.bosch-bubble {{
  padding: calc(var(--space-unit) * 1.5) calc(var(--space-unit) * 2);
  border-radius: 4px;
  max-width: 75%;
  word-wrap: break-word;
  line-height: 1.55;
  font-size: 15px;
  color: var(--color-text);
}}

.bosch-row--user {{
  display: flex;
  justify-content: flex-end;
  margin: calc(var(--space-unit) * 1) 0;
}}

.bosch-row--assistant {{
  display: flex;
  justify-content: flex-start;
  margin: calc(var(--space-unit) * 1) 0;
}}

.bosch-bubble--user {{
  background: var(--bosch-blue-tint);
  border: 1px solid #c8e3f3;
}}

.bosch-bubble--assistant {{
  background: var(--color-background-alt);
  border-left: 3px solid var(--bosch-blue);
}}

/* ====== Unauthorized card (Bosch Red — the one critical-signal usage) ====== */
.bosch-unauthorized {{
  display: flex;
  gap: calc(var(--space-unit) * 2);
  padding: calc(var(--space-unit) * 3);
  background: var(--color-background-alt);
  border-left: 4px solid var(--bosch-red);
  margin-top: calc(var(--space-unit) * 4);
}}
.bosch-unauthorized__icon {{
  font-size: 24px;
  line-height: 1;
}}
.bosch-unauthorized__body h3 {{
  margin: 0 0 calc(var(--space-unit) * 1) 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text);
}}
.bosch-unauthorized__body p {{
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text);
}}

/* ====== Sidebar ====== */
[data-testid="stSidebar"] {{
  background-color: var(--color-background-alt);
  border-right: 1px solid var(--color-border);
}}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
  font-weight: 700;
  color: var(--color-text);
}}

/* Sidebar primary action button → Bosch blue solid */
[data-testid="stSidebar"] .stButton > button {{
  background-color: var(--bosch-blue);
  color: var(--color-background) !important;
  border: none;
  border-radius: 2px;
  padding: calc(var(--space-unit) * 1.5) calc(var(--space-unit) * 3);
  font-weight: 700;
  transition: background-color 0.12s ease-in-out;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
  background-color: var(--bosch-blue-dark);
  color: var(--color-background) !important;
}}
[data-testid="stSidebar"] .stButton > button:focus {{
  outline: 2px solid var(--bosch-blue);
  outline-offset: 2px;
}}

/* Radio + selectbox: keep neutral, use Bosch blue for selected state */
[data-testid="stSidebar"] input[type="radio"]:checked + div,
[data-testid="stSidebar"] [role="radio"][aria-checked="true"] {{
  color: var(--bosch-blue);
}}

/* ====== References expander ====== */
[data-testid="stExpander"] {{
  border: 1px solid var(--color-border);
  border-radius: 2px;
  background: var(--color-background);
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] + div {{
  font-weight: 700;
  color: var(--bosch-blue);
}}

/* ====== Chat input (bottom) ====== */
[data-testid="stChatInput"] textarea {{
  border: 1px solid var(--color-border) !important;
  border-radius: 2px !important;
  background: var(--color-background) !important;
}}
[data-testid="stChatInput"] textarea:focus {{
  outline: 2px solid var(--bosch-blue) !important;
  border-color: transparent !important;
}}

/* ====== Hide Streamlit's "Made with Streamlit" footer for a cleaner brand look ====== */
footer {{
  visibility: hidden;
}}

/* ====== Tool-running status label (used by the streaming loop) ====== */
.bosch-tool-status {{
  color: var(--bosch-blue);
  font-weight: 700;
  font-size: 14px;
  padding: calc(var(--space-unit) * 1) 0;
}}
</style>
"""


# ============================================================
# Public helpers — call these from app.py
# ============================================================
def _safe_md(content: str) -> str:
    """Escape `$` so Streamlit's KaTeX parser doesn't mangle currency.

    Kept identical in spirit to the original `_safe_md` in app.py so the
    rendering behaviour for prices like "$300 fine" doesn't regress.
    """
    if not content:
        return content
    return content.replace("$", r"\$")


def inject_bosch_style() -> None:
    """Inject the Bosch global stylesheet + the supergraphic element.

    Must be called **after** `st.set_page_config(...)` and **before** any
    visual rendering. Safe to call once per Streamlit run (idempotent in
    practice — duplicate `<style>` blocks are harmless).
    """
    st.markdown(BOSCH_CSS, unsafe_allow_html=True)
    st.markdown('<div class="bosch-supergraphic"></div>', unsafe_allow_html=True)


def render_bosch_header(title: str, meta_html: str) -> None:
    """Render the white header bar with Bosch logo + page title + meta.

    Args:
        title: page title shown next to the logo (e.g. "Chatbot Demo").
        meta_html: pre-built right-side HTML snippet (e.g. environment
            + signed-in user). Pass `""` to hide it.
    """
    meta_block = (
        f'<div class="bosch-header-bar__meta">{meta_html}</div>' if meta_html else ""
    )
    st.markdown(
        f"""
<header class="bosch-header-bar">
  <div class="bosch-header-bar__brand">
    <a class="bosch-header-bar__logo" href="#" aria-label="Bosch home">
      {BOSCH_LOGO_SVG}
    </a>
    <div class="bosch-header-bar__title">{title}</div>
  </div>
  {meta_block}
</header>
""",
        unsafe_allow_html=True,
    )


def render_unauthorized_card() -> None:
    """Bosch-red 🔒 Unauthorized card used by the JWT auth gate."""
    st.markdown(
        """
<div class="bosch-unauthorized" role="alert">
  <div class="bosch-unauthorized__icon">🔒</div>
  <div class="bosch-unauthorized__body">
    <h3>Unauthorized</h3>
    <p>No valid SSO token was provided. This page must be accessed through the
    company SSO entry point (the Approuter URL). Please open it from there and
    sign in.</p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_user_bubble(content: str) -> None:
    """User chat message — Bosch-blue tint on the right."""
    st.markdown(
        f"""
<div class="bosch-row--user">
  <div class="bosch-bubble bosch-bubble--user">{_safe_md(content)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_assistant_bubble(content: str, placeholder=None) -> None:
    """Assistant chat message — neutral grey with Bosch-blue left accent.

    Args:
        content: the message body (HTML-safe markdown).
        placeholder: optional `st.empty()` placeholder. If given, the HTML
            is written into it (so it can be live-updated during streaming).
            Otherwise renders a static block.
    """
    html = f"""
<div class="bosch-row--assistant">
  <div class="bosch-bubble bosch-bubble--assistant">{_safe_md(content)}</div>
</div>
"""
    if placeholder is not None:
        placeholder.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)


def render_sources(sources: list[dict]) -> None:
    """Render the `📚 References (N)` expander under an assistant message.

    Mirrors the original behaviour from app.py: shows file name, source
    path, start_index, and a code-block preview of the snippet.
    """
    if not sources:
        return
    with st.expander(f"📚 References ({len(sources)})", expanded=False):
        for i, src in enumerate(sources, start=1):
            meta = src.get("metadata") or {}
            file_name = meta.get("file_name") or meta.get("source") or "unknown"
            source_path = meta.get("source", "")
            start_index = meta.get("start_index", "?")
            preview = src.get("page_content", "")
            st.markdown(
                f"**[{i}] {file_name}**  \n"
                f"<span style='color:#525252;font-size:0.85em;'>"
                f"source: {source_path} · start_index: {start_index}</span>",
                unsafe_allow_html=True,
            )
            st.code(
                preview[:1000] + ("…" if len(preview) > 1000 else ""),
                language="markdown",
            )


def render_tool_status(label: str, placeholder) -> None:
    """Render the small tool-running status label above the assistant bubble.

    Used by the streaming loop in app.py. `placeholder` must be an
    `st.empty()` slot so the label can be cleared once streaming starts.
    """
    placeholder.markdown(
        f'<div class="bosch-tool-status">{label}</div>',
        unsafe_allow_html=True,
    )
