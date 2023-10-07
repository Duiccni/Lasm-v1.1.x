"""
## Release Notes:
### 1.0.x -> 1.1.x:
* Becouse of the new Waiter system, the `Case` class has been changed.
* The `Case` class now has a `waiters` and `input_size` attribute.
* Becouse of the new system now code dont need to be repeated,
  and code size reduced by 86%.
## 2 Inputs:
* add
* or
* adc
* sbb
* and
* sub
* xor
* cmp
"""

import variables as var
import functions as func
from typing import Any, Callable, SupportsIndex

index_ = 0


def fhex(__number: int | SupportsIndex) -> str:
	"""
	Return the hexadecimal representation of an integer without '0x' symbol.
	>>> fhex(12648430)
	'c0ffee'
	"""
	return hex(__number)[2:]


def get_memory_addr() -> int:
	"""
	Returns the current memory address.
	>>> get_memory_addr()
	var.addr - var.orgin
	"""
	return var.addr - var.orgin


def C_int(case_: func.Case) -> list[str]:
	return ["cd", var.zeroExtend(fhex(case_.args[0]))]


def C_def(case_: func.Case) -> list[str]:
	retu: list[str] = []
	waiter_index = 0
	for i in range(len(case_.args)):
		if case_.type[i] == func.Types.else_:
			retu += [var.zeroExtend(fhex(ord(char))) for char in case_.args[i][1:-1]]
		else:
			if case_.args[i] == None:
				case_.waiters[waiter_index].start += i * var.unitSize(case_.size)
				waiter_index += 1
				retu += ["XX"] * var.unitSize(case_.size)
				continue
			retu += var.memoryProcess(case_.args[i], case_.size)
	return retu


def _jmp_call_main(case_: func.Case, type: bool) -> list[str]:
	if case_.type[0] == func.Types.reg:
		return ([var.STR_BIT_32] if case_.size == var.DWORD else []) + [
			"ff",
			fhex((0xD0 if type else 0xE0) + case_.args[0]),
		]
	cmd_size = 1 + (case_.size == var.DWORD)

	if case_.args[0] == None:
		case_.waiters[0].start += cmd_size
		case_.waiters[0].bias += -(cmd_size + var.unitSize(case_.size) + var.addr)
		memory_value = ["XX"] * var.unitSize(case_.size)
	else:
		number = case_.args[0] - var.addr
		if number == 0:
			return ["eb", "fe"]
		number -= cmd_size + var.unitSize(case_.size)
		memory_value = var.memoryProcess(number, case_.size)

	return (
		([var.STR_BIT_32] if case_.size == var.DWORD else [])
		+ [("e8" if type else ("eb" if case_.size == var.BYTE else "e9"))]
		+ memory_value
	)


def C_jmp(case_: func.Case) -> list[str]:
	return _jmp_call_main(case_, False)


def C_call(case_: func.Case) -> list[str]:
	return _jmp_call_main(case_, True)


def _global_sub(size: int, bias: int):
	return ([var.STR_BIT_32] if size == var.DWORD else []) + [
		var.zeroExtend(fhex(bias + (size != var.BYTE)))
	]


def _global_main(case_: func.Case, args: tuple[int, int, str]) -> list[str]:
	if case_.type[0] == func.Types.reg:
		return _global_sub(case_.size, args[1]) + [fhex(args[0] + case_.args[0])]

	if case_.args[0] == None:
		case_.waiters[0].start += 2 + (case_.size == var.DWORD)
		memory_value = ["XX"] * var.UNIT_PTR_SIZE
	else:
		memory_value = var.memoryProcess(case_.args[0], var.PTR_SIZE)

	return _global_sub(case_.size, args[1]) + [args[2]] + memory_value


def C_not(case_: func.Case) -> list[str]:
	return _global_main(case_, var.type1_inst["not"])


def C_neg(case_: func.Case) -> list[str]:
	return _global_main(case_, var.type1_inst["neg"])


def _mul8plus6(x: int) -> int:
	return (x << 3) + 6


def _mov_sub(case_: func.Case) -> list[str]:
	ptr_index = case_.type[1] == func.Types.ptr
	arg_reg = case_.args[ptr_index ^ 1]
	arg_ptr = case_.args[ptr_index]
	if arg_ptr == None:
		memory_value = ["XX"] * var.UNIT_PTR_SIZE
		if arg_reg != 0 and case_.size != var.SEG_REG:
			case_.waiters[0].start += 1
	else:
		memory_value = var.memoryProcess(arg_ptr, var.PTR_SIZE)
	if arg_reg == 0:
		return _global_sub(case_.size, 0xA0 if ptr_index else 0xA2) + memory_value
	if case_.size == var.SEG_REG:
		return [
			"8e" if ptr_index else "8c",
			var.zeroExtend(fhex(_mul8plus6(arg_reg))),
		] + memory_value
	return (
		_global_sub(case_.size, 0x88 + (ptr_index << 1))
		+ [var.zeroExtend(fhex(_mul8plus6(arg_reg)))]
		+ memory_value
	)


def __inst_err(type: list[int], cmd: str) -> None:
	var.raiseError(
		f"Instruction '{cmd}'",
		f"'{cmd} <{func.Types.str_type[type[0]]}>, <{func.Types.str_type[type[1]]}>' there no such a command.",
	)


def C_mov(case_: func.Case) -> list[str] | None:
	retu: list[str] = []

	if None in case_.args:
		case_.waiters[0].start = get_memory_addr() + 1 + (case_.size == var.DWORD)

	match case_.type[0]:
		case func.Types.reg:
			match case_.type[1]:
				case func.Types.const:
					retu.append(
						fhex(0xB0 + case_.args[0] + ((case_.size != var.BYTE) << 3))
					)
					retu += (
						["XX"] * var.unitSize(case_.size)
						if case_.args[1] == None
						else var.memoryProcess(case_.args[1], case_.size)
					)
				case func.Types.ptr:
					return _mov_sub(case_)
				case func.Types.reg:
					if case_.size == var.SEG_REG:
						# Reverse of normal register
						return ["8e", fhex(0xC0 + case_.args[1] + (case_.args[0] << 3))]
					if case_.args[0] == case_.args[1]:
						var.raiseError(
							"Warning",
							"You are trying to move a register to itself.",
							line=index_,
						)
					retu.append("88" if case_.size == var.BYTE else "89")
					retu.append(fhex(0xC0 + case_.args[0] + (case_.args[1] << 3)))
				case _:
					__inst_err(case_.type, "mov")
					return
		case func.Types.ptr:
			match case_.type[1]:
				case func.Types.reg:
					return _mov_sub(case_)
				case func.Types.const:
					retu.append("c6" if case_.size == var.BYTE else "c7")
					retu.append("06")

					if case_.args[0] == None:
						retu += ["XX"] * var.UNIT_PTR_SIZE
						case_.waiters[0].start += 1
					else:
						retu += var.memoryProcess(case_.args[0], var.PTR_SIZE)

					if case_.args[1] == None:
						retu += ["XX"] * var.unitSize(case_.size)
						if len(case_.waiters) == 1:
							case_.waiters[0].start += var.UNIT_PTR_SIZE + 1
						else:
							case_.waiters[1].start = (
								case_.waiters[0].start + var.UNIT_PTR_SIZE
							)
					else:
						retu += var.memoryProcess(case_.args[1], case_.size)
				case _:
					__inst_err(case_.type, "mov")
					return
		case _:
			__inst_err(case_.type, "mov")
			return

	return [var.STR_BIT_32] + retu if case_.size == var.DWORD else retu


def C_inc_dec(case_: func.Case) -> list[str]:
	is_dec = case_.command == "dec"
	if case_.type[0] == func.Types.reg and case_.size != var.BYTE:
		return ([var.STR_BIT_32] if case_.size == var.DWORD else []) + [
			fhex(0x48 if is_dec else 0x40 + case_.args[0])
		]
	return _global_main(case_, var.type1_inst["dec" if is_dec else "inc"])


def C_push_pop(case_: func.Case) -> list[str] | None:
	retu: list[str] = []
	args = var.type2_inst[case_.command]
	if case_.type[0] == func.Types.reg:
		if case_.size == var.BYTE:
			var.raiseError("Push Error", "Cant use 8 bit registers.", line=index_)
			return
		if case_.size == var.SEG_REG:
			if args[0] == 0x50:
				return var.push_segment_values[case_.args[0]]
			return var.pop_segment_values[case_.args[0]]
		retu.append(fhex(args[0] + case_.args[0]))
	elif case_.type[0] == func.Types.ptr:
		retu.append(args[1])
		retu.append(args[2])
		if case_.args[0] == None:
			case_.waiters[0].start += 2 + (case_.size == var.DWORD)
		retu += var.memoryProcess(case_.args[0], var.PTR_SIZE)
	elif case_.type[0] == func.Types.const and args[0] == 0x50:
		retu.append("6a" if case_.size == var.BYTE else "68")
		if case_.args[0] == None:
			case_.waiters[0].start += 1 + (case_.size == var.DWORD)
		retu += var.memoryProcess(case_.args[0], case_.size)
	else:
		return
	return [var.STR_BIT_32] + retu if case_.size == var.DWORD else retu


def C_lodsx(case_: func.Case) -> list[str]:
	return _global_sub(case_.size, 0xAC)


# So much simmilar with _mov_sub()
def _2input_ptr_reg_comb(case_: func.Case, bias: int) -> list[str]:
	ptr_index = case_.type[1] == func.Types.ptr
	arg_reg = case_.args[ptr_index ^ 1]
	arg_ptr = case_.args[ptr_index]
	if arg_ptr == None:
		memory_value = ["XX"] * var.UNIT_PTR_SIZE
		case_.waiters[0].start += 1
	else:
		memory_value = var.memoryProcess(arg_ptr, var.PTR_SIZE)
	return (
		_global_sub(case_.size, bias + (ptr_index << 1))
		+ [var.zeroExtend(fhex(_mul8plus6(arg_reg)))]
		+ memory_value
	)


def C_2inputs(case_: func.Case) -> list[str] | None:
	args = var.type3_inst[case_.command]

	retu: list[str] = []

	if case_.size == var.SEG_REG:
		var.raiseError(
			"Segment Reg",
			"By my knowladge, Segment registers can't be used in this 2 input commands.",
			False,
			index_,
		)
		return

	if None in case_.args:
		case_.waiters[0].start = get_memory_addr() + 1 + (case_.size == var.DWORD)

	match case_.type[0]:
		case func.Types.reg:
			match case_.type[1]:
				case func.Types.const:
					"""
					add ax, 0x43
					add .a-reg ax, 0x43  # Forces to use Special a-reg(eax, ax, al) command register

					if const value provokes an waiter, extented byte values automaticly disable.
					"""
					is_byte = (
						case_.size != var.BYTE
						and None not in case_.args
						and func.findSize(case_.args[1]) == var.BYTE
						and case_.input_size != var.FORCE_A_REG
					)
					if case_.args[0] == 0 and not is_byte:
						retu.append(
							var.zeroExtend(fhex(args[0] + (case_.size != var.BYTE)))
						)
					else:
						retu.append(
							"83"
							if is_byte
							else ("80" if case_.size == var.BYTE else "81")
						)
						retu.append(fhex(args[1] + case_.args[0]))
					retu += var.memoryProcess(
						case_.args[1], var.BYTE if is_byte else case_.size
					)
				case func.Types.ptr:
					return _2input_ptr_reg_comb(case_, args[2])
				case func.Types.reg:
					retu.append(
						var.zeroExtend(fhex(args[2] + (case_.size != var.BYTE)))
					)
					retu.append(fhex(0xC0 + case_.args[0] + (case_.args[1] << 3)))
				case _:
					__inst_err(case_.type, case_.command)
					return
		case func.Types.ptr:
			match case_.type[1]:
				case func.Types.reg:
					return _2input_ptr_reg_comb(case_, args[2])
				case func.Types.const:
					retu.append("80" if case_.size == var.BYTE else "81")
					retu.append(args[3])

					if case_.args[0] == None:
						retu += ["XX"] * var.UNIT_PTR_SIZE
						case_.waiters[0].start += 1
					else:
						retu += var.memoryProcess(case_.args[0], var.PTR_SIZE)

					if case_.args[1] == None:
						retu += ["XX"] * var.unitSize(case_.size)
						if len(case_.waiters) == 1:
							case_.waiters[0].start += var.UNIT_PTR_SIZE + 1
						else:
							case_.waiters[1].start = (
								case_.waiters[0].start + var.UNIT_PTR_SIZE
							)
					else:
						retu += var.memoryProcess(case_.args[1], case_.size)
				case _:
					__inst_err(case_.type, case_.command)
					return
		case _:
			__inst_err(case_.type, case_.command)
			return
	return [var.STR_BIT_32] + retu if case_.size == var.DWORD else retu


def C_jcc(case_: func.Case) -> list[str]:
	cmd_size = 1 + (case_.size == var.DWORD) + (case_.size != var.BYTE)

	if case_.args[0] == None:
		case_.waiters[0].start += cmd_size
		case_.waiters[0].bias += -(cmd_size + var.unitSize(case_.size) + var.addr)
		memory_value = ["XX"] * var.unitSize(case_.size)
	else:
		number = case_.args[0] - var.addr - cmd_size - var.unitSize(case_.size)
		memory_value = var.memoryProcess(number, case_.size)

	inst = var.jcc_inst[case_.command]
	return (
		([var.STR_BIT_32] if case_.size == var.DWORD else [])
		+ ([fhex(inst)] if case_.size == var.BYTE else ["0f", fhex(inst + 0x10)])
		+ memory_value
	)


def C_shift(case_: func.Case) -> list[str]:
	value = (
		1
		if len(case_.args) == 1
		else (
			-1
			if case_.type[1] == func.Types.reg and case_.args[1] == 1
			else case_.args[1]
		)
	)

	if value == 0:
		for waiter in case_.waiters:
			del waiter
		var.raiseError(
			"Warning",
			"Shift value is 0, this command will be ignored.",
			False,
			index_,
		)
		return

	retu: list[str] = []

	if case_.type[0] == func.Types.reg:
		case_.size = case_.first_reg_size
		retu.append("d3" if value == -1 else ("d1" if value == 1 else "c1"))
		retu.append(fhex(var.shift_inst[case_.command][0] + case_.args[0]))
	elif case_.type[0] == func.Types.ptr:
		retu.append(
			fhex(
				(0xD3 if value == -1 else (0xD0 if value == 1 else 0xC0))
				+ (case_.size != var.BYTE)
			)
		)
		retu.append(var.shift_inst[case_.command][1])
		if case_.args[0] == None:
			case_.waiters[0].start += 2 + (case_.size == var.DWORD)
			retu += ["XX"] * var.UNIT_PTR_SIZE
		else:
			retu += var.memoryProcess(case_.args[0], var.PTR_SIZE)
	if value > 1:
		retu.append(var.zeroExtend(fhex(value)))
	return [var.STR_BIT_32] + retu if case_.size == var.DWORD else retu


def C_test(case_: func.Case) -> list[str] | None:
	retu: list[str] = []

	if case_.size == var.SEG_REG:
		return

	if case_.args[1] == None:
		case_.waiters[0].start = get_memory_addr() + 1 + (case_.size == var.DWORD)

	if case_.type[0] == func.Types.reg:
		match case_.type[1]:
			case func.Types.const:
				if case_.args[0] == 0:
					retu.append("a8" if case_.size == var.BYTE else "a9")
				else:
					retu.append("f6" if case_.size == var.BYTE else "f7")
					retu.append(fhex(0xC0 + case_.args[0]))
					if case_.args[1] == None:
						case_.waiters[0].start += 1
				if case_.args[1] == None:
					retu += ["XX"] * var.unitSize(case_.size)
				else:
					retu += var.memoryProcess(case_.args[1], case_.size)
			case func.Types.reg:
				retu.append("84" if case_.size == var.BYTE else "85")
				retu.append(fhex(0xC0 + case_.args[0] + (case_.args[1] << 3)))
			case _:
				__inst_err(case_.type, "test")
				return
	else:
		__inst_err(case_.type, "test")
		return
	return [var.STR_BIT_32] + retu if case_.size == var.DWORD else retu


basic_dir = {
	"int": C_int,
	"def": C_def,
	"jmp": C_jmp,
	"call": C_call,
	"not": C_not,
	"neg": C_neg,
	"mov": C_mov,
	"inc": C_inc_dec,
	"dec": C_inc_dec,
	"push": C_push_pop,
	"pop": C_push_pop,
	"lods": C_lodsx,
	"test": C_test,
}

for cmd in var.type3_inst:
	basic_dir[cmd] = C_2inputs

for cmd in var.jcc_inst:
	basic_dir[cmd] = C_jcc

for cmd in var.shift_inst:
	basic_dir[cmd] = C_shift
