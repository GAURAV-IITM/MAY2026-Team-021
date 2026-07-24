"""Monthly billing, payment, receipt, and reminder use cases.

TODO: Monthly fee generation must be idempotent using the unique student/month
constraint. Receipt issuance and payment status updates belong in one database
transaction.
"""
