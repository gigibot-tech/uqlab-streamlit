#!/bin/bash
# Archive Dead Code - Move zero-usage components to /dead_code
# Generated from component reuse analysis

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

DEAD_CODE_DIR="dead_code"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_LOG="$DEAD_CODE_DIR/ARCHIVE_LOG_${TIMESTAMP}.md"

# Create dead_code directory
mkdir -p "$DEAD_CODE_DIR"

echo "# Dead Code Archive Log" > "$ARCHIVE_LOG"
echo "**Date**: $(date)" >> "$ARCHIVE_LOG"
echo "**Reason**: Zero-usage components identified by component reuse analysis" >> "$ARCHIVE_LOG"
echo "" >> "$ARCHIVE_LOG"
echo "## Components Archived" >> "$ARCHIVE_LOG"
echo "" >> "$ARCHIVE_LOG"

# List of zero-usage components (103 total)
DEAD_COMPONENTS=(
    "AcquisitionFunction"
    "AleatoricConfig"
    "AsyncBatchRunner"
    "BALDAcquisition"
    "BaselineResNet18"
    "BaselineResNet50"
    "BaselineVGG16"
    "BatchContext"
    "BatchCreate"
    "BatchExperimentConfig"
    "BatchExperimentSummary"
    "BatchListResponse"
    "BatchResponse"
    "BatchRunner"
    "BatchStatus"
    "BatchUpdateRequest"
    "CallbackProtocol"
    "CheckpointCallback"
    "CheckpointConfig"
    "CheckpointManager"
    "CIFAR10Dataset"
    "CIFAR10NLoader"
    "ClassificationModel"
    "CNNFeatureExtractor"
    "CNNMCDropout"
    "ConfigValidator"
    "CutMix"
    "DataConfig"
    "DataLoaderProtocol"
    "DataQualityChecker"
    "DatasetSpec"
    "DeepEnsemble"
    "DINOv2FeatureExtractor"
    "DINOv2WithMCDropout"
    "DropoutHead"
    "DualXDASignalAcquisition"
    "EarlyStoppingCallback"
    "EarlyStoppingConfig"
    "EntropyAcquisition"
    "EpistemicConfig"
    "EvaluationConfig"
    "EvaluationGroup"
    "ExperimentContext"
    "ExperimentCreate"
    "ExperimentResponse"
    "ExperimentStatus"
    "ExperimentVizAnalysis"
    "FeatureExtractor"
    "FormulaOperator"
    "FormulaPart"
    "GlobalConfig"
    "HeteroscedasticMCDropoutResNet"
    "InferenceRequest"
    "InferenceResponse"
    "LinearHead"
    "LoggingCallback"
    "MaxVarianceAcquisition"
    "MCDropoutCNN"
    "MCDropoutModel"
    "MCDropoutResNet"
    "MetricsCalculator"
    "MetricSpec"
    "MetricType"
    "MixUp"
    "MLPHead"
    "ModelCache"
    "ModelInfo"
    "ModelListResponse"
    "ModelLoadRequest"
    "ModelProtocol"
    "ModelRegistry"
    "OptimizerConfig"
    "PathConfig"
    "PathsConfig"
    "PredictionResult"
    "ProgressCallback"
    "RandomAcquisition"
    "RegularizationConfig"
    "ResNetFeatureExtractor"
    "ResourceManager"
    "ResourceRequirements"
    "ResultStorage"
    "ResultValidator"
    "RiskCoverageArtifacts"
    "RunArtifacts"
    "RunSpecError"
    "SchedulerConfig"
    "SignalCalculator"
    "SignalFormulaSpec"
    "SignalType"
    "SplitType"
    "SurgicalScoreAcquisition"
    "SVHNDataset"
    "SweepConfig"
    "SweepLoadResult"
    "SystemConfig"
    "TestResNetTrainingModes"
    "UncertaintySuite"
    "UnifiedBuilderConfig"
    "UnifiedRow"
    "UqModel"
    "WorkflowConfig"
    "WorkflowDatasetConfig"
    "WorkflowEvaluationConfig"
    "WorkflowTrainingConfig"
    "WorkflowUncertaintyConfig"
)

echo "Found ${#DEAD_COMPONENTS[@]} zero-usage components to archive"
echo ""

# Function to find file containing a class
find_class_file() {
    local class_name="$1"
    # Search in component docs for the definition location
    local doc_file="docs/components/${class_name}.md"
    if [ -f "$doc_file" ]; then
        grep "^src/" "$doc_file" | head -1 | cut -d':' -f1
    fi
}

# Track files to move
declare -A FILES_TO_MOVE

# Find all files containing dead components
for component in "${DEAD_COMPONENTS[@]}"; do
    file_path=$(find_class_file "$component")
    if [ -n "$file_path" ]; then
        FILES_TO_MOVE["$file_path"]=1
        echo "- \`$component\` → \`$file_path\`" >> "$ARCHIVE_LOG"
    fi
done

echo "" >> "$ARCHIVE_LOG"
echo "## Files Archived" >> "$ARCHIVE_LOG"
echo "" >> "$ARCHIVE_LOG"

# Move files to dead_code, preserving directory structure
for file_path in "${!FILES_TO_MOVE[@]}"; do
    if [ -f "$file_path" ]; then
        # Create target directory structure
        target_dir="$DEAD_CODE_DIR/$(dirname "$file_path")"
        mkdir -p "$target_dir"
        
        # Move file
        target_file="$DEAD_CODE_DIR/$file_path"
        echo "Moving: $file_path → $target_file"
        mv "$file_path" "$target_file"
        
        echo "- \`$file_path\`" >> "$ARCHIVE_LOG"
    fi
done

echo "" >> "$ARCHIVE_LOG"
echo "## Restoration Instructions" >> "$ARCHIVE_LOG"
echo "" >> "$ARCHIVE_LOG"
echo "To restore a file:" >> "$ARCHIVE_LOG"
echo "\`\`\`bash" >> "$ARCHIVE_LOG"
echo "# Example: Restore a specific file" >> "$ARCHIVE_LOG"
echo "mv dead_code/src/path/to/file.py src/path/to/file.py" >> "$ARCHIVE_LOG"
echo "\`\`\`" >> "$ARCHIVE_LOG"
echo "" >> "$ARCHIVE_LOG"
echo "To restore all files:" >> "$ARCHIVE_LOG"
echo "\`\`\`bash" >> "$ARCHIVE_LOG"
echo "# WARNING: This will overwrite any changes made since archival" >> "$ARCHIVE_LOG"
echo "rsync -av dead_code/src/ src/" >> "$ARCHIVE_LOG"
echo "\`\`\`" >> "$ARCHIVE_LOG"

echo ""
echo "✅ Dead code archived to: $DEAD_CODE_DIR"
echo "📋 Archive log: $ARCHIVE_LOG"
echo ""
echo "Summary:"
echo "- Components identified: ${#DEAD_COMPONENTS[@]}"
echo "- Files moved: ${#FILES_TO_MOVE[@]}"

# Made with Bob
