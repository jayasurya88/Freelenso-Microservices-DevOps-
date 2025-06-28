pipeline {
    agent any
    environment {
        REGISTRY = "docker.io/yourusername" // Change to your Docker Hub username if pushing images
    }
    stages {
        stage('Build Docker Images') {
            steps {
                script {
                    def services = ['user-service', 'project-service', 'payment-service', 'notification-service', 'api-gateway']
                    for (svc in services) {
                        dir("services/${svc}") {
                            sh "docker build -t $REGISTRY/${svc}:latest ."
                        }
                    }
                }
            }
        }
        // Optionally add a test stage here if you have tests
        stage('Deploy to Kubernetes') {
            steps {
                sh 'kubectl apply -f k8s/'
            }
        }
    }
} 