import re

# 1. LEXICAL ANALYSIS (Scanner)

TOKEN_RULES = [
    ('KEYWORD',  r'\b(int|float|return|if|else|while)\b'), 
    ('ID',       r'[A-Za-z_][A-Za-z0-9_]*'),               
    ('NUMBER',   r'\d+(\.\d+)?'),                          
    ('STRING',   r'"[^"]*"'), 
    ('OP',       r'==|!=|<=|>=|[+\-*/=<>]'),                             
    ('PUNCT',    r'[;,\{\}\(\)]'),                         
    ('SPACE',    r'[ \t]+'),                               
    ('NEWLINE',  r'\n'),                                   
    ('MISMATCH', r'.'),                                    
]
token_regex = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_RULES)
get_token = re.compile(token_regex).match

def lexical_analyze(code):
    line_num = 1
    tokens = []
    for match in re.finditer(token_regex, code):
        token_type = match.lastgroup
        token_value = match.group()
        if token_type == 'NEWLINE':
            line_num += 1
            continue 
        elif token_type == 'SPACE':
            continue
        elif token_type == 'MISMATCH':
            raise ValueError(f"Lexical Error: Unexpected character '{token_value}' on line {line_num}")
        tokens.append({"type": token_type, "value": token_value, "line": line_num})
    return tokens


# 2. SYNTAX ANALYSIS (Parser)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current_token(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type, expected_value=None):
        token = self.current_token()
        if not token:
            raise ValueError(f"Syntax Error: Unexpected end of input.")
        if token['type'] == expected_type and (not expected_value or token['value'] == expected_value):
            self.pos += 1
            return token
        raise ValueError(f"Syntax Error: Expected {expected_value or expected_type} but got {token['value']} on line {token['line']}")
    
    def parse_program(self):
        body = []
        while self.current_token() is not None:
            body.append(self.parse_statement())
        return {"type": "Program", "body": body}

    def parse_block(self):
        self.consume('PUNCT', '{')
        body = []
        while self.current_token() and self.current_token()['value'] != '}':
            body.append(self.parse_statement())
        self.consume('PUNCT', '}')
        return body

    def parse_statement(self):
        token = self.current_token()
        if token['type'] == 'KEYWORD':
            if token['value'] in ['int', 'float']: return self.parse_declaration()
            elif token['value'] == 'return': return self.parse_return()
            elif token['value'] == 'if': return self.parse_if()       # NEW
            elif token['value'] == 'while': return self.parse_while() # NEW
        elif token['type'] == 'ID':
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok['value'] == '(':
                return self.parse_function_call()
            elif next_tok and next_tok['value'] == '=':
                return self.parse_assignment() # NEW
                
        raise ValueError(f"Syntax Error: Unexpected statement starting with '{token['value']}' on line {token['line']}")

    def parse_expression(self):
        # Handles + and -
        node = self.parse_term()
        while self.current_token() and self.current_token()['value'] in ['+', '-', '==', '!=', '<', '>']:
            op = self.consume('OP')['value']
            right = self.parse_term()
            node = {"type": "BinaryExpression", "operator": op, "left": node, "right": right}
        return node

    def parse_term(self):
        # Handles * and / (High precedence)
        node = self.parse_factor()
        while self.current_token() and self.current_token()['value'] in ['*', '/']:
            op = self.consume('OP')['value']
            right = self.parse_factor()
            node = {"type": "BinaryExpression", "operator": op, "left": node, "right": right}
        return node

    def parse_factor(self):
        # Handles raw numbers, variables, or parenthesis (Highest precedence)
        token = self.current_token()
        if token['type'] == 'NUMBER':
            return {"type": "Literal", "value": self.consume('NUMBER')['value']}
        elif token['type'] == 'ID':
            return {"type": "Identifier", "name": self.consume('ID')['value']}
        elif token['value'] == '(':
            self.consume('PUNCT', '(')
            node = self.parse_expression()
            self.consume('PUNCT', ')')
            return node
        raise ValueError(f"Syntax Error: Expected Number, Variable, or '(' but got {token['value']}")

    # --- STATEMENT PARSERS ---
    def parse_declaration(self):
        var_type = self.consume('KEYWORD')['value']  
        var_name = self.consume('ID')['value']       
        self.consume('OP', '=')                      
        expr = self.parse_expression() # Uses the new math parser
        self.consume('PUNCT', ';')                   
        return {"type": "VariableDeclaration", "var_type": var_type, "id": var_name, "init_value": expr}

    def parse_assignment(self):
        # NEW: x = 10;
        var_name = self.consume('ID')['value']
        self.consume('OP', '=')
        expr = self.parse_expression()
        self.consume('PUNCT', ';')
        return {"type": "Assignment", "id": var_name, "value": expr}

    def parse_if(self):
        # NEW: if (x > 5) { ... }
        self.consume('KEYWORD', 'if')
        self.consume('PUNCT', '(')
        condition = self.parse_expression()
        self.consume('PUNCT', ')')
        body = self.parse_block()
        return {"type": "IfStatement", "condition": condition, "body": body}

    def parse_while(self):
        # NEW: while (x < 10) { ... }
        self.consume('KEYWORD', 'while')
        self.consume('PUNCT', '(')
        condition = self.parse_expression()
        self.consume('PUNCT', ')')
        body = self.parse_block()
        return {"type": "WhileStatement", "condition": condition, "body": body}

    def parse_return(self):
        self.consume('KEYWORD', 'return')            
        expr = self.parse_expression() 
        self.consume('PUNCT', ';')                   
        return {"type": "ReturnStatement", "argument": expr}

    def parse_function_call(self):
        func_name = self.consume('ID')['value']
        self.consume('PUNCT', '(')
        args = []
        while self.current_token() and self.current_token()['value'] != ')':
            token = self.current_token()
            if token['type'] == 'STRING':
                args.append({"type": "String", "value": self.consume('STRING')['value']})
            else:
                args.append(self.parse_expression())
            
            if self.current_token() and self.current_token()['value'] == ',':
                self.consume('PUNCT', ',')
        self.consume('PUNCT', ')')
        self.consume('PUNCT', ';')
        return {"type": "FunctionCall", "name": func_name, "arguments": args}


# 3. SEMANTIC ANALYSIS

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {"printf": {"type": "function", "scope": "builtin"}}

    def analyze(self, ast):
        self.visit(ast)
        return self.symbol_table

    def visit(self, node):
        visitor = getattr(self, f"visit_{node['type']}", self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"Semantic Error: No visit method for {node['type']}")

    def visit_Program(self, node):
        for stmt in node['body']: self.visit(stmt)

    def visit_VariableDeclaration(self, node):
        if node['id'] in self.symbol_table:
            raise ValueError(f"Semantic Error: Variable '{node['id']}' already declared.")
        self.visit(node['init_value']) # Check math expression
        self.symbol_table[node['id']] = {"type": node['var_type'], "scope": "global"}

    def visit_Assignment(self, node):
        if node['id'] not in self.symbol_table:
            raise ValueError(f"Semantic Error: Assignment to undeclared variable '{node['id']}'.")
        self.visit(node['value'])

    def visit_IfStatement(self, node):
        self.visit(node['condition'])
        for stmt in node['body']: self.visit(stmt)

    def visit_WhileStatement(self, node):
        self.visit(node['condition'])
        for stmt in node['body']: self.visit(stmt)

    def visit_ReturnStatement(self, node):
        self.visit(node['argument'])

    def visit_FunctionCall(self, node):
        if node['name'] not in self.symbol_table:
             raise ValueError(f"Semantic Error: Undeclared function '{node['name']}'")
        for arg in node['arguments']:
            if arg['type'] != 'String': self.visit(arg)

    def visit_BinaryExpression(self, node):
        self.visit(node['left'])
        self.visit(node['right'])

    def visit_Literal(self, node): pass

    def visit_Identifier(self, node):
        if node['name'] not in self.symbol_table:
            raise ValueError(f"Semantic Error: Undeclared variable '{node['name']}' used.")


# 4. INTERMEDIATE CODE GENERATION (IR)
class IRGenerator:
    def __init__(self):
        self.instructions = []  
        self.temp_count = 1     
        self.label_count = 1

    def new_temp(self):
        name = f"t{self.temp_count}"; self.temp_count += 1; return name
        
    def new_label(self):
        name = f"L{self.label_count}"; self.label_count += 1; return name

    def generate(self, ast):
        self.visit(ast)
        return self.instructions

    def visit(self, node):
        visitor = getattr(self, f"visit_{node['type']}", self.generic_visit)
        return visitor(node)

    def generic_visit(self, node): raise Exception(f"IR Error: No visit for {node['type']}")

    def visit_Program(self, node):
        for stmt in node['body']: self.visit(stmt)

    def visit_Literal(self, node): return str(node['value'])
    def visit_Identifier(self, node): return node['name']

    def visit_BinaryExpression(self, node):
        # NEW: Generates t1 = a + b recursively
        left_val = self.visit(node['left'])
        right_val = self.visit(node['right'])
        temp = self.new_temp()
        self.instructions.append(f"{temp} = {left_val} {node['operator']} {right_val}")
        return temp

    def visit_VariableDeclaration(self, node):
        val = self.visit(node['init_value'])
        self.instructions.append(f"{node['id']} = {val}")

    def visit_Assignment(self, node):
        val = self.visit(node['value'])
        self.instructions.append(f"{node['id']} = {val}")

    def visit_IfStatement(self, node):
        # NEW: Generates Jump Labels for IF
        cond_val = self.visit(node['condition'])
        l_end = self.new_label()
        self.instructions.append(f"if_false {cond_val} goto {l_end}")
        for stmt in node['body']: self.visit(stmt)
        self.instructions.append(f"{l_end}:")

    def visit_WhileStatement(self, node):
        # NEW: Generates Jump Labels for WHILE
        l_start = self.new_label()
        l_end = self.new_label()
        self.instructions.append(f"{l_start}:")
        cond_val = self.visit(node['condition'])
        self.instructions.append(f"if_false {cond_val} goto {l_end}")
        for stmt in node['body']: self.visit(stmt)
        self.instructions.append(f"goto {l_start}")
        self.instructions.append(f"{l_end}:")

    def visit_ReturnStatement(self, node):
        val = self.visit(node['argument'])
        self.instructions.append(f"return {val}")

    def visit_FunctionCall(self, node):
        for arg in node['arguments']:
            if arg['type'] == 'String': self.instructions.append(f"param {arg['value']}")
            else: self.instructions.append(f"param {self.visit(arg)}")
        self.instructions.append(f"call {node['name']}, {len(node['arguments'])}")


# 5. CODE OPTIMIZATION

class CodeOptimizer:
    def __init__(self, instructions):
        self.instructions = instructions

    def optimize(self):
        opt = []
        for instr in self.instructions:
            match = re.match(r'^(\w+)\s*=\s*(\d+)\s*([+\-*/])\s*(\d+)$', instr.strip())
            if match:
                var, left, op, right = match.groups()
                left, right = int(left), int(right)
                if op == '+': result = left + right
                elif op == '-': result = left - right
                elif op == '*': result = left * right
                elif op == '/': result = left // right 
                opt.append(f"{var} = {result}")
            else:
                opt.append(instr)
        return opt



# 6. TARGET CODE GENERATION

class TargetGenerator:
    def __init__(self, tac_instructions):
        self.tac_instructions = tac_instructions
        self.assembly = []
        self.register_counter = 1

    def get_reg(self):
        reg = f"R{self.register_counter}"; self.register_counter += 1; return reg

    def generate(self):
        for instr in self.tac_instructions:
            instr = instr.strip()
            
            # Match Labels
            if instr.endswith(':'):
                self.assembly.append(instr)
                continue
                
            # Match Gotos
            match_goto = re.match(r'^goto\s+(L\d+)$', instr)
            if match_goto:
                self.assembly.append(f"JMP {match_goto.group(1)}")
                continue
                
            # Match If False
            match_if = re.match(r'^if_false\s+(\w+)\s+goto\s+(L\d+)$', instr)
            if match_if:
                var, label = match_if.groups()
                self.assembly.append(f"CMP {var}, 0")
                self.assembly.append(f"JE {label}") # Jump if Equal to 0 (False)
                continue

            match_math = re.match(r'^(\w+)\s*=\s*(\w+)\s*(==|!=|<=|>=|[+\-*/<>])\s*(\w+)$', instr)
            if match_math:
                res, left, op, right = match_math.groups()
                r1 = self.get_reg()
                r2 = self.get_reg()
                r3 = self.get_reg()
                self.assembly.append(f"LOAD {r1}, {left}")
                self.assembly.append(f"LOAD {r2}, {right}")
                if op == '+': self.assembly.append(f"ADD {r3}, {r1}, {r2}")
                elif op == '-': self.assembly.append(f"SUB {r3}, {r1}, {r2}")
                elif op == '*': self.assembly.append(f"MUL {r3}, {r1}, {r2}")
                elif op == '/': self.assembly.append(f"DIV {r3}, {r1}, {r2}")
                else: self.assembly.append(f"COMPARE_{op} {r3}, {r1}, {r2}") # Simplified for educational view
                self.assembly.append(f"STORE {res}, {r3}")
                continue

            match_assign = re.match(r'^(\w+)\s*=\s*(\w+)$', instr)
            if match_assign:
                var, val = match_assign.groups()
                self.assembly.append(f"MOV {var}, {val}")
                continue
            
            match_return = re.match(r'^return\s+(\w+)$', instr)
            if match_return:
                self.assembly.append(f"MOV R0, {match_return.group(1)}")
                self.assembly.append("RET")
                continue
            
            match_param = re.match(r'^param\s+(.+)$', instr)
            if match_param:
                self.assembly.append(f"PUSH {match_param.group(1)}")
                continue

            match_call = re.match(r'^call\s+(\w+),\s*(\d+)$', instr)
            if match_call:
                self.assembly.append(f"CALL {match_call.group(1)}")
                continue
                
        return self.assembly




if __name__ == "__main__":
    sample_code = """
    int limit = 5 + 5 * 2;
    int count = 0;
    
    while (count < limit) {
        count = count + 1;
        if (count == 10) {
            printf("Warning: Approaching Limit!");
        }
    }
    return count;
    """
    
    print("--- COMPILING CODE ---")
    print(sample_code.strip())
    print("-" * 22)
    
    try:
        tokens = lexical_analyze(sample_code)
        parser = Parser(tokens)
        ast = parser.parse_program()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        ir_gen = IRGenerator()
        tac = ir_gen.generate(ast)
        opt = CodeOptimizer(tac)
        opt_tac = opt.optimize()
        target = TargetGenerator(opt_tac)
        assembly = target.generate()
        
        print("\n Compilation Successful!\n")
        
        print("Final TAC (Notice the Labels and Math Variables!):")
        for line in tac: print(f"  {line}")
            
        print("\nFinal Assembly:")
        for line in assembly: print(f"  {line}")
        
    except ValueError as e:
        print(f"\n Compilation Failed: {e}")