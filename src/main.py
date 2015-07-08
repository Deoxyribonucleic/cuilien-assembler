import sys
import re
import struct


data_instructions = {
	"ALLOC_BYTE": 1,
	"ALLOC_SHORT": 2,
	"ALLOC_LONG": 4
}

instructions = {
	"NOP":	{"opcode": 0x0000, "operands": 0},
	"HALT":	{"opcode": 0x0001, "operands": 0},
	"INT":	{"opcode": 0x0002, "operands": 0},
	"MOV":	{"opcode": 0x0003, "operands": 2},
	"JMP":	{"opcode": 0x0004, "operands": 1},
	"INC":	{"opcode": 0x0006, "operands": 1},
	"DEC":	{"opcode": 0x0007, "operands": 1},
	"ADD":	{"opcode": 0x000A, "operands": 2},
	"SUB":	{"opcode": 0x000B, "operands": 2},
	"MUL":	{"opcode": 0x000C, "operands": 2},
	"DIV":	{"opcode": 0x000D, "operands": 2},
	"SHOW":	{"opcode": 0x0010, "operands": 1},
	"CMP":	{"opcode": 0x0020, "operands": 2},
	"TEST":	{"opcode": 0x0022, "operands": 1},
	"JZ":	{"opcode": 0x0024, "operands": 1},
	"JNZ":	{"opcode": 0x0025, "operands": 1},
	"JEQ":	{"opcode": 0x0026, "operands": 1},
	"JNEQ":	{"opcode": 0x0027, "operands": 1},
	"JGT":	{"opcode": 0x0028, "operands": 1},
	"JNGT":	{"opcode": 0x0029, "operands": 1},
	"JLT":	{"opcode": 0x002A, "operands": 1},
	"JNLT":	{"opcode": 0x002B, "operands": 1},
	"AND":	{"opcode": 0x0040, "operands": 2},
	"OR":	{"opcode": 0x0041, "operands": 2},
	"XOR":	{"opcode": 0x0042, "operands": 2},
	"NOT":	{"opcode": 0x0043, "operands": 1},
	"PUSH":	{"opcode": 0x0050, "operands": 1},
	"POP":	{"opcode": 0x0051, "operands": 1},
	"CALL":	{"opcode": 0x0060, "operands": 1},
	"RET":	{"opcode": 0x0061, "operands": 0},
	"PUTC":	{"opcode": 0x0070, "operands": 1}
}

registers = {
	"A": 1,
	"B": 2,
	"C": 3,
	"D": 4,
	"IP": 5,
	"SP": 6,
	"FLAGS": 7
}


class CASMError(BaseException):
	def __init__(self, line):
		self.line = line

	def what(self):
		return "line %d: %s: %s"%(self.line, self.error_type(), self.error_string())

	def error_type(self):
		return "general"

	def error_string(self):
		return "unknown"


class CASMSyntaxError(CASMError):
	def __init__(self, line, error):
		super(CASMSyntaxError, self).__init__(line)
		self.error = error

	def error_type(self):
		return "syntax error"

	def error_string(self):
		return self.error


class CASMMnemonicError(CASMError):
	def __init__(self, line, mnemonic):
		super(CASMMnemonicError, self).__init__(line)
		self.mnemonic = mnemonic

	def error_type(self):
		return "mnemonic error"

	def error_string(self):
		return "unknown mnemonic '" + self.mnemonic + "'"


class CASMSymbolError(CASMError):
	def __init__(self, line, symbol):
		super(CASMSymbolError, self).__init__(line)
		self.symbol = symbol

	def error_type(self):
		return "symbol error"

	def error_string(self):
		return "unresolved symbol '" + self.symbol + "'"


class CASMOperandError(CASMError):
	def __init__(self, line, mnemonic, expected, actual):
		super(CASMOperandError, self).__init__(line)
		self.mnemonic = mnemonic
		self.expected = expected
		self.actual = actual

	def error_type(self):
		return "operand error"

	def error_string(self):
		return "instruction %s requires exactly %s operands (was given %d)"%(self.mnemonic, self.expected, self.actual)


def tokenize(line_number, line):
	# Behold the glory that is regular expressions
	# ^\s*([a-z_]+)(\s+((long|short|byte|)\s*([\[\]a-z0-9_]+)\s*(,\s*((long|short|byte|)\s*([\[\]a-z0-9_]+)))?)?)?\s*($|[#;])
	match = re.search("^\\s*([a-z_]+)(\\s+((long|short|byte|)\\s*([\\[\\]a-z0-9_]+)\\s*(,\\s*((long|short|byte|)\\s*([\\[\\]a-z0-9_]+)))?)?)?\\s*($|[#;])", line, re.IGNORECASE)
	if match:
		return {
			"mnemonic": match.group(1),
			"op1size": match.group(4),
			"op1": match.group(5),
			"op2size": match.group(8),
			"op2": match.group(9)
		}
	else:
		raise CASMSyntaxError(line_number, "invalid syntax or invalid size specifier")


def get_size(size_string):
	if size_string.upper()=="BYTE":
		return 1
	elif size_string.upper()=="SHORT":
		return 2
	else:
		return 4


def get_operand(line_number, operand_string):
	match = re.match("^\\[([a-z0-9]+)\\]$", operand_string, re.IGNORECASE)
	try:
		if match:
			if match.group(1).upper() in registers:
				return {"register": True, "dereference": True, "symbol": False, "value": registers[match.group(1).upper()]}
			elif re.match("[a-z]", match.group(1)[:1], re.IGNORECASE):
				return {"register": False, "dereference": True, "symbol": True, "value": match.group(1)}
			else:
				return {"register": False, "dereference": True, "symbol": False, "value": int(match.group(1), 0)}
		else:
			if operand_string.upper() in registers:
				return {"register": True, "dereference": False, "symbol": False, "value": registers[operand_string.upper()]}
			elif re.match("[a-z]", operand_string[:1], re.IGNORECASE):
				return {"register": False, "dereference": False, "symbol": True, "value": operand_string}
			else:
				return {"register": False, "dereference": False, "symbol": False, "value": int(operand_string, 0)}
	except ValueError:
		raise CASMSyntaxError(line_number, "bad operand at '%s'"%operand_string)


def make_instruction(line_number, tokens):
	if tokens["mnemonic"].upper() in instructions:
		instruction_info = instructions[tokens["mnemonic"].upper()]
		instruction = {"type": "instruction", "info": instruction_info, "line": line_number}

		operand_count = 0;
		if tokens["op1"]!=None:
			operand_count += 1
		if tokens["op2"]!=None:
			operand_count += 1

		if instruction_info["operands"] != operand_count:
			raise CASMOperandError(line_number, tokens["mnemonic"].upper(), instruction_info["operands"], operand_count)

		if tokens["op1"]!=None:
			instruction["op1"] = {
				"size": get_size(tokens["op1size"]),
				"data": get_operand(line_number, tokens["op1"])
			}

		if tokens["op2"]!=None:
			instruction["op2"] = {
				"size": get_size(tokens["op2size"]),
				"data": get_operand(line_number, tokens["op2"])
			}

		return instruction
	elif tokens["mnemonic"].upper() in data_instructions:
		return {"type": "data", "size": data_instructions[tokens["mnemonic"].upper()]}
	else:
		raise CASMMnemonicError(line_number, tokens["mnemonic"].upper())


def make_label(line):
	match = re.match("^\\s*([a-z_][a-z0-9_]*)\\s*:(.*)$", line, re.IGNORECASE)

	if match:
		return {"label": match.group(1), "remaining": match.group(2)}
	else:
		return None


def encode_instruction(instruction):
	if instruction["type"] == "data":
		return b"\0" * instruction["size"]
	else:
		op1flags = "op1" in instruction and (instruction["op1"]["data"]["register"] and 8 or 0) | (instruction["op1"]["data"]["dereference"] and 4 or 0) | (instruction["op1"]["size"] - 1) or 0
		op2flags = "op2" in instruction and (instruction["op2"]["data"]["register"] and 8 or 0) | (instruction["op2"]["data"]["dereference"] and 4 or 0) | (instruction["op2"]["size"] - 1) or 0
		return struct.pack("<HBBLL",
			instruction["info"]["opcode"],
			op1flags,
			op2flags,
			"op1" in instruction and instruction["op1"]["data"]["value"] or 0,
			"op2" in instruction and instruction["op2"]["data"]["value"] or 0)


def get_instruction_size(instruction):
	if instruction["type"] == "data":
		return instruction["size"]
	else:
		return 12


def resolve_symbols(instruction, symbol_list):
	if instruction["type"] == "data":
		return

	if "op1" in instruction and instruction["op1"]["data"]["symbol"]:
		symbol_name = instruction["op1"]["data"]["value"]

		if symbol_name in symbol_list:
			instruction["op1"]["data"]["value"] = symbol_list[symbol_name]
		else:
			raise CASMSymbolError(instruction["line"], symbol_name)

	if "op2" in instruction and instruction["op2"]["data"]["symbol"]:
		symbol_name = instruction["op2"]["data"]["value"]

		if symbol_name in symbol_list:
			instruction["op2"]["data"]["value"] = symbol_list[symbol_name]
		else:
			raise CASMSymbolError(instruction["line"], symbol_name)



def main():
	base_address = 0xFF000000

	if len(sys.argv) < 2:
		print("Usage:\n$ " + sys.argv[0] + " <source>")
		exit()

	source_filename = sys.argv[1]
        if len(sys.argv) > 2:
            base_address = int(sys.argv[2], 16)

	source_file = None
	try:
		source_file = open(source_filename, "r")
	except OSError as e:
		print("Couldn't open source file.");
		exit()

	instruction_list = []
	symbol_list = {}
	line_number = 1
	instruction_address = base_address

	while True:
		line = source_file.readline()
		if line == "":
			break

		# Check if the line begins with a label
		label_line = make_label(line)
		if label_line != None:
			line = label_line["remaining"]
			label = label_line["label"]
			symbol_list[label] = instruction_address

		# Check if entire line is empty or a comment
		if line.strip()=="" or re.search("^\\s*[#;]", line):
			line_number = line_number + 1;
			continue

		try:
			tokens = tokenize(line_number, line)
			instruction = make_instruction(line_number, tokens)

			if instruction == None:
				line_number = line_number + 1;
				continue

			instruction_list.append(instruction)
			instruction_address += get_instruction_size(instruction)

		except CASMError as e:
			print("[Error]", e.what())

		line_number = line_number + 1;

	with open(re.search("(.+?)(\\.[^.]+)?$", source_filename).group(1) + ".cx", "wb") as output_file:

		for instruction in instruction_list:
			try:
				resolve_symbols(instruction, symbol_list)

				encoded = encode_instruction(instruction)
				output_file.write(encoded)
			except CASMSymbolError as e:
				print("[Linker Error]", e.what())


main()
