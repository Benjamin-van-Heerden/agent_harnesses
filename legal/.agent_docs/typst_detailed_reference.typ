// =============================================================================
// typst_reference.typ
//
// A reference for the Praxis system of work.
//
// Audience and purpose
// --------------------
// This file is written for two readers: a working lawyer who is not a
// programmer but who works with coding agents to produce documents, and the
// agents themselves. It is a single .typ file because that gives both readers
// the same artefact: the lawyer compiles it to PDF and reads the formatted
// output; the agent reads the source. Agent-only notes (heuristics, common
// failure modes, "do not do this") live in line comments like this one — they
// are invisible in the rendered PDF.
//
// How the file is structured
// --------------------------
// The reference reads top to bottom as a course. Each section assumes the one
// before it. Code samples appear in raw `typ` blocks (triple-backtick fenced
// code), so they are shown as inert source rather than executed inside this
// document. That keeps the rendered reference clean and prevents earlier
// examples from leaking styling into later ones. When you want to see what an
// example does, copy it into a fresh .typ file and compile.
//
// Version target
// --------------
// Typst 0.13 / 0.14 conventions. The syntax shown here is current as of late
// 2025. Older patterns (#locate, #style, the old #counter.display without
// context) are deprecated and not used. If you find an older tutorial on the
// web that uses them, prefer the patterns in this file.
//
// Convention: "Agent note" callouts in the rendered output flag heuristics
// that LLMs in particular tend to get wrong. "Gotcha" callouts flag genuinely
// surprising language behaviour.
// =============================================================================


// -----------------------------------------------------------------------------
// Document metadata and page setup for THIS reference document.
// (The reference is itself a Typst document, so it eats its own dog food.)
// -----------------------------------------------------------------------------

#set document(
  title: "Typst Reference (Praxis)",
  author: "Praxis",
)

#set page(
  paper: "a4",
  margin: (x: 2.2cm, y: 2.4cm),
  numbering: "1",
  number-align: center + bottom,
  header: context {
    // First page (the title page) gets no header.
    if counter(page).get().first() > 1 [
      #set text(size: 9pt, fill: luma(110))
      Typst Reference #h(1fr) Praxis system of work
      #v(-0.6em)
      #line(length: 100%, stroke: 0.4pt + luma(180))
    ]
  },
)

#set text(size: 10.5pt, lang: "en")
#set par(justify: true, leading: 0.62em, spacing: 1.05em)

#set heading(numbering: "1.1")
#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block(above: 1.5em, below: 0.9em)[
    #set text(size: 18pt, weight: "bold")
    #if it.numbering != none [#counter(heading).display(it.numbering) #h(0.4em)]
    #it.body
  ]
}
#show heading.where(level: 2): it => block(above: 1.2em, below: 0.6em)[
  #set text(size: 13pt, weight: "bold")
  #if it.numbering != none [#counter(heading).display(it.numbering) #h(0.3em)]
  #it.body
]
#show heading.where(level: 3): it => block(above: 1em, below: 0.4em)[
  #set text(size: 11pt, weight: "bold", style: "italic")
  #if it.numbering != none [#counter(heading).display(it.numbering) #h(0.3em)]
  #it.body
]

// Inline code and code blocks: subtle background, slightly smaller font.
#show raw.where(block: false): box.with(
  fill: luma(240),
  inset: (x: 3pt, y: 0pt),
  outset: (y: 3pt),
  radius: 2pt,
)
#show raw.where(block: true): block.with(
  fill: luma(245),
  inset: 10pt,
  radius: 4pt,
  width: 100%,
)
#show raw: set text(font: ("DejaVu Sans Mono",), size: 9pt)

// Helper: a callout box for "Agent note" and "Gotcha".
#let callout(kind, body) = {
  let accent = if kind == "agent" { rgb("#3b82f6") } else { rgb("#f59e0b") }
  let bg = if kind == "agent" { rgb("#eef4fb") } else { rgb("#fff4e5") }
  let label = if kind == "agent" { "Agent note." } else { "Gotcha." }
  block(
    fill: bg,
    stroke: (left: 3pt + accent),
    inset: 10pt,
    radius: 2pt,
    width: 100%,
    above: 0.9em,
    below: 0.9em,
  )[
    #set text(size: 9.5pt)
    #strong(label) #body
  ]
}


// -----------------------------------------------------------------------------
// Title page
// -----------------------------------------------------------------------------

#align(center + horizon)[
  #v(-2cm)
  #text(size: 26pt, weight: "bold")[Typst Reference]
  #v(0.3em)
  #text(size: 13pt, style: "italic")[for the Praxis system of work]

  #v(2cm)
  #text(size: 11pt)[
    A practical guide to writing professional documents in Typst, \
    written for lawyers working with coding agents and for the agents themselves.
  ]
]


// -----------------------------------------------------------------------------
// Table of contents
// -----------------------------------------------------------------------------

#pagebreak()

#outline(
  title: [Contents],
  depth: 2,
  indent: auto,
)


// =============================================================================
// PART 1 — MENTAL MODEL
// =============================================================================

= What Typst is, and how to think about it

Typst is a typesetting system. You write a plain-text source file with the
extension `.typ`, the Typst compiler reads it, and out comes a PDF. Conceptually
it sits between Markdown (lightweight, easy to type) and LaTeX (programmable,
precise control over the page). In practice it is closer to LaTeX in what it
can do but closer to Markdown in how it feels to write.

Three things make Typst a good fit for legal work:

- Short documents (letters, memoranda) and long documents (contracts, briefs)
  use the same primitives. There is no equivalent of LaTeX's `\documentclass`
  fork in the road; you just write.
- Layout, numbering, headers, footers, and cross-references are all programmable
  with one consistent language. A clause-numbering scheme that fits your firm
  is a one-line set rule, not a 200-line preamble.
- Compilation is fast (milliseconds), so the iteration loop with an agent is
  short.

== The three modes: markup, code, math

Every character in a `.typ` file is being read in one of three modes.

*Markup mode* is the default. You type prose, and special characters like `=`,
`*`, `_`, `-`, and `+` are markup shorthand for headings, bold, italic, bullet
lists, and numbered lists. This is what you spend most of your time writing.

*Code mode* is what you switch into when you want to call a function, define a
variable, write an `if` or a `for`, or do anything else programmatic. You enter
code mode from markup by typing `#` immediately followed by an expression, and
you stay in code mode until that expression ends.

*Math mode* is for typesetting equations. You enter it with `$ ... $`. It is
not relevant for most legal work and is covered briefly in Part 14.

```typ
// Markup mode — this is just prose.
The agreement was signed on 12 March 2026.

// Code mode — entered with #, lasts until the expression ends.
The discount is #(100 - 15)%.

// Math mode — surrounded by dollar signs.
Compound interest: $A = P(1 + r)^n$.
```

== The hash (`#`) is your one trick

In markup, `#` switches into code mode for one expression. That expression can
be a function call (`#image("logo.png")`), a variable name (`#client-name`), an
arithmetic expression (`#(2 + 2)`), a method call (`#"Hello".lower()`), and so
on. After the expression ends, you are back in markup.

You do *not* need a `#` when you are already in code mode. Inside a function's
argument list, inside a `let` binding's right-hand side, inside a code block
`{ ... }` — you are in code mode, so write expressions plainly without leading
hashes.

```typ
// In markup: hash needed.
The font is #text(font: "Inria Serif")[important].

// Inside the call to text, "Inria Serif" is in code mode — no hash on it.
// And inside the [...] content block, we're back in markup.

// In a code block: hashes not needed for any code, but still needed when you
// dip back into markup via [...].
#{
  let n = 5
  let title = "Schedule " + str(n)
  // To insert content, dip back into markup with square brackets:
  [The title is *#title*.]
}
```

#callout("agent")[Inserting hashes inside argument lists is one of the most
common mistakes. `#text(font: #"Inria Serif")` is wrong — the inner `#` is
spurious because you are already in code mode. Just write `#text(font: "Inria
Serif")`.]

== Content is a value

Every chunk of formatted text in Typst is a value of type `content`. You can
store it in a variable, pass it as a function argument, return it from a
function, and concatenate it with `+`. This is the single most important idea
in Typst, because it means the document is not a stream of formatting commands
acting on a typesetter; it is a tree of content values, and you compose that
tree with code.

You write a content value with square brackets: `[some markup here]`. Inside
the brackets you are in markup mode, so you can use any markup you like.

```typ
#let recital = [The parties hereby agree as follows:]
// recital now holds a content value. It can be:
//   - inserted with #recital
//   - passed to functions: #emph(recital)
//   - concatenated: #(recital + [ Witness whereof, ...])
//   - stored in a list, dictionary, or returned from a function
```

The other text-like type is `string` (`"text in double quotes"`). A string is
just a sequence of characters; it has no formatting. Functions that accept a
file path, a font name, or a numbering pattern want a string. Functions that
accept document content want content. Most of the time the difference is
obvious from the function's documentation.


// =============================================================================
// PART 2 — MARKUP ESSENTIALS
// =============================================================================

= Markup essentials

This section is the minimum markup vocabulary needed to write plain documents.
Everything here has a corresponding function call form (because markup is
syntactic sugar for function calls), so anything you cannot do with markup you
can do by calling the underlying function directly.

== Headings

One `=` per nesting level, followed by a space.

```typ
= Top-level heading
== Sub-heading
=== Sub-sub-heading
```

Headings drive the table of contents, the heading counter, and any show rule
that targets headings. To turn on automatic numbering, set the `numbering`
parameter on the `heading` element.

```typ
#set heading(numbering: "1.1")     // 1, 1.1, 1.1.1, ...
#set heading(numbering: "1.a.i")   // 1, 1.a, 1.a.i, ...
#set heading(numbering: "I.")      // I, II, III, ...
```

For a contract or court document with the common `1` / `1.1` / `1.1.1` clause
scheme, `numbering: "1.1"` is what you want. For an opinion or memorandum that
nests as `1.` / `(a)` / `(i)`, see the cookbook for the show-rule pattern that
produces that.

To exclude a heading from the table of contents, set its `outlined` field to
`false`:

```typ
#heading(outlined: false)[Acknowledgements]
```

== Emphasis, strong, underline, strike

```typ
*strong*           // bold
_emphasis_         // italic
#underline[text]   // underlined
#strike[text]      // struck through
#highlight[text]   // highlighted
```

Note that the markup forms `*...*` and `_..._` work only when surrounded by
word boundaries. To make a partial word italic you may need to use the
function form: `#emph[Pty] Ltd`.

== Lists

Bullet lists use `-`. Numbered lists use `+`. Term lists (definition lists) use
`/ Term: definition`. Indentation creates nesting.

```typ
- One thing
- Another
  - A nested point
- A third

+ First step
+ Second step
+ Third step

/ Buyer: the party identified in clause 1.
/ Seller: the party identified in clause 2.
/ Goods: the items listed in Schedule A.
```

The term list is particularly useful for definitions sections in contracts.

== Links

```typ
https://example.com               // bare URL becomes a link automatically
#link("https://example.com")      // explicit link, displays the URL
#link("https://example.com")[the website]  // with custom display text
#link("mailto:counsel@firm.co.za")[Email counsel]
```

== Labels and references

A label is a unique identifier you attach to an element so you can reference
it later. You write a label as `<some-name>` immediately after the element it
labels. You reference a label with `@some-name`.

```typ
= Payment <clause-payment>

The Buyer shall pay the Purchase Price as set out in @clause-payment.
```

When the heading is renumbered, the reference updates automatically. Labels
also work on figures, tables (when wrapped in a figure), and equations. They
are how you build cross-references in legal documents.

== Comments

```typ
// line comment — to end of line
/* block comment
   spans multiple lines */
```

Comments are stripped before rendering. Use them generously in source files
that agents will work with: they are how you communicate intent without
polluting the output.

== Escapes

```typ
// To produce a literal special character, escape it with a backslash:
\#  \$  \*  \_  \[  \]  \\

// To produce an arbitrary Unicode codepoint:
\u{2014}   // em dash
```


// =============================================================================
// PART 3 — VARIABLES, TYPES, FUNCTIONS
// =============================================================================

= Variables, types, and functions

This is where Typst stops being just a markup language and starts being a
programming language. You will use these features whenever you build anything
reusable: a clause that is referenced by a defined term, a parties block that
fills itself in from a list, a template you reuse across matters.

== Let bindings

`let` introduces a name. Once a name is bound, you can use it for the rest of
the surrounding block (or the rest of the file if there is no surrounding
block).

```typ
#let client-name = "Acme Industries (Pty) Ltd"
#let purchase-price = 1_500_000
#let contract-date = datetime(year: 2026, month: 4, day: 15)

The Buyer is #client-name.
The Purchase Price is R#purchase-price.
```

You can store anything in a variable: a string, a number, a length, a colour,
content, an array, a dictionary, a function. The right-hand side of `let` is an
expression evaluated once, and the variable holds the result.

== Defining functions with let

A function is a `let` whose name is followed by parentheses listing parameters.

```typ
#let greeting(name) = [Dear #name,]

#greeting("Ms Khumalo")
```

You can give parameters default values, making them optional named arguments:

```typ
#let signoff(closer: "Yours faithfully", name) = [
  #closer, \
  \
  \
  #name
]

#signoff[John Doe]
#signoff(closer: "Yours sincerely")[Jane Smith]
```

A function returns the value of its last expression. If the body is a content
block in square brackets, it returns content. If the body is a code block in
curly braces, it returns whatever the last expression yields.

== Trailing content blocks

Because passing content to functions is so common, Typst lets you move the
final content argument out of the parentheses and into square brackets right
after them.

```typ
// These two calls are equivalent:
#text(weight: "bold", size: 14pt)[Notice to Defendants]
#text(weight: "bold", size: 14pt, [Notice to Defendants])

// And if there are no other arguments, you can drop the parens entirely:
#emph[important]
```

This is a syntactic convenience, not a semantic distinction. Use whichever
form reads better.

== Named arguments and the `.with()` method

Most Typst functions accept a mix of positional arguments (where order
matters) and named arguments (passed as `name: value`). Named arguments make
calls self-documenting:

```typ
#rect(width: 5cm, height: 3cm, fill: luma(230), stroke: 0.5pt)
```

`.with()` is a method available on every function; it returns a new function
with some arguments pre-supplied. This is the standard way to apply a
template:

```typ
#let firm_letter = letter.with(
  letterhead: "Doe & Doe Inc.",
  footer: "Confidential",
)

#show: firm_letter
```

`.with()` does not call the function; it just freezes some of its arguments.
You can chain `.with()` and pass the result around like any other value.

== The spread operator `..`

The spread operator unpacks an array into positional arguments, or a
dictionary into named arguments, of a function call. It also works the other
way: in a function definition, `..rest` collects extra arguments.

```typ
#let parties = ("Buyer", "Seller", "Guarantor")

// Spread into positional arguments:
#enum(..parties)

// Spread into a function definition (variadic):
#let join_with_comma(..items) = items.pos().join(", ")
#join_with_comma("a", "b", "c")
```

You will see `..` heavily used in templates that forward arguments to
underlying functions.

== Destructuring

You can pull apart arrays and dictionaries on the left side of a `let`:

```typ
#let (first, second) = ("Smith", "Jones")
#let (year, month, day, ..) = (2026, 4, 30, "extra", "ignored")

#let parties = (buyer: "Acme", seller: "Beta")
#let (buyer, seller) = parties      // pulls those two keys

// Destructuring also works in function parameter lists:
#let format_party((name, role)) = [#name (#role)]
#format_party(("Acme Industries", "Buyer"))
```

== Data types you will actually use

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(180),
  inset: 6pt,
  align: (left, left),
  [*Type*], [*What it is, with examples*],
  [`str`], [Plain text in double quotes. `"Acme Industries"`],
  [`content`], [Formatted text in square brackets. `[*bold*]`],
  [`int`], [Whole number. `42`, `1_500_000`],
  [`float`], [Decimal number. `3.14`, `0.5e-3`],
  [`bool`], [`true` or `false`],
  [`length`], [Distance with a unit. `12pt`, `2.5cm`, `1in`, `1.2em`, `50%`, `1fr`. See Part 9.],
  [`color`], [`red`, `blue`, `luma(80)`, `rgb("#1a4d8c")`, `cmyk(...)`],
  [`alignment`], [`left`, `right`, `center`, `top`, `bottom`, `horizon`. Combine with `+`: `top + right`.],
  [`array`], [Ordered list. `(1, 2, 3)`. A one-element array needs a trailing comma: `(1,)`.],
  [`dictionary`], [Key-value map. `(key: "value", another: 42)`.],
  [`datetime`], [Calendar date and/or time. `datetime(year: 2026, month: 4, day: 30)`.],
  [`function`], [A callable value. `text`, `image`, your own `let f(x) = x + 1`.],
  [`none`], [Absence of a value. Different from an empty string or empty content.],
  [`auto`], [A "smart default" placeholder that lets a function pick a sensible value.],
)

#callout("gotcha")[A one-element array needs a trailing comma. `(5)` is just
a parenthesised expression that evaluates to the integer 5; `(5,)` is an
array of one element. This matters whenever a function accepts either a
scalar or an array and you want it to take the array path. The safe rule:
when you mean an array, always include the trailing comma — even if the
array has more than one element, the trailing comma is harmless.]


// =============================================================================
// PART 4 — CONTROL FLOW
// =============================================================================

= Control flow

Control flow is what lets you write a "Page X of Y" footer, a parties block
that adapts to one or three signatories, or a clause that appears only when
a flag is set.

== Conditionals

```typ
#let value = 42

#if value > 0 [positive] else if value < 0 [negative] else [zero]
```

The body of each branch can be a code block `{...}` or a content block
`[...]`. The expression as a whole evaluates to the body of the matching
branch (or `none` if no branch matched and there is no `else`).

A common pattern: conditionally include some content based on a flag.

```typ
#let include-appendix = true

= Conclusion
...

#if include-appendix [
  = Appendix A — Schedule of payments
  ...
]
```

== `for` loops

`for` iterates over an array, dictionary, string, or any other collection.

```typ
// Over an array
#for item in ("apples", "oranges", "pears") [
  - #item
]

// Destructuring as you go
#let parties = (
  (name: "Acme Industries", role: "Buyer"),
  (name: "Beta Holdings", role: "Seller"),
)

#for (name, role) in parties.map(p => (p.name, p.role)) [
  *#role:* #name \
]

// Over the key-value pairs of a dictionary
#let definitions = (
  Buyer: "the party identified in clause 1",
  Seller: "the party identified in clause 2",
)
#for (term, meaning) in definitions [
  / #term: #meaning
]
```

== `while` loops

```typ
#let n = 1
#while n < 100 {
  n = n * 2
}
```

Useful in scripting, less useful in document content. Most of the time `for`
is what you want.

== Joining

The bodies of code blocks, content blocks, and loops *join*: the values they
produce are concatenated together. For content, this means the markup pieces
combine into one block of formatted text. This is why `for ... [ ... ]` does
something useful: each iteration produces content, and the iterations join
into one big block of content.

```typ
#let signatories = ("J. Doe", "M. Khumalo", "S. van der Merwe")

The undersigned: #for s in signatories [#s, ]
```

#callout("agent")[Loops in Typst do not need a list to "build up" — they
produce content directly. If an agent writes `let result = []; for x in arr {
result += [...] }; result` it will work, but the idiomatic version is just
`for x in arr [...]`. Use the join behaviour.]


// =============================================================================
// PART 5 — MODULES AND PACKAGES
// =============================================================================

= Splitting work across files

Real legal work means you do not put everything in one file. You have a firm
template, a set of standard clauses, a parties block factory, a watermark
helper. Typst's module system lets you put each piece in its own file and pull
in only what you need.

== Importing from another file

```typ
// In firm_template.typ:
#let firm-name = "Doe & Doe Inc."
#let letter(addressee, body) = [
  #firm-name \
  \
  Dear #addressee, \
  #body
]

// In your document:
#import "firm_template.typ": firm-name, letter

// Now `firm-name` and `letter` are in scope.
#letter("Mr Tau", [Please find enclosed ...])
```

Variants:

```typ
// Import everything from the file as a module under one name:
#import "firm_template.typ"
#firm_template.firm-name        // dot access

// Import everything by name (uses the filename, snake_case):
#import "firm_template.typ" as ft
#ft.firm-name

// Import every public name (rarely the cleanest choice, but available):
#import "firm_template.typ": *
```

`#include "other.typ"` is the other option: it inlines the *content* of the
other file at that point. Use `import` for definitions you want to reuse.
Use `include` only for plain content you want to splice in.

== Packages

Typst has a package ecosystem at *Typst Universe*. You import a package with
the syntax `@<namespace>/<name>:<version>`. The community namespace is
`@preview`.

```typ
#import "@preview/cetz:0.4.1": *      // a drawing/diagram package
#import "@preview/cmarker:0.1.6"       // markdown converter
```

The first time the compiler sees a package import it downloads and caches the
package. Versions are pinned to the exact string you wrote, so a document
compiled today will compile the same way next year.

You can also create your own *local* packages under the `@local` namespace.
This is what you do when your firm has a template you want to reuse across
matters. See Part 13 for the full pattern.

#callout("agent")[Pin package versions explicitly. `@preview/cetz:0.4.1` is
correct; `@preview/cetz` (no version) is a hard error. When suggesting a
package to install, an agent should always look up the current latest version
on Typst Universe and pin it.]


// =============================================================================
// PART 6 — SET RULES
// =============================================================================

= Set rules

A set rule changes the default values of an element's parameters for the rest
of the surrounding scope. It is the primary tool for "make all the headings
look like X" or "make the page A4 with these margins".

```typ
#set text(font: "Libertinus Serif", size: 11pt)
#set page(paper: "a4", margin: 2.5cm)
#set par(justify: true, leading: 0.65em)
#set heading(numbering: "1.1")
```

A top-level set rule is in effect from the line where it appears to the end of
the file. A set rule inside a block (a code block, a content block, or
inside another function call) is in effect only inside that block. This is
how you scope a styling change to one section without affecting the rest of
the document.

```typ
// The set rule below applies to the whole document.
#set par(justify: true)

This paragraph is justified.

// Inside this content block, the set rule is overridden, but only here.
#[
  #set par(justify: false)
  This paragraph is ragged-right.
]

This paragraph is justified again.
```

== What can be set

Not every parameter of every function can be set. Generally:

- Parameters that say "how" something looks can be set: font, size, weight,
  alignment, numbering pattern, and so on.
- Parameters that say "what" the function should act on cannot be set: the
  body of `text(...)`, the path passed to `image(...)`, and so on.

The function reference indicates which parameters are settable. Agents
working with Typst should consult the reference rather than guessing — the
language is consistent enough that the wrong guess often produces a confusing
error.

== Set-if rules

You can apply a set rule conditionally. This is occasionally useful inside
template functions.

```typ
#let critical_block(body, urgent: false) = {
  set text(fill: red) if urgent
  body
}
```

== The functions you will set most often

For document work, in rough order of importance:

- `page` — paper size, margins, header, footer, columns, numbering. See Part 8.
- `text` — font, size, weight, fill, language. See Part 10.
- `par` — justification, leading, first-line indent. See Part 10.
- `heading` — numbering pattern.
- `document` — PDF metadata (title, author, keywords).
- `enum`, `list`, `terms` — list bullet styles, numbering format.
- `table`, `figure` — global table/figure defaults.

If you find yourself wanting to set "everything", you are probably reaching
for a template — see Part 13.


// =============================================================================
// PART 7 — SHOW RULES
// =============================================================================

= Show rules

A show rule transforms an element. It is broader and more powerful than a
set rule. There are several flavours; learn them in this order.

== Show-set rule (the most common)

`show <selector>: set <function>(...)` reads as "for every element matching
the selector, apply this set rule". This is how you change the appearance of
*just* one kind of element.

```typ
#show heading: set text(font: "Libertinus Serif", weight: "bold")
#show heading.where(level: 1): set align(center)
#show heading.where(level: 2): set text(style: "italic")
```

The `where(...)` clause filters by element fields. Headings have a `level`
field, figures have `kind`, tables have any of their own settable fields. You
can stack `where` filters by AND-ing fields:
`heading.where(level: 1, numbering: "1.1")`.

== Transformational show rule (full control)

When show-set is not enough — when you need to wrap an element in extra
content, or replace it entirely — you write a show rule whose right-hand side
is a function.

```typ
#show heading.where(level: 1): it => [
  #v(2em)
  #align(center)[
    #text(size: 16pt, weight: "bold", upper(it.body))
  ]
  #v(0.5em)
  #line(length: 100%, stroke: 0.5pt)
  #v(0.5em)
]
```

The function receives `it`, the element being transformed. `it.body` is the
content; other fields depend on the element. For a heading: `it.level`,
`it.numbering`, `it.outlined`, `it.body`. For a figure: `it.body`, `it.caption`,
`it.kind`. For a table cell: `it.x`, `it.y`, `it.body`. The reference page for
each element lists its fields.

#callout("agent")[A common mistake: writing a show rule for headings that
forgets `it.numbering`. If you replace `it` with `it.body`, the heading number
disappears. To preserve numbering, write something like:
`it.numbering #h(0.5em) #it.body` (or use `counter(heading).display()`).]

== Selectors other than element functions

```typ
// Match a literal string. Every occurrence of "Buyer" gets bolded:
#show "Buyer": strong

// Match a regular expression:
#show regex("\d{4}-\d{2}-\d{2}"): match => emph(match.text)

// Match by label:
#show <urgent>: set text(fill: red)

// Match every element passing through (everything-show — see below):
#show: my_template
```

Show rules are checked in declaration order, with later rules overriding
earlier ones for matching elements.

== The everything-show rule (templating)

`show: function` (no selector) sends the entire rest of the document to a
function. This is the standard way to apply a template.

```typ
#let firm_letter(body) = {
  set page(paper: "a4", margin: (x: 2.5cm, top: 4cm, bottom: 3cm))
  set text(font: "Libertinus Serif", size: 11pt)
  set par(justify: true)
  // Letterhead at the top:
  align(center, text(size: 14pt, weight: "bold", "Doe & Doe Inc."))
  v(2cm)
  body
}

#show: firm_letter

Dear Ms Khumalo, ...
```

When you import a template from a separate file, you typically use `.with()`
to pre-supply named arguments, then pass the resulting partially-applied
function to `#show:`.

```typ
#import "firm_letter.typ": firm_letter

#show: firm_letter.with(
  matter: "Acme v. Beta",
  date: datetime.today(),
)

Dear Ms Khumalo, ...
```

Templates are covered in detail in Part 13.

== Replace, don't transform: literal right-hand side

The right-hand side of a show rule does not have to be a function. It can be
content (which replaces the element) or a string (which performs a
substitution).

```typ
#show "Acme Industries": "the Company"
#show "TBD": text(fill: red, weight: "bold")[TO BE DETERMINED]
```

This is fine for spot fixes but resist the urge to use it for important
substitutions in legal documents — defined-term replacement is better handled
with a `let` so the source is unambiguous about what value is in play.


// =============================================================================
// PART 8 — PAGE SETUP (DEEP DIVE)
// =============================================================================

= Page setup

Page setup is the foundation of any professional document. In Typst, almost
everything about how the page looks is controlled by the `page` element, which
you configure with `set page(...)`. This section walks through every aspect of
that configuration. It is the longest section of this reference; legal
documents live or die by their page setup.

== The `page` element at a glance

Every page has a width and height (or a paper size that determines them),
margins on all four sides, and an optional header, footer, background, and
foreground. The `page` element accepts these parameters:

- `paper` — a string naming a standard size: `"a4"`, `"a5"`, `"us-letter"`,
  `"us-legal"`, `"iso-b5"`, etc.
- `width`, `height` — explicit dimensions, overriding `paper`. Set either to
  `auto` to let the page grow to fit content (useful for one-pagers and
  posters; almost never useful for legal docs).
- `flipped` — `true` swaps width and height (landscape).
- `margin` — a length, or a dictionary; see below.
- `binding` — `left`, `right`, or `auto`. Affects the meaning of "inside" and
  "outside" margins.
- `columns` — an integer giving the number of equal-width columns.
- `fill` — a colour for the page background.
- `numbering` — a numbering pattern string for page numbers, or a function.
- `number-align` — where the page number sits.
- `header`, `footer` — content that appears in the top and bottom margins.
- `header-ascent`, `footer-descent` — the offset of header/footer from the
  edge of the body.
- `background`, `foreground` — content placed behind or over the page body
  (watermarks, stamps).

The `page` set rule is best placed at the very top of the document or in your
template. Changing it part-way through the document forces a page break onto
a new page that conforms to the new settings.

== Paper size

```typ
#set page(paper: "a4")              // default in Typst
#set page(paper: "us-letter")
#set page(paper: "us-legal")        // long document, US legal
#set page(paper: "a5", flipped: true)   // A5 landscape
```

Or specify dimensions directly:

```typ
#set page(width: 21cm, height: 29.7cm)
#set page(width: 5in, height: auto)     // page grows to fit content
```

== Margins

Margins are the second-most-important page setting after paper size. There
are four sides and several ways to specify them, listed from simplest to most
specific.

```typ
// One length: all four margins the same.
#set page(margin: 2.5cm)

// A dictionary with sides:
#set page(margin: (top: 3cm, bottom: 2cm, left: 2.5cm, right: 2.5cm))

// x and y as shortcuts:
#set page(margin: (x: 2.5cm, y: 3cm))

// Mixed: x takes care of left+right, individual keys override:
#set page(margin: (x: 2cm, top: 4cm, bottom: 2.5cm))

// `rest` fills any sides you have not named:
#set page(margin: (left: 1.5in, rest: 1in))
```

For two-sided documents (printed books, formal contracts bound at the spine),
you use `inside` and `outside` instead of `left` and `right`. The `binding`
parameter controls which is which:

```typ
// Bound on the left (English-language convention):
#set page(margin: (inside: 3cm, outside: 2cm, y: 2.5cm), binding: left)
```

On odd (right-hand) pages, `inside` is the left margin; on even (left-hand)
pages, `inside` is the right margin. The compiler keeps track of which side
of the binding each page is on.

== Headers and footers

`header` and `footer` accept content. Whatever you put there is rendered
in the top and bottom margin of every page.

```typ
#set page(
  header: [
    _Doe & Doe Inc._
    #h(1fr)
    Confidential
  ],
  footer: [
    #h(1fr)
    Page #context counter(page).display()
    #h(1fr)
  ],
)
```

`#h(1fr)` is a horizontal spacer that absorbs all available remaining space.
You use it to push things apart inside a header or footer (so two items end
up at left and right of the page).

The header is bottom-aligned by default (so it sits as close as possible to
the body without overlapping). The footer is top-aligned by default. To
override, wrap in `align`:

```typ
#set page(header: align(top, [Top of header]))
```

`header-ascent` and `footer-descent` control how far into the margin the
header and footer sit. The defaults are 30% of the respective margin. Adjust
when you have a tall header or want it tucked closer to the body.

== Page numbering — the easy way

The simplest page number is via the `numbering` parameter:

```typ
#set page(numbering: "1")           // 1, 2, 3, ...
#set page(numbering: "i")           // i, ii, iii, ...
#set page(numbering: "I")           // I, II, III, ...
#set page(numbering: "1 / 1")       // 1 / 12, 2 / 12, ... (current / total)
#set page(numbering: "Page 1 of 1") // Page 1 of 12, ...
#set page(numbering: "— 1 —")
```

The pattern is a string. Any character that is not interpreted as a number
template is rendered literally. Two number positions in the same string mean
"current page / total pages".

`number-align` controls placement. Default is `center + bottom`:

```typ
#set page(numbering: "1", number-align: right + bottom)
```

When you set both `numbering` and a custom `footer`, the custom footer wins
and the `numbering` parameter is ignored. To put the page number inside a
custom footer, see the next section.

== Page numbering — the powerful way (custom footer)

For anything beyond a bare number — page number left-aligned with the firm
name on the right, or "Page X of Y" with extra context — write a custom
footer that renders the page counter manually.

```typ
#set page(footer: context [
  *Doe & Doe Inc.*
  #h(1fr)
  Page #counter(page).display("1 of 1", both: true)
])
```

`context` here is required because the page number changes from page to page,
and Typst needs to know it must re-evaluate the footer in each page's
context. `counter(page).display(pattern, both: true)` displays the page
counter using the given pattern; `both: true` means "use the pattern's two
slots for current and total, not just current".

For a "first page differs" pattern (typical: title page has no header/footer,
all subsequent pages do), use `context` with a conditional:

```typ
#set page(header: context {
  if counter(page).get().first() > 1 [
    _Matter: Acme v. Beta_
    #h(1fr)
    File: 2026/03/441
  ]
})
```

`counter(page).get()` returns the current page counter as an array (because
counters can have multiple levels — see Part 12). For pages, it is always a
single-element array, so `.first()` extracts the actual page number.

== Resetting the page counter

Common in formal documents: the front matter (title page, table of contents,
preface) is paginated `i, ii, iii, ...` and the body is paginated `1, 2, 3, ...`
starting at 1.

```typ
#set page(numbering: "i")
#title-page-and-toc

// Switch to body numbering and reset the counter to 1:
#set page(numbering: "1")
#counter(page).update(1)

= Introduction
...
```

The `counter(page).update(1)` line creates an invisible "update" element. It
takes effect at the position where it sits in the document. Place it
*after* the `set page` change.

== Columns

`columns` on `set page(...)` puts the entire body into N equal columns,
gutter included.

```typ
#set page(columns: 2)
```

For a document where most of the body is two-column but the title and
abstract span both columns, use `place` with `scope: "parent"` and
`float: true` (see Part 9).

For columns inside a region of the document (rather than affecting the whole
page), call the `columns()` function as a wrapper:

```typ
#columns(2, gutter: 1.5em)[
  Body content here will be laid out in two columns,
  but the surrounding page is single-column.
]
```

Column gap is set with the `columns` element's set rule:

```typ
#set columns(gutter: 1.5em)
#set page(columns: 2)
```

For single-column legal work this is rarely relevant. It matters for
academic-style briefs and some pleadings.

== Background and foreground (watermarks, stamps)

`background` is content rendered behind every page. `foreground` is content
rendered on top.

```typ
// "DRAFT" watermark
#set page(background: rotate(-30deg, text(
  size: 80pt,
  fill: rgb(220, 220, 220),
  weight: "bold",
  "DRAFT",
)))

// A foreground stamp on the first page only — see Part 12 for context+counter.
```

For a watermark that appears on every page, `background` is what you want.
For a once-off stamp ("FILED 2026-04-30"), draw it as a foreground that
checks the page counter and renders nothing on other pages.

== Ad-hoc page overrides (a single landscape page mid-document)

You do not have to change global page settings to insert one differently-laid-out
page. Calling `page` as a function (not via `set page`) inserts new pages with
overrides for that call only:

```typ
// Body continues in normal A4 portrait...

#page(flipped: true, margin: 1cm)[
  = Schedule A — Asset register

  #table(
    columns: 6,
    ...
  )
]

// ...and after the call, we are back to the original page settings.
```

This is the standard pattern for inserting a wide table or a chart that
needs landscape orientation, then returning to portrait. The compiler creates
as many new pages as needed to fit the body, and reverts.

== Manual page breaks

```typ
#pagebreak()                           // hard break to a new page
#pagebreak(weak: true)                 // break unless we are already at the
                                       // top of a page
#pagebreak(to: "odd")                  // break until the next odd page
                                       // (e.g. so a chapter starts recto)
```

`weak: true` is what you usually want at the start of major sections in a
template — if the section happened to start fresh anyway, you do not insert a
blank page.


// =============================================================================
// PART 9 — LAYOUT AND ALIGNMENT (DEEP DIVE)
// =============================================================================

= Layout and alignment

Page setup gets the page itself right. Layout is what you do *inside* the
page: positioning paragraphs, side-by-side blocks, signatures, address blocks,
multi-column captions. This section covers the layout primitives and the
units they take.

== Length units

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(180),
  inset: 6pt,
  align: (left, left),
  [*Unit*], [*Meaning*],
  [`pt`], [Typographer's point. 72pt = 1 inch. The default unit for type sizes.],
  [`mm`, `cm`, `in`], [Physical units. Use for margins, page dimensions, and other things measured in the real world.],
  [`em`], [Multiple of the *current font size*. `1em` is one current font size; `1.2em` is 120% of it. Use for spacing tied to text size.],
  [`%`], [Percentage of the containing element. Use for widths within a parent: `width: 60%`.],
  [`fr`], [Fraction of remaining free space. Used in track sizes (grid columns, page columns) and in horizontal/vertical spacers (`#h(1fr)`, `#v(1fr)`). A `2fr` track gets twice the free space of a `1fr` track.],
)

The flexible-length system is what makes Typst layouts behave well across
paper sizes and font changes. Pin physical things in physical units, pin type
spacing in `em`, pin "fill the rest" in `fr`. This is a habit; cultivating it
makes templates portable.

== `align` — block-level alignment

`align(alignment, content)` aligns a block of content along one or both axes.

```typ
#align(center)[Centred line]
#align(right)[Right-aligned paragraph.]
#align(center + horizon)[Centred horizontally and vertically in its container.]
```

`set align(...)` applies to all subsequent content in the scope.

The available alignments:

- Horizontal: `left`, `right`, `center`, `start`, `end`. (`start` and `end`
  are language-aware: in left-to-right scripts, `start = left` and `end =
  right`. Prefer `start`/`end` in templates that may be used in RTL languages.)
- Vertical: `top`, `bottom`, `horizon` (vertical centre).
- Combined with `+`: `top + right`, `horizon + center`, etc.

== `block` and `box`

A *block* takes up the full width available, breaks lines, and forces a
paragraph break before and after. Most things in a document are blocks
(paragraphs, headings, figures).

A *box* is inline: it lays out content on the current line, does not force a
break, and reserves space for itself within the surrounding text flow.

```typ
// A block — its own paragraph:
#block(fill: luma(240), inset: 8pt, radius: 4pt, [
  Important notice.
])

// A box — sits inline:
This signatory: #box(stroke: 0.5pt, inset: 4pt, [#sig-name]) signed today.
```

Both accept `fill`, `stroke`, `inset` (interior padding), `outset` (exterior
overhang), `radius` (corner rounding), `width`, and `height`.

Boxes are how you keep things together that should not wrap to a new line —
useful for "Mr Smith", phone numbers, or clause labels you do not want
breaking across lines.

== `pad`

`pad` adds spacing around content without drawing any background or border.

```typ
#pad(left: 2cm, right: 2cm)[
  Indented quotation block.
]

#pad(x: 1cm, y: 0.5cm)[Padding shorthand: x is left+right, y is top+bottom.]
```

== `stack`

`stack` lays out a list of items along an axis, with optional spacing.

```typ
// Three items stacked vertically:
#stack(
  dir: ttb,            // top-to-bottom
  spacing: 1em,
  [First item],
  [Second item],
  [Third item],
)

// Two items stacked horizontally:
#stack(dir: ltr, spacing: 1cm,
  align(center)[Signature \ ____________ \ Buyer],
  align(center)[Signature \ ____________ \ Seller],
)
```

`dir` accepts `ttb`, `btt`, `ltr`, `rtl`. `spacing` is the default gap; you
can also pass explicit lengths *between* items in the argument list.

== `grid` — explicit row/column layout

`grid` is the workhorse for anything that wants explicit columns and rows.
It is what you use for a parties block, a signature row, a header with three
zones, or any layout where alignment between cells matters.

```typ
#grid(
  columns: (1fr, 1fr),
  column-gutter: 1em,
  row-gutter: 0.6em,

  [*Buyer*],          [*Seller*],
  [Acme Industries],  [Beta Holdings],
  [123 Main Road],    [456 Park Avenue],
  [Johannesburg],     [Cape Town],
)
```

Column sizes can be:

- `auto` — size to fit the cell's content
- A fixed length: `4cm`, `2in`
- A ratio: `30%`
- A fraction: `1fr`, `2fr`
- A mix: `(auto, 1fr, 4cm)`

Rows work the same. If you do not specify rows, Typst adds rows automatically
to fit all the cells you provide. Common shorthand for "five equal columns":
`columns: (1fr,) * 5` or `columns: 5 * (1fr,)`.

`align`, `fill`, and `stroke` accept the same forms as `table` (a value, an
array cycled per cell, or a function `(x, y) => ...`). See Part 11 for the
`table` deep-dive — `grid` and `table` share an API.

== `place` — escaping the flow

`place(alignment, content)` puts content at a specific location in the
parent container, and (by default) takes it out of the normal flow so that
surrounding content lays out as if it were not there.

```typ
// Drop a logo at the top-right corner of the page:
#place(top + right, dx: -1cm, dy: 1cm, image("logo.svg", width: 3cm))
```

The `dx` and `dy` parameters offset the placed content from the chosen
alignment.

`place` is also how you create a *spanning* element across columns. If your
document is two-column but you want the title and abstract to span both
columns, use `place` with `scope: "parent"` and `float: true`:

```typ
#set page(columns: 2)

#place(
  top + center,
  scope: "parent",      // span the whole page, not just the column
  float: true,          // reserve space at the top instead of overlapping
  clearance: 2em,       // space between the placed content and the body
)[
  #align(center, text(size: 16pt, weight: "bold")[Document Title])
]

This body text is two-column. Lorem ipsum dolor sit amet, ...
```

`float: true` is the difference between "place this on top of the body" and
"reserve space and let the body flow around it". For headings and titles, you
want `float: true`.

== `h` and `v` — horizontal and vertical spacers

```typ
#h(1cm)         // 1cm of horizontal space
#h(1fr)         // absorbs all remaining horizontal space
#v(2em)         // 2em of vertical space
#v(1fr)         // absorbs remaining vertical space (within a container)
```

The most common idiom is `#h(1fr)` inside a header, footer, or row to push
items apart:

```typ
[Left side #h(1fr) Right side]
// In a footer of width 16cm with no other content,
// "Left side" sits at the left and "Right side" at the right.
```

== `move`, `rotate`, `scale`

`move` shifts content visually without changing its layout footprint.
`rotate` and `scale` likewise affect appearance only by default; pass
`reflow: true` to make the rotation or scale affect surrounding layout.

```typ
#rotate(-90deg, reflow: true)[Rotated table or label]
```

Use these sparingly. They are useful for sideways labels in tables and
landscape elements in portrait pages.

== `hide` and `measure`

`hide(content)` reserves space for the content but does not draw it. Useful
for invisible alignment crutches.

`measure(content)` (called inside a `context` block) returns the laid-out
size of content as a dictionary `(width: ..., height: ...)`. Useful when you
need to know how big something is before deciding how to lay out around it.
Niche; you will rarely need it.


// =============================================================================
// PART 10 — TEXT AND PARAGRAPHS
// =============================================================================

= Text and paragraphs

The `text` and `par` functions control how text looks and how paragraphs
flow. Most documents need only a few set rules on each.

== `text` — the parameters that matter

```typ
#set text(
  font: "Libertinus Serif",     // font family (string or array for fallback)
  size: 11pt,                   // type size
  weight: "regular",            // "thin"..."black", or 100–900
  style: "normal",              // "normal", "italic", "oblique"
  fill: black,                  // colour
  tracking: 0pt,                // letter-spacing
  lang: "en",                   // ISO 639 language code; affects hyphenation
                                // and language-aware quotes
  region: "GB",                 // ISO 3166 region; refines language behaviour
)
```

`font` accepts a single string or an array of strings (a fallback list).
Always provide a fallback list when you target documents that may compile on
different machines, or when using uncommon fonts. Typst ships with several
fonts ("Libertinus Serif", "DejaVu Sans Mono", "New Computer Modern", and
others). For maximum portability across the web app and CLI, prefer those.

```typ
// Fallback list — first available is used:
#set text(font: ("Libertinus Serif", "Times New Roman", "Liberation Serif"))
```

Common subsets:

```typ
#text(weight: "bold")[bold]
#text(style: "italic")[italic]
#text(fill: rgb("#1a4d8c"))[brand colour]
#text(size: 9pt)[smaller text]
```

== `par` — the parameters that matter

```typ
#set par(
  justify: true,                // full-width justification
  leading: 0.65em,              // space between lines within a paragraph
  spacing: 1.2em,               // space between paragraphs
  first-line-indent: 1.5em,     // first-line indent (auto from second paragraph
                                // onwards by default; pass a dict to indent
                                // every paragraph)
  hanging-indent: 0pt,          // every line *except* the first is indented
                                // (used for bibliographies and definitions)
  linebreaks: auto,             // "simple" or "optimized"
)
```

For first-line-indent on *every* paragraph (not just consecutive ones), pass
a dictionary:

```typ
#set par(first-line-indent: (amount: 1.5em, all: true))
```

For tighter or looser line spacing, leading is the lever. The default is
font-dependent; `0.65em` is a good legal-document default.

If you want both first-line indent and a small inter-paragraph gap, you
typically reduce the gap to nearly zero so the indent does the work:

```typ
#set par(first-line-indent: 1.5em, leading: 0.65em, spacing: 0.65em)
```

#callout("gotcha")[The `par.first-line-indent` setting only applies to
*proper paragraphs* — text that is between paragraph breaks. It does not
apply to text inside table cells, captions, or many other inline contexts.
This is by design but it surprises agents and humans alike.]

== Smaller text utilities

```typ
#smallcaps[abc]            // small caps
#upper[abc]                // ABC
#lower[ABC]                // abc
#sub[2]                    // subscript
#super[2]                  // superscript
#strike[deleted]           // struck through
#underline[underlined]
#overline[overlined]
#highlight[yellow background]
```

== Smart quotes

By default, Typst replaces straight quotes with curly quotes appropriate to
the current language.

```typ
"hello"  →  “hello”      // in English
"hello"  →  „hello“      // in German
'apostrophe' is fine    →  ’apostrophe’ is fine
```

To turn this off (rare):

```typ
#set smartquote(enabled: false)
```


// =============================================================================
// PART 11 — DOCUMENT STRUCTURE FOR LEGAL DOCS
// =============================================================================

= Document structure for legal documents

This section covers the structural elements you will use for contracts,
opinions, briefs, and similar work: numbered headings beyond the simple
default, defined-term lists, footnotes, the table of contents, tables,
cross-references, and bibliography (when needed).

== Headings and clause numbering

For a contract using `1` / `1.1` / `1.1.1`:

```typ
#set heading(numbering: "1.1")
```

For a structure using `1` / `(a)` / `(i)` (common in opinions and some
contracts), the simplest path is a custom numbering function:

```typ
#set heading(numbering: (..nums) => {
  let levels = nums.pos()
  let formats = ("1.", "(a)", "(i)")
  let idx = levels.len() - 1
  if idx < formats.len() {
    numbering(formats.at(idx), levels.last())
  } else {
    numbering("1.", levels.last())
  }
})
```

The numbering function receives the levels as positional arguments. You decide
how to render them. The `numbering(pattern, ..nums)` global function applies
a pattern to a list of numbers and returns the rendered string.

For most legal work, the built-in `"1.1"` and `"1.a"` patterns are enough.

To suppress numbering on one heading, set `numbering: none` on that heading
explicitly:

```typ
#heading(numbering: none, level: 1)[Acknowledgements]
```

== Defined terms

The cleanest way to handle defined terms in a contract is a `let` for each
defined term and a single definitions section that uses a term list.

```typ
#let buyer = [the *Buyer*]
#let seller = [the *Seller*]
#let goods = [the *Goods*]

= Definitions and interpretation

/ Buyer: the party identified in clause 1.1 as the buyer of the Goods;
/ Seller: the party identified in clause 1.1 as the seller of the Goods;
/ Goods: the items listed in Schedule A.

= Sale and purchase

#buyer shall purchase #goods from #seller on the terms set out in this
agreement.
```

Two advantages over straight inline text: (i) renaming a defined term is one
edit to the `let`; (ii) the source is self-documenting about what is a
defined term and what is not.

For more aggressive usage (every appearance of "Buyer" in plain prose
auto-bolded) you can combine the `let` with a string show rule, but be
careful — string show rules can be heavy-handed. Prefer the explicit `let`
pattern.

== Cross-references

Label the heading or other element you want to reference, then cite the
label:

```typ
= Payment of the Purchase Price <clause-payment>

The Buyer shall pay the Purchase Price in accordance with @clause-payment.
```

By default, `@clause-payment` renders as the heading number ("3.2" or
similar). You can customise the form:

```typ
// Cite as page number instead:
#ref(<clause-payment>, form: "page")

// Use a custom supplement (e.g., "see clause 3.2"):
#ref(<clause-payment>, supplement: [see clause])
```

To customise globally how all heading references render, use a show rule on
`ref`. This is template-level work and rarely needs to be done case by case.

== Table of contents

```typ
#outline(
  title: [Contents],
  depth: 2,
  indent: auto,
)
```

Parameters:

- `title` — the heading shown above the outline. `auto` uses the language
  default ("Contents" in English). `none` omits it.
- `depth` — the deepest heading level to include.
- `indent` — `auto` aligns nested entries to their parent's body; a length
  indents by that length per level; a function customises the indent.
- `target` — what to outline. Default is `heading`; pass `figure.where(kind:
  table)` for a list of tables, `figure.where(kind: image)` for a list of
  figures.

A list of tables, then a list of images, after the main TOC:

```typ
#outline(title: [Contents])
#pagebreak()
#outline(title: [List of tables], target: figure.where(kind: table))
#outline(title: [List of figures], target: figure.where(kind: image))
```

To customise outline entries (e.g. tighter spacing for top-level items, dot
leaders, custom fill character), use show rules on `outline.entry`. A typical
pattern:

```typ
#show outline.entry.where(level: 1): set block(above: 1.2em)
#set outline.entry(fill: repeat[. ])
```

== Footnotes

```typ
The agreement was signed#footnote[on 12 March 2026, at the offices of Doe & Doe]
in Johannesburg.
```

The footnote marker appears in the body, the footnote text appears at the
bottom of the page. To customise the marker style, set the `footnote` element:

```typ
#set footnote(numbering: "1")        // default: 1, 2, 3, ...
#set footnote(numbering: "*")        // *, †, ‡, etc.
```

For footnotes that share a marker (the same footnote referenced from two
places), use a label:

```typ
The first reference#footnote(<note-1>)[The first definition.]
A later reference back to the same note: see footnote#footnote(<note-1>).
```

== Tables

The `table` function arranges content in cells. It is for *data*, not
layout. For layout, use `grid` (Part 9). The two share most of their API,
so this section covers `table`; everything also works for `grid` with
`grid.cell`, `grid.hline`, `grid.vline` substituted.

```typ
#table(
  columns: (1fr, auto, auto),
  align: (left, right, right),
  stroke: 0.5pt + luma(150),

  table.header(
    [*Item*], [*Quantity*], [*Price*],
  ),

  [Widget A], [10],  [R150.00],
  [Widget B], [5],   [R220.00],
  [Widget C], [25],  [R 80.00],
)
```

Column widths use the same vocabulary as `grid` columns. `stroke` accepts a
single stroke (applied to all cell borders), a dictionary `(top: ..., x: ...)`,
or a function `(x, y) => ...` for fully custom strokes.

Common patterns:

```typ
// Striped rows:
#set table(fill: (_, y) => if calc.odd(y) { luma(245) })

// No vertical strokes (a quiet, modern look):
#set table(stroke: (x: none))

// No strokes at all:
#set table(stroke: none)

// Bold header row:
#show table.cell.where(y: 0): strong
```

Spanning cells:

```typ
#table(
  columns: 3,
  table.cell(colspan: 3, align: center)[*Schedule of Payments*],
  [*Date*], [*Amount*], [*Note*],
  [2026-04-30], [R250 000], [Deposit],
  [2026-07-31], [R750 000], [Balance],
)
```

`table.cell` lets you override per-cell properties: `fill`, `stroke`, `align`,
`colspan`, `rowspan`. Use it inline in the argument list when you need it.

To break a long table across pages, wrap it in a `figure` and make the figure
breakable:

```typ
#show figure: set block(breakable: true)

#figure(
  caption: [Schedule of payments],
  table(
    columns: 3,
    table.header[Date][Amount][Note],
    ..rows
  ),
) <schedule-payments>
```

`table.header(...)` (and `table.footer(...)`) automatically repeat at the top
(or bottom) of every page the table spans across — exactly what you want for
a long schedule.

== Figures

A figure wraps content (an image, a table, a code block) and adds an optional
caption and a number that participates in the figure counter.

```typ
#figure(
  image("seal.png", width: 4cm),
  caption: [Official seal of the Court],
) <fig-seal>
```

To reference: `as shown in @fig-seal`.

For a figure containing a table, set the `kind`:

```typ
#figure(
  table(...),
  caption: [Asset register],
  kind: table,                     // counts in the table counter, not figure
) <table-assets>
```

This separates the numbering for tables and figures, and lets you produce a
"List of Tables" outline distinct from a "List of Figures".

== Bibliography

Rare in legal work but available. Typst's bibliography reads from a Hayagriva
YAML file or a BibLaTeX `.bib` file.

```typ
#bibliography("references.bib", style: "ieee")

In a recent case @smith2024, the court held ...
```

Citations use the same `@key` syntax as labels. Style strings accept built-in
CSL styles (over 80 are bundled) or a path to a custom CSL file.


// =============================================================================
// PART 12 — INTROSPECTION (CONTEXT, COUNTERS, STATE, QUERY)
// =============================================================================

= Introspection: context, counters, state, query

You will not use these every day, but when you need to do something
"reactive" — a header that shows the current section's title, a "Page X of
Y" footer that knows the total, a watermark that appears only on draft
versions — these are the tools.

== Why context exists

In normal Typst code, an expression returns a single value. But many things
in a document are *position-dependent*: the page number changes from page
to page, the current heading changes from section to section. Code that
reads "the current page number" at the top of the file cannot have a single
answer; the answer depends on where the code is evaluated.

Typst handles this with `context`. A `context` block defers its evaluation
until the surrounding layout knows where the block is sitting, and then
evaluates with that location in scope.

```typ
This page is page #context counter(page).get().first().
```

Inside the `context` expression, you have access to introspection functions
that need to know "where am I": `counter(...).get()`, `counter(...).at(...)`,
`locate(...)`, `query(...)`, and `here()`.

== Counters

A counter is a named integer (or array of integers, for multi-level counters
like the heading counter) that you can read, increment, or set throughout
the document.

Built-in counters: `counter(page)`, `counter(heading)`, `counter(figure)`,
`counter(footnote)`, etc. Custom counters: `counter("my-name")`.

```typ
// Read a counter (must be inside context):
#context counter(page).get()         // returns an array, e.g. (12,)
#context counter(heading).get()      // (3, 2) for section 3.2

// Update a counter:
#counter(page).update(1)             // reset to 1
#counter(page).update(n => n + 5)    // add 5

// Step by one:
#counter("my-name").step()

// Display the current counter using a numbering pattern:
#context counter(heading).display("1.1")
```

The `update` and `step` calls produce *invisible content* that takes effect
at the position they sit in the document. Storing them in a variable and
forgetting to insert the variable means the update never happens.

== Common counter recipes

"Page X of Y" in a footer:

```typ
#set page(footer: context [
  #h(1fr)
  Page #counter(page).get().first()
  of #counter(page).final().first()
  #h(1fr)
])
```

Reset the page counter for the body of a document (after a roman-numeralled
front matter):

```typ
#set page(numbering: "i")
#title-and-toc-content

#set page(numbering: "1")
#counter(page).update(1)
```

A "draft revision" counter that increments at marked points:

```typ
#let revision = counter("revision")
#revision.update(1)

This is revision #context revision.get().first().
```

== State

State is like a counter but holds an arbitrary value, not just an integer.
You use it when you need to track something that varies through the document
beyond a number — for example, the current chapter title for the running
header.

```typ
#let chapter-title = state("chapter-title", "")

// Mark a chapter:
= Introduction
#chapter-title.update("Introduction")

// Display the current value (must be in context):
Currently in #context chapter-title.get().
```

For most legal-document needs, counters are enough; state is the more general
tool you reach for when you outgrow them.

== `query` and `locate`

`query(selector)` (in a context block) returns all elements in the document
matching the selector. `locate(selector)` returns the location of a unique
match. These let you build outlines of figures, current-section headers,
and other "the document looking at itself" patterns.

```typ
// Header that shows the title of the most recent level-1 heading:
#set page(header: context {
  let headings = query(heading.where(level: 1))
  let current-page = here().page()
  let current = headings.find(h => h.location().page() <= current-page)
  if current != none [
    _#current.body_  #h(1fr)  Doe & Doe Inc.
  ]
})
```

`here()` gives you the current location. `.page()` extracts the page number.
`.location()` on an element gives you its location.

#callout("agent")[Most agents reach for `query` and `locate` too eagerly.
Before writing one, check whether a counter or a label suffices. Heavy
use of `query` slows compilation and can cause "layout did not converge"
warnings if your queries depend on themselves.]

== Metadata

`metadata(value) <label>` exposes a value to `query` without producing
visible content. Useful for "data" you want to attach to your document and
look up programmatically — for instance, a draft version number, a matter
reference, or a sign-off date.

```typ
#metadata("2026-04-30") <draft-date>

// Elsewhere, in context:
#context query(<draft-date>).first().value
```


// =============================================================================
// PART 13 — TEMPLATES
// =============================================================================

= Building templates

A template in Typst is just a function that wraps the document. You write
the function, expose its parameters, and apply it via the everything-show
rule. There is no special template syntax. This makes templates trivial to
read, modify, and version.

== The basic shape

```typ
#let firm_letter(
  // Named parameters with sensible defaults:
  matter: "",
  date: datetime.today(),
  ref: "",
  letterhead: "Doe & Doe Inc.",
  // The document body comes last as a positional parameter:
  doc,
) = {
  // 1. Set rules that apply to the whole document.
  set page(
    paper: "a4",
    margin: (x: 2.5cm, top: 4.5cm, bottom: 3cm),
    header: align(center, text(size: 14pt, weight: "bold", letterhead)),
  )
  set text(font: "Libertinus Serif", size: 11pt)
  set par(justify: true, leading: 0.65em)

  // 2. Show rules — sometimes.
  show heading: set text(weight: "bold")

  // 3. Any pre-body content (date, reference, salutation block).
  align(right, [#date.display("[day] [month repr:long] [year]")])
  v(1em)
  if matter != "" [Matter: *#matter* \ ]
  if ref != "" [Our ref: #ref \ ]
  v(1em)

  // 4. The body.
  doc

  // 5. Optionally, post-body content (signoff, signature blocks).
}
```

To use:

```typ
#show: firm_letter.with(
  matter: "Acme Industries v. Beta Holdings",
  ref: "DD/2026/441",
)

Dear Ms Khumalo,

Further to our telephone conversation of yesterday, ...

Yours sincerely,

#sig_block("J. Doe")
```

The everything-show rule passes the rest of the document to `firm_letter`.
`.with(matter: ..., ref: ...)` pre-supplies those parameters, leaving the
body parameter (`doc`) to be filled by Typst with whatever comes after the
show rule.

== Splitting the template into its own file

For real use, put the template in its own file:

```typ
// firm_letter.typ
#let firm_letter(
  matter: "",
  date: datetime.today(),
  letterhead: "Doe & Doe Inc.",
  doc,
) = {
  // ... as above
}

// In the document file:
#import "firm_letter.typ": firm_letter

#show: firm_letter.with(matter: "Acme v. Beta")

Dear Ms Khumalo, ...
```

== Local packages (`@local`)

When you have a template — or several — that you want to use across multiple
projects without copying files, publish it as a local package. The mechanics
differ slightly between operating systems, but the principle is the same:

1. Decide on a package name and version, e.g. `firm_templates:0.1.0`.
2. Create a directory under your local data directory at the path
   `typst/packages/local/firm_templates/0.1.0/`.
3. Inside that directory, put a `typst.toml` manifest describing the package
   and a `lib.typ` containing your `let` definitions.
4. Import in any document with `#import "@local/firm_templates:0.1.0":
   firm_letter`.

Sample `typst.toml`:

```toml
[package]
name = "firm_templates"
version = "0.1.0"
entrypoint = "lib.typ"
authors = ["Doe & Doe Inc."]
license = "MIT-0"
description = "Internal letter and contract templates."
```

Sample `lib.typ`:

```typ
#let firm_letter(matter: "", doc) = {
  set page(...)
  set text(...)
  doc
}

#let memorandum(to: "", from: "", re: "", doc) = {
  // ...
}
```

For the exact data-directory paths on Windows, macOS, and Linux, consult
the Typst package documentation. On most setups it sits at:

- Windows: `%APPDATA%\typst\packages\local\<name>\<version>\`
- macOS: `~/Library/Application Support/typst/packages/local/<name>/<version>/`
- Linux: `~/.local/share/typst/packages/local/<name>/<version>/`

== Template parameters that scale

A few patterns make templates much more useful:

*Pass an array of parties, not individual parameters.* Your template should
accept `parties: ()` and decide layout based on `parties.len()`. The earlier
two-author conference paper template is a good model.

```typ
#let contract(
  parties: (),
  effective-date: datetime.today(),
  doc,
) = {
  set page(...)
  ...
  // Lay out the parties block:
  let count = parties.len()
  let cols = calc.min(count, 2)
  grid(
    columns: (1fr,) * cols,
    column-gutter: 1em,
    ..parties.map(p => [
      *#p.name* \
      #p.role \
      Registration: #p.reg-no \
      Address: #p.address
    ])
  )
  doc
}
```

*Provide sensible defaults so the minimal call works.* Lawyers should be
able to apply your template with `#show: contract` and have a usable
document, then add detail as needed.

*Document the parameters in source comments.* Future you (and any agent
revisiting the file) will thank you.

== Anti-pattern: deep show-rule chains in templates

It is tempting to have a template with twenty show rules that style every
element. This works, but it makes the template fragile — overriding any one
rule from the user's document is awkward, and one rule's effect can hide
another's.

Better: keep templates focused on the rules that *must* be in place
(page setup, default text, and a handful of show-set rules for headings).
Give the user clear extension points (named parameters, content slots) for
the rest.


// =============================================================================
// PART 14 — MENTIONED IN PASSING
// =============================================================================

= Mentioned in passing: math, drawing, code, plugins

These exist; you will rarely need them for legal work. Brief notes so an
agent does not invent the wrong syntax when the rare need arises.

== Math mode

`$ ... $` for inline math, `$ ... $` with surrounding spaces for display
math. Single letters render as variables; multi-letter sequences resolve to
named variables, function calls, or symbol names. To render literal text,
use double quotes: `$"interest" = P r t$`.

For typical legal work — a percentage calculation, a few formulae in a
schedule — math mode is overkill; just write `R125 000 \u{00d7} 12% = R15
000` in plain markup.

== Drawing primitives

`rect`, `square`, `circle`, `ellipse`, `line`, `path`, `curve`, `polygon`.
For complex diagrams there is a community package `cetz` (Cause-Effect Typst,
similar to TikZ for LaTeX). For a stamp box on a contract, `rect(stroke:
1pt, inset: 8pt)[Initial here]` is enough.

== Code blocks (showing source)

`raw` is the function; backticks are the syntax.

````typ
Inline: `print("hello")`

Block with language tag for syntax highlighting:
```python
def hello(name):
    return f"Hello, {name}"
```
````

For legal documents, code blocks are rare except in technology-related
schedules and exhibits.

== WebAssembly plugins

Typst supports loading WASM modules as plugins. This is a power-user feature
for things like custom barcode generation or exotic data processing. You will
not need it; if a problem ever calls for a plugin, the agent should flag the
fact rather than reach for it lightly.


// =============================================================================
// PART 15 — COOKBOOK (LEGAL-DOCUMENT-FLAVOURED)
// =============================================================================

= Cookbook

Working examples of the patterns you will hit most often. These are
*starting points*, not finished templates — adapt margins, fonts, and
wording to your firm's house style.

== A simple letter

```typ
#set page(paper: "a4", margin: (x: 2.5cm, top: 3cm, bottom: 2.5cm))
#set text(font: "Libertinus Serif", size: 11pt)
#set par(justify: true, leading: 0.65em)

#align(right, [#datetime.today().display("[day] [month repr:long] [year]")])

#v(1em)

Acme Industries (Pty) Ltd \
Attention: The Managing Director \
123 Main Road \
Johannesburg, 2196

#v(1em)

Dear Sir / Madam,

#v(0.5em)

#align(center, text(weight: "bold")[Re: Sale of immovable property])

#v(0.5em)

We act for the Buyer in the abovementioned matter. Further to our previous
correspondence, we confirm that ...

#v(2em)

Yours faithfully,

#v(2cm)

#line(length: 6cm) \
Doe & Doe Inc.
```

== A "Page X of Y" footer

```typ
#set page(footer: context [
  #h(1fr)
  Page #counter(page).get().first() of #counter(page).final().first()
  #h(1fr)
])
```

== A "DRAFT" watermark

```typ
#set page(background: rotate(-30deg, text(
  size: 100pt,
  fill: rgb(220, 220, 220),
  weight: "bold",
  "DRAFT",
)))
```

To make the watermark conditional on a flag — so the same source compiles to
both a draft and a final version — wrap the call:

```typ
#let draft = true

#set page(
  background: if draft {
    rotate(-30deg, text(size: 100pt, fill: rgb(220, 220, 220), weight: "bold", "DRAFT"))
  } else { none }
)
```

== A first-page-different layout

The title page has no header and no footer; subsequent pages have both.

```typ
#set page(
  header: context {
    if counter(page).get().first() > 1 [
      _Matter: Acme v. Beta_  #h(1fr)  File: 2026/03/441
    ]
  },
  footer: context {
    if counter(page).get().first() > 1 [
      #h(1fr)
      Page #counter(page).get().first()
      #h(1fr)
    ]
  },
)
```

== A two-sided contract with binding

```typ
#set page(
  paper: "a4",
  margin: (inside: 3cm, outside: 2cm, y: 2.5cm),
  binding: left,                    // bound on the left for English
)
```

On odd-numbered (recto) pages the left margin is wide; on even-numbered
(verso) pages the right margin is wide. Set this once at the top of the
document.

== A schedule on a landscape page

```typ
// Body of contract continues...

#page(flipped: true, margin: 1.5cm)[
  = Schedule A — Asset register

  #table(
    columns: 6,
    align: (left, left, right, right, right, left),
    table.header[Asset ID][Description][Original cost][Current value][Depreciation][Notes],

    [A-001], [Office furniture], [R 45 000], [R 22 000], [R 23 000], [Headquarters],
    [A-002], [Computer hardware], [R 120 000], [R 60 000], [R 60 000], [All offices],
    // ...
  )
]

// Body resumes in portrait orientation.
```

== A signature block

A two-party signature row using `grid`:

```typ
#v(2cm)

#grid(
  columns: (1fr, 1fr),
  column-gutter: 2cm,
  row-gutter: 0.6em,

  [#line(length: 100%) \ Buyer \ Date:],
  [#line(length: 100%) \ Seller \ Date:],
)
```

For a witnessed signature with extra fields:

```typ
#grid(
  columns: (1fr, 1fr),
  column-gutter: 2cm,
  row-gutter: 1.5em,

  [
    Signed at #line(length: 4cm) on the \
    #line(length: 1cm) day of #line(length: 4cm) 20#line(length: 1cm)
  ],
  [
    Witness 1: #line(length: 6cm) \
    Witness 2: #line(length: 6cm)
  ],

  // ...
)
```

== A definitions section

```typ
= Definitions and interpretation

In this Agreement, unless the context otherwise indicates:

/ Agreement: this written agreement and all of its schedules and annexures;
/ Buyer: the party identified in clause #ref(<parties>) as the buyer;
/ Effective Date: the date on which the last party signs this Agreement;
/ Goods: the items more fully described in Schedule A;
/ Purchase Price: the amount set out in clause #ref(<price>), exclusive of VAT;
/ Seller: the party identified in clause #ref(<parties>) as the seller;
/ VAT: value-added tax levied in terms of the Value-Added Tax Act, 89 of 1991.
```

== A clause-numbered contract structure

```typ
#set heading(numbering: "1.1")

#show heading.where(level: 1): it => block(above: 1.5em, below: 0.8em)[
  #set text(size: 12pt, weight: "bold")
  #upper(it)
]

= Parties <parties>
1.1. The parties to this Agreement are: ...

= Definitions and interpretation
2.1. In this Agreement: ...

= Sale and purchase <price>
3.1. The Seller hereby sells to the Buyer ...
3.2. The Purchase Price is ...

= Payment <clause-payment>
The Buyer shall pay the Purchase Price as set out in @price.
```

== A title page with a logo

```typ
#page(numbering: none, header: none, footer: none)[
  #v(1fr)

  #align(center)[
    #image("firm_logo.svg", width: 6cm)

    #v(2cm)

    #text(size: 22pt, weight: "bold")[Sale of Business Agreement]

    #v(1em)

    #text(size: 14pt, style: "italic")[
      between
    ]

    #v(0.5em)

    #text(size: 14pt, weight: "bold")[Acme Industries (Pty) Ltd]

    #v(0.5em)

    #text(size: 14pt, style: "italic")[and]

    #v(0.5em)

    #text(size: 14pt, weight: "bold")[Beta Holdings (Pty) Ltd]
  ]

  #v(1fr)

  #align(center, text(size: 11pt)[Effective date: 30 April 2026])

  #v(1em)
]

#counter(page).update(1)
#set page(numbering: "1")

= Definitions
...
```

== A memorandum

```typ
#set page(paper: "a4", margin: (x: 2.5cm, y: 3cm))
#set text(font: "Libertinus Serif", size: 11pt)

#align(center, text(size: 14pt, weight: "bold")[MEMORANDUM])

#v(1em)

#grid(
  columns: (auto, 1fr),
  column-gutter: 1em,
  row-gutter: 0.6em,

  [*To:*],     [Senior Partner],
  [*From:*],   [Junior Counsel],
  [*Date:*],   [#datetime.today().display("[day] [month repr:long] [year]")],
  [*Re:*],     [Liability of directors under section 22 of the Companies Act],
  [*Privileged & Confidential*], [],
)

#v(1em)
#line(length: 100%, stroke: 0.5pt)
#v(1em)

= Question presented

Whether ...

= Brief answer

In short, ...

= Discussion

== Statutory framework

...
```


// =============================================================================
// PART 16 — GOTCHAS
// =============================================================================

= Gotchas and surprises

Things that surprise both humans and agents the first time they hit them.
Each of these has cost someone hours; learn from those hours.

== Empty parens vs empty brackets

`#title()` calls `title` with no arguments. `#title[]` calls `title` with one
argument: an empty content block. These are not the same. The first asks
"what's the document title?"; the second sets the title to nothing. The bug
is silent.

== Set rule scoping

A set rule applies until the end of the *current scope*, not the end of the
file unconditionally. Inside a content block, a code block, or a function
body, set rules are local. This is usually what you want, but it bites when
you write a template function and forget that set rules inside it stay in
scope only inside the function — until you remember that the function's body
is the rest of the document (because of the everything-show pattern), so the
set rules effectively persist anyway. The interaction is consistent once
you internalise it; until then it confuses.

== Layout convergence

Typst lays out the document multiple times to resolve interactions between
counters, queries, and content. If your code creates a feedback loop —
"this query depends on the result of itself" — Typst gives up after five
attempts and emits "layout did not converge within 5 attempts". When you see
this, look for a `query` or `state.update` whose result feeds back into
something that affects the same query.

== `par` does not control everything that looks like a paragraph

`par.first-line-indent` and `par.hanging-indent` apply to *semantic
paragraphs* — text between paragraph breaks at the document level. Text
inside table cells, captions, list items, and many other inline contexts
does not get these treatments. This is by design, but it surprises agents
who expect "all paragraphs everywhere" to mean exactly that.

== Order of show rules matters

Show rules are checked in declaration order, with later rules taking
precedence on matches. Two show rules that affect the same element can
shadow each other in subtle ways. When debugging unexpected styling, comment
out show rules in pairs and re-enable them one at a time.

== `auto` vs `none`

`auto` means "you (Typst) pick a sensible value". `none` means "explicitly
nothing". They are not interchangeable. `header: auto` keeps the default
header (which by default shows the page number if numbering is set);
`header: none` removes the header entirely. Read function docs to know which
is which.

== Single-element arrays

`(5)` is an integer in parentheses; `(5,)` is an array of one element. The
trailing comma matters. Most of the time the parser figures out what you
meant, but in places where an array is explicitly required and a single
value is also accepted with different meaning, the comma changes behaviour.
When in doubt, use the comma.

== Package paths from inside a package

A package can only read files from inside its own directory. If your
template needs an image from the user's project, the user has to pass the
already-loaded image as a parameter:

```typ
// In the user's document:
#show: contract.with(seal: image("seal.png"))

// In the template (inside the package):
#let contract(seal: none, doc) = {
  if seal != none [#seal]
  ...
}
```

== `context` is not a free pass

Wrapping something in `context` lets you read counters and locations, but
the wrapped expression evaluates separately for each context it lands in.
This can be expensive. If you find yourself wrapping the entire document
in `context`, you are doing it wrong; reach for state, counters, or
labels first.


// =============================================================================
// PART 17 — WHERE TO LOOK THINGS UP
// =============================================================================

= Where to look things up

This reference is not exhaustive. Typst is a large system and the official
documentation is very good. When you (or an agent) need to know something
not covered here, the canonical references are:

- *The official tutorial*: typst.app/docs/tutorial/. Four short chapters.
  Read once.
- *The function reference*: typst.app/docs/reference/. Every element and
  every function with all parameters and short examples. The single most
  useful thing for an agent is to consult the relevant reference page
  before guessing parameter names.
- *The layout category* (typst.app/docs/reference/layout/) is where `page`,
  `align`, `block`, `box`, `grid`, `place`, `columns`, `pad`, `stack`, `h`,
  `v`, `pagebreak` live. Page setup and layout questions almost all answer
  here.
- *The model category* (typst.app/docs/reference/model/) is where `heading`,
  `figure`, `table`, `outline`, `enum`, `list`, `terms`, `bibliography`,
  `cite`, `ref`, `footnote`, `par`, `quote`, `document` live. Document
  structure questions answer here.
- *Typst Universe* (typst.app/universe/) is the package gallery. Search for
  packages by category or keyword. Always pin a specific version.
- *The Typst Forum* (forum.typst.app) and *Discord*. Real questions and
  real answers, often from the core team.

For agent workflows, the heuristic is:

1. If it is a question about syntax — what does this mean — answer from
   memory or this reference.
2. If it is a question about a parameter — what does `text` accept —
   consult the function reference page.
3. If it is "is there a package for X" — search Typst Universe.
4. If it is "the document is doing something I don't expect" — narrow it
   down by commenting out set and show rules until the unexpected behaviour
   disappears, then read the reference for the rule that turned out to
   matter.

This reference is intended to last; the language is stable but evolving.
When a reader encounters something here that no longer matches the official
docs, the official docs are right.


// =============================================================================
// END OF REFERENCE
// =============================================================================

// Closing notes for any agent reading this file:
//
// - Treat this file as read-only. If you need to extend the Praxis system of
//   work, add new files (firm_letter.typ, contract_template.typ, etc.) and
//   reference them by import.
// - Pin every package version you import. Document why.
// - Comment your code. Future readers — including yourself — will thank you.
