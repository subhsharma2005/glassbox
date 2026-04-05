from flask import Flask, request, jsonify
from flask_cors import CORS
# Import all 6 phases!
from compiler import lexical_analyze, Parser, SemanticAnalyzer, IRGenerator, CodeOptimizer, TargetGenerator

app = Flask(__name__)
CORS(app)

@app.route('/api/compile', methods=['POST'])
def compile_code():
    data = request.get_json()
    
    if not data or 'code' not in data:
        return jsonify({"status": "error", "message": "No code provided"}), 400
        
    source_code = data['code']
    
    try:
        # 1. Lexical Analysis
        tokens = lexical_analyze(source_code)
        
        # 2. Syntax Analysis
        parser = Parser(tokens)
        ast = parser.parse_program()
        
        # 3. Semantic Analysis
        analyzer = SemanticAnalyzer()
        symbol_table = analyzer.analyze(ast)
        
        # 4. Intermediate Code
        ir_gen = IRGenerator()
        tac = ir_gen.generate(ast)
        
        # 5. Optimization
        optimizer = CodeOptimizer(tac)
        optimized_tac = optimizer.optimize()
        
        # 6. Target Code Generation (NEW!)
        target_gen = TargetGenerator(optimized_tac)
        assembly = target_gen.generate()
        
        # The Final Output!
        return jsonify({
            "status": "success",
            "lexical": tokens,
            "syntax": ast,
            "semantic": {
                "symbol_table": symbol_table
            },
            "intermediate": tac,
            "optimization": optimized_tac,
            "target": assembly
        })
        
    except ValueError as e: 
        error_msg = str(e)
        if "Syntax Error" in error_msg: phase = "syntax"
        elif "Semantic Error" in error_msg: phase = "semantic"
        else: phase = "lexical"
        
        return jsonify({ "status": "error", "phase": phase, "message": error_msg }), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)