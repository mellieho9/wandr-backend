#!/bin/bash

# Cleanup script for results/ directory
# Removes all processed files to free up space

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$PROJECT_ROOT/results"

echo "🧹 Cleaning up results directory..."

if [ ! -d "$RESULTS_DIR" ]; then
    echo "❌ Results directory not found: $RESULTS_DIR"
    exit 1
fi

# Count files before cleanup
BEFORE_COUNT=$(find "$RESULTS_DIR" -type f | wc -l)
BEFORE_SIZE=$(du -sh "$RESULTS_DIR" 2>/dev/null | cut -f1 || echo "0B")

echo "📊 Before cleanup:"
echo "   Files: $BEFORE_COUNT"
echo "   Size: $BEFORE_SIZE"

# Remove all files in results directory
echo "🗑️  Removing files..."
find "$RESULTS_DIR" -type f -delete

# Count files after cleanup
AFTER_COUNT=$(find "$RESULTS_DIR" -type f | wc -l)
AFTER_SIZE=$(du -sh "$RESULTS_DIR" 2>/dev/null | cut -f1 || echo "0B")

echo "✅ Cleanup complete!"
echo "📊 After cleanup:"
echo "   Files: $AFTER_COUNT"
echo "   Size: $AFTER_SIZE"
echo "   Removed: $((BEFORE_COUNT - AFTER_COUNT)) files"

# Optional: Remove empty subdirectories
find "$RESULTS_DIR" -type d -empty -delete 2>/dev/null || true

echo "🎉 Results directory cleaned!"