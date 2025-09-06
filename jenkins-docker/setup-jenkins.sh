#!/bin/bash

# Create Jenkins backup directory
mkdir -p jenkins_backup

# Start Jenkins and SonarQube
echo "🚀 Starting Jenkins and SonarQube..."
docker-compose up -d

# Wait for Jenkins to start
echo "⏳ Waiting for Jenkins to start..."
sleep 30

# Get initial admin password
echo "🔑 Jenkins Initial Admin Password:"
docker-compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

echo "📋 Setup Instructions:"
echo "1. Open http://localhost:8080"
echo "2. Use the password above to unlock Jenkins"
echo "3. Install suggested plugins"
echo "4. Create admin user"
echo "5. SonarQube available at http://localhost:9000 (admin/admin)"
