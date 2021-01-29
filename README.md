# shazzam

Not your daddy's C64 cross-assembler...

![Pylint](https://github.com/shazz/shazzam/workflows/Pylint/badge.svg)

## What is Shazzam?

It is probably easier to say what Shazzam is NOT:

- a new 6502 cross-assembler (it relies on existing ones)
- a python compiler for 6502

And where it took its inspiration from multiple famous C64 tools:

- `KickC`: a Kiss Assembler code generator using a C-like language.
- `C64jasm`: a Cross Assembler supporting inline extensions using pure Javacript.
- `bass`: an ACME-like cross assembler using Lua for scripting and internal emulator for testing.
- `Sparkle`: an IRQ Loader managing on time loading of data and code segments.

As a result, by using all those great modern C64 Development tools, I found out that state of the art demo effects are mostly based on code generation, most of the time using cross-assembler macros and external tools.

So the usage of non assembler tooling became more important than the assembly code itself, that's why I thought that "reversing" the cross assembler idea (meaning providing a good but basic cross-assembler with quite powerful, complex and more or less standard macro language) would make sense: don't extend the cross assembler with some kind of complex scripting language but extend existing high level languages with simple assembler capabilities.

This is the magic of shazzam, write Python code as usual, to process your images, create your lookup tables, read your SID files.... no limit to your creativity then, generate the assembly code required to use this data as you would do with the cross-assembler.

## Installation

### From pypi

Requirements

- Python 3.7+ with pip
- `nox` (`pip install nox`) in your base Python installation if you want to build from sources

````bash
pip install shazzam
````

Then, if you're not using `nox`, you'll have to install the various mandatory and optional tools manually:

- CC65 (mandatory)
- Exomizer (optional)
- Apultra (optional)
- lzsa (optional)
- Dyonamite (optional)
- pucrunch (optional)
- nucrunch (optional)
- Sparkle (optional)

### From sources

Shazzam provides a `noxfile` to automate the creation of the various virtual environments and install the various tools

````bash
git clone https://github.com/shazz/shazzam
cd shazzam
nox -s install
nox -s install_3rd_party
````

## 4 lines example

As Shazzam is just a Python library, everything is Python. So even your generated assembly code looks like Python.

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

One of the funny feature of Shazzam, that's that in real-time the assembly code is generated and assembled (and crunched, and...). So that means, each time you type any assembly function in Python, you can see the result without executing any python script of whatever except your current code.

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
import shazzam.macros.macros_math as m

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
````

## Inline testing thru emulation

Inspired from bass, shazzam includes [py65emu](https://github.com/docmarionum1/py65emu), a generic 6502 emulator written in Python, it doesn't emulate a C64 or any other hardware than the 6502 CPU. But that's good enough to emulate your routines and check the registers and what is written in the memory.

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
````

And you'll see in your IDE or terminal:

````python
Address: $081B
Result: 266
````

So this is good news, the macro works :)

## Segments support

The main weakness I found in most 6502 cross-assemblers is the non-existent to minimal support of code segments. At worst you can specify the memory location of the next block (`* = $1000` for example), at best some inline segment definition is possible. But fortunately a few cross-assemblers like [CC65](https://github.com/cc65/cc65) have a real great support for relocatable segments and Shazzam is using it.

What does it mean? Simply that you can split your code in segment, assemble each one separately and finally link them accordingly by setting the optimal location based on your constraints (VIC banks, memory locations, SID driver...) without tweaking your code, the order of the routines, where sprites should be located...

How does it look like? Extract from the provided `hello_world` example

````python
with segment(0x0801, assembler.get_code_segment()) as s:

    jsr(at(0x0e544))        # ROM routine to clear the screen Clear screen.Input: – Output: – Used registers: A, X, Y.

    lda(imm(0))
    sta(at(vic.border_col)) # set border color
    sta(at(vic.bck_col))    # and window color to black
````

Within this block, all the code will be starting at address 0x0801, in a segment in this example called CODE (`get_code_segment()`).

And icing on the cake, Shazzam features a Segment Optimizer which automatically finds the best memory arrangement based on the application and C64 constraints.

## Crunchers support

Obviously, you can add any cruncher/packer to shrink your data or generated PRG but by default, Shazzam supports:

- Exomizer
- pucrunch
- nucrunch
- Alpultra
- lzsa
- Dyonamite

Extract from the `crunch_crunch` provided example:

````python
prg_cruncher  = Exomizer("third_party/exomizer/exomizer")

def code():
    ...

# finally assemble segments to PRG using cross assembler then crunch it!
assemble_prg(assembler, start_address=0x0801, cruncher=prg_cruncher)
````

And to crunch a SID file for example:

````python
data_cruncher = Apultra("third_party/apultra/apultra", mode=PackingMode.FORWARD)

def code():
    ...

    with segment(segments["packedata"], "packedata") as s:
        incbin(data_cruncher.crunch_incbin(sidfile))

    with segment(segments["depacker"], "depacker") as s:
        data_cruncher.generate_depacker_routine(s.get_stats().start_address)

````

With each data cruncher, the depacking routine is also provided, just call `generate_depacker_routine()` as shown in the example.

## IRQ Loaders support

As segments and data can be managed independently, using an IRQ Loader is straight forward. Shazzam is able to generate the Sparkle configuration script and run the Sparkle image builder.

## Rasterline racer

Racing the beam is probably the traditional hobby of most C64 coders. So to help a little, Shazzan can track the instructions timings to be sure yoru code will fit in the rasterline (including DMA stealing periods, badlines,...).

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