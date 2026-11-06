# Security

This covers v2, at `v2/index.html`. v1 is kept unchanged as a historical version and has none of the page-level controls below.

## What is being protected

The site is a public demo with sample data and no login, server or stored data. The realistic risks are:

- script injection through text typed into a task
- abuse of the FormSubmit mailbox
- exposure of the destination email address
- tampering with what gets deployed

## Threats and controls

| Threat (STRIDE) | Control | Where |
| --- | --- | --- |
| Script injection (tampering, elevation) | User text is escaped. A Content Security Policy allows only the page's own hashed script and style, with no `eval`. Trusted Types make `setHtml()` the only way to insert HTML. | `v2/index.html` |
| Data sent to another site (information disclosure) | `default-src 'none'`, and `connect-src` allows only `https://formsubmit.co`. `form-action 'none'` and `base-uri 'none'` close the other routes. | Policy meta tag |
| Clickjacking (spoofing) | The page refuses to run inside a frame. | `isFramed()` |
| Forged or malformed input (tampering) | Control and text-direction characters are removed, lengths are capped, list values are checked against the allowed lists, and dates must be real. | `readFormValues()`, `validateTask()` |
| Email header injection (tampering) | Line breaks are removed from the title and assignee before they reach the subject. | `cleanLine()` |
| Mailbox flooding (denial of service) | This page sends at most 5 emails a minute. Only the board keeps working beyond that. | `takeNotifySlot()` |
| Credential or URL leakage (information disclosure) | Requests omit credentials and refuse redirects. The referrer is limited to the origin. | `notifyNewTask()` |
| Compromised CI action (tampering) | Actions are pinned to commit SHAs, with read-only default permissions and no persisted checkout credentials. | `pages.yml` |
| Accidental publication (information disclosure) | Only the two pages are deployed, and Gitleaks scans for secrets. | `pages.yml` |
| Hidden code in a change (tampering) | CI rejects stale policy hashes, raw invisible characters, external URLs, inline handlers and new HTML sinks. | `check_site.py` |

## Known limits

- **GitHub Pages can't set response headers.** The policy is a meta tag, which can't include `frame-ancestors` or reporting, and `X-Frame-Options` and `X-Content-Type-Options` can't be added. The frame check is a JavaScript fallback, so it needs a host with header control to be replaced properly.
- **Browser checks can be bypassed.** Validation and the email limit run in the browser, so anyone can post directly to the FormSubmit endpoint. Only FormSubmit can enforce limits there.
- **FormSubmit is a third party.** It receives everything in a new-task email, and `_captcha` is off because the page sends by AJAX. Use sample data only.
- **The source is public.** A real address in `FORMSUBMIT_ENDPOINT` is visible to everyone. After activation, use the random alias FormSubmit issues instead.
- **Trusted Types depend on the browser.** Where they aren't supported, the page relies on `escapeHtml()` and the rest of the policy.
- **v1 shares v2's origin.** v1 has no Content Security Policy. Neither page stores data, so there is nothing for one to read from the other.

## Changing v2

The policy allows the inline blocks by hash, so any edit to the page's style or script block stops it loading until the hashes are updated:

```
python .github/scripts/check_site.py --write
```

## Reporting a problem

Report a vulnerability through this repository's [security advisories](https://github.com/alfredang/kanban9/security/advisories/new). If that form isn't enabled, open an issue that leaves out the details and asks for a private contact.
