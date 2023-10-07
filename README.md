# LASM v1.1.2
Lime Assembler
### Searching for Tester.
This is a simple **32-bit x86 Assembler** language written in **Python 3.11.5**.
Its supports basic x86 instructions and some advanced commands.

https://github.com/Duiccni

### Dont Sure to Add:
* 'def :const(size) const(value)'

## variables.py:
* Sizes				(Line 68)
* no_input_inst		(Line 320)
* jcc_inst			(Line 354)
* shift_inst		(Line 396)
* type1-2-3_inst	(Line 400-430)
* push-pop-segments	(Line 442)

## Variables:
* $, $$, (<n1> (+ | -) <n2>...),
* 0x<hex>, <decimal>, 0b<bin>, &<name>, '<char>'
### Variables that removed in v1.0.1:
* $<const>, ?
### Code from v0.0.1-beta:
* process(v, s, n): zeroExtend(toHex(v, s), s, n)
* memProc(v, s): reverse(splitBytes(process(v, s, False)))

### Example command:
```
python3 main.py -s release -f 0 -ver 111 -of 1 -i test.lasm -o test
python3 main.py -help
python3 main.py -version
```

### Close all verboses for less anoying and more readable output.
```
python3 main.py -s release -f 0 -ver 000 -of 1 -i test.lasm -o test
```
### But in case you want to learn how code works open it.

Note: I used Black Formatter for making code more Prettier

## Lasm Code with Lasm-Syntax
![image](https://github.com/Duiccni/Lasm-v1.0.x/assets/143947543/c7ce0ec4-0121-4536-ac5f-bc290bb6cffb)

Lasm has 3 main codes:

* main.py (Main thread.)
* variables.py (Variables, constants, colors and settings.)
* functions.py (Basic functions like toInt(x) for converting string to int.)
* instructions.py (Complex commands and instructions.)

## Getting Started

To get started, you will need to install Python 3.6 or later.
Once you have Python installed, you can clone the LASM repository from GitHub:

```
git clone https://github.com/Duiccni/Lasm-v1.1.x.git
```

When you have the code you can run it with python like:

```
python main.py -i <input-file.lasm> -o <output-file>
```

NOTE: Dont add output file extension to command.

### Unlimited Thanks To

* NASM (Netwide Assembler)
