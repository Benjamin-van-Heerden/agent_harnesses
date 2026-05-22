= Typst Agent Brief

Condensed Typst reference for agents working in the Praxis system of work. Targets Typst 0.13 / 0.14. Older patterns (`#locate`, `#style`, `counter.display` without `context`) are deprecated — do not use them.


== Mental model

Three modes: markup (default), code (entered with `#`), math (`$...$`).

Content is a value. `[some markup]` is a `content` value: storable in variables, passable to functions, concatenable with `+`. Strings (`"..."`) are not content; they are plain character sequences. Functions that want a path, font name, or numbering pattern take strings. Functions that want document material take content.

In markup, `#` switches to code mode for one expression. In code mode (inside argument lists, `let` RHS, code blocks `{}`), no `#` is needed for code; use `[...]` to dip back into markup.

```typ
#text(font: "Inria Serif")[important]
```

Inside the parens, `"Inria Serif"` is already code — no `#` on it. Inside the `[...]`, you are back in markup.


== Syntax cheat sheet

```typ
= / == / ===           // heading levels (one space after the = required)
*bold*                 // works at word boundaries; else use #strong[]
_italic_               // else #emph[]
- / + / / Term: ...    // bullet / numbered / term list
`inline code`
```lang ... ```        // raw block with syntax highlighting
<label>                // attach label to preceding element
@label                 // reference a label
#func(arg)[body]       // function call: positional, named, content
#(1 + 2)               // parenthesized expression in markup
\#  \$  \*  \[         // escape literal special characters
\u{2014}               // Unicode codepoint (em dash)
//  /* */              // line / block comments
```


== Data types

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(180),
  inset: 6pt,
  align: (left, left),
  [`str`], [`"text"`],
  [`content`], [`[text with *markup*]`],
  [`int` / `float`], [`42` / `3.14`. Underscores allowed: `1_500_000`],
  [`bool`], [`true` / `false`],
  [`length`], [`12pt`, `2.5cm`, `1in`, `1.2em`, `50%`, `1fr`],
  [`color`], [`red`, `luma(80)`, `rgb("#1a4d8c")`, `cmyk(...)`],
  [`alignment`], [`left`, `right`, `center`, `top`, `bottom`, `horizon`, `start`, `end`. Combine with `+`.],
  [`array`], [`(1, 2, 3)`. One-element: `(1,)` — trailing comma matters.],
  [`dictionary`], [`(key: "value")`],
  [`datetime`], [`datetime(year: 2026, month: 4, day: 30)`],
  [`function`], [`text`, `image`, your own `#let f(x) = x + 1`],
  [`none`], [Explicit absence.],
  [`auto`], [Smart default — let Typst pick.],
)

`none` and `auto` are not interchangeable. `header: auto` keeps the default; `header: none` removes it entirely. Read the function ref to know which to pass.


== Length units — when to use which

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(180),
  inset: 6pt,
  align: (left, left),
  [`pt` `mm` `cm` `in`], [Physical units — page dimensions, margins, drawing.],
  [`em`], [Relative to current font size — text-related spacing.],
  [`%`], [Relative to parent — widths within containers.],
  [`fr`], [Fraction of remaining free space — track sizes, `h(1fr)` spacers.],
)

Habit: physical things in physical units, type spacing in `em`, "fill rest" in `fr`. Templates that follow this rule survive font changes and paper-size changes without manual fixup.


== Styling: the one thing to internalise

*Set rule* — change default parameters of a function for the rest of scope.

```typ
#set text(font: "Libertinus Serif", size: 11pt)
#set page(margin: 2.5cm)
#set par(justify: true, leading: 0.65em)
```

*Show-set rule* — apply a set rule only to elements matching a selector.

```typ
#show heading: set text(weight: "bold")
#show heading.where(level: 1): set align(center)
```

*Transformational show rule* — replace or wrap an element with arbitrary content.

```typ
#show heading: it => [
  #v(1em) #upper(it.body)
  #if it.numbering != none [ #counter(heading).display(it.numbering)]
]
```

*Everything-show* (templating) — pass the rest of the document to a function.

```typ
#show: my_template
#show: my_template.with(matter: "Acme v Beta")  // pre-supply named args
```

*Literal replacement* — a string or content RHS substitutes directly.

```typ
#show "TBD": text(fill: red, weight: "bold")[TO BE DETERMINED]
```

Set rules apply to the *end of scope* (block, file, function body). Inside a content block they are local. This is consistent but confuses templates.

Show rules apply in *declaration order*, later rules taking precedence on matches. When debugging styling, comment out show rules and re-enable one at a time.

Selectors: element function (`heading`), `element.where(field: value)`, `"literal string"`, `regex("...")`, `<label>`.


== Common set targets

```typ
#set page(
  paper: "a4",                          // or "us-letter", "a5", "iso-b5", ...
  margin: (x: 2.5cm, y: 3cm),           // dict; also: top, bottom, left, right,
                                        //   inside, outside, rest
  numbering: "1",                       // "1", "i", "I", "1 / 1", "Page 1 of 1"
  number-align: center + bottom,
  // header / footer: see Page patterns
)

#set text(
  font: ("Libertinus Serif", "Times New Roman"),  // fallback list
  size: 11pt,
  weight: "regular",                    // "thin"..."black" or 100..900
  style: "normal",                      // "normal" / "italic" / "oblique"
  fill: black,
  lang: "en",                           // affects hyphenation, smart quotes
  region: "GB",
)

#set par(
  justify: true,
  leading: 0.65em,                      // line-to-line within a paragraph
  spacing: 1.05em,                      // paragraph-to-paragraph
  first-line-indent: 0pt,               // pass (amount: 1.5em, all: true) for
                                        //   indent on EVERY paragraph
  hanging-indent: 0pt,
)

#set heading(numbering: "1.1")          // "1.1", "1.a.i", "I.", or a function
```

*Gotcha.* `par.first-line-indent` and `hanging-indent` apply only to *semantic paragraphs* — text between paragraph breaks at the document level. They do not apply inside table cells, captions, list items, or many other inline contexts. This is by design.


== Page patterns

=== Custom header or footer with content

```typ
#set page(header: [
  _Matter: Acme v Beta_  #h(1fr)  File: 2026/03/441
])
```

`h(1fr)` absorbs all remaining horizontal space — use it to push items apart. The header is bottom-aligned by default; wrap in `align(top, ...)` to override.

=== First-page-different (no header on title page)

```typ
#set page(header: context {
  if counter(page).get().first() > 1 [
    _Matter: Acme v Beta_ #h(1fr) File: 2026/03/441
  ]
})
```

`counter(page).get()` returns an array (counters can be multi-level); `.first()` extracts the page number. `context` is required because the value changes per page — the header must be re-evaluated per page.

=== Page X of Y in a custom footer

```typ
#set page(footer: context [
  #h(1fr)
  Page #counter(page).get().first() of #counter(page).final().first()
  #h(1fr)
])
```

When you set a custom footer, the `page` element's `numbering` parameter is *ignored*. Render the page counter manually as above.

=== Reset page counter (front matter to body)

```typ
#set page(numbering: "i")
// title page, TOC, etc.

#set page(numbering: "1")
#counter(page).update(1)                  // resets to 1
```

`counter().update()` emits invisible content that takes effect at its position in the document. Storing the call in a `let` and forgetting to insert the variable means the update never fires.

=== Watermark on every page

```typ
#set page(background: rotate(-30deg, text(
  size: 100pt, fill: rgb(220, 220, 220), weight: "bold", "DRAFT"
)))
```

`background` and `foreground` take content. `background` goes behind the body; `foreground` over it.

=== One-off page override

For a single landscape page mid-document, call `page` as a function (not via `#set page`) — overrides apply only to that call and revert afterwards.

```typ
#page(flipped: true, margin: 1.5cm)[
  = Schedule A
  #table(...)
]
```

=== Two-sided binding

```typ
#set page(margin: (inside: 3cm, outside: 2cm, y: 2.5cm), binding: left)
```

On odd (recto) pages, `inside` is the left margin; on even (verso) pages, `inside` is the right margin.

=== Manual page break

```typ
#pagebreak()                              // hard break
#pagebreak(weak: true)                    // break only if not already on a fresh page
#pagebreak(to: "odd")                     // break until next odd page
```


== Layout primitives

=== `align` — block-level alignment

```typ
#align(center)[Centred]
#align(top + right)[Corner]
#set align(center)                        // applies to scope
```

Horizontal: `left`, `right`, `center`, `start`, `end` (start/end are RTL-aware). Vertical: `top`, `bottom`, `horizon` (vertical centre).

=== `block` vs `box`

`block` is full-width and paragraph-breaking — most things in a document are blocks. `box` is inline; it does not break and reserves space within text flow. Both accept `fill`, `stroke`, `inset`, `outset`, `radius`, `width`, `height`. Use `box` for things that must not wrap (names, phone numbers, "Mr Smith").

=== `pad` — spacing without decoration

```typ
#pad(left: 2cm, right: 2cm)[Indented quote]
#pad(x: 1cm, y: 0.5cm)[All-around shorthand]
```

=== `stack` — items along an axis

```typ
#stack(dir: ttb, spacing: 1em, [a], [b], [c])
#stack(dir: ltr, spacing: 1cm, sig-a, sig-b)
```

=== `grid` — explicit columns and rows (workhorse for layout)

```typ
#grid(
  columns: (1fr, 1fr),                    // or (auto, 1fr, 4cm); 5*(1fr,)
  column-gutter: 1em,
  row-gutter: 0.6em,
  align: (left, right),                   // or (x, y) => alignment
  fill: (_, y) => if calc.odd(y) { luma(245) },
  [Buyer], [Seller],
  [Acme],  [Beta],
)
```

Column and row sizes: `auto` (fits), length, ratio (`%`), fraction (`fr`), or array. Shorthand for N equal columns: `columns: (1fr,) * 5`.

`grid` is for *layout*. `table` is for *data*. Same API, different semantic intent — agents and screen readers treat them differently.

=== `place` — escape the flow, span beyond columns

```typ
#place(top + right, dx: -1cm, dy: 1cm, image("logo.svg", width: 3cm))
```

By default, `place` takes content out of the flow; surrounding content lays out as if it were not there. With `float: true`, the space is *reserved*.

Two-column body with a title that spans both columns:

```typ
#set page(columns: 2)
#place(top + center, scope: "parent", float: true, clearance: 2em)[
  #align(center, text(size: 16pt, weight: "bold")[Document Title])
]

// ...two-column body content...
```

`scope: "parent"` makes placement relative to the page rather than the column.

=== `h`, `v` — spacers

```typ
#h(1cm)                                   // fixed horizontal gap
#h(1fr)                                   // absorbs remaining horizontal space
#v(2em)                                   // fixed vertical gap
#v(1fr)                                   // absorbs remaining vertical space
```


== Document structure

=== Custom heading numbering (e.g., 1 / (a) / (i))

```typ
#set heading(numbering: (..nums) => {
  let levels = nums.pos()
  let formats = ("1.", "(a)", "(i)")
  let idx = levels.len() - 1
  numbering(formats.at(calc.min(idx, formats.len() - 1)), levels.last())
})
```

=== Cross-references

```typ
= Payment <clause-payment>

...as set out in @clause-payment.

#ref(<clause-payment>, supplement: [see clause])
#ref(<clause-payment>, form: "page")        // cite as page number
```

=== Outline (table of contents)

```typ
#outline(title: [Contents], depth: 2, indent: auto)
#outline(title: [List of figures], target: figure.where(kind: image))
#outline(title: [List of tables], target: figure.where(kind: table))
```

=== Footnotes

```typ
The agreement was signed#footnote[on 12 March 2026] in Johannesburg.

#set footnote(numbering: "1")               // or "*" for symbols
```

=== Tables and grids

`table` and `grid` share most of their API. Use `table` for data, `grid` for layout.

```typ
#table(
  columns: (1fr, auto, auto),
  align: (left, right, right),
  stroke: 0.5pt + luma(150),
  table.header[*Item*][*Qty*][*Price*],
  [Widget A], [10], [R150.00],
)
```

Stroke recipes:

```typ
stroke: none                                // no strokes
stroke: (x: none)                           // horizontal lines only
stroke: (y: none)                           // vertical lines only
stroke: (_, y) => if y > 0 { (top: 0.8pt) } // function form
```

Striping: `fill: (_, y) => if calc.odd(y) { luma(245) }`. \
Bold header row: `#show table.cell.where(y: 0): strong`. \
Cell override: `table.cell(colspan: 2, fill: orange, [merged])`. \
Spanning lines: `table.hline(y: 2)`, `table.vline(x: 1, start: 1)`.

Long tables — repeating header on every page:

```typ
#show figure: set block(breakable: true)

#figure(
  table(table.header[A][B], ..rows),
  caption: [...],
)
```


== Control flow

`if` / `else if` / `else` — body is a code or content block.

```typ
#if x > 0 [positive] else if x < 0 [negative] else [zero]
```

`for` iterates arrays, dictionaries, strings, ranges. Bodies *join* into one value.

```typ
#for item in items [- #item ]
#for (k, v) in dict [#k -> #v \ ]
```

Loops produce content directly via joining — do not build up arrays manually.

```typ
// Idiomatic:
#for s in signatories [#s, ]

// Not this:
#let acc = []; for s in signatories { acc += [#s, ] }; acc
```

`while` follows the same shape; rare in document code. `break` and `continue` work as expected inside loops.


== Functions

Definition with positional and named parameters and defaults:

```typ
#let signoff(closer: "Yours faithfully", name) = [
  #closer, \ \ \ #name
]
```

Trailing content block — last content argument moves out of the parens:

```typ
#emph[important]                            // == #emph([important])
#text(size: 14pt)[Heading]
```

Spread `..` unpacks arrays into positional args, dictionaries into named args, and in definitions collects extras:

```typ
#grid(columns: 3, ..cells)
#let log(..items) = items.pos().join(", ")
```

`.with()` partially applies — returns a new function with some args fixed:

```typ
#show: contract.with(matter: "Acme v Beta")
```

Destructuring on the LHS of `let`:

```typ
#let (year, month, day) = (2026, 4, 30)
#let (a, .., b) = (1, 2, 3, 4)              // a=1, b=4, middle discarded
#let (buyer, seller) = parties              // dict by key
#let (_, y, _) = (1, 2, 3)                  // discard with underscore
```


== Modules and packages

Local files:

```typ
#import "firm_letter.typ": firm_letter, firm-name
#import "firm_letter.typ"                   // module accessed as firm_letter.x
#import "firm_letter.typ" as fl
#import "firm_letter.typ": *                // import all public names
#include "boilerplate.typ"                  // splice content (not definitions)
```

Packages — *always pin a version*; unversioned imports are an error.

```typ
#import "@preview/cetz:0.4.1": *
#import "@local/firm_templates:0.1.0": contract, letter
```

A package can only read files inside its own directory. If a package needs a project resource (logo, seal), the user passes it loaded:

```typ
#show: contract.with(seal: image("seal.png"))
```


== Templates

A template is a function that wraps the document. Apply via everything-show. Standard shape:

```typ
#let firm_letter(
  matter: "",
  date: datetime.today(),
  letterhead: "Doe & Doe Inc.",
  doc,                                      // body — last positional param
) = {
  // 1. Page-wide set rules.
  set page(
    paper: "a4",
    margin: (x: 2.5cm, top: 4cm, bottom: 3cm),
    header: align(center, text(weight: "bold", letterhead)),
  )
  set text(font: "Libertinus Serif", size: 11pt)
  set par(justify: true, leading: 0.65em)

  // 2. Show rules.
  show heading: set text(weight: "bold")

  // 3. Pre-body content.
  align(right, [#date.display("[day] [month repr:long] [year]")])
  v(1em)
  if matter != "" [Matter: *#matter* \ ]
  v(1em)

  // 4. Body.
  doc
}
```

Application:

```typ
#import "firm_letter.typ": firm_letter

#show: firm_letter.with(matter: "Acme v Beta")

Dear Ms Khumalo, ...
```

*Anti-pattern.* A template with twenty show rules is fragile to override. Set the page, set the text, set a few headings, and expose named parameters for the rest. Let users compose.


== Introspection: context, counters, state, query

`context` defers evaluation until layout knows where the expression sits. It is required for anything position-dependent: page numbers, current heading, state values, query results.

```typ
#context counter(page).get()                // (12,)
#context counter(heading).get()             // (3, 2) for section 3.2
#context counter(page).final()              // total pages
```

Counters: `counter(page)`, `counter(heading)`, `counter(figure)`, `counter(footnote)`, or `counter("custom-name")` for your own. Methods: `.get()`, `.at(<label>)`, `.final()`, `.display(pattern)`, `.step()`, `.update(n)`, `.update(n => n + 1)`.

State — like counters but holds arbitrary values:

```typ
#let chapter = state("chapter", "")
#chapter.update("Introduction")
#context chapter.get()
```

Counters and state update in *layout order* (where `.update()` lands in the document), not evaluation order. Storing an update in a variable without inserting it = no effect.

`query` finds elements by selector (in `context`):

```typ
#context query(heading.where(level: 1))
#context query(<some-label>).first().value
```

`here()` returns the current location. `.page()` and `.position()` work on a location.

`metadata` exposes an invisible value that is queryable later:

```typ
#metadata("2026-04-30") <draft-date>
#context query(<draft-date>).first().value
```

Heuristic: before reaching for `query`, check whether a counter, state, or label suffices. Heavy `query` use slows compilation and risks "layout did not converge" if results feed back into themselves.


== Gotchas

+ *Spurious `#` inside argument lists.* Wrong: `#text(font: #"Inria Serif")`. Right: `#text(font: "Inria Serif")`. Inside parens you are already in code mode — no inner `#`.

+ *`()` vs `[]` when calling a function.* `#title()` asks the document for its title. `#title[]` sets the title to empty content. Different. Silent bug.

+ *Single-element array needs trailing comma.* `(5)` is the integer 5; `(5,)` is an array of one element. Habit: always include the trailing comma when you mean an array.

+ *Show rules preserve numbering only if you keep it.* `show heading: it => it.body` makes numbering disappear. Preserve it explicitly:

  ```typ
  show heading: it => [
    #if it.numbering != none [#counter(heading).display(it.numbering) ]
    #it.body
  ]
  ```

+ *`par.first-line-indent` does not apply inside table cells, captions, or list items.* Only between document-level paragraph breaks.

+ *Custom footer overrides `page(numbering: ...)`.* If you want page numbers in a custom footer, render `counter(page)` manually inside it.

+ *`context` is required wherever the value changes per location:* page numbers, counter values, query results. If a value "doesn't update" or "shows the wrong thing", missing `context` is the first thing to check.

+ *Set rules scope to block end.* Inside a content block `[...]` or a function body, set rules are local. Consistent but surprising.

+ *Show rule order matters.* Later rules override earlier on matching elements. Two rules for the same element can shadow each other in subtle ways.

+ *Layout convergence.* Typst lays out 2--5 times to resolve introspection. If a query depends on its own output you get "layout did not converge within 5 attempts". Look for state and query feedback loops.

+ *Packages need pinned versions.* `@preview/cetz` alone is an error; `@preview/cetz:0.4.1` works.

+ *A package can only read files inside its own directory.* User project resources (images, data files) must be passed in by the user as pre-loaded values.

+ *`auto` is not `none`.* `auto` means "default sensible value"; `none` means "explicitly empty or disabled". Read the function ref to know which to pass.

+ *`&` is not special in Typst markup.* Don't backslash-escape it. LaTeX habit; harmless but noisy.

+ *Compilation iterates.* Don't expect single-pass behaviour. Counters, queries, and `final()` values all rely on multi-pass.


== Reference lookup heuristic

Before guessing parameter names or syntax for an unfamiliar function, search Typst's official reference at `typst.app/docs/reference/`. Categories most likely to contain what you need:

#table(
  columns: (auto, 1fr),
  stroke: 0.4pt + luma(180),
  inset: 6pt,
  align: (left, left),
  [`layout/`], [`page`, `align`, `block`, `box`, `grid`, `place`, `columns`, `pad`, `stack`, `h`, `v`, `pagebreak`, `hide`, `measure`, `move`, `rotate`, `scale`],
  [`model/`], [`heading`, `figure`, `table`, `outline`, `enum`, `list`, `terms`, `bibliography`, `cite`, `ref`, `footnote`, `par`, `quote`, `document`],
  [`text/`], [`text`, `raw`, `smallcaps`, `smartquote`, `sub`, `super`, `underline`, `strike`, `highlight`, `overline`, `upper`, `lower`, `lorem`, `linebreak`],
  [`introspection/`], [`counter`, `state`, `query`, `locate`, `here`, `metadata`, `location`],
  [`foundations/`], [`calc`, `datetime`, `str`, `array`, `dictionary`, `regex`, `type`, `symbol`],
  [`visualize/`], [`rect`, `square`, `circle`, `ellipse`, `line`, `path`, `curve`, `polygon`, `image`, `color`, `gradient`, `stroke`],
)

For packages, search `typst.app/universe/`. Always pin the version shown.

When uncertain, prefer asking the user to clarify over guessing. Typst is consistent enough that wrong guesses produce confusing errors rather than working code.


== Praxis house rules

+ Pin every package version explicitly. Document why a particular package was chosen.
+ Comment generously. Future agents (and humans) read this code.
+ Prefer `let`-bound defined terms over inline string literals for any name, party, amount, or date that appears more than once.
+ Templates live in their own files. Documents import them; documents do not redefine them inline.
+ When asked to modify document styling, prefer changing the template over adding overrides at the call site. Overrides are a smell.
+ When uncertain about how something will render, say so and ask for a sample compile rather than guessing across multiple turns.
