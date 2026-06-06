#!/bin/bash

################################################################################
# SECURITY REMEDIATION SCRIPT - opspulse Repository
# Purpose: Permanently remove exposed .env files from git history
# Usage: bash cleanup_credentials.sh
# 
# WARNING: This script will rewrite git history. All team members must:
# 1. Back up any local work
# 2. Force pull after script completes
# 3. Verify all functionality before resuming development
################################################################################

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        OPSPULSE SECURITY REMEDIATION - STARTING               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 0: Pre-flight checks
echo -e "${BLUE}[Step 0/5]${NC} Running pre-flight checks..."

if ! command -v git &> /dev/null; then
    echo -e "${RED}ERROR: git not found${NC}"
    exit 1
fi

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Not in a git repository${NC}"
    exit 1
fi

REPO_PATH=$(git rev-parse --show-toplevel)
REPO_NAME=$(basename "$REPO_PATH")

if [ "$REPO_NAME" != "opspulse" ]; then
    echo -e "${RED}ERROR: This script must be run from opspulse repository${NC}"
    echo -e "${RED}Current: $REPO_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Git repository validated${NC}"
echo -e "${GREEN}✓ Repository: $REPO_PATH${NC}"
echo ""

# Step 1: Backup
echo -e "${BLUE}[Step 1/5]${NC} Creating backup..."

BACKUP_DIR="/tmp/opspulse_backup_$(date +%s)"
mkdir -p "$BACKUP_DIR"
cp -r "$REPO_PATH/.git" "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backup created at: $BACKUP_DIR${NC}"
echo ""

# Step 2: Check for BFG or install git-filter-repo
echo -e "${BLUE}[Step 2/5]${NC} Setting up git history cleaning tools..."

CLEANING_TOOL="git-filter-repo"

if command -v bfg &> /dev/null; then
    CLEANING_TOOL="bfg"
    echo -e "${GREEN}✓ Found BFG Repo-Cleaner${NC}"
elif command -v git-filter-repo &> /dev/null; then
    echo -e "${GREEN}✓ Found git-filter-repo${NC}"
else
    echo -e "${YELLOW}Installing git-filter-repo...${NC}"
    pip install git-filter-repo
    echo -e "${GREEN}✓ git-filter-repo installed${NC}"
fi

echo ""

# Step 3: Remove sensitive files using chosen tool
echo -e "${BLUE}[Step 3/5]${NC} Removing sensitive files from history..."

if [ "$CLEANING_TOOL" = "bfg" ]; then
    echo -e "${YELLOW}Using BFG to remove .env files...${NC}"
    bfg --delete-files .env "$REPO_PATH"
    bfg --delete-files app/.env "$REPO_PATH"
    echo -e "${GREEN}✓ BFG processing complete${NC}"
else
    echo -e "${YELLOW}Using git-filter-repo to remove .env files...${NC}"
    cd "$REPO_PATH"
    git filter-repo --path .env --invert-paths --force
    git filter-repo --path app/.env --invert-paths --force
    cd - > /dev/null
    echo -e "${GREEN}✓ git-filter-repo processing complete${NC}"
fi

echo ""

# Step 4: Clean git references
echo -e "${BLUE}[Step 4/5]${NC} Cleaning git references and garbage collection..."

cd "$REPO_PATH"

# Expire all reflog entries
git reflog expire --expire=now --all 2>/dev/null || true

# Garbage collection
git gc --prune=now --aggressive

echo -e "${GREEN}✓ Git references cleaned${NC}"
echo ""

# Step 5: Display next steps
echo -e "${BLUE}[Step 5/5]${NC} Verification and next steps..."
echo ""
echo -e "${GREEN}✓ CREDENTIAL REMOVAL COMPLETE${NC}"
echo ""

# Verify .env files are gone
echo -e "${YELLOW}Verifying sensitive files are removed...${NC}"

if git log --all --name-only --pretty=format: | grep -E "\.env|\.env\." | grep -v "\.env\."; then
    echo -e "${RED}WARNING: .env files still found in history${NC}"
else
    echo -e "${GREEN}✓ No .env files detected in history${NC}"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              NEXT STEPS - READ CAREFULLY                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${YELLOW}1. VERIFY LOCAL CHANGES:${NC}"
echo "   git log --oneline --all | head -10"
echo ""
echo -e "${YELLOW}2. PUSH FORCE UPDATE (⚠️  IRREVERSIBLE):${NC}"
echo "   git push origin --force-with-lease --all"
echo "   git push origin --force-with-lease --tags"
echo ""
echo -e "${YELLOW}3. NOTIFY TEAM MEMBERS:${NC}"
echo "   All collaborators must:"
echo "   - Back up any uncommitted work"
echo "   - Clone fresh: rm -rf opspulse && git clone ..."
echo "   - Or force pull: git fetch && git reset --hard origin/main"
echo ""
echo -e "${YELLOW}4. VERIFY GITHUB STATUS:${NC}"
echo "   Visit: https://github.com/Kethanreddy30/opspulse"
echo "   Check that history is rewritten"
echo ""
echo -e "${YELLOW}5. UPDATE GITHUB SECRETS:${NC}"
echo "   Go to: https://github.com/Kethanreddy30/opspulse/settings/secrets/actions"
echo "   Add:"
echo "   - SUPABASE_KEY (new rotated key)"
echo "   - UPSTASH_REDIS_TOKEN (new rotated token)"
echo "   - REDIS_URL (new connection string)"
echo ""
echo -e "${YELLOW}6. VERIFY CI/CD:${NC}"
echo "   Check that GitHub Actions workflows use secrets correctly"
echo ""
echo -e "${YELLOW}BACKUP LOCATION (keep for 30 days):${NC}"
echo "   $BACKUP_DIR"
echo ""
echo -e "${YELLOW}IMPORTANT - REVOKE OLD CREDENTIALS:${NC}"
echo "   Before proceeding, ensure you have already:"
echo "   ✓ Rotated Supabase anon key"
echo "   ✓ Rotated Upstash Redis token"
echo "   ✓ Updated all environment variables"
echo ""
echo -e "${GREEN}Script execution successful!${NC}"
