"""
https://github.com/Duiccni

### Dont Sure to Add:
* 'def :<const>(size) <const>(value)'

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
* python3 main.py -s release -f 0 -ver 111 -of 1 -i test.lasm -o test
* python3 main.py -help
* python3 main.py -version

### Close all verboses for less anoying and more readable output.
* python3 main.py -s release -f 0 -ver 000 -of 1 -i test.lasm -o test
### But in case you want to learn how code works open it.
"""

VERSION = "v1.1.3"
COMP_VERSION = "s1654 u6d10 7.10.23"
AUTHOR = "Egemen Yalin"

import os
import time
import sys

start_t = time.time()

try:
	import variables as var
	from variables import Colors
	import functions as func
	import instructions as inst
except Exception as e:
	print(
		"\n\033[41m * \033[0m \033[31mCode cant find the Module files\033[0m, please check the files in the same directory with main.py. (variables.py, functions.py, instructions.py)\n"
	)
	raise e

"""
Info for 'GitHub Copilot':
Test case1: 'mov .dword eax, *5301'
Test case2: 'mov .dword *&num1, (-5+3)'
"""

INTRODUCTION = (
	f"\033[44m * \033[0m LASM Assembler {VERSION}({COMP_VERSION}) Created by {AUTHOR}."
)

_disable = False
index = 0
_times_c_active = False
_times_cooldown = -1
_test_mode = 0
# _test_mode = 3 if os.getlogin() == "duiccni" else 0
_memory_sections: list[int] = []
_perf_mode = False

# nasm -f bin /home/duiccni/Documents/Projects/Lasm-v1.1.x-trash2/nasm_test.asm
if _test_mode > 0:
	os.system("clear")

var.Settings.tab_size = 48

input_path = ""
output_path = ""
argv_type = ""
if "-help" in sys.argv or "-h" in sys.argv:
	print(
		f"""
{INTRODUCTION}
\t-help, -h\tShow this message.
\t-version, -v\tShow version.
\t-i <path>.lasm\tInput file path.
\t-o <path>\tOutput file path.
\t-f <int>\tForce exit code.
\t-s <mode>\tMode (e.g. debug, release, perf).
\t-ver <verbose>\t<pb><lw><aw> (e.g. 011)
\t-of <int>\tIgnore overflow errors ('0' for ignore '1' for show).
		"""
	)
	exit()
if "-version" in sys.argv or "-v" in sys.argv:
	print(INTRODUCTION)
	exit()

for arg in sys.argv:
	if argv_type == "" and arg[0] == "-":
		argv_type = arg[1:]
	else:
		match argv_type:
			case "s":
				if arg == "debug":
					var.Settings.mode(-1, False, False, True, True, True)
				elif arg == "release":
					var.Settings.mode(0, False, False, False, True, False)
				elif arg == "perf":
					var.Settings.mode(-1, True, False, False, False, False)
					var.Settings.mode_verbose(False, False, False)
					_perf_mode = True
			case "i":
				input_path = arg
			case "o":
				output_path = arg
			case "f":
				var.Settings.force_exit = int(arg)
			case "ver":
				var.Settings.mode_verbose(*[i == "1" for i in arg])
			case "of":
				var.Settings.overflow_errors = arg == "1"
			case _:
				pass
		argv_type = ""

if _test_mode > 0:
	input_path = "test.lasm"
	output_path = "test"

if input_path == "":
	print("Use -help for info.")
	var.raiseError("No Input", "No input file specified. (Use '-i <path>.lasm')")
	exit()

_input_file = open(input_path, "r")
all_cases = [i.strip() for i in _input_file.readlines()]
if not all_cases:
	print("Use -help for info.")
	var.raiseError("Empty Input", "Input File is Empty.")
	exit()
_input_file.close()

TClen = len(all_cases)


def printOutput(
	_case: str,
	retu: list[str] | None,
	args: tuple[int, int] | None = None,
	tab_bias: int = 0,
	comment_: str = "",
) -> None:
	if retu == []:
		var.raiseError(
			"Print Error",
			"There is a 'retu' list with no elements in 'printOutput' function.",
			True,
			index,
		)
		print(f"({Colors.DARK}{all_cases[index]}{Colors.ENDL})")
		print(Colors.SECOND + "Code has forged to Exit." + Colors.ENDL)
		exit()

	if var.Settings.skip_print or (not _times_c_active and _times_cooldown > 0):
		return

	if args == None:
		args = (index, var.addr)

	if _case == "":
		print(
			(Colors.ERROR if args[0] > 0xFF else "\033[1m")
			+ var.zeroExtend(hex(args[0] % 0x100)[2:]),
			Colors.ENDL,
		)
		return

	if comment_ != "":
		comment_ = "//" + comment_

	print(
		(Colors.ERROR if args[0] > 0xFF else "\033[1m")
		+ var.zeroExtend(hex(args[0] % 0x100)[2:]),
		Colors.DARK
		+ (
			"    "
			if retu == None and _case[0] != ":"
			else var.zeroExtend(hex(args[1])[2:], var.WORD)
		)
		+ ("" if _disable else Colors.ENDL),
		_case + (" " if _case else "") + Colors.DARK + comment_,
		end=Colors.DARK,
	)

	if retu == None:
		print(Colors.ENDL)
		return

	tmp = var.Settings.tab_size - len(_case) + tab_bias - len(comment_)
	print(
		" " * tmp + Colors.DARK,
		("" if retu[0] == var.STR_BIT_32 else "   ") + " ".join(retu) + Colors.ENDL,
	)

	if tmp < 0 and var.Settings.print_breakpoint:
		var.raiseError(
			"Print Breakpoint",
			f"var.Settings.tab_size({var.Settings.tab_size}, +{-tmp}) is too small.",
			False,
			args[0],
		)


def handleCase(_case: str) -> list[str] | None:
	if _case == "":
		return
	global all_cases, TClen, _disable, index, _times_c_active, _times_cooldown
	case1 = func.splitCase(_case, index)
	if _test_mode == 2:
		print(f"\n{Colors.DARK}{case1}{Colors.ENDL}")

	if case1.args == None and case1.command in var.no_input_inst:
		value = var.no_input_inst[case1.command]
		del case1
		return value

	if case1.command[0] == "#":
		if not var.Settings.debug:
			var.raiseError("Debug Command", "Debug mode is disabled.", line=index)
			return
		command = case1.command[1:]
		match command:
			case "jmp":
				index += case1.args[0]  # type: ignore
			case "set":
				assert type(case1.args[0]) == int  # type: ignore
				index = case1.args[0]  # type: ignore
			case "flush":
				var.consts.clear()
			case "stop":
				TClen = 0
			case _:
				var.raiseError(
					"Command",
					f"'{case1.command}' isn't reconized by Assembler.",
					line=index,
				)
		del case1
		return

	match case1.command:
		case "org":
			var.raiseError(
				"Command",
				"'org' can only be used in First line of code.",
				line=index,
			)
		case "con":
			if case1.args[0] in var.consts:  # type: ignore
				var.raiseError(
					"Constant Overwrite",
					f"Isn't allowed in this version({VERSION}).",
					line=index,
				)
				del case1
				return
			var.consts[case1.args[0]] = case1.args[1]  # type: ignore
			checkWaiters(case1.args[0])  # type: ignore
		case "times":
			if case1.args[0] < 0:  # type: ignore
				var.raiseError(
					"Index Error",
					f"The input of 'times command cant be Negative({case1.args[0]})'",  # type: ignore
					line=index,
				)
			if not var.Settings.show_times:
				_times_c_active = True
				_times_cooldown = case1.args[0]  # type: ignore
			TClen += case1.args[0]  # type: ignore
			all_cases = (
				all_cases[: index + 1]
				+ [case1.args[1]] * case1.args[0]  # type: ignore
				+ all_cases[index + 1 :]
			)
		case _:
			if case1.command[0] == ":":
				command = case1.command[1:]
				if command in var.consts:
					var.raiseError(
						"Constant Overwrite",
						f"Isn't allowed in this version({VERSION}).",
						line=index,
					)
				var.consts[command] = var.addr
				checkWaiters(command)
				if case1.args != None:
					return handleCase(_case[len(command) + 2 :])
				return
			if case1.command in inst.basic_dir:
				return inst.basic_dir[case1.command](case1)
			var.raiseError(
				"Command",
				f"'{case_}'({case1.command if case1.command[0].isalpha else hex(var.computeInt(case1.command))}) isn't reconized by Assembler.",  # type: ignore
				line=index,
			)
			print(repr(case1))
	del case1


def checkWaiters(name: str) -> None:
	waiter_index = 0
	len_ = len(var.waiters)
	while waiter_index < len_:
		waiter = var.waiters[waiter_index]
		if waiter.check(name):
			if var.Settings.linewrite_msg:
				var.raiseError(
					"Line Rewrite",
					f"Function found wanted values({waiter.bias}, &{', &'.join(waiter.NAMES)}) and function rewrited as:",
					False,
					waiter.index,
				)
			waiter_end = waiter.start + var.unitSize(waiter.size)
			printOutput(
				f"({Colors.DARK}{all_cases[waiter.index].split('//')[0].strip()}{Colors.ENDL})",
				[var.memory[waiter.start - 1] + Colors.GREEN]
				+ var.memory[waiter.start : waiter_end]
				+ [
					Colors.DARK + var.memory[waiter_end]
					if waiter_end < len(var.memory)
					else Colors.DARK
				],
				(waiter.index, waiter.start + var.orgin),
				9,  # its comes from 7 (colors) + 2 (brackets)
			)
			var.waiters.pop(waiter_index)
			len_ -= 1
		else:
			waiter_index += 1


if __name__ != "__main__":
	print("Use -help for info.")
	exit()

if _test_mode == 1:
	case1 = func.splitCase("mov .dword *&num1, (-5+3)", 0)
	print(
		case1.command,
		var.str_size[case1.size],
		[func.Types.str_type[i] for i in case1.type],  # type: ignore
		case1.args,
	)

	printOutput(
		"mov .dword *&num1, (-5+3)",
		["66", "XX", "XX"],
		(0x10, 0x20),
		comment_=" Test Case",
	)

print(INTRODUCTION)

if all_cases[0].startswith("org"):
	print(" " * 7, all_cases[0])
	var.addr = var.toInt(all_cases[0].split()[1])
	var.orgin = var.addr
	all_cases.pop(0)
	TClen -= 1

while index < TClen:
	case_ = all_cases[index].strip()

	if case_ == "'''":
		print(f"\t {Colors.DARK}'''{Colors.ENDL}")
		_disable = not _disable
		index += 1
		continue

	if var.Settings.skip_times and case_.startswith("times"):
		print(
			f"\t {Colors.DARK}Skipped Times",
			f"{Colors.ITALIC}(Line {index}){Colors.ENDL}",
		)
		index += 1
		continue

	# *** main ***
	inst.index_ = index
	tmp = case_.split("//")
	case_, comment = tmp if len(tmp) == 2 else (tmp[0], "")
	case_ = case_.strip()
	retu = None if _disable else handleCase(case_)
	printOutput(case_, retu, comment_=comment)
	if retu:
		_memory_sections.append(inst.get_memory_addr())

	if _times_cooldown != -1 and not var.Settings.show_times:
		_times_c_active = False
		_times_cooldown -= 1

	if retu:
		var.addr += len(retu)
		var.memory += retu
	index += 1
	# *** end ***

	if var.WaiterEvent.names:
		var.raiseError(
			"Event Handle Error",
			f"Assembler didn't handle an Event({' '.join(var.WaiterEvent.names)}).",
			line=index,
		)

_next_color = -1


def createTitle(title: str) -> str:
	global _next_color
	_next_color += 1
	return f"\n\033[40m * \033[{41 + _next_color % 7}m {title} \033[0m"


if var.waiters:
	var.raiseError(
		"Waiter Error",
		"A waiter didn't get a wanted value.",
	)
	print(" ".join(["(&" + ", &".join(waiter.names) + ")" for waiter in var.waiters]))

tmp = time.time() - start_t
print(createTitle("Process info"))
print("Size:", len(var.memory))
print(f"Time(μs): {tmp * 1_000_000:,.0f} ({tmp:,.3f}s)")

tmp = ""
for byte in var.memory:
	if byte == "##":
		print(tmp)
		tmp = ""
	else:
		tmp += byte + " "

if output_path == "":
	var.raiseError(
		"No Output Path",
		"No output file specified. (Use '-o <path>', DO NOT ADD EXTENSION)",
		False,
	)
	exit()

print(createTitle("Output Files"))
tmp = output_path + ".txt"
print(Colors.SECOND + tmp)
output_file = open(tmp, "w")
output_file.write(" ".join(var.memory))
output_file.close()

if var.waiters:
	print("Binary file is skipped becouse of waiters.", Colors.DARK)
	exit()

tmp = output_path + "_bin.bin"
output_file = open(tmp, "wb")
tmp2 = []
continue_write = True
for i in var.memory:
	if i == "XX":
		var.raiseError("Binary Error", "Found an 'XX' and no waiters left.")
		continue_write = False
		break
	tmp2.append(int(i, 16))
if continue_write:
	output_file.write(bytes(tmp2))
	print(tmp)
output_file.close()
del tmp2

if _perf_mode:
	exit()

print(createTitle("Constants"))
for const in var.consts:
	print(f"&{const}: {hex(var.consts[const])}({var.consts[const]})", end=" ")

print("\n" + createTitle("Error Statistics"))
if var.error_statistics:
	print(
		"\n".join([f"'{i}': {var.error_statistics[i]}" for i in var.error_statistics])
	)
else:
	print(f"{Colors.SECOND}Perfect! No errors found.")

print(createTitle("Memory"))

start_i = 0
_memory_sections.append(len(var.memory))
_new_line = 0
_tab_size_ofms = 27
_hor_amount = 4
for i in range(1, len(_memory_sections)):
	tmp = str(i - 1)
	tmp2 = _tab_size_ofms - (_memory_sections[i] - start_i) * 3
	_new_line += 1
	if tmp2 < 0:
		_new_line = 0
	print(
		f"\033[1m{Colors.DARK}{tmp}:{Colors.ENDL}{' ' * (3 - len(tmp))}",
		" ".join(var.memory[start_i : _memory_sections[i]]),
		end="\n" if _new_line % _hor_amount == 0 else " " + " " * tmp2,
	)

	start_i = _memory_sections[i]

while True:
	sector_inp = input(
		createTitle("Ndisasm")
		+ Colors.SECOND
		+ " Section of Memory('q' for quit)"
		+ Colors.ENDL
		+ " -> "
	)

	if sector_inp == "" or sector_inp == "q":
		break

	tmp2 = []
	value = int(sector_inp)
	continue_write = True
	for i in var.memory[_memory_sections[value] : _memory_sections[value + 1]]:
		if i == "XX":
			var.raiseError("Binary Error", "Found an 'XX'.")
			continue_write = False
			break
		tmp2.append(int(i, 16))
	if continue_write:
		ndisasm_file = open("ndisasm_tmp.bin", "wb")
		ndisasm_file.write(bytes(tmp2))
		ndisasm_file.close()

		os.system("ndisasm ndisasm_tmp.bin")
