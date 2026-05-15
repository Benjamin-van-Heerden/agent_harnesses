#import "assert.typ": assert_each, assert_required, assert_type

/// Sum shareholder `number-of-shares` values.
///
/// - shareholders (array): ShareHolder values already using number-of-shares.
/// -> int
#let _shareholder-shares-total(shareholders) = shareholders.fold(
  0,
  (total, shareholder) => {
    assert_type(shareholder, "ShareHolder");
    total + shareholder.number-of-shares
  },
)

/// Sum shareholder `percentage-ownership` values.
///
/// - shareholders (array): ShareHolder values already using percentage-ownership.
/// -> int | float
#let _shareholder-percentage-total(shareholders) = shareholders.fold(
  0,
  (total, shareholder) => {
    assert_type(shareholder, "ShareHolder");
    total + shareholder.percentage-ownership
  },
)

/// Validate shareholder records against company ownership metadata.
///
/// - shareholders (array): ShareHolder values to validate.
/// - number-of-shares (int, none): Total number of issued shares.
/// -> array
#let _validate-shareholders(shareholders, number-of-shares) = {
  assert_each(shareholders, "shareholders", "ShareHolder");

  if shareholders.len() > 0 {
    let uses-shares = shareholders.all(shareholder => shareholder.number-of-shares != none)
    let uses-percentages = shareholders.all(shareholder => shareholder.percentage-ownership != none)

    if not uses-shares and not uses-percentages {
      panic("Company shareholders must all use number-of-shares or all use percentage-ownership")
    }

    if uses-shares {
      if number-of-shares == none {
        panic("Company requires number-of-shares when shareholders use number-of-shares")
      }

      let shares-total = _shareholder-shares-total(shareholders)
      if shares-total != number-of-shares {
        panic("Company shareholder shares must add to number-of-shares")
      }
    }

    if uses-percentages {
      let percentage-total = _shareholder-percentage-total(shareholders)
      if percentage-total != 100 {
        panic("Company shareholder percentage-ownership values must add to 100")
      }
    }
  }

  shareholders
}

/// Construct a company profile for document wrappers and issuer metadata.
///
/// - name (str): [required] Registered company name.
/// - trading-name (str): [required] Trading or display name.
/// - registration (str): [required] Company registration number.
/// - director (str): [required] Primary director or representative.
/// - registered-address (str): [required] Registered address, usually comma-separated.
/// - tax-number (str, none): Tax registration number.
/// - number-of-shares (int, none): Total number of issued shares.
/// - shareholders (array): ShareHolder values. See `src/types/ShareHolder.typ`.
/// - postal-address (str, none): Postal address.
/// - email (str, none): Contact email.
/// - cell (str, none): Contact number.
/// - website (str, none): Website URL.
/// - enterprise-name (str, none): Registered enterprise name.
/// - enterprise-type (str, none): Registered enterprise type.
/// - enterprise-status (str, none): Current enterprise status.
/// - registration-date (str, none): Company registration date.
/// - business-start-date (str, none): Business start date.
/// - financial-year-end (str, none): Financial year end month.
/// -> dictionary
#let Company(
  name: none,
  trading-name: none,
  registration: none,
  director: none,
  registered-address: none,
  tax-number: none,
  number-of-shares: none,
  shareholders: (),
  postal-address: none,
  email: none,
  cell: none,
  website: none,
  enterprise-name: none,
  enterprise-type: none,
  enterprise-status: none,
  registration-date: none,
  business-start-date: none,
  financial-year-end: none,
) = {
  // type checks
  assert_required(name, "name", str);
  assert_required(trading-name, "trading-name", str);
  assert_required(registration, "registration", str);
  assert_required(director, "director", str);
  assert_required(registered-address, "registered-address", str);
  //

  let shareholders = _validate-shareholders(shareholders, number-of-shares)

  (
    kind: "Company",
    name: name,
    trading-name: trading-name,
    registration: registration,
    tax-number: tax-number,
    director: director,
    registered-address: registered-address,
    number-of-shares: number-of-shares,
    shareholders: shareholders,
    postal-address: postal-address,
    email: email,
    cell: cell,
    website: website,
    enterprise-name: enterprise-name,
    enterprise-type: enterprise-type,
    enterprise-status: enterprise-status,
    registration-date: registration-date,
    business-start-date: business-start-date,
    financial-year-end: financial-year-end,
  )
}

/// Return registered-address lines for a `Company(...)` value.
///
/// - company (dictionary): Company value to inspect.
/// -> array
#let Company_registered_address_lines(company) = {
  // type checks
  assert_required(company, "company", "Company");
  //

  let parts = company.registered-address
    .split(",")
    .map(part => part.trim())
    .filter(part => part != "")

  parts
    .chunks(2)
    .map(chunk => chunk.join(", "))
}
