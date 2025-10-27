# Data Source Knowledge Base

This document provides a high-level overview of available data sources to help you decide which databases and schemas to query based on the question asked.

## Available Databases

### 1. customer_db (Customer Relationship Management)
**File:** `customer_db.yaml`

**Purpose:** Customer interactions, marketing, complaints, and satisfaction data

**Use this database when questions involve:**
- Customer profiles, contact information, and segmentation (retail, premium, corporate, private_banking)
- Customer lifecycle status (active, dormant, closed) and onboarding
- Marketing campaigns (email, direct_mail, digital, cross_sell) and their effectiveness
- Campaign responses (clicked, opened, unsubscribed, purchased) and conversion rates
- Customer complaints and resolution tracking (service, fee, product, fraud)
- Complaint priority levels and resolution times
- Customer interactions across channels (phone, email, web, mobile_app, branch)
- Interaction types (call, email, chat, branch_visit) and outcomes
- Customer satisfaction surveys, NPS scores, and ratings
- KYC (Know Your Customer) verification status
- Customer risk ratings (low, medium, high)

**Key relationships:**
- Links to `employees_db` via assigned agents, complaint handlers, and interaction handlers
- Customer IDs match across all systems (used for cross-database joins)

**Sample questions:**
- "Which customers filed complaints in Q4 2024?"
- "What is the average NPS score for premium customers?"
- "Which marketing campaigns had the highest conversion rates?"
- "Show me all unresolved high-priority complaints"

---

### 2. accounts_db (Core Banking - Accounts & Transactions)
**File:** `accounts_db.yaml`

**Purpose:** Bank accounts, customer master data, and financial transactions

**Use this database when questions involve:**
- Bank accounts (savings, checking, money_market, CD)
- Account status (active, frozen, closed)
- Account balances and currencies (USD, CAD, etc.)
- Account opening and closing dates
- Customer master data (names, DOB, contact info)
- Financial transactions (deposit, withdrawal, transfer, payment, fee, salary)
- Transaction amounts, dates, and descriptions
- Account balances after transactions
- Account relationships (joint_owner, beneficiary, authorized_user)
- Branch codes and locations

**Key relationships:**
- Customer IDs link to all other databases
- Referenced by `loans_db` for loan disbursement accounts
- Transaction data links to accounts

**Sample questions:**
- "What is the total balance across all active accounts?"
- "Show me all transactions over $10,000 in December"
- "Which customers have multiple joint accounts?"
- "What are the top 10 accounts by balance?"

---

### 3. loans_db (Lending & Credit)
**File:** `loans_db.yaml`

**Purpose:** Loan applications, active loans, repayments, and risk management

**Use this database when questions involve:**
- Loan applications and their status (pending, approved, rejected, withdrawn)
- Loan types (mortgage, personal, auto, business, education)
- Loan approvals, rejections, and reasons
- Active loan accounts and their status (active, paid_off, defaulted, restructured)
- Loan principal amounts, interest rates, and terms
- Outstanding balances and default status
- Repayment schedules and installments
- Payment status (pending, paid, late, missed)
- Loan collateral (property, vehicle, equipment, securities)
- Collateral appraisal values and Loan-to-Value (LTV) ratios
- Loan guarantors and their relationships
- Credit risk assessments and scores (0-1000)
- Credit grades (AAA, AA, A, BBB, BB, B, CCC)
- Probability of Default (PD) calculations

**Key relationships:**
- Links to `accounts_db.public.customers` for borrower information
- Links to `accounts_db.public.accounts` for disbursement and repayment accounts
- Links to `employees_db` for loan officers and approving officers

**Sample questions:**
- "How many loan applications were rejected in 2024?"
- "What is the average interest rate for mortgage loans?"
- "Which loans are currently in default?"
- "Show me all loans with credit grade below BBB"

---

### 4. insurance_db (Insurance Products)
**File:** `insurance_db.yaml`

**Purpose:** Insurance policies, claims, and beneficiaries

**Use this database when questions involve:**
- Insurance policies sold to customers
- Policy types (life, health, auto, property)
- Policy status (active, lapsed, cancelled)
- Premium amounts and payment frequencies
- Insurance claims filed by policyholders
- Claim types (death, accident, property_damage, medical)
- Claim amounts and approval status
- Claim settlement dates and approved amounts
- Policy beneficiaries and their allocations

**Key relationships:**
- Links to customer master data via customer_id
- Claims link to policies
- Beneficiaries link to policies

**Sample questions:**
- "How many insurance claims were approved this quarter?"
- "What is the average claim settlement time?"
- "Which policies have claims exceeding $50,000?"
- "Show me all life insurance policies with multiple beneficiaries"

---

### 5. compliance_db (Regulatory & Risk)
**File:** `compliance_db.yaml`

**Purpose:** AML screening, audit trails, compliance rules, and regulatory reporting

**Use this database when questions involve:**
- Anti-Money Laundering (AML) checks and screening
- AML check types (watchlist, sanctions, pep_screening, transaction_monitoring)
- AML flags and risk levels
- System audit trails for all critical actions
- Audit logs for entity changes (create, update, delete, view)
- Who performed what action and when
- Compliance rules and thresholds
- Rule types (transaction_limit, velocity_check, geographic_restriction)
- Regulatory reporting and submissions
- Compliance violations and incidents

**Key relationships:**
- References customers and transactions for AML checks
- Tracks employee actions via audit trails
- Links to employees for compliance officers and reviewers

**Sample questions:**
- "How many AML flags were raised this month?"
- "Show me all high-risk AML checks from last quarter"
- "Which employees accessed customer data in the past week?"
- "What compliance rules were violated in 2024?"

---

### 6. employees_db (Human Resources & Organization)
**File:** `employees_db.yaml`

**Purpose:** Employee data, departments, assignments, and training

**Use this database when questions involve:**
- Employee information (names, titles, contact info)
- Employee status (active, on_leave, terminated)
- Employment dates (hire date, termination date)
- Salaries and compensation
- Organizational departments and their budgets
- Department heads and reporting structure
- Employee assignments to customers, projects, or branches
- Employee roles (loan officer, relationship manager, compliance officer)
- Employee training programs and completion status
- Training enrollment and completion dates

**Key relationships:**
- Referenced by many tables across other databases:
  - Customer assigned agents (customer_db)
  - Complaint handlers (customer_db)
  - Interaction handlers (customer_db)
  - Loan officers (loans_db)
  - Loan approvers (loans_db)
  - Compliance reviewers (compliance_db)
  - Audit trail performers (compliance_db)

**Sample questions:**
- "Which employees are assigned to premium customer portfolios?"
- "Who are the top loan officers by number of approvals?"
- "Which employees have not completed required compliance training?"
- "What is the average salary by department?"

---

## Cross-Database Relationships

The databases are interconnected through customer_id and employee_id references:

### Customer Journey Flow
1. **accounts_db.customers** ’ Core customer master data
2. **customer_db.customer_profiles** ’ CRM and interaction data
3. **loans_db.loan_applications** ’ Loan requests
4. **loans_db.loans** ’ Active loans linked to accounts
5. **insurance_db.policies** ’ Insurance products
6. **compliance_db.aml_checks** ’ Regulatory screening

### Employee Context
- Employees from **employees_db** are referenced throughout:
  - Relationship managers (customer_db)
  - Loan officers and approvers (loans_db)
  - Compliance officers (compliance_db)
  - Transaction processors (accounts_db)

### Cross-Database Query Patterns

**Customer 360 View:** Combine customer_db + accounts_db + loans_db + insurance_db
```
Get customer profile, all accounts, loans, insurance policies, and interactions
```

**Risk Analysis:** Combine loans_db + compliance_db + customer_db
```
Analyze loan risk assessments with AML checks and customer risk ratings
```

**Employee Performance:** Combine employees_db + loans_db + customer_db
```
Track employee assignments, loan approvals, and customer satisfaction
```

**Financial Health:** Combine accounts_db + loans_db + insurance_db
```
Calculate customer net worth: account balances - loan balances + policy values
```

---

## Query Strategy Guidelines

### 1. Identify the Primary Domain
- **Transactions & Balances** ’ accounts_db
- **Lending & Credit** ’ loans_db
- **Customer Service & Marketing** ’ customer_db
- **Insurance** ’ insurance_db
- **Compliance & Audit** ’ compliance_db
- **Workforce & Organization** ’ employees_db

### 2. Determine if Cross-Database Join is Needed
- Customer-centric queries often need customer_db + accounts_db
- Risk queries often need loans_db + compliance_db
- Performance queries often need employees_db + (loans_db or customer_db)

### 3. Use Fully Qualified Table Names
```sql
-- Single database
SELECT * FROM accounts_db.public.accounts

-- Cross-database join
SELECT a.*, c.*
FROM accounts_db.public.accounts a
JOIN customer_db.public.customer_profiles c ON a.customer_id = c.customer_id
```

### 4. Leverage Sample Values
Many categorical columns have sample_values listed. Use exact values from the schema:
- account_status: active, frozen, closed
- loan_status: active, paid_off, defaulted, restructured
- customer_segment: retail, premium, corporate, private_banking

### 5. Check Foreign Keys and Cross-DB References
- Use `foreign_key` for same-database JOINs
- Use `cross_db_reference` for cross-database JOINs
- The cross_db_reference includes a description explaining the relationship

---

## Quick Reference by Question Type

| Question Type | Primary Database(s) | Key Tables |
|--------------|---------------------|------------|
| Account balances, transactions | accounts_db | accounts, transactions |
| Loan applications, approvals | loans_db | loan_applications, loans |
| Loan defaults, risk | loans_db | loans, risk_assessments |
| Customer complaints | customer_db | complaints, customer_profiles |
| Marketing campaigns | customer_db | campaigns, campaign_responses |
| Customer satisfaction | customer_db | satisfaction_surveys |
| Insurance claims | insurance_db | claims, policies |
| AML/fraud checks | compliance_db | aml_checks |
| Audit logs | compliance_db | audit_trails |
| Employee info | employees_db | employees, departments |
| Customer 360 | customer_db + accounts_db + loans_db | customer_profiles, accounts, loans |

---

## Schema Usage Reference

For detailed information about the YAML structure, column types, and SQL generation guidelines, refer to:
- **backend/knowledge/docs/schema_usage.md** - Complete technical documentation

For specific table schemas, columns, and relationships, load the appropriate YAML file:
- **accounts_db.yaml** - Banking core
- **loans_db.yaml** - Lending
- **customer_db.yaml** - CRM
- **insurance_db.yaml** - Insurance
- **compliance_db.yaml** - Regulatory
- **employees_db.yaml** - HR
