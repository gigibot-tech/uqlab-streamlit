# Code Readability Audit Skill

**Purpose:** Systematically improve code readability through clear naming, documentation, and structure

**When to use:** When code is functional but hard to understand, or when onboarding new developers

---

## 🎯 Readability Principles

### The 5 Pillars of Readable Code

1. **Clear Naming** - Names reveal intent without comments
2. **Logical Structure** - Code flows like a story
3. **Minimal Complexity** - Simple solutions over clever ones
4. **Good Documentation** - Explains WHY, not WHAT
5. **Consistent Style** - Predictable patterns throughout

---

## 📋 Audit Checklist

### Level 1: Naming (Most Important)

- [ ] **Variables** - Descriptive, not abbreviated
  - ❌ `df`, `tmp`, `x`, `data`
  - ✅ `user_dataframe`, `temporary_result`, `feature_vector`, `training_dataset`

- [ ] **Functions** - Verb phrases that describe action
  - ❌ `process()`, `handle()`, `do_stuff()`
  - ✅ `calculate_uncertainty()`, `validate_config()`, `fetch_experiment_results()`

- [ ] **Classes** - Nouns that describe entities
  - ❌ `Manager`, `Handler`, `Processor`
  - ✅ `ExperimentRunner`, `DatasetLoader`, `UncertaintyCalculator`

- [ ] **Constants** - UPPER_CASE with clear meaning
  - ❌ `MAX`, `LIMIT`, `SIZE`
  - ✅ `MAX_BATCH_SIZE`, `API_TIMEOUT_SECONDS`, `DEFAULT_DROPOUT_RATE`

- [ ] **Booleans** - Start with is/has/can/should
  - ❌ `valid`, `ready`, `enabled`
  - ✅ `is_valid`, `has_results`, `can_execute`, `should_retry`

### Level 2: Function Design

- [ ] **Single Responsibility** - Each function does ONE thing
  - ❌ `process_and_save_and_visualize()`
  - ✅ `process_data()`, `save_results()`, `create_visualization()`

- [ ] **Short Functions** - Aim for <50 lines, max 100
  - If longer, extract helper functions

- [ ] **Few Parameters** - Max 5 parameters
  - If more, use config object or dataclass

- [ ] **Clear Return Types** - Type hints for all functions
  ```python
  def calculate_auroc(predictions: np.ndarray, labels: np.ndarray) -> float:
      """Calculate AUROC score."""
      ...
  ```

- [ ] **No Side Effects** - Functions don't modify global state
  - Pass dependencies explicitly
  - Return new values instead of mutating

### Level 3: Code Structure

- [ ] **Logical Grouping** - Related code stays together
  ```python
  # ✅ Good: Grouped by functionality
  # Data Loading
  def load_dataset(): ...
  def preprocess_data(): ...
  def split_train_test(): ...
  
  # Model Building
  def create_model(): ...
  def compile_model(): ...
  ```

- [ ] **Consistent Ordering** - Predictable file structure
  ```python
  # 1. Imports (stdlib, third-party, local)
  # 2. Constants
  # 3. Type definitions
  # 4. Helper functions
  # 5. Main functions
  # 6. Classes
  # 7. Entry point (if __name__ == "__main__")
  ```

- [ ] **Separation of Concerns** - Each module has clear purpose
  - `data/` - Data loading only
  - `models/` - Model definitions only
  - `training/` - Training logic only
  - `evaluation/` - Metrics and evaluation only

### Level 4: Documentation

- [ ] **Module Docstrings** - Explain module purpose
  ```python
  """
  Uncertainty quantification metrics for classification tasks.
  
  Provides functions to calculate epistemic and aleatoric uncertainty
  using MC Dropout and information-theoretic measures.
  """
  ```

- [ ] **Function Docstrings** - Explain purpose, args, returns
  ```python
  def calculate_mutual_info(predictions: np.ndarray) -> np.ndarray:
      """
      Calculate mutual information (epistemic uncertainty).
      
      Args:
          predictions: MC Dropout predictions, shape (n_passes, n_samples, n_classes)
      
      Returns:
          Mutual information per sample, shape (n_samples,)
      
      Formula:
          MI = H(y|x) - E[H(y|x,θ)]
          where H is entropy and θ are model parameters
      """
      ...
  ```

- [ ] **Inline Comments** - Explain WHY, not WHAT
  ```python
  # ❌ Bad: Explains what (obvious from code)
  # Loop through predictions
  for pred in predictions:
      ...
  
  # ✅ Good: Explains why (non-obvious reasoning)
  # Use balanced sampling to prevent class imbalance bias in AUROC
  for pred in predictions:
      ...
  ```

- [ ] **README Files** - Every major directory has README
  - Purpose of directory
  - Key files and their roles
  - Usage examples
  - Dependencies

### Level 5: Complexity Reduction

- [ ] **Avoid Deep Nesting** - Max 3 levels
  ```python
  # ❌ Bad: 4 levels of nesting
  if condition1:
      if condition2:
          if condition3:
              if condition4:
                  do_something()
  
  # ✅ Good: Early returns
  if not condition1:
      return
  if not condition2:
      return
  if not condition3:
      return
  if not condition4:
      return
  do_something()
  ```

- [ ] **Extract Complex Conditions** - Name them
  ```python
  # ❌ Bad: Complex inline condition
  if (user.age > 18 and user.verified and 
      user.subscription == "premium" and not user.banned):
      grant_access()
  
  # ✅ Good: Named condition
  is_eligible_user = (
      user.age > 18 and 
      user.verified and 
      user.subscription == "premium" and 
      not user.banned
  )
  if is_eligible_user:
      grant_access()
  ```

- [ ] **Avoid Magic Numbers** - Use named constants
  ```python
  # ❌ Bad: Magic numbers
  if dropout > 0.5:
      raise ValueError("Dropout too high")
  
  # ✅ Good: Named constants
  MAX_DROPOUT_RATE = 0.5
  if dropout > MAX_DROPOUT_RATE:
      raise ValueError(f"Dropout must be <= {MAX_DROPOUT_RATE}")
  ```

---

## 🔍 Audit Process

### Step 1: Identify Problem Areas

Run these checks to find readability issues:

```bash
# Find long functions (>100 lines)
grep -n "^def " file.py | while read line; do
    start=$(echo $line | cut -d: -f1)
    # Count lines until next function
done

# Find files with poor naming (short variable names)
grep -E "\b[a-z]{1,2}\b\s*=" file.py

# Find missing docstrings
grep -L '"""' *.py

# Find complex functions (high cyclomatic complexity)
radon cc file.py -a
```

### Step 2: Prioritize Fixes

**High Priority** (Fix First):
1. Unclear function/variable names in core logic
2. Missing docstrings for public APIs
3. Functions >100 lines
4. Deep nesting (>3 levels)

**Medium Priority**:
1. Inconsistent naming conventions
2. Magic numbers
3. Missing type hints
4. Poor code organization

**Low Priority**:
1. Inline comments
2. README improvements
3. Cosmetic formatting

### Step 3: Apply Fixes Systematically

For each file:

1. **Rename** - Fix all naming issues first
2. **Extract** - Break long functions into smaller ones
3. **Document** - Add docstrings and comments
4. **Simplify** - Reduce complexity and nesting
5. **Organize** - Group related code together

### Step 4: Verify Improvements

- [ ] Code review with fresh eyes
- [ ] Run tests to ensure no breakage
- [ ] Check that new names are used consistently
- [ ] Verify documentation is accurate

---

## 📊 Readability Metrics

### Quantitative Measures

1. **Average Function Length** - Target: <30 lines
2. **Cyclomatic Complexity** - Target: <10 per function
3. **Documentation Coverage** - Target: >80% of public APIs
4. **Naming Consistency** - Target: 100% follow conventions

### Qualitative Measures

1. **Can a new developer understand the code in 5 minutes?**
2. **Can you explain what a function does without reading it?**
3. **Are variable names self-documenting?**
4. **Is the code flow logical and predictable?**

---

## 🎓 Examples

### Example 1: Poor Naming → Clear Naming

**Before:**
```python
def proc(d, t):
    r = []
    for x in d:
        if x > t:
            r.append(x)
    return r
```

**After:**
```python
def filter_values_above_threshold(
    values: List[float], 
    threshold: float
) -> List[float]:
    """
    Filter values that exceed the threshold.
    
    Args:
        values: List of numeric values to filter
        threshold: Minimum value to include
    
    Returns:
        List of values above threshold
    """
    filtered_values = []
    for value in values:
        if value > threshold:
            filtered_values.append(value)
    return filtered_values

# Or more Pythonic:
def filter_values_above_threshold(
    values: List[float], 
    threshold: float
) -> List[float]:
    """Filter values that exceed the threshold."""
    return [v for v in values if v > threshold]
```

### Example 2: Long Function → Extracted Functions

**Before:**
```python
def run_experiment(config):
    # Load data (20 lines)
    dataset = load_dataset(config.dataset_name)
    train_data = dataset.train
    test_data = dataset.test
    # ... 15 more lines
    
    # Build model (30 lines)
    if config.model == "dinov2":
        model = DINOv2Model()
        # ... 25 more lines
    
    # Train (40 lines)
    for epoch in range(config.epochs):
        # ... 35 more lines
    
    # Evaluate (30 lines)
    predictions = model.predict(test_data)
    # ... 25 more lines
    
    return results
```

**After:**
```python
def run_experiment(config: ExperimentConfig) -> ExperimentResults:
    """
    Run complete ML experiment pipeline.
    
    Args:
        config: Experiment configuration
    
    Returns:
        Experiment results with metrics and predictions
    """
    # Load and prepare data
    train_data, test_data = load_and_split_data(config)
    
    # Build and train model
    model = build_model(config)
    trained_model = train_model(model, train_data, config)
    
    # Evaluate and return results
    results = evaluate_model(trained_model, test_data, config)
    return results

def load_and_split_data(config: ExperimentConfig) -> Tuple[Dataset, Dataset]:
    """Load dataset and split into train/test."""
    dataset = load_dataset(config.dataset_name)
    return dataset.train, dataset.test

def build_model(config: ExperimentConfig) -> nn.Module:
    """Build model based on configuration."""
    if config.model == "dinov2":
        return DINOv2Model(config.hidden_dim, config.dropout)
    elif config.model == "resnet":
        return ResNetModel(config.hidden_dim, config.dropout)
    else:
        raise ValueError(f"Unknown model: {config.model}")

def train_model(
    model: nn.Module, 
    train_data: Dataset, 
    config: ExperimentConfig
) -> nn.Module:
    """Train model on training data."""
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    for epoch in range(config.epochs):
        train_one_epoch(model, train_data, optimizer)
    return model

def evaluate_model(
    model: nn.Module, 
    test_data: Dataset, 
    config: ExperimentConfig
) -> ExperimentResults:
    """Evaluate trained model on test data."""
    predictions = model.predict(test_data)
    metrics = calculate_metrics(predictions, test_data.labels)
    return ExperimentResults(metrics=metrics, predictions=predictions)
```

### Example 3: Poor Documentation → Good Documentation

**Before:**
```python
def calc_mi(preds):
    # Calculate MI
    h1 = entropy(preds.mean(0))
    h2 = entropy(preds).mean()
    return h1 - h2
```

**After:**
```python
def calculate_mutual_information(mc_predictions: np.ndarray) -> np.ndarray:
    """
    Calculate mutual information (epistemic uncertainty) from MC Dropout predictions.
    
    Mutual information measures the information gain about the model parameters
    from observing the prediction. High MI indicates epistemic uncertainty that
    can be reduced with more training data.
    
    Args:
        mc_predictions: MC Dropout predictions with shape (n_passes, n_samples, n_classes)
                       where n_passes is the number of MC forward passes
    
    Returns:
        Mutual information per sample, shape (n_samples,)
        Higher values indicate more epistemic uncertainty
    
    Formula:
        MI = H(y|x) - E[H(y|x,θ)]
        
        where:
        - H(y|x) is the entropy of the predictive distribution (averaged predictions)
        - E[H(y|x,θ)] is the expected entropy across MC samples
        - θ represents model parameters (varied by dropout)
    
    Example:
        >>> predictions = np.random.rand(20, 100, 10)  # 20 passes, 100 samples, 10 classes
        >>> mi = calculate_mutual_information(predictions)
        >>> mi.shape
        (100,)
    """
    # Entropy of averaged predictions (total uncertainty)
    predictive_entropy = entropy(mc_predictions.mean(axis=0))
    
    # Average entropy of individual predictions (aleatoric uncertainty)
    expected_entropy = entropy(mc_predictions).mean(axis=0)
    
    # Mutual information (epistemic uncertainty)
    mutual_info = predictive_entropy - expected_entropy
    
    return mutual_info
```

---

## 🚀 Quick Wins

### 5-Minute Improvements

1. **Rename one poorly-named function** - Biggest impact
2. **Add docstring to main entry point** - Helps onboarding
3. **Extract one magic number to constant** - Improves maintainability
4. **Add type hints to one function** - Catches bugs early
5. **Write README for one directory** - Clarifies structure

### 30-Minute Improvements

1. **Refactor one long function** - Break into 3-5 smaller functions
2. **Document all public APIs in one module** - Add comprehensive docstrings
3. **Rename all variables in one file** - Consistent naming throughout
4. **Add README to project root** - Explain overall structure
5. **Create SYSTEM_FLOW.md** - Document how everything fits together

---

## 🎯 Success Criteria

**Code is readable when:**

1. ✅ New developers can understand it in <10 minutes
2. ✅ Function names explain what they do without reading code
3. ✅ No need to ask "what does this do?"
4. ✅ Code flows logically from top to bottom
5. ✅ Documentation explains WHY, not WHAT
6. ✅ Consistent patterns throughout codebase
7. ✅ No "clever" code that requires deep thought
8. ✅ Easy to modify without breaking things

---

## 📚 Related Skills

- **DRY/SSOT Audit** - `.bob/skills/code-quality-audit.md`
- **Architecture Refactoring** - `.bob/skills/architecture-aware-refactoring.md`
- **Testing Strategy** - `.bob/skills/testing-strategy.md` (if exists)

---

**Remember:** Readable code is maintainable code. Invest time in clarity now, save hours debugging later.