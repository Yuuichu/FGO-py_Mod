#!/bin/bash
# 创建新功能规范目录
# 用法: ./scripts/create-new-feature.sh <feature-name>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ -z "$1" ]; then
    echo "用法: $0 <feature-name>"
    echo "示例: $0 auto-story-skip"
    exit 1
fi

FEATURE_NAME="$1"
FEATURE_DIR="$PROJECT_ROOT/specs/$FEATURE_NAME"

if [ -d "$FEATURE_DIR" ]; then
    echo "错误: 功能目录已存在: $FEATURE_DIR"
    exit 1
fi

echo "创建功能目录: $FEATURE_DIR"
mkdir -p "$FEATURE_DIR"

# 复制模板
cp "$PROJECT_ROOT/templates/spec-template.md" "$FEATURE_DIR/spec.md"
cp "$PROJECT_ROOT/templates/plan-template.md" "$FEATURE_DIR/plan.md"
cp "$PROJECT_ROOT/templates/tasks-template.md" "$FEATURE_DIR/tasks.md"

# 替换模板中的占位符
sed -i "s/\[功能名称\]/$FEATURE_NAME/g" "$FEATURE_DIR/spec.md"
sed -i "s/\[功能名称\]/$FEATURE_NAME/g" "$FEATURE_DIR/plan.md"
sed -i "s/\[功能名称\]/$FEATURE_NAME/g" "$FEATURE_DIR/tasks.md"

echo "✅ 功能规范目录已创建"
echo ""
echo "下一步:"
echo "  1. 编辑 specs/$FEATURE_NAME/spec.md 定义功能需求"
echo "  2. 编辑 specs/$FEATURE_NAME/plan.md 制定实现计划"
echo "  3. 编辑 specs/$FEATURE_NAME/tasks.md 分解具体任务"
