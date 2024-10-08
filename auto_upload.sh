#!/bin/bash

# Navigate to the repository
cd "C:\Users\CrudeIntern\OneDrive - Hengli Petrochemical International Pte Ltd\Market Analysis\Current Projects\Hurricane"

# Add files, commit, and push
git add .
git commit -m "Automated commit $(date +'%Y-%m-%d %H:%M:%S')"
git push origin main
