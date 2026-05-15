#import "assert.typ": assert_required

/// Construct a shareholder record for company ownership metadata.
///
/// Provide either `number-of-shares` or `percentage-ownership`, not both.
///
/// - name (str): [required] Shareholder name.
/// - number-of-shares (int, none): Number of shares held.
/// - percentage-ownership (int, float, none): Percentage ownership.
/// -> dictionary
#let ShareHolder(
  name: none,
  number-of-shares: none,
  percentage-ownership: none,
) = {
  // type checks
  assert_required(name, "name", str);
  //

  if number-of-shares == none and percentage-ownership == none {
    panic("ShareHolder requires number-of-shares or percentage-ownership")
  }
  if number-of-shares != none and percentage-ownership != none {
    panic("ShareHolder cannot use both number-of-shares and percentage-ownership")
  }

  (
    kind: "ShareHolder",
    name: name,
    number-of-shares: number-of-shares,
    percentage-ownership: percentage-ownership,
  )
}
