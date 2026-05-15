#import "assert.typ": assert_required

/// Construct a client record for invoices and business documents.
///
/// - name (str): [required] Legal or trading name of the client.
/// - address (str, none): Billing or registered address.
/// - email (str, none): Billing contact email.
/// - cell (str, none): Billing contact phone number.
/// - details (array): Additional rows to render under standard client fields. Each item should be `(label: str, value: any)`.
/// -> dictionary
#let Client(
  name: none,
  address: none,
  email: none,
  cell: none,
  details: (),
) = {
  // type checks
  assert_required(name, "name", str);
  //

  (
    kind: "Client",
    name: name,
    address: address,
    email: email,
    cell: cell,
    details: details,
  )
}
