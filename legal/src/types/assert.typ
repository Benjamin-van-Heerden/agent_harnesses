/// Return the soft type tag stored on a constructed value.
///
/// - value (dictionary): Soft-typed dictionary value.
/// -> str | none
#let kind_of(value) = {
  if type(value) != dictionary {
    none
  } else {
    value.at("kind", default: none)
  }
}

/// Validate that a value was produced by the expected constructor.
///
/// - value (dictionary): Value to validate.
/// - expected (str): Expected soft type tag, for example `"Client"`.
/// -> dictionary
#let assert_kind(value, expected) = {
  let actual = kind_of(value)
  if actual != expected {
    panic("Expected " + expected + ", got " + str(actual))
  }
  value
}

/// Validate a value against a built-in Typst type or soft type kind.
///
/// - value (any): Value to validate.
/// - expected-type (type, str, array): Built-in Typst type, soft type kind, or allowed specs.
/// -> none
#let assert_type(value, expected-type) = {
  if type(expected-type) == array {
    let matches = expected-type.any(spec => {
      if type(spec) == type {
        type(value) == spec
      } else if type(spec) == str {
        kind_of(value) == spec
      } else {
        false
      }
    })
    if not matches {
      panic("Expected one of " + str(expected-type) + ", got " + str(type(value)))
    }
  } else if type(expected-type) == type {
    let actual-type = type(value)
    if actual-type != expected-type {
      panic("Expected " + str(expected-type) + ", got " + str(actual-type))
    }
  } else if type(expected-type) == str {
    let _ = assert_kind(value, expected-type)
  } else {
    panic("Expected type specifier must be a Typst type or soft type kind string")
  }
  none
}

/// Validate that a required value is present and has the expected type.
///
/// - value (any): Value to validate.
/// - prop (str): Property or parameter name for panic messages.
/// - expected-type (type, str, array): Built-in Typst type, soft type kind, or allowed specs.
/// -> none
#let assert_required(value, prop, expected-type) = {
  if value == none {
    panic(prop + " is required")
  }
  assert_type(value, expected-type)
  none
}

/// Validate every item in an array against a built-in Typst type or soft type kind.
///
/// - values (array): Values to validate.
/// - prop (str): Property or parameter name for panic messages.
/// - expected-type (type, str, array): Built-in Typst type, soft type kind, or allowed specs.
/// -> none
#let assert_each(values, prop, expected-type) = {
  assert_required(values, prop, array)
  for value in values {
    assert_type(value, expected-type)
  }
  none
}
