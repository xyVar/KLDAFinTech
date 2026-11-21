# ONBOARDING CHECKLIST — document status (no personal data in this file)

> Companion to `docs/BROKER_ONBOARDING.md`. Tick the boxes and note the folder; **never paste the
> documents, numbers or addresses here or anywhere in the repo.** Keep the files on the PC in
> `C:\Users\PC\Desktop\onboarding_docs\` (outside the repo; also git-ignored) and in one encrypted
> off-machine copy.

Declared facts (from the owner, 2026-11-16):
- Applicant / director / beneficial owner: the owner, **resident in Albania** (Tirana).
- Company: KLDA Technologies OÜ, Estonia. Owner holds Estonian e-Residency (digital identity only;
  residence and tax residence stay Albania).
- Account: IBKR institutional → Corporation, EU entity.

| # | Document | Status | Where kept | Notes |
|---|---|---|---|---|
| 1 | Company registry extract (*registrikaart*) — from `ariregister.rik.ee`, log in with the e-Residency card | ☐ | | < 3 months old; also serves as 3 and 6 |
| 2 | Articles of association (*põhikiri*) — same site, same download | ☐ | | |
| 3 | Directors + beneficial owners | ☐ | | covered by 1 |
| 4 | Owner's passport | ☑ have | | check expiry covers the next 6 months |
| 5 | Owner's personal proof of address | ☑ ready | | Albanian bank statement, Oct 2026, Tirana address — the address in the application must match it character for character; keep the original language |
| 6 | Company registered-address proof | ☐ | | the address on the registry extract (service-provider address is normal); no separate document |
| 7 | Source of **wealth** of the company (IBKR asks where the company's money comes from in general, not for a deposit amount) | ☐ | | answer: revenue from KLDA Technologies' services; evidence: a recent Wise Business statement showing normal activity. **No funding amount is committed at application time**; funding comes later, in slices, after the strategy passes its tests |
| 8 | Company tax number (EE) + owner's personal tax ID (AL) | ☑ have | | |
| 9 | **Wise Business** account in the company's name (KLDA Technologies OÜ IBAN) | ☑ exists | | confirm it is the business account, not personal Wise: IBKR matches the sender name to the account holder and returns mismatched wires |
| 10 | IBKR pre-qualification answers (support chat) | ☐ | `docs/evidence/s5/` | one message: (1) does IBKR Ireland accept an Estonian OÜ whose director/owner is resident in Albania; (2) which account type for a company trading its own capital via the API; (3) can it be funded from a Wise Business account in the company's name |
| 11 | The two earlier IBKR applications | ☑ known | | individual applications from Albania; both closed with IBKR's standard no-reason decline. Details in BROKER_ONBOARDING §7 |
| 12 | Corporate resolution (written decision of the board / sole shareholder) authorising the IBKR account and naming the authorised user(s) | ☐ | | required by IBKR for institutional accounts; draft with the Estonian accountant or Xolo |
| 13 | Beneficial ownership certification | ☐ | | a form inside the IBKR application; same facts as the registry extract |
| 14 | Financial profile of the company (revenue, net worth, liquid assets) and trading experience (years, asset classes) | ☐ | | answer truthfully; also feeds the futures approval and the MiFID appropriateness check |

Rules
- Documents live in the `onboarding_docs` folder on the PC, never in chat, never in git.
- Dates: anything dated must be < 3 months old on the day of upload; upload everything in one sitting.
- Any change of address or company data → redo the affected document before applying.

Capital plan (owner, 2026-11-16) — for `config/trading_config.json`, not for the application
- Account currency USD; instruments micro futures (MCL crude, MNQ Nasdaq, FDXS DAX; MNG gas later).
- Capital enters in slices from company earnings, treasury-style; target ~50k allocated in year 1.
- "Leverage 5" ⇒ ~250k notional. At IBKR leverage is inside the futures contract (exchange margin,
  roughly 5–20% of notional); 50k cash supports ~250k notional at ~20% margin use. Rule to encode:
  **max margin use 20% of allocated capital**; unused cash may sit in T-bills / money-market inside
  the account (the investment-grade slice).
- Risk stays **1% of allocated capital per trade**, max 3 open ⇒ 1.5% at the stops. Leverage sets
  contract size, never risk.
