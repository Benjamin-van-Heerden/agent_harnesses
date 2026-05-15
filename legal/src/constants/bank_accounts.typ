#import "../types/BankAccount.typ": BankAccount

/// Placeholder default payment account.
///
/// Replace this with the lawyer or firm's real trust/business account before
/// using payment instructions in client-facing documents.
/// -> dictionary
#let default-bank-account = BankAccount(
  "TODO Bank",
  "TODO Account Holder",
  "TODO Account Number",
  account-type: "TODO Account Type",
  registered-entity: "TODO Registered Entity",
)
