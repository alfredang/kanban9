# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An IT project management Kanban board for a fictitious bank's IT PMO, used for demos and training. All of the app is in `index.html`: markup, CSS and JS, with no other source files.

## Commands

There is no build step, package manifest, linter or test suite.

- **Run the board:** open `index.html` directly (double-click). It must keep working this way.
- **Test email sending:** serve the folder over http(s), for example `python -m http.server`, then open `http://localhost:8000`. FormSubmit rejects pages opened from `file://`, so a local-file page always ends in the warning toast.
- **Check a change:** drive the page in a real browser. Stub `fetch` to cover the email outcomes: success, a 500, `success: "false"` in a 200 response, and a network failure.

## Constraints from the project brief

- Vanilla HTML, CSS and JS only: no frameworks, build tools or external resources (fonts, CDNs, images). Use system fonts and Unicode or inline SVG icons.
- No storage of any kind: no `localStorage`, `sessionStorage`, `indexedDB` or cookies. A refresh resets the board, and the page says so.
- FormSubmit is the only backend. The destination email address may go nowhere except `FORMSUBMIT_ENDPOINT`.
- The branding is a neutral "IT PMO" text wordmark on a corporate blue palette. Do not use UOB's logo or trademarks, or imitate an official UOB system. "UOB" appears only in `TASK_ID_PREFIX` and `EMAIL_SUBJECT_TAG`, because the brief specifies those formats.
- No `alert()`, `confirm()` or `!important`. Validation errors and the delete confirmation are inline.

## Architecture

**State and rendering.** `state` is the single source of truth, including transient UI modes in `state.ui` such as the open Move panel and the pending delete confirmation. To change the UI, update `state` and call `renderBoard()`, which rebuilds the whole board with `innerHTML`. This has three consequences:

- Any user-supplied string placed in a template must go through `escapeHtml()`.
- Board events use delegated listeners on `#board`, dispatched by `data-action`. Don't bind listeners to individual cards, because they are lost on the next render.
- A re-render destroys the focused element, so keyboard actions must restore focus afterwards with `focusInCard()` or `focusColumnHeading()`.

**Filters.** `applyFilters()` only affects which cards are visible. The summary strip always counts all tasks, and column badges show "x of y" while filtering.

**Moving cards.** Drag and drop and the Move ▸ control both go through `moveTask()`. Move ▸ is also the only way to move cards by keyboard or on touch devices, so it can't be removed in favour of drag and drop.

**Add Task and email.** Adding a task is optimistic: `handleFormSubmit()` adds the card first, then awaits `notifyNewTask()`. An email failure must never change the board; it only shows a warning toast. `notifyNewTask()` deliberately:

- skips the network call while the endpoint still contains the placeholder address
- treats `success: false` or `"false"` in the JSON body as a failure, because FormSubmit can report errors in a 200 response
- aborts after `FORMSUBMIT_TIMEOUT_MS`, so "Sending…" can't get stuck

**Toasts and the dialog.** The Add Task form is a native modal `<dialog>`, which makes the rest of the page inert. That is why there are two toast regions: `showToast()` uses the one inside the dialog while it is open.

**Dates and IDs.** Due dates are local-time `YYYY-MM-DD` strings compared as strings, so use `todayIso()` rather than UTC-based `toISOString()` dates. Seed dates are relative to today, so Overdue badges always appear. `nextTaskId()` increments a counter and never reuses IDs after a delete.

## Configuration

The settings are constants at the top of the script: `FORMSUBMIT_ENDPOINT` (replace `YOUR_EMAIL@example.com`), `TASK_ID_PREFIX` and `EMAIL_SUBJECT_TAG`. FormSubmit also needs one-time activation: the first submission sends a confirmation email to that address, and nothing is delivered until its link is clicked.
