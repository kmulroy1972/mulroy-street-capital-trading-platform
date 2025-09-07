from datetime import datetime

def generate_change_script(change):
    """Generate working execution script based on change description"""
    description = change['description'].lower()
    change_id = change['id']
    timestamp = datetime.now().isoformat()
    
    # Real working scripts for different types of changes
    if 'remove' in description and 'orange' in description and 'mulroy' in description:
        return generate_remove_orange_header_script(change_id, timestamp)
    elif 'remove' in description and ('weather' in description or 'time' in description):
        return generate_remove_weather_script(change_id, timestamp, description)
    elif 'color' in description and 'blue' in description:
        return generate_color_change_script(change_id, timestamp, description)
    else:
        return generate_generic_change_script(change_id, timestamp, description)

def generate_remove_orange_header_script(change_id, timestamp):
    return f'''#!/bin/bash
# Working script to remove orange MULROY STREET CAPITAL
# Change ID: {change_id}
# Generated: {timestamp}

set -e  # Exit on any error

echo "=== Executing Real Change #{change_id} ==="
echo "Removing orange MULROY STREET CAPITAL from header"
echo "Started: \Fri Sep  5 21:35:30 EDT 2025"

cd /home/ktmulroy/apps/web

# Backup current file
cp components/modules/Header.tsx components/modules/Header.tsx.backup-\20250905-213530 2>/dev/null || true

# Use sed to remove the orange header line
sed -i 's/<h1 className="text-xl font-bold text-orange-500">MULROY STREET CAPITAL<\/h1>//g' components/modules/Header.tsx

# Update the comment from "Logo and Status" to just "Status"
sed -i 's/Left: Logo and Status/Left: Status/g' components/modules/Header.tsx

echo "Code changes completed"

# Build the project
echo "Building project..."
npm run build

if [ \0 -eq 0 ]; then
    echo "Build successful"
    
    # Deploy to production
    echo "Deploying to production..."
    npx swa deploy ./out --deployment-token \78463feaa293efcb87191304b4f24a1cd2884d069c353bff596f5c956669f84901-901f81c1-011d-4cb9-b79e-af3aad8ab4f400f271203a07990f --env production
    
    if [ \0 -eq 0 ]; then
        echo "✅ Deployment successful"
        echo "Changes should be visible at https://www.mulroystreetcap.com"
        echo "Completed: \Fri Sep  5 21:35:30 EDT 2025"
        exit 0
    else
        echo "❌ Deployment failed"
        exit 1
    fi
else
    echo "❌ Build failed, rolling back changes"
    # Restore backup if it exists
    latest_backup=\
    if [ -n "\" ]; then
        cp "\" components/modules/Header.tsx
        echo "Restored from backup: \"
    fi
    exit 1
fi
'''

def generate_remove_weather_script(change_id, timestamp, description):
    return f'''#!/bin/bash
# Working script to remove weather/time information
# Change ID: {change_id}
# Description: {description}
# Generated: {timestamp}

set -e

echo "=== Executing Real Change #{change_id} ==="
echo "Removing weather and time information from header"
echo "Started: \Fri Sep  5 21:35:30 EDT 2025"

cd /home/ktmulroy/apps/web

# Backup current file
cp components/Header.tsx components/Header.tsx.backup-\20250905-213530 2>/dev/null || true

# Remove the entire weather/time div section
sed -i '/flex items-center gap-4 text-sm text-text-secondary/,/<\/div>/d' components/Header.tsx

echo "Code changes completed"

# Build and deploy
echo "Building project..."
npm run build

if [ \0 -eq 0 ]; then
    echo "Build successful - deploying..."
    npx swa deploy ./out --deployment-token \78463feaa293efcb87191304b4f24a1cd2884d069c353bff596f5c956669f84901-901f81c1-011d-4cb9-b79e-af3aad8ab4f400f271203a07990f --env production
    
    if [ \0 -eq 0 ]; then
        echo "✅ Changes deployed successfully"
        echo "Completed: \Fri Sep  5 21:35:30 EDT 2025"
        exit 0
    else
        echo "❌ Deployment failed"
        exit 1
    fi
else
    echo "❌ Build failed, rolling back"
    latest_backup=\
    if [ -n "\" ]; then
        cp "\" components/Header.tsx
    fi
    exit 1
fi
'''

def generate_color_change_script(change_id, timestamp, description):
    return f'''#!/bin/bash
# Working script to change header colors
# Change ID: {change_id}
# Description: {description}
# Generated: {timestamp}

set -e

echo "=== Executing Real Change #{change_id} ==="
echo "Changing header colors"
echo "Started: \Fri Sep  5 21:35:30 EDT 2025"

cd /home/ktmulroy/apps/web

# Backup current file
cp components/modules/Header.tsx components/modules/Header.tsx.backup-\20250905-213530 2>/dev/null || true

# Change orange to blue
sed -i 's/text-orange-500/text-blue-500/g' components/modules/Header.tsx

echo "Code changes completed"

# Build and deploy
npm run build && npx swa deploy ./out --deployment-token \78463feaa293efcb87191304b4f24a1cd2884d069c353bff596f5c956669f84901-901f81c1-011d-4cb9-b79e-af3aad8ab4f400f271203a07990f --env production

if [ \0 -eq 0 ]; then
    echo "✅ Color changes deployed successfully"
    echo "Completed: \Fri Sep  5 21:35:30 EDT 2025"
else
    echo "❌ Build or deployment failed"
    exit 1
fi
'''

def generate_generic_change_script(change_id, timestamp, description):
    return f'''#!/bin/bash
# Generic change script - requires manual implementation
# Change ID: {change_id}
# Description: {description}
# Generated: {timestamp}

set -e

echo "=== Change #{change_id} Requires Manual Implementation ==="
echo "Description: {description}"
echo "Started: \Fri Sep  5 21:35:30 EDT 2025"

cd /home/ktmulroy/apps/web

echo "⚠️  This change type requires manual code implementation"
echo "Change description: {description}"
echo ""
echo "To implement manually:"
echo "1. Edit the appropriate files in components/ directory"
echo "2. Run: npm run build"
echo "3. Run: npx swa deploy ./out --deployment-token \\\78463feaa293efcb87191304b4f24a1cd2884d069c353bff596f5c956669f84901-901f81c1-011d-4cb9-b79e-af3aad8ab4f400f271203a07990f --env production"
echo ""
echo "Common file locations:"
echo "- Main header: components/Header.tsx"
echo "- Dashboard header: components/modules/Header.tsx"
echo "- Other components: components/modules/"

echo "Completed: \Fri Sep  5 21:35:30 EDT 2025"
'''

def generate_add_test_text_script(change_id, timestamp, description):
    return f'''#!/bin/bash
# Working script to add test text to header
# Change ID: {change_id}
# Description: {description}
# Generated: {timestamp}

set -e

echo "=== Executing Real Change #{change_id} ==="
echo "Adding ADMIN TEST text to header"
echo "Started: \Fri Sep  5 21:42:44 EDT 2025"

cd /home/ktmulroy/apps/web

# Backup current file
cp components/modules/Header.tsx components/modules/Header.tsx.backup-\20250905-214244 2>/dev/null || true

# Add ADMIN TEST text to the header
/usr/bin/sed -i 's/<span className="text-sm">LIVE<\/span>/<span className="text-sm">LIVE - ADMIN TEST<\/span>/g' components/modules/Header.tsx

echo "Code changes completed"

# Build and deploy
echo "Building project..."
export PATH=/usr/bin:/bin:\/Library/Frameworks/Python.framework/Versions/3.13/bin:/opt/homebrew/bin:/opt/homebrew/sbin:/Library/Frameworks/Python.framework/Versions/3.11/bin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/Users/kylemulroy/.cursor/extensions/ms-python.debugpy-2025.8.0-darwin-arm64/bundled/scripts/noConfigScripts
npm run build

if [ \0 -eq 0 ]; then
    echo "Build successful - deploying..."
    npx swa deploy ./out --deployment-token \78463feaa293efcb87191304b4f24a1cd2884d069c353bff596f5c956669f84901-901f81c1-011d-4cb9-b79e-af3aad8ab4f400f271203a07990f --env production
    
    if [ \0 -eq 0 ]; then
        echo "✅ ADMIN TEST text added successfully"
        echo "Check https://www.mulroystreetcap.com for the change"
        echo "Completed: \Fri Sep  5 21:42:44 EDT 2025"
        exit 0
    else
        echo "❌ Deployment failed"
        exit 1
    fi
else
    echo "❌ Build failed, rolling back"
    latest_backup=\
    if [ -n "\" ]; then
        cp "\" components/modules/Header.tsx
    fi
    exit 1
fi
'''
