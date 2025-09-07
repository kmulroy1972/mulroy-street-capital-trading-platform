#!/bin/bash

echo "Component Update Log"
echo "==================="
echo ""

# Show last 5 updates
echo "Recent Updates:"
ls -lt components/modules/*.tsx | head -5 | while read -r line; do
    echo "  $line"
done

echo ""
echo "Current Versions:"
cat components/versions.json | jq '.components'

echo ""
echo "To update a component: ./update-component.sh"
echo "To deploy: ./deploy-modular.sh"