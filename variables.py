"""
## variables.py:
* Sizes				(Line 68)
* no_input_inst		(Line 320)
* jcc_inst			(Line 354)
* shift_inst		(Line 396)
* type1-2-3_inst	(Line 400-430)
* push-pop-segments	(Line 442)
"""

from typing import Any


class Settings:
	tab_size = 24
	force_exit = -1
	skip_print = False
	skip_times = False
	show_times = False
	print_error = True
	debug = True
	overflow_errors = True

	# Visual Settings:
	print_breakpoint = True
	linewrite_msg = True
	autowaitersys_msg = True

	@staticmethod
	def mode(*args: Any) -> None:
		Settings.force_exit = args[0]
		Settings.skip_print = args[1]
		Settings.skip_times = args[2]
		Settings.show_times = args[3]
		Settings.print_error = args[4]
		Settings.debug = args[5]

	@staticmethod
	def mode_verbose(*args: bool) -> None:
		Settings.print_breakpoint = args[0]
		Settings.linewrite_msg = args[1]
		Settings.autowaitersys_msg = args[2]


class Colors:
	ENDL = "\033[0m"
	ITALIC = "\033[3m"
	DARK = "\033[90m"
	WARNING = "\033[32m"
	ERROR = "\033[31m"
	SECOND = "\033[34m"
	PINK = "\033[94m"
	GREEN = "\033[93m"


memory: list[str] = []
consts: dict[str, int] = {}
addr = 0
orgin = 0

# BIT_32 = 0x66
STR_BIT_32 = "66"

FORCE_A_REG = -2
SEG_REG = -1
BYTE = 2
WORD = 4
DWORD = 8


def unitSize(x: int) -> int:
	return x >> 1


PTR_SIZE = WORD
UNIT_PTR_SIZE = unitSize(WORD)


sizes = {
	"b": BYTE,
	"w": WORD,
	"d": DWORD,
	"byte": BYTE,
	"word": WORD,
	"dword": DWORD,
	"x8": BYTE,
	"x16": WORD,
	"x32": DWORD,
	"short": BYTE,
	"near": WORD,
	"long": DWORD,
	"far": DWORD,
	"a-reg": FORCE_A_REG,
}

str_size = {
	FORCE_A_REG: "a-reg",
	SEG_REG: "seg-reg",
	0: "zero",
	BYTE: "byte",
	WORD: "word",
	DWORD: "dword",
}


def replaceMemory(start: int, values: list[str]) -> None:
	for i in range(len(values)):
		memory[start + i] = values[i]


class WaiterEvent:
	names: list[str] = []
	signs: list[bool] = []
	_added = False

	class Next:
		start = 0
		index = 0
		size = 0

		@staticmethod
		def set(start: int, index: int, size: int) -> None:
			WaiterEvent.Next.start = start
			WaiterEvent.Next.index = index
			WaiterEvent.Next.size = size

	@staticmethod
	def addName(x: str) -> None:
		WaiterEvent.names.append(x)
		WaiterEvent._added = True

	@staticmethod
	def addSign(x: bool) -> None:
		if WaiterEvent._added:
			WaiterEvent.signs.append(x)
			WaiterEvent._added = False

	@staticmethod
	def clear() -> None:
		WaiterEvent.names.clear()
		WaiterEvent.signs.clear()


event: Any = None
error_statistics = {}


def raiseError(
	title: str, msg: str, error: bool = True, line: int | None = None
) -> None:
	if msg not in error_statistics:
		error_statistics[msg] = 1
	else:
		error_statistics[msg] += 1
	if Settings.print_error:
		print(
			Colors.WARNING + title + ":",
			(Colors.ERROR if error else Colors.SECOND) + msg + Colors.ENDL,
			f"{Colors.ITALIC}(Line {line if line != None else '?'}){Colors.ENDL}",
		)
	if error and Settings.force_exit != -1:
		if Settings.force_exit == 0:
			exit()
		Settings.force_exit -= 1


def toInt(x: str) -> int:
	if x == "$":
		return addr
	if x == "$$":
		return orgin
	if x[0] == "&":
		x = x[1:]
		if x in consts:
			return consts[x]
		WaiterEvent.addName(x)
		return 0
	if x[0] == "'" and x[2] == "'" and len(x) == 3:
		return ord(x[1])
	if x[0] == "^":
		return 1 << toInt(x[1:])
	return int(x, 0)


def toSignInt(x: str) -> int:
	sign = x[0] == "-"
	value = toInt(x[1:] if sign or x[0] == "+" else x)
	WaiterEvent.addSign(sign)
	return -value if sign else value


def calculateInt(x: str) -> int:
	tmp = ""
	retu = 0
	sign = x[0] == "-"
	if sign or x[0] == "+":
		x = x[1:]
	for char in x:
		sign_tmp = char == "-"
		if sign_tmp or char == "+":
			retu += -toInt(tmp) if sign else toInt(tmp)
			WaiterEvent.addSign(sign)
			tmp = ""
			sign = sign_tmp
		elif tmp != " ":
			tmp += char
	retu += -toInt(tmp) if sign else toInt(tmp)
	WaiterEvent.addSign(sign)
	return retu


def computeInt(x: str, _waiter_to_event: bool = False) -> int | None:
	global event
	x = x.strip()
	value = calculateInt(x[1:-1]) if x[0] == "(" and x[-1] == ")" else toSignInt(x)
	if WaiterEvent.names:
		waiters.append(
			Waiter(
				WaiterEvent.Next.start,
				value,
				WaiterEvent.Next.index,
				WaiterEvent.Next.size,
			)
		)
		if _waiter_to_event:
			event = waiters[-1]
		return None
	return value


def toHex(x: int, size: int = BYTE) -> str:
	tmp = 1 << (size << 2)
	if x >= tmp:
		raiseError(
			"Overflow Error",
			f"toHex function found an input 'x'({x}) thats bigger than the input size({str_size[size]}, {tmp}).",
			Settings.overflow_errors,
		)
	return hex(x % tmp)[2:]


def zeroExtend(x: str, size: int = BYTE) -> str:
	tmp = size - len(x)
	if tmp < 0:
		raiseError(
			"Overflow Warning",
			"zeroExtend function found an Negative value, so return will be Shrink of input",
			Settings.overflow_errors,
		)
		return x[-tmp:]
	return "0" * tmp + x


def splitBytes(x: str) -> list[str]:
	if len(x) % 2 != 0:
		raiseError(
			"Warning",
			f"splitBytes did get an string({x}) with odd length.",
			False,
		)
	return [x[i : i + BYTE] for i in range(0, len(x), BYTE)]


def memoryProcess(x: int | None, size: int) -> list[str]:
	if x == None:
		if Settings.autowaitersys_msg:
			raiseError("Auto Waiter Sys", "memoryProcess function got an None value and return XX.", False)
		return ["XX"] * unitSize(size)
	tmp = splitBytes(zeroExtend(toHex(x, size), size))
	tmp.reverse()
	return tmp


class Waiter:
	"""
	When a constant value cant found its triggers an waiter.
	## Release Notes
	### Lasm-v1.0.1
	* Waiters get name and sign values by itself then clear.
	### Lasm-v1.1.0
	* Now waiters automatically added when there is an Next event value.
	"""

	def __init__(self, start: int, bias: int, index: int, size: int) -> None:
		self.NAMES = WaiterEvent.names.copy()
		self.names = WaiterEvent.names.copy()
		self.signs = WaiterEvent.signs.copy()
		WaiterEvent.clear()

		self.bias = bias
		self.start = start
		self.index = index
		self.size = size

	def check(self, name: str) -> bool:
		if name in self.names:
			self.names.remove(name)
		if self.names:
			return False
		replaceMemory(
			self.start,
			memoryProcess(
				self.bias
				+ sum(
					[
						-consts[self.NAMES[i]]
						if self.signs[i]
						else consts[self.NAMES[i]]
						for i in range(len(self.NAMES))
					]
				),
				self.size,
			),
		)
		return True
	
	def __repr__(self) -> str:
		return f"Waiter(bias={self.bias}, start={self.start}, index={self.index}, size={self.size})"


waiters: list[Waiter] = []

register_8 = ["al", "cl", "dl", "bl", "ah", "ch", "dh", "bh"]
register_16_32 = ["ax", "cx", "dx", "bx", "sp", "bp", "si", "di"]
seg_register = ["es", "cs", "ss", "ds", "fs", "gs"]

str_register = register_8 + register_16_32

# REGS_LEN = 16
REG_INDEX_LEN = 8

no_input_inst = {
	"nop": ["90"],
	"hlt": ["f4"],
	"cmc": ["f5"],
	"clc": ["f8"],
	"stc": ["f9"],
	"cli": ["fa"],
	"sti": ["fb"],
	"cld": ["fc"],
	"std": ["fd"],
	"pusha": ["60"],
	"popa": ["61"],
	"pushad": [STR_BIT_32, "60"],
	"popad": [STR_BIT_32, "61"],
	"ret": ["c3"],
	"sret": ["c3"],
	"fret": ["cb"],
	"int3": ["cc"],
	"int0": ["ce"],
	"int1": ["f1"],
	"syscall": ["0f", "05"],
	"stosb": ["aa"],
	"stosw": ["ab"],
	"stosd": [STR_BIT_32, "ab"],
	"lodsb": ["ac"],
	"lodsw": ["ad"],
	"lodsd": [STR_BIT_32, "ad"],
}  # TODO: Add all string instructions.

# mbr: 0x55AA
# borg: 0x7C00
# hkb: 0x200

# Jump if condition (.short)
jcc_inst = {
	"jo": 0x70,
	"jno": 0x71,
	"jb": 0x72,
	"jc": 0x72,
	"jnae": 0x72,
	"jnb": 0x73,
	"jnc": 0x73,
	"jae": 0x73,
	"je": 0x74,
	"jz": 0x74,
	"jne": 0x75,
	"jnz": 0x75,
	"jbe": 0x76,
	"jna": 0x76,
	"ja": 0x77,
	"jnbe": 0x77,
	"js": 0x78,
	"jns": 0x79,
	"jpe": 0x7A,
	"jp": 0x7A,
	"jpo": 0x7B,
	"jnp": 0x7B,
	"jnge": 0x7C,
	"jl": 0x7C,
	"jge": 0x7D,
	"jnl": 0x7D,
	"jle": 0x7E,
	"jng": 0x7E,
	"jnle": 0x7F,
	"jg": 0x7F,
	"jcxz": 0xE3,
}

shift_inst: dict[str, tuple[int, str]] = {"shl": (0xE0, "26")}
shift_names = ["rol", "ror", "rcl", "rcr", "sal", "shr", "sar"]

for i in range(len(shift_names)):
	byte_x = i << 3
	shift_inst[shift_names[i]] = (
		0xC0 + byte_x,
		zeroExtend(hex(0x06 + byte_x)[2:]),
	)

del shift_names

type1_inst = {
	"inc": (0xC0, 0xFE, "06"),
	"dec": (0xC8, 0xFE, "0e"),
	"not": (0xD0, 0xF6, "16"),
	"neg": (0xD8, 0xF6, "1e"),
}

type2_inst = {
	"push": (0x50, "ff", "36"),
	"pop": (0x58, "8f", "06"),
}

type4_inst = {
	"mul": (0xE0, "26"),
	"div": (0xF0, "36"),
}

# (0x04 + 8x, 0xC0 + 8x, 8x, str(0x06 + 8x))
type3_inst: dict[str, tuple[int, int, int, str]] = {}
type3_names = ["add", "or", "adc", "sbb", "and", "sub", "xor", "cmp"]

for i in range(len(type3_names)):
	byte_x = i << 3
	type3_inst[type3_names[i]] = (
		0x04 + byte_x,
		0xC0 + byte_x,
		byte_x,
		zeroExtend(hex(0x06 + byte_x)[2:]),
	)

del type3_names

push_segment_values = [
	["06"],
	["0e"],
	["16"],
	["1e"],
	["0f", "a0"],
	["0f", "a8"],
]

pop_segment_values = [
	["07"],
	None,
	["17"],
	["1f"],
	["0f", "a1"],
	["0f", "a9"],
]

"""
* Lasm-v1.0.0
_test_cases_file = open("test_cases.txt")
test_cases = _split_list(_test_cases_file.readlines())
_test_cases_file.close()
"""


if __name__ == "__main__":
	memory = ["??" for _ in range(10)]

	def add_const(name: str, value: int) -> None:
		consts[name] = value
		for waiter in waiters:
			if waiter.check(name):
				waiters.remove(waiter)

	WaiterEvent.Next.set(1, 0, DWORD)
	computeInt("(-0x1+&num)")
	print(" ".join(memory))

	add_const("num", 0xF011)
	print(" ".join(memory))
