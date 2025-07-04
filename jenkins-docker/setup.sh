#!/bin/bash

# Build and start Jenkins container
docker-compose up -d

# Wait for Jenkins to start
echo "Waiting for Jenkins to start..."
until $(curl --output /dev/null --silent --head --fail http://localhost:8080); do
    printf '.'
    sleep 5
done

echo "\nJenkins is up and running!"

# Get the initial admin password
echo "\nJenkins initial admin password:"
docker-compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

echo "\nAccess Jenkins at http://localhost:8080"
echo "Use the password above for initial setup" 