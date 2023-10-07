"""
## Variables:
* $, $$, (<n1> (+ | -) <n2>...),
* 0x<hex>, <decimal>, 0b<bin>, &<name>, '<char>'
### Variables that removed in v1.0.1:
* $<const>, ?
### Code from v0.0.1-beta:
* process(v, s, n): zeroExtend(toHex(v, s), s, n)
* memProc(v, s): reverse(splitBytes(process(v, s, False)))
"""

import variables as var


def overflowError(size: int, expected: int, index: int | None = None) -> None:
	var.raiseError(
		"Overflow Error",
		f"Used size({var.str_size[size]}) is smaller than should({var.str_size[expected]}) be used.",
		line=index,
	)


def findSize(x: int, algin: bool = True, forge_sign: bool = False) -> int:
	"""
	This function calculates the size of a given integer value in bytes.
	### Args:
	* x (int): The integer value to calculate the size of.
	* algin (bool, optional): Makes return value powers of 2 (3 bytes -> 4 bytes (dword)). Defaults to True.
	* forge_sign (bool, optional): Whether or not to forge the sign bit. Defaults to False.
	### Returns:
	* int: The size of the integer value in bytes times 2.
	"""
	if not x:
		return var.BYTE

	if x < 0:
		x = (-x << 1) - 1
	elif forge_sign:
		x <<= 1

	if x > 0xFFFF_FFFF:
		var.raiseError(
			"Overflow Error",
			"This Assembler can't handle 64 bit integer.",
		)
		return var.DWORD

	tmp = 0
	while x:
		x >>= 8
		tmp += 2

	return var.DWORD if (tmp == 6 and algin) else tmp


class Types:
	reg = 0
	ptr_reg = 1
	const = 2
	ptr = 3
	else_ = 4

	str_type = ["reg", "ptr_reg", "const", "ptr", "else"]


def getRegister(x: str, mod: bool = True) -> tuple[int, int]:
	"""
	Returns the index and size of a register given its name.
	### Args:
	* x (str): The name of the register.
	* mod (bool, optional): Whether to return the index modulo the register index length. Defaults to True.
	### Returns:
	* tuple[int, int]: The index and size of the register.
	"""
	if x in var.seg_register:
		return var.seg_register.index(x), var.SEG_REG

	tmp = var.str_register.index(x[-2:])
	return (
		tmp % var.REG_INDEX_LEN if mod else tmp,
		var.DWORD
		if len(x) == 3
		else (var.BYTE if tmp < var.REG_INDEX_LEN else var.WORD),
	)


"""
This comment for you 'GitHub Copilot':
'a b c 123' is else cuz of spaces.
'eax' is a reg
'*eax' is a ptr_reg
'0x1234' is a const
'*0x1234' is a ptr
WARNING:
'(...)' is also a const
'$$' is also a const
'-10' is also a const
"""


def getType(x: str) -> int:
	if x[0] == '"' or " " in x:
		return Types.else_

	if x[0] == "*":
		if x[1].isalpha():
			return Types.ptr_reg
		return Types.ptr

	if x[0].isalpha():
		return Types.reg

	return Types.const


class Case:
	def __init__(
		self, command: str, size: int, index: int, args: list[str] | None
	) -> None:
		"""
		Initializes a Case object with the given command, size, index, and arguments.
		Args:
		* command (str): The command to be executed.
		* size (int): The size of the input.
		* index (int): The index of the input.
		* args (list[str] | None): The arguments to be passed to the command.
		Returns:
		* None
		"""
		self.type: list[int] | None
		self.args: list[int | str] | None
		self.waiters: list[var.Waiter] | None
		self.command = command
		self.input_size = size
		self.size = size

		if args == None:
			self.args = None
			self.type = None
			self.waiters = None
			return

		self.first_reg_size = 0
		self.waiters = []

		var.WaiterEvent.Next.start = var.addr - var.orgin
		var.WaiterEvent.Next.index = index

		self.args = []

		# Expections
		if command == "times":
			args[1] = args[1][1:-1]
			self.type = [Types.const, Types.else_]
		else:
			self.type = [getType(x) for x in args]

		if command == "con":
			self.type[0] = Types.else_

		if command[0] == ":":
			self.type = [Types.else_]
		# End of Expections

		const_waiters = []
		posiable_overflow = []
		for i in range(len(args)):
			arg = args[i]

			if self.type[i] == Types.ptr or self.type[i] == Types.ptr_reg:
				arg = arg[1:]
				var.WaiterEvent.Next.size = var.PTR_SIZE
			else:
				var.WaiterEvent.Next.size = self.size

			if self.type[i] == Types.reg or self.type[i] == Types.ptr_reg:
				tmp = getRegister(arg)
				if self.type[i] == Types.reg and self.size >= 0:
					self.size = tmp[1]
					if self.first_reg_size == 0:
						self.first_reg_size = tmp[1]
				self.args.append(tmp[0])
			elif self.type[i] == Types.const or self.type[i] == Types.ptr:
				value = var.computeInt(arg, True)
				if var.event != None:
					self.waiters.append(var.event)
					if self.type[i] == Types.const:
						const_waiters.append(var.event)
					var.event = None
				if self.type[i] == Types.const:
					tmp = findSize(value)
					if self.size < tmp:
						posiable_overflow.append(tmp)
				self.args.append(value)
			else:
				self.args.append(arg)

		for po in posiable_overflow:
			if self.size < po:
				overflowError(self.size, po, index)

		for cw in const_waiters:
			cw.size = self.size

	def __repr__(self) -> str:
		return f"Case({self.command}, {var.str_size[self.size]}, {None if self.type == None else [Types.str_type[i] for i in self.type]}, {None if self.args == None else self.args}, {self.waiters})"


def includedSplit(x: str, spliter: str, includeds: str) -> list[str]:
	retu: list[str] = []
	tmp = ""
	include = True
	for char in x:
		if char in includeds:
			include = not include
			tmp += char
		elif char in spliter and include:
			if tmp != "":
				retu.append(tmp)
				tmp = ""
		else:
			tmp += char
	retu.append(tmp)
	return retu


def splitCase(x: str, index: int) -> Case:
	"""
	Splits a string into a Case object.
	## Args:
	* x (str): The string to split.
	* index (int): The index of the string.
	## Returns:
	* Case: A Case object containing the paramaters of string.
	"""
	tmp = x.split(maxsplit=1)
	command = tmp[0]
	if command[0] == ":":
		return Case(command, 0, index, None if len(tmp) == 1 else [tmp[1]])

	if len(tmp) == 2 and tmp[1][0] == ".":
		tmp = tmp[1].split(maxsplit=1)
		size = var.sizes[tmp[0][1:]]
	else:
		size = var.BYTE if command == "def" else var.WORD

	if len(tmp) == 1:
		return Case(command, size, index, None)
	args = includedSplit(tmp[1], ",", """"'()""")
	return Case(command, size, index, [arg.strip() for arg in args])


if __name__ == "__main__":
	case1 = splitCase("mov .byte *eax, 0x1234", 0)
	print(case1.command, case1.size, case1.type, case1.args)

	case2 = splitCase("mov .byte", 0)
	print(case2.command, case2.size, case2.type, case2.args)

	case3 = splitCase("con abc 123", 0)
	print(case3.command, case3.size, case3.type, case3.args)

	case3 = splitCase("nop", 0)
	print(case3.command, case3.size, case3.type, case3.args)
