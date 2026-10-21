# Fictional source data

These small, hand-authored fixtures are for development and portfolio demonstrations.
All people, branches, payees and identifiers are fictional; there are no real account
numbers or contact details. Raw files intentionally contain invalid records.

For command usage, configuration, output behavior and troubleshooting, see the
[operations guide](operations.md).

## File conventions

- CSV files use UTF-8, comma delimiters and one header row. JSON is an array of objects.
- IDs are strings. Empty CSV fields and JSON `null` represent missing values.
- Money is in ZAR. CSV fields are read as text so IDs keep leading zeroes and
  decimal values keep their original precision. Amounts and balances are parsed
  with decimal arithmetic; values with more than two decimal places or outside
  PostgreSQL `NUMERIC(12, 2)` range are rejected. JSON amounts are strings to
  preserve source precision.
- Dates represent calendar dates without time zones. Accepted source formats are
  `YYYY-MM-DD`, `DD/MM/YYYY` and `YYYY/MM/DD`, normalised to `YYYY-MM-DD`.
- The pipeline trims surrounding whitespace and accepts known category and
  province variants. It rejects impossible dates, unknown IDs, and unsupported
  categories rather than silently correcting them.
- Balances are illustrative snapshots, not opening balances. These partial transaction
  histories cannot be reconciled to the account balances.
- Transaction amounts must be positive; type describes the activity. Transfers are
  single activity records without a destination account, not double-entry ledger entries.
- Payments are a separate source, with no promised correspondence to transactions.
  Do not combine their amounts into transaction totals. Payments load into their
  own PostgreSQL table.

## Fields and enforced validation rules

All fields below are required and must be nonblank. Invalid rows are retained in
the rejected output with one or more reason codes in the rejection_reasons field.
Validation keeps source values unchanged; accepted rows are trimmed and
standardised in a separate transformation step.
If a required column is missing from an input file, validation stops with a
schema error instead of rejecting individual rows.

| File | Fields | Meaning and enforced rules |
| --- | --- | --- |
| branches.csv | branch_id, branch_name, city, province | Required values; province must be one of the nine South African provinces; exact duplicate rows are rejected |
| customers.csv | customer_id, first_name, last_name, province, join_date | Required values; valid province and date; exact duplicate rows are rejected |
| accounts.csv | account_id, customer_id, branch_id, account_type, balance, opened_date | Required values; references an accepted customer and branch; savings/current type; finite balance with at most two decimal places and absolute value no greater than 9,999,999,999.99; valid opening date on or after the customer's join date; exact duplicate rows are rejected |
| transactions.csv | transaction_id, account_id, branch_id, transaction_type, amount, transaction_date | Required values; references an accepted account and branch; deposit/withdrawal/transfer/card_payment type; positive finite amount no greater than 9,999,999,999.99 with at most two decimal places; valid date on or after account opening; exact duplicate rows are rejected |
| payments.json | payment_id, account_id, payee, amount, payment_date, status | Required values; references an accepted account; positive finite amount no greater than 9,999,999,999.99 with at most two decimal places; valid date on or after account opening; completed/pending/failed status; exact duplicate rows are rejected |

Exact duplicates are compared across every field in the dataset, and the first
occurrence is accepted while subsequent copies are rejected. If a nonblank ID
appears on different records, every record with that ID is rejected with a
`conflicting_<dataset>_id` reason. This prevents the database loader's primary-key
upsert from silently choosing one version.

Province names use the nine South African provinces. `KZN` maps to
`KwaZulu-Natal`; province casing and repeated/outer whitespace are normalised.
`CARD PAYMENT` maps to `card_payment`; account types, transaction types and
payment statuses are case-insensitive. Dates in the accepted source formats are
written as `YYYY-MM-DD`. Monetary values are standardised to decimal values, and
text fields are trimmed.

## Rejection reason codes

Each rejected row can have multiple reason codes. Missing-value codes use the
`missing_<field>` form, where `<field>` is the name of the missing column.
Other codes are:

| Dataset | Additional reason codes |
| --- | --- |
| Branches | `invalid_province`, `duplicate_branch`, `conflicting_branch_id` |
| Customers | `invalid_province`, `invalid_join_date`, `duplicate_customer`, `conflicting_customer_id` |
| Accounts | `unknown_customer_id`, `unknown_branch_id`, `invalid_account_type`, `invalid_balance`, `invalid_opened_date`, `opened_date_before_customer_join_date`, `duplicate_account`, `conflicting_account_id` |
| Transactions | `unknown_account_id`, `unknown_branch_id`, `invalid_transaction_type`, `invalid_amount`, `nonpositive_amount`, `invalid_transaction_date`, `transaction_date_before_account_opened_date`, `duplicate_transaction`, `conflicting_transaction_id` |
| Payments | `unknown_account_id`, `invalid_status`, `invalid_amount`, `nonpositive_amount`, `invalid_payment_date`, `payment_date_before_account_opened_date`, `duplicate_payment`, `conflicting_payment_id` |

## Intentional quality cases

Record positions below are one-based, excluding CSV headers.

| File | Raw rows | Cases |
| --- | ---: | --- |
| branches.csv | 5 | All valid |
| customers.csv | 14 | Positions 6-8 need normalisation; 11 duplicates C002; 12 has no ID; 13 has no first name; 14 has an impossible date |
| accounts.csv | 16 | Positions 6-7 need normalisation; 11 duplicates A003; 12 references C999; 13 references B999; 14 has a nonnumeric balance; 15 has no ID; 16 has unsupported investment type |
| transactions.csv | 22 | Positions 6-7 need normalisation; 13 duplicates T003; 14 references A999; 15 references B999; 16 has a negative amount; 17 has zero amount; 18 has a nonnumeric amount; 19 has an impossible date; 20 has no ID; 21 has unsupported refund type; 22 has no account ID |
| payments.json | 11 | Positions 4-5 need normalisation; 6 duplicates P002; 7 references A999; 8 has a null ID; 9 has a nonnumeric amount; 10 has an impossible date; 11 has unknown status |

Under these rules, expected accepted/rejected counts are: branches 5/0,
customers 10/4, accounts 10/6, transactions 12/10, and payments 5/6.
That is 68 source records: 42 accepted after normalisation and 26 rejected.
The large T011 deposit is valid; any later anomaly flag must not automatically reject it.
