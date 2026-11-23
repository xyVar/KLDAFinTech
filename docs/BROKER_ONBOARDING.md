# BROKER ONBOARDING — canonical steps for the KLDA company account

> Stage S5 of `docs/ROADMAP.md`. Written 2026-11-16 from the owner's situation as described in
> session; **not legal, tax or regulatory advice** — section 6 lists what must be confirmed by a
> professional. Update this file whenever a step is done or a fact changes.

## 1. Decision: why a new broker, and which

- **Pepperstone is dropped for new capital.** Live account 52028179 was trade-disabled without
  explanation (retcode 10017), demo accounts expire, and onboarding from Albania is reportedly closed.
  The Pepperstone tick archive stays as research data only.
- **Target: Interactive Brokers (IBKR), institutional / corporate account**, under the EU entity
  (IBKR Ireland). Reasons: listed, well-capitalised, segregated client money, written restriction
  rules, real futures instead of CFDs, near-zero FX conversion cost, free paper account with live data.
- **Consequence for the software:** IBKR has no MetaTrader. The MT5 bridge and the MT5 executor
  must be rewritten against the IBKR API (branch `lane-c/ibkr`). Database, signal logic, risk layer
  and the terminal stay.
- **Instruments (proposed):** micro futures — crude, natural gas, Nasdaq, DAX — rather than CFDs.
  **Account currency (proposed): USD.** Both to be confirmed by the owner.

## 2. Who is applying, in which role

The account belongs to **KLDA Technologies OÜ** (Estonia). The owner appears three times:

| Role | Meaning | Declared with |
|---|---|---|
| Applicant / authorised person | the human filling in the form and trading | own name, **personal residential address (where the person actually lives)**, passport, personal tax residence and tax number |
| Director | legal representative of the OÜ | Estonian e-Business Register extract |
| Beneficial owner | owns 25% or more | ownership percentage |

**Terminology that matters on the form**
- *E-Residency* (Estonia) is a digital identity for running a company remotely. It is **not** tax
  residence and **not** physical residence. "Country of residence" on IBKR's personal pages means
  where the person lives; declare that country, not Estonia, unless the person physically lives there.
- IP address: brokers always see it. Declarations must match it and the address documents.
  **Never use a VPN to appear elsewhere** — a mismatch between IP, declared residence and documents
  is a common reason applications stall.
- Purpose of account: *"trading the company's own capital, systematically, via API"*. Do **not**
  describe it as a fund, asset management, or trading for others. If outside money ever enters, that
  is a different account type and a lawyer's question first (see section 6).

## 3. Documents to prepare (PDF, dated ones < 3 months old)

1. Company registry extract (e-Business Register, signed with the e-Residency card)
2. Articles of association
3. Directors and beneficial owners (usually covered by 1)
4. Owner's valid passport
5. **Proof of the owner's personal address** — utility bill or bank statement, same address as declared
6. Proof of the company's registered address
7. **Source of funds**: short written statement (company revenue / owner's capital contribution) plus
   a bank statement that shows it
8. Company tax number (Estonia) and the owner's personal tax identification number in the tax-residence country
9. **The company bank account** the deposit will come from — must be in the company's name;
   corporate accounts cannot be funded from a personal account

Items 5 and 7 are the usual blockers.

## 4. The procedure

1. **Before starting**, ask IBKR support chat two questions and save the answers in
   `docs/evidence/s5/ibkr_prequalification.md`:
   - "Does IBKR Ireland currently onboard an Estonian OÜ whose director is resident in <country>?"
   - "Which account type and which entity for an EU company trading its own capital via the API?"
2. Open the application as **Institutional → Corporation**, filed by the director in their own name.
3. Fill the company pages from documents 1–3 and 6; the personal pages from 4, 5 and 8.
   Every name, address and date must match the documents character for character.
4. Upload all documents in one sitting. An unfinished application is closed after some weeks —
   this is one likely cause of the two earlier drops.
5. Answer the trading-experience and financial-information questions honestly; they decide which
   products (futures, options) are enabled.
6. Request **futures trading permissions** for the exchanges needed (CME for crude, gas, Nasdaq
   micro; Eurex for DAX micro) and **API access**.
7. After approval: enable the **paper trading account** (free, live data once funded) — that is the
   demo for stage S3.
8. Fund by wire from the company bank account (document 9). First a small amount to prove the
   path; record the transfer in `docs/capital/<YYYY-MM>.md`.

## 5. Costs to expect (as understood on 2026-11-16; verify on IBKR's pricing page)

| Item | Typical cost |
|---|---|
| Incoming wire | IBKR: none; own bank: its wire fee |
| EUR→USD conversion | ~0.002% (≈ $2 per $100,000) |
| Withdrawal | one free per month, then a small fee |
| Idle cash | interest paid above a threshold |
| Micro futures round trip | under $1–2 per contract incl. exchange fees |
| Market data | some exchanges charge a monthly fee; waived or reduced at activity thresholds |

## 6. Must be confirmed by a professional before funding (not answered here)

- **Accountant (tax residence country):** does trading the company's own capital from there create
  a permanent-establishment, tax or reporting duty for the OÜ or the owner?
- **Accountant (Estonia):** booking of trading results, fees and currency differences; any
  registration the OÜ needs for own-capital trading (normally none, confirm).
- **Lawyer:** what changes if any third-party money is ever accepted; whether the words
  "investor / fund / NAV" in the software's schema should be renamed to avoid implying a regulated
  activity.
- **IBKR support:** current onboarding policy for the owner's country of residence; which IBKR
  entity holds the account; demo/paper account rules.

## 7. The two earlier IBKR applications (facts, owner-provided 2026-11-19)

- Both were **individual (personal) applications from Albania**, not corporate ones.
- Both were closed with IBKR's standard discretionary-decline notice ("sole discretion, but not the
  obligation" to give a reason). No document was flagged; no reason was given.
- So there is nothing specific to "fix" from them. IBKR's own list of accepted countries
  (interactivebrokers.com/en/accounts/open-account-country-list.php, read 2026-11-23) includes both
  Albania and Estonia with no footnote, so it was **not a country ban**: those were case-by-case
  discretionary decisions, and IBKR never gives the reason.
- The corporate application is a different review, under the EU entity, years later. It does not
  inherit the decline. It does mean the pre-qualification question (section 4, step 1) comes first.

## 8. What the software needs once the account exists

- `config/accounts.json`: the IBKR account id(s) marked paper / live; the executor refuses any other
- `lane-c/ibkr`: IBKR data feed → `ticks` table; IBKR executor behind the same order router and
  risk layer; symbol mapping (micro futures) in `config/trading_config.json`
- sizing rule: 1% of allocated capital per trade, from contract specifications, replacing the
  fixed 0.01-lot placeholder
- Pepperstone live account: logged out and marked "never trade" in `config/accounts.json`

## 9. IBKR is the chosen institution — lowering the risk of an unexplained decline

Owner decision 2026-11-21: **IBKR corporate account is the target.** Retail CFD/MT5 brokers are
rejected (the broker is the counterparty to every trade). Prime brokers are out of reach at this
capital size.

Before applying
1. Pre-qualify by chat or phone. A "no" there costs nothing and leaves no new declined application.
2. Disclose any earlier declined applications. IBKR will match the same person anyway;
   volunteering it reads as transparency.
3. Fix what KLDA controls: an EMTAK code for the activity (e.g. 64.99) next to the existing one;
   purpose stated plainly; source of wealth = service invoices → retained earnings; funding account
   in the company's name.
4. Submit everything in one sitting, every name, address and date matching the documents.
5. Optional: a GDPR Article 15 access request for the data IBKR holds on earlier applications
   (applies to IBKR's EU/UK entities). Anti-money-laundering notes may lawfully be withheld.

Pre-qualification message: template held outside the repo (personal details). It asks:
(1) whether IBKR accepts a corporate application for an Estonian OÜ given the director's country of
residence; (2) which account type suits a company trading its own capital in micro futures via the
API; (3) whether a Wise Business account in the company's name can fund it; (4) whether earlier
declined applications would prevent this one. Save the reply outside the repo; record only
the outcome here.

If IBKR still declines
- Plan B at the same tier: Saxo Bank (licensed Danish bank, exchange access), or an introducing
  broker whose trades clear at a futures clearing firm (StoneX, Marex, ADM Investor Services).
- A decline does not stop stages S0–S2 (data, research, paper trading). Applying early means a
  "no" is found while there is still time.
- The software stays broker-agnostic: each institution is one adapter behind the same order router
  and safety gates.

## 10. What IBKR's own pages say (fetched 2026-11-21)

Sources: interactivebrokers.com/en/accounts/configuring-your-account.php,
/en/accounts/account-guide.php, /en/accounts/required-minimums.php,
/en/accounts/trading-and-market-data.php, /en/accounts/legalDocuments/custIdentificationNotice.php.
These are IBKR's global (US-site) pages; IBKR states that account types, margin and products
"vary by country of residence and IBKR legal entity", so the EU entity's form may differ in detail.

**Account type for KLDA:** "Small Businesses — for corporations, LLCs, partnerships and operating
businesses" (account guide: "a single account which holds assets owned by the entity account
holder"; Cash, Reg T and Portfolio Margin available). The "Proprietary Trading Firms" type is for
multi-trader firms; with one trader, Small Business / Organization fits. Confirm in pre-qualification.

**Documents IBKR lists for institutional accounts:**
- formation documents (articles of association)
- tax identification number
- a completed **beneficial ownership certification** (a form filled in during the application)
- ID information for every **authorized user** (each person who will log in or trade)
- a **corporate resolution** authorising the account and the authorised users — not on our list
  before; for an OÜ this is a written decision of the board / sole shareholder

**What the application assesses:** entity type, regulatory status, financial profile, trading
experience, jurisdiction. The individual form asks income, net worth, liquid net worth, years of
experience per asset class, bank details and an **intended deposit amount** (an estimate, not a
commitment); expect equivalent questions for the company.

**Futures:** "Futures trading requires specific approval. Approval is based on trading experience,
financial profile, and regulatory requirements." No numeric threshold is published. Under EU rules
(MiFID II) a non-advised client trading complex products such as futures is also given an
appropriateness check of knowledge and experience — answer it truthfully.

**Margin and shorting:** a Cash account cannot borrow or short. A Margin account allows both;
minimum equity **USD 2,000** to open margin. Portfolio Margin requires **USD 110,000**. "Futures
margin is performance collateral, not a loan." Positions may be reduced or liquidated if
maintenance margin is not met.

**Costs on the IBKR Pro, Org account line:** account minimum USD 0.00, inactivity fee USD 0.00.
TWS API and REST API over the internet: USD 0.00 monthly minimum. FIX connections: USD 1,500/month
minimum — not needed. Real-time data requires paid exchange subscriptions; institutional accounts
may be charged professional data fees — ask the price for CME and Eurex data in pre-qualification.

**Identity rule (Customer Identification Program):** IBKR must obtain, verify and record identity
for the entity and "persons related to your organization", may request documents such as articles
of incorporation, and "may not be able to open your account" without them.
