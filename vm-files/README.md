# VM Files for Code Review

These files were downloaded from the Azure VM (`172.174.232.173`) where the backend API runs.

## Files Included

- **main.py** - FastAPI backend that handles admin panel requests
- **working_generators.py** - Script generators (attempted fix for placeholder issue)  
- **admin-changes.json** - Change queue data showing all submitted requests
- **change-23.sh** - Example generated script (working implementation)
- **manual_test_change.sh** - Manual test script that was executed

## Key Issue

The FastAPI backend successfully:
1. Receives change requests from admin panel
2. Generates working bash scripts (not placeholders)
3. Executes scripts that modify source files
4. Builds Next.js project successfully  
5. Deploys to Azure Static Web Apps without errors

However, **NO CHANGES appear on the live dashboard** at https://www.mulroystreetcap.com despite successful completion of all steps above.

## SSH Access

To access VM files directly:
```bash
ssh -i /Users/kylemulroy/ktmulroy-msc-key.pem ktmulroy@172.174.232.173
```

## API Process Location
- Main API: `/home/ktmulroy/trading-api/main.py`
- Source Code: `/home/ktmulroy/apps/web/`
- Change Scripts: `/home/ktmulroy/pending-changes/`
- Change Queue: `/home/ktmulroy/admin-changes.json`
