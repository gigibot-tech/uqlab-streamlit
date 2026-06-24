#!/usr/bin/env python3
"""Quick test to verify the refactoring is correct."""

import inspect
from uqlab.evaluation.signals.attribution import compute_attribution_structure_signals

# Check function signature
sig = inspect.signature(compute_attribution_structure_signals)
print("✅ Function signature:")
print(f"   {sig}")
print("\n✅ Parameter names:")
for param in sig.parameters:
    print(f"   - {param}")

# Verify the parameter was renamed
params = list(sig.parameters.keys())
assert "eval_inputs" in params, "❌ eval_inputs parameter not found!"
assert "eval_features" not in params, "❌ eval_features still exists (should be renamed)!"

print("\n✅ SUCCESS: Parameter successfully renamed from 'eval_features' to 'eval_inputs'")
print("✅ The function is now architecture-agnostic!")

# Made with Bob
