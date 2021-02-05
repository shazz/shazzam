# `Shazzam`

Not your daddy's C64 cross-assembler...

![Pylint](https://github.com/shazz/`Shazzam`/workflows/Pylint/badge.svg)

- [`Shazzam`](#-shazzam-)
  * [What is `Shazzam`?](#what-is--shazzam--)
    + [Features in brief](#features-in-brief)
  * [Installation](#installation)
    + [From pypi](#from-pypi)
      - [Cross-Assemblers](#cross-assemblers)
      - [Packers](#packers)
      - [IRQ Loaders](#irq-loaders)
    + [From sources](#from-sources)
  * [4 lines example](#4-lines-example)
  * [Python and Assembly](#python-and-assembly)
  * [Realtime code generation](#realtime-code-generation)
  * [Python-based macros](#python-based-macros)
  * [Inline testing thru emulation](#inline-testing-thru-emulation)
  * [Segments support](#segments-support)
  * [Crunchers support](#crunchers-support)
  * [IRQ Loaders support](#irq-loaders-support)
  * [Rasterline racer](#rasterline-racer)
  * [Python-based C64 files parsers](#python-based-c64-files-parsers)
  * [BeamRacer support](#beamracer-support)
  * [Multi-files application](#multi-files-application)
  * [Simple disassembler](#simple-disassembler)
  * [Shazzam assembler directives](#shazzam-assembler-directives)
- [Thanks to](#thanks-to)

## What is `Shazzam`?

It is probably easier to say what `Shazzam` is NOT:

- a new 6502 cross-assembler (it relies on existing ones)
- a python compiler for 6502
- some kind of `Micro-Python` or `Circuit-Python` implementation

And where it took its inspiration from multiple famous C64 tools:

- `KickC`: a Kiss Assembler code generator using a C-like language.
- `C64jasm`: a Cross Assembler supporting inline extensions using pure Javacript.
- `Bass`: an `ACME`-like cross assembler using Lua for scripting and internal emulator for testing.
- `Sparkle`: an IRQ Loader managing on time loading of data and code segments.
- `Raistlin's C++ code generator`: Raistlin/G*P's top secret framework to code awesome demos

As a result, by using all those great modern C64 Development tools, I found out that state of the art demo effects are mostly based on code generation, most of the time using cross-assembler macros and external tools.

So the usage of non assembler tooling became more important than the assembly code itself, that's why I thought that "reversing" the cross assembler idea (meaning providing a good but basic cross-assembler with quite powerful, complex and more or less standard macro language) would make sense: don't extend the cross assembler with some kind of complex scripting language but extend existing high level languages with simple assembler capabilities.

This is the magic of `Shazzam`, write Python code as usual, to process your images, create your lookup tables, read your SID files.... no limit to your creativity then, generate the assembly code required to use this data as you would do with the cross-assembler.

### Features in brief

- Python code generator for official and illegal 6502 instructions
- Generate `cc65` or `c64jasm` assembly code from your Python application in real-time
- 6502 emulator to write unit tests and debug step-by-step routines
- Pre-integrated packers (Exomizer, Apultra, zx7...) for `incbin` and `prg`
- Export Sparkle compatible script (D64 generation on Windows only)
- Plugins to load and parse `SID`, `SPD`, `KLA` files
- Support multi-files, multi-segments
- Segment optimizer to maximize contiguous memory usage
- Support `VASYL` opcodes for [BeamRacer](beamracer.net) expansion card
- Rasterline cycles simulation to race the beam
- Simple disassembler
- Integrate well in any Python and 6502 assembly code compatible IDE. (Visual code works great)
- OS agnostic (Linux, MacOS, Windows...)

## Installation

### From pypi

Requirements

- Python 3.7+ with pip
- `nox` (`pip install nox`) in your base Python installation if you want to build from sources

````bash
pip install `Shazzam`
````

Then, if you're not using `nox`, you'll have to install the various mandatory and optional tools manually:

#### Cross-Assemblers

- [CC65](https://github.com/cc65/cc65) (mandatory)
- [c64jasm](https://github.com/nurpax/c64jasm) (supported soon!!!)

#### Packers

- [Exomizer](https://bitbucket.org/magli143/exomizer/wiki/downloads/exomizer-3.1.0.zip) (optional)
- [Apultra](https://github.com/emmanuel-marty/apultra.git) (optional)
- [lzsa](https://github.com/emmanuel-marty/lzsa.git) (optional)
- [Dyonamite](https://csdb.dk/release/download.php?id=160764) (optional)
- [pucrunch](https://github.com/mist64/pucrunch.git) (optional)
- [nucrunch](https://csdb.dk/release/download.php?id=206619) (optional)
- [zx7](https://github.com/jsmolina/pyzx7) / [x64f](https://github.com/antoniovillena/c64f) (optional)

#### IRQ Loaders

- [Sparkle](https://csdb.dk/release/download.php?id=241780) (optional)

### From sources

`Shazzam` provides a `noxfile` to automate the creation of the various virtual environments and install the various tools and docs

````bash
git clone https://github.com/shazz/`Shazzam`
cd `Shazzam`
nox -s install
nox -s install_3rd_party
nox -rs docs
````

Note that you may need to install some OS packages to compile and install the 3rd party tools. Build tools like `make`, `gcc`, `node`, `npm`, `cargo`... and archiving tools like `unzip`, `tar`...

## 4 lines example

As `Shazzam` is just a Python library, everything is Python. So even your generated assembly code looks like Python.

Let's set the C64 border and window color to black:

````python
    label("start")              # define a start label
    lda(imm(0))                 # set accumulator to 0
    sta(at(vic.border_col))     # set border color
    sta(at(vic.bck_col))        # and window color to black
````

That's it! That's a little more chatty than your traditional assembler but also less prone to error as, as you can see, you have to clearly state if the opcode argument is an address (`at`), an immediate (`imm`),...

## Python and Assembly

As you can see, this is not some kind of python libraries to generate code, you really write your assembly code, surrounded by any Python code that can interact with the assembly code.
Let's try another example, setting the Sprite X and Y coordinates to given values:

````python
    coords = []
    for i in range(80):
        x = int(160+160*(math.sin(i/80*math.pi*2)))
        y = int(100+100*(math.sin(3*i/80*math.pi*2)))
        coords.append((x, y))

    for s in range(8):
        lda(imm(coords[s*10]))
        ldx(imm(coords[s*10]))
        sta(at(vic.sprite0_x+(2*s)))
        sty(at(vic.sprite0_y+(2*s)))
````

I hope this gave you a basic idea of how Python and the assembly code can mix, the only limit is your imagination :)

## Realtime code generation

One of the funny feature of `Shazzam`, that's that in real-time the assembly code is generated and assembled (and crunched, and...). So that means, each time you type any assembly function in Python, you can see the result without executing any python script of whatever except your current code.

A little video is probably better than a lot of words:

[ Insert vscode video here ]

## Python-based macros

Like any cross-assembler, you can code in Python generic and reusable snippets to simplify your assembly code. But in this case, this is simple Python function. Here is the `16bits addition` macro provided in the library:

````python
def add16(n1, n2, res):
    clc()
    lda(at(n1))
    adc(at(n2))
    sta(at(res)+0)
    lda(at(n1)+1)
    adc(at(n2)+1)
    sta(at(res)+1)
````

Then in your code, simply import and call it to perform 256+10

````python
import `Shazzam`.macros.macros_math as m

    m.add16(at("var1"), at("var2"), at("result"))

    label("var1")
    byte(0)
    byte(1)
    label("var2")
    byte(10)
    byte(0)
    label("result")
    byte(0)
    byte(0)

    [...]
````

`Shazzam` provides various sets of ready to use macros to set the `VIC` banks and memory, some 16bits math operations, to set IRQs, to wate cycles.... Just check ``Shazzam`/macros/`

## Inline testing thru emulation

Inspired from bass, `Shazzam` includes [py65emu](https://github.com/docmarionum1/py65emu), a generic 6502 emulator written in Python, it doesn't emulate a C64 or any other hardware than the 6502 CPU. But that's good enough to emulate your routines and check the registers and what is written in the memory.

Practically, in your code, you can add typical `assert` statements. Here is an example to

````python
    m.add16("var1", "var2", "result")
    brk()

    label("var1")
    byte(0)
    byte(1)
    label("var2")
    byte(10)
    byte(0)
    label("result")
    byte(0)
    byte(0)

    cpu, mmu = s.emulate()
    res = mmu.read(get_current_address()-1)*256 + mmu.read(get_current_address()-2)}
    print(f"Address: ${get_current_address():04X}")
    print(f"Result: {res}")
    assert res == 256

    [...]
````

And you'll see in your IDE or terminal:

````python
Address: $081B
Result: 266
````

So this is good news, the macro works :)

And using the built-in 6502 emulator you can do more, check how many cycles were really used between 2 locations in the code, or even step-by-step debugging.

## Segments support

The main weakness I found in most 6502 cross-assemblers is the non-existent to minimal support of code segments. At worst you can specify the memory location of the next block (`* = $1000` for example), at best some inline segment definition is possible. But fortunately a few cross-assemblers like [c64jasm](http://github.com/nurpax/c64jasm) or [cc65](https://github.com/cc65/cc65) have a real great support for relocatable segments and `Shazzam` is using it.

What does it mean? Simply that you can split your code in segment, assemble each one separately and finally link them accordingly by setting the optimal location based on your constraints (VIC banks, memory locations, SID driver...) without tweaking your code, the order of the routines, where sprites should be located...

How does it look like? Extract from the provided `hello_world` example

````python
with segment(0x0801, assembler.get_code_segment()) as s:

    jsr(at(0x0e544))        # ROM routine to clear the screen Clear screen.Input: – Output: – Used registers: A, X, Y.

    lda(imm(0))
    sta(at(vic.border_col)) # set border color
    sta(at(vic.bck_col))    # and window color to black

    [...]
````

Within this block, all the code will be starting at address 0x0801, in a segment in this example called CODE (`get_code_segment()`).

And icing on the cake, `Shazzam` features a Segment Optimizer which automatically finds the best memory arrangement based on the application and C64 constraints.

## Crunchers support

Obviously, you can add any cruncher/packer to shrink your data (`incbin`) or generated `PRG` but by default, `Shazzam` supports:

- `Exomizer` (PRG) (incbin missing)
- `pucrunch` (PRG) (incbin missing)
- `nucrunch` (PRG) (incbin missing)
- `Alpultra` (incbin) (PRG missing)
- `lzsa` (PRG and incbin depacker missing)
- `Dyonamite` ((PRG and incbin depacker missing))
- `zx7` (incin) (PRG missing)
- `c64f` (incbin) (PRG missing)
- `zx0` (todo)

Extract from the `crunch_crunch` provided example:

````python
prg_cruncher  = Exomizer("third_party/exomizer/exomizer")

def code():
    ...

# finally assemble segments to PRG using cross assembler then crunch it!
assemble_prg(assembler, start_address=0x0801, cruncher=prg_cruncher)
````

And to crunch a `SID` file for example:

````python
data_cruncher = Apultra("third_party/apultra/apultra", mode=PackingMode.FORWARD)

def code():
    ...

    with segment(segments["packedata"], "packedata") as s:
        incbin(data_cruncher.crunch_incbin(sidfile))

    with segment(segments["depacker"], "depacker") as s:
        data_cruncher.generate_depacker_routine(s.get_stats().start_address)

    [...]
````

With each data cruncher, the depacking routine is also provided, just call `generate_depacker_routine()` as shown in the example.

## IRQ Loaders support

As segments and data can be managed independently, using an IRQ Loader is straight forward. `Shazzam` is able to generate the Sparkle configuration script and run the Sparkle image builder.

## Rasterline racer

Racing the beam is probably the traditional hobby of most C64 coders. So to help a little, `Shazzam` can track the instructions timings to be sure your code will fit in the rasterline (including DMA stealing periods, badlines,...).

How does it work? Check this extract from the `sprites_galore` example:

````python
for y in range(y_scroll, y_scroll+10):
    with rasterline(nb_sprites=8, y_pos=y, y_scroll=y_scroll):
        if (y & 7) == y_scroll:
            nop()
            nop()
            nop()
        else:
            nop()
````

## Python-based C64 files parsers

As this is just Python, up to you to do what you like to do but if it helps, `Shazzam` includes some useful parsers ready to use:

- `SID` music player files
- `Koala` multicolor pictures
- `SPD` v2 sprites files

Just import them!

The `i_love_kaoalas` example shows how to display a Koala picture in a few lines of code. A little extract:

````python
import `Shazzam`.plugins.plugins as p

def code():

    kla = p.read_kla('resources/panda.kla')

    with segment(0x0801, assembler.get_code_segment()) as s:

        lda(imm(kla.bg_color))      # set border and window color to picture background color
        sta(at(vic.border_col))
        sta(at(vic.bck_col))

    with segment(0xd800, "color_ram", segment_type=SegmentType.REGISTERS) as s:
        incbin(kla.colorram)

    [...]
````

## BeamRacer support

The `VLIB` and `VASYL` libraries are ported to `Shazzam` using the ``Shazzam`.macros.vlib` and ``Shazzam`.macros.vasyl` packages.

Extract from `examples/hello_vasyl`:

````python
from `Shazzam`.macros.vasyl import *

with segment(0x00, "VASYL") as s:

    label("dl_start", is_global=True)
    WAIT(48 ,0)

    dl_line_0 = label("dl_line_0")
    MASKV(0)
    WAIT(0, 15)
    MOV(0x20, 0)
    DELAYV(1)
    SKIP()
    WAIT(55 , 59)
    BRA(dl_line_0)
    WAIT(56 ,0)

    [...]
````

## Multi-files application

If your application/demo/game gets big, you can easily split your code by relocatable segments dispatch your segments' code in various files. Simply use the python `import` statement to include them like in the `examples/multi-files` example:

````python
@reloading
def code():

    # define here or anywhere, doesn't matter, your variables
    import examples.multi_files.segment_start
    import examples.multi_files.segment_charset

    # generate listing
    gen_code(assembler, gen_listing=True)

    # finally assemble segments to PRG using cross assembler then crunch it!
    assemble_prg(assembler, start_address=0x0801)

    [...]
````

## Simple disassembler

Each time your python code generates some assembly code, the assembly and listing files are generated. But if you want to be sure and check the final generated code, a little 6502 disassembler is provided in `tools/`.

Usage:
`python tools/disasm.py -i generated/hello_world/hello_word.prg -o /tmp/hello_word.lst`

In case of a prg, the starting address is automatically extracted from the header. Else the -a option can be used to define a specific address.

## Shazzam assembler directives

As a lot of things can be done directly in Python, `shazzam` support a minimal set of specific assembler directives:

````python
from shazzam.py64gen import *
````

- `align(value: int)`: align the next instruction at a `value` boundary (will generate call to `byte(0)` to pad the data)
- `byte(value :int or List[value]`: add a byte or a sequence of bytes
- `word(value: int or List[value]`: add a word or a sequence of words
- `label(name: str, is_global: bool)`: define a local or global label at the current address
- `get_anonymous_label(name: str)`: define an anonymous label
- `incbin(data: bytearray)`: include a sequence of bytes from an external source (code, file... will generate call to `byte()`)
- `get_current_address()`: return current address in the segment
- `get_label_address(label: str)`: get address for a given label

For each 6502 opcode function (ex `lda()` or `LDA()`), the operand type (immediate, address, relative address) has to be specified using the functions:

- `at(value: Any)`: for an absolute address
- `ind_at(value: Any)`: for an indirect address
- `rel_at(value: Any)`: for a relative address
- `imm(value: Any)`: for an immediate value

and associated 6502 registers:

````python
from shazzam.py64gen import RegisterX as x, RegisterY as y, RegisterACC as a
````

# Thanks to

All the various open-source projects `Shazzam` is relying on:

- `c64jasm` by Nurpax
- `cc65` by cc65 community
- `Doynamite` by Bitbreaker
- `Exomizer` by Magnus Lind
- `Lzsa` by Emmanuel Marty
- `Nucrunch` by Christopher Jam
- `Pucrunch` by Pasi Ojala
- `Pultra` by Emmanuel Marty
- `py65emu` by Jeremy Neiman
- `Simple 6502 disassembler` by Arthur Ferreira
- `Sparkle` by Sparta/OMG
- `zx7` by Einar Saukas and 6502 port by Antonio Villena

And also the beta-testers!