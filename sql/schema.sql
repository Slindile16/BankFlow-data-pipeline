-- PostgreSQL schema for the accepted, transformed BankFlow datasets.
-- Load parent tables before child tables: branches/customers, accounts, then
-- transactions/payments.

CREATE TABLE IF NOT EXISTS branches (
    branch_id TEXT PRIMARY KEY,
    branch_name TEXT NOT NULL,
    city TEXT NOT NULL,
    province TEXT NOT NULL CHECK (province IN (
        'Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal', 'Limpopo',
        'Mpumalanga', 'North West', 'Northern Cape', 'Western Cape'
    ))
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    province TEXT NOT NULL CHECK (province IN (
        'Eastern Cape', 'Free State', 'Gauteng', 'KwaZulu-Natal', 'Limpopo',
        'Mpumalanga', 'North West', 'Northern Cape', 'Western Cape'
    )),
    join_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    account_type TEXT NOT NULL CHECK (account_type IN ('savings', 'current')),
    balance NUMERIC(12, 2) NOT NULL,
    opened_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    transaction_type TEXT NOT NULL CHECK (transaction_type IN (
        'deposit', 'withdrawal', 'transfer', 'card_payment'
    )),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    transaction_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    payee TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    payment_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'pending', 'failed'))
);
