from compiler import lexical_analyze, Parser, SemanticAnalyzer, IRGenerator, CodeOptimizer, TargetGenerator

print("========== GLASSBOX COMPILER PIPELINE ==========\n")

source_code = """
int age = 25;
int a= 2;
int c=age+a;
printf("%d",c);
"""

try:
    print("Source Code:")
    print(source_code.strip() + "\n")
    
    # Phase 1
    tokens = lexical_analyze(source_code)
    print("1. Lexical Analysis Complete")
    
    # Phase 2
    parser = Parser(tokens)
    ast = parser.parse_program()
    print("2. Syntax Analysis Complete")
    
    # Phase 3
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    print("3. Semantic Analysis Complete")
    
    # Phase 4
    ir_gen = IRGenerator()
    tac = ir_gen.generate(ast)
    print("4. IR Generation Complete")
    
    # Phase 5
    optimizer = CodeOptimizer(tac)
    opt_tac = optimizer.optimize()
    print("5. Code Optimization Complete")
    
    # Phase 6
    target_gen = TargetGenerator(opt_tac)
    assembly = target_gen.generate()
    print("6. Target Code Generation Complete")
    
    print("\n--- Final Assembly Output ---")
    for instr in assembly:
        print(f"  {instr}")
        
except ValueError as e:
    print(f"\nCompilation Failed: {e}")