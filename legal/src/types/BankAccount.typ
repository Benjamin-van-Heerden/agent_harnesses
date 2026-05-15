#import "assert.typ": assert_required

/// Construct a bank account record for payment instructions.
///
/// - bank (str): [required] Bank name.
/// - account-holder (str): [required] Account holder name.
/// - account-number (str): [required] Account number.
/// - account-type (str, none): Account type.
/// - registered-entity (str, none): Registered entity for the account.
/// -> dictionary
#let BankAccount(
  bank: none,
  account-holder: none,
  account-number: none,
  account-type: none,
  registered-entity: none,
) = {
  // type checks
  assert_required(bank, "bank", str);
  assert_required(account-holder, "account-holder", str);
  assert_required(account-number, "account-number", str);
  //

  (
    kind: "BankAccount",
    bank: bank,
    account-holder: account-holder,
    account-number: account-number,
    account-type: account-type,
    registered-entity: registered-entity,
  )
}
