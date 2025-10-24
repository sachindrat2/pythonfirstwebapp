#!/usr/bin/env python3
"""
Create a simple deployment trigger file to force Azure update
"""

import json
import time
from datetime import datetime

def create_deployment_trigger():
    """Create a deployment trigger with timestamp"""
    
    deployment_info = {
        "deployment_id": f"deploy-{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.4-fixed",
        "docker_image": "sachindra785/ownnoteapp:latest",
        "changes": [
            "Fixed admin login redirect issue",
            "Added proper form handling for web interface",
            "Enhanced admin dashboard with 3D charts",
            "Improved error handling and debugging"
        ],
        "status": "ready_for_deployment",
        "force_update": True
    }
    
    # Save deployment info
    with open('deployment_trigger.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    print("📦 Deployment Trigger Created")
    print("=" * 40)
    print(f"Deployment ID: {deployment_info['deployment_id']}")
    print(f"Version: {deployment_info['version']}")
    print(f"Docker Image: {deployment_info['docker_image']}")
    print(f"Timestamp: {deployment_info['timestamp']}")
    print()
    print("🔧 Manual Azure Update Steps:")
    print("1. Go to Azure Portal")
    print("2. Navigate to App Service: ownnoteapp")
    print("3. Go to 'Deployment Center'")
    print("4. Click 'Restart' or 'Redeploy'")
    print("5. Or go to 'Overview' → 'Restart'")
    print()
    print("🐳 Docker Hub Image Status:")
    print("- Image: sachindra785/ownnoteapp:latest")
    print("- Version: v1.0.4 (with admin fixes)")
    print("- Status: Pushed and ready")
    print()
    print("✅ Once restarted, test at:")
    print("https://ownnoteapp-hedxcahwcrhwb8hb.canadacentral-01.azurewebsites.net/admin/login")

if __name__ == "__main__":
    create_deployment_trigger()