# Fictional source data

These small, hand-authored fixtures are for development and portfolio demonstrations.
All people, branches, payees and identifiers are fictional; there are no real account
numbers or contact details. Raw files intentionally contain invalid records.

## File conventions

- CSV files use UTF-8, comma delimiters and one header row. JSON is an array of objects.
- IDs are strings. Empty CSV fields and JSON `null` represent missing values.
- Money is in ZAR. Valid money values have two decimal places; parse with decimal
  arithmetic in later implementation. JSON amounts are strings to preserve source precision.
- Dates represent calendar dates without time zones. Accepted source formats will be
  `YYYY-MM-DD`, `DD/MM/YYYY` and `YYYY/MM/DD`, normalised to `YYYY-MM-DD`.
- Trim surrounding whitespace and normalise known category/province variants before
  checking allowed values. Do not silently correct impossible dates or unknown IDs.
- Balances are illustrative snapshots, not opening balances. These partial transaction
  histories cannot be reconciled to the account balances.
- Transaction amounts must be positive; type describes the activity. Transfers are
  single activity records without a destination account, not double-entry ledger entries.
- Payments are a separate source, with no promised correspondence to transactions.
  Do not combine their amounts into transaction totals. Database mapping is still pending.

## Fields and proposed fixture rules

All fields below are required. These rules define the sample data's intended meaning;
pipeline enforcement belongs to later roadmap steps.

| File | Fields | Meaning and rules |
| --- | --- | --- |
| branches.csv | branch_id, branch_name, city, province | Unique branch ID; nonblank name and city; South African province |
| customers.csv | customer_id, first_name, last_name, province, join_date | Unique customer ID; nonblank names; province; valid join date |
| accounts.csv | account_id, customer_id, branch_id, account_type, balance, opened_date | Unique account ID; references accepted customer and branch; savings/current type; decimal balance; valid opening date on or after customer join date |
| transactions.csv | transaction_id, account_id, branch_id, transaction_type, amount, transaction_date | Unique transaction ID; references accepted account and branch; deposit/withdrawal/transfer/card_payment type; positive decimal amount; valid date on or after account opening |
| payments.json | payment_id, account_id, payee, amount, payment_date, status | Unique payment ID; references accepted account; nonblank fictional payee; positive decimal amount; valid date on or after account opening; completed/pending/failed status |

Province names use the nine South African provinces. `KZN` maps to `KwaZulu-Natal`;
province casing and whitespace can be normalised. `CARD PAYMENT` maps to
`card_payment`; account types, transaction types and payment statuses are case-insensitive.
For these fixtures, retain the first occurrence of an exact duplicate and reject
subsequent occurrences. Conflicting records with the same ID will need a separate policy.

## Intentional quality cases

Record positions below are one-based, excluding CSV headers.

| File | Raw rows | Cases |
| --- | ---: | --- |
| branches.csv | 5 | All valid |
| customers.csv | 14 | Positions 6-8 need normalisation; 11 duplicates C002; 12 has no ID; 13 has no first name; 14 has an impossible date |
| accounts.csv | 16 | Positions 6-7 need normalisation; 11 duplicates A003; 12 references C999; 13 references B999; 14 has a nonnumeric balance; 15 has no ID; 16 has unsupported investment type |
| transactions.csv | 22 | Positions 6-7 need normalisation; 13 duplicates T003; 14 references A999; 15 references B999; 16 has a negative amount; 17 has zero amount; 18 has a nonnumeric amount; 19 has an impossible date; 20 has no ID; 21 has unsupported refund type; 22 has no account ID |
| payments.json | 11 | Positions 4-5 need normalisation; 6 duplicates P002; 7 references A999; 8 has a null ID; 9 has a nonnumeric amount; 10 has an impossible date; 11 has unknown status |

Under these proposed rules, expected accepted/rejected counts are: branches 5/0,
customers 10/4, accounts 10/6, transactions 12/10, and payments 5/6.
That is 68 source records: 42 accepted after normalisation and 26 rejected.
The large T011 deposit is valid; any later anomaly flag must not automatically reject it.
