#!/usr/bin/env bash
# 用法：
#   ./new.sh 1 two-sum
#   ./new.sh 1 two-sum 哈希表
#
# 会在 leetcode/ 下生成 0001-two-sum.md 并自动打开

set -euo pipefail

NUM="${1:?用法: ./new.sh <题号> <英文短名> [专题]}"
SLUG="${2:?用法: ./new.sh <题号> <英文短名> [专题]}"
TAG="${3:-未分类}"

cd "$(dirname "$0")"

PAD=$(printf "%04d" "$NUM" 2>/dev/null || echo "$NUM")
FILE="${PAD}-${SLUG}.md"
DATE=$(date +%Y-%m-%d)

if [ -e "$FILE" ]; then
  echo "已存在：leetcode/$FILE"
  exit 1
fi

cat > "$FILE" <<EOF
# ${NUM}. ${SLUG}

- **难度**：
- **专题**：${TAG}
- **日期**：${DATE}
- **链接**：https://leetcode.cn/problems/${SLUG}/

## 思路

（两三句话，说清核心方法。不要抄题解，用你自己的话）

## 复杂度

- 时间：
- 空间：

## 代码

\`\`\`python
# 从 LeetCode 复制过来贴在这里
\`\`\`

## 易错点

-
EOF

echo "✓ 已创建 leetcode/$FILE"
echo
echo "下一步："
echo "  1. 打开这个文件（VS Code 里 ⌘+P 输入 ${FILE}）"
echo "  2. 从 LeetCode 复制代码，粘贴到「代码」那段"
echo "  3. 填「思路」和「易错点」"
echo "  4. git add -A && git commit -m \"feat: 刷题 ${NUM} ${SLUG}\" && git push"
