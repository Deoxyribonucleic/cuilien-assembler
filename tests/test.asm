
start:
MOV A, 1
main: # void main()
MOV B, 0
MOV B, A
MOV C, short [0x0666]
MOV [C], short 0x1234
SHOW SHORT [C]

MOV [lawng], 0xFFFF0666
MOV A, short [lawng]
MOV A, [A]
INC [A]
SHOW SHORT [A]

show short 1337

MOV byte [0x100], long 0x12345678
SHOW byte [0x100]
SHOW long [0x100]
SHOW long [0x97]


loop:	MOV A, [C]
		INT
		JMP loop
endloop:

HALT

# DATA SECTION
short_test: ALLOC_SHORT
byte1: ALLOC_BYTE
byte2: ALLOC_BYTE
lawng: ALLOC_LONG