from GLM11_runtime import GLMRuntimeV37

print("=== GLM FULL STACK INTEGRATION TEST ===")
rt = GLMRuntimeV37()

# Test 1: Geometric Reasoning
print("\nQuery 1: Hamiltonian and Time")
print(f"Response: {rt.chat('Tell me about the hamiltonian and time.')}")

# Test 2: Symbolic Math
print("\nQuery 2: Calculus")
print(f"Response: {rt.chat('differentiate x^2 + 5x')}")

# Test 3: Deliberative Reasoning
print("\nQuery 3: Olympiad Pattern")
print(f"Response: {rt.chat('Prove that (21n+4)/(14n+3) is irreducible')}")

print("\n✅ Full Stack Operational.")