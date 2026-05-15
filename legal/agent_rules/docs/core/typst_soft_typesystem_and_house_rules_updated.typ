= Typst Soft Type System

This repository uses a small, explicit soft type system for reusable Typst
business-document templates. Typst does not provide nominal user-defined types,
so we model domain records with constructor functions that return dictionaries
containing a `kind` tag.

The goals are:

- keep public template calls readable and self-documenting;
- avoid anonymous ad hoc dictionaries at call sites;
- validate domain values at template boundaries;
- make Tinymist hover documentation useful;
- keep renderer functions modular and narrow.

== Directory and Naming

Soft type constructors live under `src/types/`.

Default project naming distinguishes callable methods from variables:

- callable functions and methods use `snake_case`;
- variables, parameters, named arguments, and dictionary fields use kebab-case;
- type constructors use `CamelCase`;
- type methods use `{Type}_{method}`, where the type is `CamelCase` and the
  method is `snake_case`.

Type module filenames are the exception to normal underscore file naming. They
use `CamelCase` and match the constructor exported by the file:

```typ
src/types/Client.typ
src/types/BankAccount.typ
src/types/Company.typ
src/types/Money.typ
src/types/ShareHolder.typ
...
```

`src/types/assert.typ` is not a type module. It stays lowercase because it only
exports shared methods that act on soft-typed values, such as `assert_kind`.

The constructor exported by each type file is also capitalized:

```typ
#import "../src/types/Client.typ": Client

#let client = Client(
  name: "URBTEC (PTY) LTD",
  email: "accounts@urbtec.co.za",
)
```

Type operations exported from type modules use `{Type}_{method}`:

```typ
#import "../types/Money.typ": Money_display, Money_sum
#import "../types/Company.typ": Company_registered_address_lines
```

This keeps type operations visually tied to their type while preserving the
method naming rule.

Validation is centralized in `src/types/assert.typ` through `assert_type`,
`assert_required`, and `assert_each`.

Public exported names must not start with `_`. Helpers scoped to the same file
must start with `_`, for example `_client_rows` or `_date_display`.

Do not introduce snake_case variables in new Typst code. If touching existing
Typst code, keep callable names as `snake_case`, but use kebab-case for
variables, parameters, named arguments, and dictionary fields.

Shared soft-type infrastructure lives in `src/types/assert.typ`; its exported
functions follow regular `snake_case`, for example `assert_kind`.

Do not create soft types that only wrap built-in Typst values without adding a
domain invariant. In particular, use Typst's built-in `datetime` directly for
dates and format it at the rendering boundary. Plain display strings are also
acceptable when the date is already presentation text.

Typed constants live under `src/constants/`. Constants that represent domain
records should be constructed with the relevant soft type, for example
`yhat-company = Company(...)` or `default-bank-account = BankAccount(...)`.
Name constants for their actual semantic role, not for incidental defaultness.
For example, prefer `business-bank-account` over `default-bank-account` when
the value is specifically the business payment account.

All reusable colors and visual tokens live in `src/constants/theme.typ`. Do not
introduce literal `rgb(...)`, `luma(...)`, or hex colors in templates or
rendering functions. Add a named theme constant first, then import it where
needed.

Rendering functions live under `src/functions/`. Small generic helpers may live
under `src/functions/helpers/` when the same simple behavior is needed across
multiple rendering modules.

== Constructor Shape

Constructors, templates, rendering functions, and reusable helpers use named
arguments for all parameters. Required parameters default to `none`, are marked
with `[required]` in the docstring description, and are checked in the opening
`// type checks` block.
This is an intentional house rule. Typst only makes an argument nameable when
it has a default, so required arguments use `none` as the sentinel and runtime
validation supplies the failure mode.

Use named arguments at call sites, including required arguments. Do not mix
positional required values with named optional values. Small callback functions
such as `.map(item => ...)` or `.fold(0, (total, item) => ...)` are the only
normal exception.

Prefer this:

```typ
/// Construct a client record for invoices and business documents.
///
/// - name (str): [required] Legal or trading name of the client.
/// - email (str, none): Billing contact email.
/// -> dictionary
#let Client(
  name: none,
  email: none,
) = {
  // type checks
  assert_required(name, "name", str);
  //

  (
    kind: "Client",
    name: name,
    email: email,
  )
}
```

Use this call shape:

```typ
#let client = Client(
  name: "URBTEC (PTY) LTD",
  email: "accounts@urbtec.co.za",
)
```

The `[required]` marker belongs after the colon in the description, not before
it. Tinymist ignores the text before the colon except for the documented type
annotation. Use this:

```typ
/// - name (str): [required] Legal or trading name.
```

Not this:

```typ
/// - name (str) [required]: Legal or trading name.
```

When a required argument can accept more than one type, pass an array of
allowed type specs to `assert_required`:

```typ
/// - date (str, datetime): [required] Date or date display.
/// - client (dictionary): [required] Client value. See `src/types/Client.typ`.
#let render_row(date: none, client: none) = {
  // type checks
  assert_required(date, "date", (str, datetime));
  assert_required(client, "client", "Client");
  //
}
```

== Constructor Invariants

Constructors should validate invariants that define the domain record itself.
Do not defer intrinsic consistency checks to templates or renderers.

Examples:

- `ShareHolder(...)` requires exactly one of `number-of-shares` or
  `percentage-ownership`.
- `Company(...)` validates that shareholders all use the same ownership basis.
- If shareholders use `number-of-shares`, `Company(...)` requires
  `number-of-shares` and validates the shareholder share total against it.
- If shareholders use `percentage-ownership`, `Company(...)` validates that the
  percentages add to `100`.
- Optional fields such as `tax-number` should default to `none` rather than
  using empty strings as absence markers.
- Money-like domain values should use `Money(...)` rather than display strings
  whenever the value participates in invoice totals, rates, or arithmetic.

Preferred ownership model:

```typ
#let company = Company(
  name: "Yhat Solutions (Pty) Ltd",
  trading-name: "Yhat Solutions",
  registration: "2023/699445/07",
  director: "Benjamin van Heerden",
  registered-address: "49 De Havilland Cres, Persequor, Pretoria, 0020",
  number-of-shares: 180,
  shareholders: (
    ShareHolder(name: "Benjamin van Heerden", number-of-shares: 180),
  ),
)
```

== Domain Types vs Display Rows

Use soft types for domain concepts that carry meaning or invariants:

- `Client(...)` for the invoice recipient/contact.
- `Money(...)` for monetary amounts and rates.
- `Company(...)` and `ShareHolder(...)` for issuer/company metadata.

Do not overload domain types with fields from a more specific concept. For
example, `Client(...)` should not have `registration`; registration is a company
concept and should be included in display `details` only when a particular
client row needs it.

Display rows are intentionally open dictionaries shaped as
`(label: str, value: any)`. They are acceptable for presentation extension
points such as `details` and `extra-details`. They are not a substitute for
soft types at public call sites when the data has domain meaning.

must not contain invoice amounts or rates. Hourly invoice totals are derived by
the template from `work`, `hourly-rate`, and optional `billable-hours`.

Money should remain money until the final render boundary. Use `Money_display`
only when placing the value into visible document content. If a template accepts
a payable amount, rate, or total as a parameter, that parameter should generally
be a `Money(...)` value and should be validated with `assert_required(value,
"prop", "Money")` or `assert_type(value, "Money")`.

== Documentation Comments

Use Tinymist-style `///` comments immediately before definitions. This applies
to public exports and to private helpers scoped to a file.

Document parameters in the main doc block, not as `///` comments inside the
function parameter list. The parameter-list style was intentionally avoided here
because it produced worse hover output for this project.

Preferred style:

```typ
/// Construct a money value from minor units.
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
```

Use `str`, `int`, `float`, `array`, `dictionary`, `datetime`, `none`, and
`markup` in docs. Use `markup` when callers may pass a Typst markup block such
as `[Due upon receipt]`. Avoid `content` in human-facing type hints unless the
internal Typst value type itself is the point being discussed.

Required fields should not be documented as nullable. Only optional fields
should include `none`.

Private helper documentation should still be precise and short:

```typ
/// Return display rows for a bank account.
///
/// - bank (dictionary): Bank account. See `src/types/BankAccount.typ`.
/// -> array
#let _bank_rows(bank: none) = {
  // type checks
  assert_required(bank, "bank", "BankAccount");
  //

  (
    (label: "Bank", value: bank.bank),
    (label: "Account Number", value: bank.account-number),
  )
}
```

== Runtime Validation

Every constructor returns a dictionary with a `kind` tag:

```typ
(
  kind: "Client",
  name: name,
)
```

`src/types/assert.typ` provides shared validation methods:

- `assert_kind(value, expected)` validates a soft type tag and returns the value
  for local rebinding when needed.
- `assert_type(value, expected-type)` validates a built-in Typst type or soft
  type kind string and returns `none`.
- `assert_required(value, prop, expected-type)` validates presence and type and
  returns `none`.
- `assert_each(values, prop, expected-type)` validates each item in an array and
  returns `none`.

`expected-type` can be a built-in Typst type such as `str`, `int`, `float`,
`array`, `dictionary`, or `datetime`; a soft type kind string such as
`"Client"` or `"Money"`; or an array of allowed specs such as `(str, datetime)`.

Because `assert_type`, `assert_required`, and `assert_each` return `none`, call
them as statement-like checks inside a code block and terminate each call with a
semicolon:

```typ
// type checks
assert_required(invoice-number, "invoice-number", str);
assert_required(client, "client", "Client");
//
```

Keep validation direct and centralized: call `assert_type`, `assert_required`,
or `assert_each` in the `// type checks` block, then use the original parameter
normally below the block.

Templates validate soft types at their boundaries:

```typ
#import "../types/assert.typ": assert_required

#let hourly_invoice(client: none, ..args) = {
  // type checks
  assert_required(client, "client", "Client");
  //

  // render...
}
```

This catches accidental plain dictionaries or wrong soft types early.

Use the explicit `// type checks` block at the start of any function that
accepts soft-typed values. Keep all boundary assertions together, then close the
block with a plain `//` separator before doing derivation or rendering work:

```typ
#let render_invoice(client: none, total-payable: none, ..args) = {
  // type checks
  assert_required(client, "client", "Client");
  assert_required(total-payable, "total-payable", "Money");
  //

  let subtitle = if subtitle == none { issue-date } else { subtitle }
  // render...
}
```

Private helpers are not exempt from validation. If a private helper accepts a
soft-typed value, it should assert that value even when its public caller also
asserted it. This keeps helpers self-documenting, copyable, and robust when
they are reused later.

== Template Call Signatures

Templates should use named parameters for all values. Required values default
to `none`, are marked with `[required]` in the docstring description, and are
validated in the opening `// type checks` block. If a parameter expects a soft
type, document it by pointing at the type module, because Tinymist cannot infer
the nominal type from a dictionary.

Do not design public templates around one large open dictionary such as
`project_invoice(invoice)`. Templates should have explicit, documented
parameters like regular functions:

- required named parameters for the minimum meaningful invoice;
- optional named parameters for presentation and extensions;
- soft-typed values for domain concepts;
- `extra-details` for genuinely template-specific display rows.

This keeps Tinymist signatures useful and prevents one-off invoice cases from
leaking into general templates.

Example:

```typ
/// Render an hourly-work invoice.
///
/// - invoice-number (str): [required] Unique invoice number.
/// - client (dictionary): [required] The Client for whom to render the invoice. See `src/types/Client.typ`.
/// - hourly-rate (dictionary): [required] Hourly rate. See `src/types/Money.typ`.
/// -> content
#let hourly_invoice(
  invoice-number: none,
  client: none,
  description: none,
  hourly-rate: none,
  billable-hours: none,
) = {
  // type checks
  assert_required(invoice-number, "invoice-number", str);
  assert_required(client, "client", "Client");
  assert_required(hourly-rate, "hourly-rate", "Money");
  //
}
```

This intentionally trades Typst's built-in positional required-parameter
failure for explicit, documented runtime validation. The upside is consistent
named call sites and clearer Tinymist hovers for document templates.

Arrays of dictionaries are acceptable for repeated domain values only when each
item is created by a constructor, for example:

```typ
work: (
  WorkEntry(date: "2026-04-02", hours: 8),
  WorkEntry(date: "2026-04-09", hours: 7),
)
```

Avoid arbitrary anonymous dictionaries at public call sites unless the data is
genuinely open-ended extension data, such as `(label: str, value: any)` rows.

Project and hourly invoices should follow the same API style. If an invoice
needs fields such as installment, remaining balance, or project cost, those are
case-specific display rows unless they become a reusable domain concept. Put
them in `extra-details`; do not hard-code them into the general template.

== Module Size

Keep `src/functions/` modules small and self-contained. A module should usually
own one rendering primitive, such as payment instructions, invoice details, or a
work log. Do not create broad god files for entire domains.
