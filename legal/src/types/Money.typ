#import "assert.typ": assert_each, assert_required, assert_type

/// Construct a money value from minor units.
///
/// `cents` keeps arithmetic predictable. Formatting is handled by
/// `Money_display`.
///
/// - cents (int): [required] Amount in minor units.
/// - currency (str): Currency label.
/// -> dictionary
#let Money(
  cents: none,
  currency: "ZAR",
) = {
  // type checks
  assert_required(cents, "cents", int);
  assert_required(currency, "currency", str);
  //

  (
    kind: "Money",
    cents: cents,
    currency: currency,
  )
}

/// Add thousands separators to a positive whole-number string.
///
/// - digits (str): Whole-number digits.
/// -> str
#let _group_digits(digits) = {
  let chars = digits.clusters()
  let first-len = calc.rem(chars.len(), 3)
  let first-len = if first-len == 0 { 3 } else { first-len }

  if chars.len() <= 3 {
    digits
  } else {
    let groups = (
      chars.slice(0, first-len).join(""),
    ) + chars
      .slice(first-len)
      .chunks(3)
      .map(chunk => chunk.join(""))

    groups.join(",")
  }
}

/// Format a `Money(...)` value for display.
///
/// - money (dictionary): Money value to format.
/// -> str
#let Money_display(money) = {
  // type checks
  assert_required(money, "money", "Money");
  //

  let sign = if money.cents < 0 { "-" } else { "" }
  let abs-cents = calc.abs(money.cents)
  let whole = calc.quo(abs-cents, 100)
  let cents = calc.rem(abs-cents, 100)
  let whole-text = _group_digits(str(whole))

  if cents == 0 {
    sign + money.currency + " " + whole-text
  } else {
    let cents-text = if cents < 10 { "0" + str(cents) } else { str(cents) }
    sign + money.currency + " " + whole-text + "." + cents-text
  }
}

/// Sum multiple `Money(...)` values.
///
/// All values must use the same currency.
///
/// - monies (array): Money values to add.
/// -> dictionary
#let Money_sum(monies) = {
  if monies.len() == 0 {
    panic("Money_sum requires at least one Money value")
  }

  // type checks
  assert_each(monies, "monies", "Money");
  //

  let currency = monies.first().currency
  let cents = monies.fold(0, (total, money) => {
    if money.currency != currency {
      panic("Cannot sum Money values with different currencies")
    }
    total + money.cents
  })

  (
    kind: "Money",
    cents: cents,
    currency: currency,
  )
}

/// Multiply a `Money(...)` value by a numeric factor.
///
/// - money (dictionary): Money value to multiply.
/// - factor (int, float): Multiplier.
/// -> dictionary
#let Money_multiply(money, factor) = {
  // type checks
  assert_required(money, "money", "Money");
  assert_required(factor, "factor", (int, float));
  //

  (
    kind: "Money",
    cents: money.cents * factor,
    currency: money.currency,
  )
}
