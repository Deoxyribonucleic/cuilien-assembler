;
;        Cuilien VM
;   Brainfuck Interpreter
; (Turing completeness test)
;
; By Deoxyribonucleic
;


; C is our instruction pointer
mov c, 0xffe00000

; D is our data pointer
mov d, 0xfff00000


main:
	; Advance instruction pointer until we reach something that is a valid brainfuck instruction or @
	instruction_search_loop:
		mov b, byte [c]

		; <
		check_less_than:
			cmp b, 0x3C
			jneq check_greater_than
			call decrement_data_pointer
			jmp next

		; >
		check_greater_than:
			cmp b, 0x3E
			jneq check_plus
			call increment_data_pointer
			jmp next

		; +
		check_plus:
			cmp b, 0x2B
			jneq check_minus
			call increment_value
			jmp next

		; -
		check_minus:
			cmp b, 0x2D
			jneq check_period
			call decrement_value
			jmp next

		; .
		check_period:
			cmp b, 0x2E
			jneq check_comma
			call output
			jmp next

		; ,
		check_comma:
			cmp b, 0x2C
			jneq check_bracket_open
			call input
			jmp next

		; [
		check_bracket_open:
			cmp b, 0x5B
			jneq check_bracket_close
			call bracket_open
			jmp next

		; ]
		check_bracket_close:
			cmp b, 0x5D
			jneq check_at
			call bracket_close
			jmp next

		; @
		check_at:
			cmp b, 0x40
			jneq next
			jmp end


		next:
		; Increment instruction pointer
		inc c
		jmp instruction_search_loop

end: halt


increment_data_pointer:
	inc d
	ret

decrement_data_pointer:
	dec d
	ret

increment_value:
	inc byte [d]
	ret

decrement_value:
	dec byte [d]
	ret

output:
	putc byte [d]
	ret

input: ; not implemented
	mov byte [d], 0
	ret

bracket_open:
	test byte [d]
	jnz do_nothing1

	; Search for the corresponding end bracket and move instruction pointer there
	; A is the current level of nested brackets -- the found end bracket is only valid if A is 0
	mov a, 1
	bracket_close_search:
		inc c
		cmp byte [c], 0x5B
		jneq check_close_bracket2
		; If the character at C is a [, increment nesting level
		inc a

		check_close_bracket2:
		cmp byte [c], 0x5D
		jneq bracket_close_search
		; If the character at C is a ], decrement nesting level
		dec a
		; Check if A is 0 -- if it is, break; if it isn't, continue search
		test a
		jnz bracket_close_search

	do_nothing1:
	ret

bracket_close:
	test byte [d]
	jz do_nothing2

	; (Do the same, but backwards)
	; Search for the corresponding opening bracket and move instruction pointer there
	; A is the current level of nested brackets -- the found opening bracket is only valid if A is 0
	mov a, 1
	bracket_open_search:
		dec c
		cmp byte [c], 0x5D
		jneq check_open_bracket2
		; If the character at C is a ], increment nesting level
		inc a

		check_open_bracket2:
		cmp byte [c], 0x5B
		jneq bracket_open_search
		; If the character at C is a [, decrement nesting level
		dec a
		; Check if A is 0 -- if it is, break; if it isn't, continue search
		test a
		jnz bracket_open_search

	do_nothing2:
	ret
