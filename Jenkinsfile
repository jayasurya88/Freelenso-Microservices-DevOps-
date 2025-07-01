pipeline {
    agent any

    environment {
        DOCKER_USERNAME = 'jayasurya88'
        USER_SERVICE_IMAGE = "${DOCKER_USERNAME}/freelenso-user-service:latest"
        PROJECT_SERVICE_IMAGE = "${DOCKER_USERNAME}/freelenso-project-service:latest"
        NOTIFICATION_SERVICE_IMAGE = "${DOCKER_USERNAME}/freelenso-notification-service:latest"
        PAYMENT_SERVICE_IMAGE = "${DOCKER_USERNAME}/freelenso-payment-service:latest"
        WEB_IMAGE = "${DOCKER_USERNAME}/freelenso-web:latest"
        API_GATEWAY_IMAGE = "${DOCKER_USERNAME}/freelenso-api-gateway:latest"
        SCANNER_HOME = tool 'sonar-scanner'
    }

    stages {
        stage('Git Checkout') {
            steps {
                git url: 'https://github.com/jayasurya88/Freelenso-Microservices-DevOps-.git', 
                    branch: 'main'
            }
        }

        stage('File System Security Scan') {
            steps {
                sh "trivy fs --security-checks vuln,config --format table -o trivy-fs-report.html ."
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('sonar') {
                    sh """
                    ${SCANNER_HOME}/bin/sonar-scanner \
                    -Dsonar.projectName=freelenso-microservices \
                    -Dsonar.projectKey=freelenso-microservices \
                    -Dsonar.sources=services,core,freelenso \
                    -Dsonar.language=py \
                    -Dsonar.python.version=3 \
                    -Dsonar.host.url=http://localhost:9000
                    """
                }
            }
        }

        stage('Build User Service Image') {
            steps {
                dir('services/user-service') {
                    script {
                        withDockerRegistry(credentialsId: 'docker-cred', toolName: 'docker') {
                            sh "docker build -t ${USER_SERVICE_IMAGE} ."
                            sh "docker push ${USER_SERVICE_IMAGE}"
                        }
                    }
                }
            }
        }

        stage('Build Project Service Image') {
            steps {
                dir('services/project-service') {
                    script {
                        withDockerRegistry(credentialsId: 'docker-cred', toolName: 'docker') {
                            sh "docker build -t ${PROJECT_SERVICE_IMAGE} ."
                            sh "docker push ${PROJECT_SERVICE_IMAGE}"
                        }
                    }
                }
            }
        }

        stage('Build Notification Service Image') {
            steps {
                dir('services/notification-service') {
                    script {
                        withDockerRegistry(credentialsId: 'docker-cred', toolName: 'docker') {
                            sh "docker build -t ${NOTIFICATION_SERVICE_IMAGE} ."
                            sh "docker push ${NOTIFICATION_SERVICE_IMAGE}"
                        }
                    }
                }
            }
        }

        stage('Build Payment Service Image') {
            steps {
                dir('services/payment-service') {
                    script {
                        withDockerRegistry(credentialsId: 'docker-cred', toolName: 'docker') {
                            sh "docker build -t ${PAYMENT_SERVICE_IMAGE} ."
                            sh "docker push ${PAYMENT_SERVICE_IMAGE}"
                        }
                    }
                }
            }
        }

        stage('Build Web Application Image') {
            steps {
                script {
                    withDockerRegistry(credentialsId: 'docker-cred', toolName: 'docker') {
                        sh "docker build -t ${WEB_IMAGE} ."
                        sh "docker push ${WEB_IMAGE}"
                    }
                }
            }
        }

        stage('Build API Gateway Image') {
            steps {
                dir('services/api-gateway') {
                    script {
                        withDockerRegistry(credentialsId: 'docker-cred', toolName: 'docker') {
                            sh "docker build -t ${API_GATEWAY_IMAGE} ."
                            sh "docker push ${API_GATEWAY_IMAGE}"
                        }
                    }
                }
            }
        }

        stage('Docker Scout Analysis') {
            steps {
                script {
                    withDockerRegistry(credentialsId: 'docker-cred', toolName: 'docker') {
                        sh "docker-scout quickview ${USER_SERVICE_IMAGE}"
                        sh "docker-scout quickview ${PROJECT_SERVICE_IMAGE}"
                        sh "docker-scout quickview ${WEB_IMAGE}"
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    // Apply all Kubernetes manifests
                    sh "kubectl apply -f k8s/"
                    
                    // Wait for deployments to be ready
                    sh """
                    kubectl wait --for=condition=available --timeout=300s deployment/user-db
                    kubectl wait --for=condition=available --timeout=300s deployment/project-db
                    kubectl wait --for=condition=available --timeout=300s deployment/notification-db
                    kubectl wait --for=condition=available --timeout=300s deployment/user-service
                    kubectl wait --for=condition=available --timeout=300s deployment/project-service
                    kubectl wait --for=condition=available --timeout=300s deployment/notification-service
                    kubectl wait --for=condition=available --timeout=300s deployment/payment-service
                    kubectl wait --for=condition=available --timeout=300s deployment/web
                    kubectl wait --for=condition=available --timeout=300s deployment/api-gateway
                    """
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                echo "=== Pod Status ==="
                kubectl get pods
                echo "=== Service Status ==="
                kubectl get services
                echo "=== Testing Web Service ==="
                kubectl port-forward service/web 8000:8000 &
                sleep 10
                curl -I http://localhost:8000 || true
                pkill -f "kubectl port-forward"
                '''
            }
        }
    }

    post {
        success {
            echo '🚀 Freelenso Microservices deployed successfully!'
            sh 'kubectl get pods'
            archiveArtifacts artifacts: 'trivy-fs-report.html', allowEmptyArchive: true
        }
        failure {
            echo '❗ Pipeline failed. Check logs above.'
            sh '''
            echo "=== Pod Logs ==="
            kubectl logs -l app=web --tail=50 || true
            kubectl logs -l app=user-service --tail=50 || true
            '''
        }
        always {
            sh '''
            echo "=== Final Status ==="
            kubectl get pods
            kubectl get services
            '''
            archiveArtifacts artifacts: 'trivy-fs-report.html', allowEmptyArchive: true
        }
    }
} 