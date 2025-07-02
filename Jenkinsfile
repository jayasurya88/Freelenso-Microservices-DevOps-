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
    }

    tools {
        'hudson.plugins.sonar.SonarRunnerInstallation' 'sonar-scanner'
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
                script {
                    def scannerHome = tool 'sonar-scanner'
                    withSonarQubeEnv('sonar') {
                        sh """
                            ${scannerHome}/bin/sonar-scanner \
                            -Dsonar.projectName=freelenso-microservices \
                            -Dsonar.projectKey=freelenso-microservices \
                            -Dsonar.sources=services,core,freelenso \
                            -Dsonar.language=py \
                            -Dsonar.python.version=3 \
                            -Dsonar.host.url=http://172.22.2.14:9000 \
                            -Dsonar.sourceEncoding=UTF-8
                        """
                    }
                }
            }
        }

        stage('Build User Service Image') {
            steps {
                dir('services/user-service') {
                    script {
                        sh '''
                        echo "=== Checking files in user-service ==="
                        ls -la
                        echo "=== Dockerfile content ==="
                        cat Dockerfile || echo "Dockerfile not found"
                        echo "=== Requirements content ==="
                        cat requirements.txt || echo "requirements.txt not found"
                        '''
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
                        sh '''
                        echo "=== Checking files in project-service ==="
                        ls -la
                        echo "=== Dockerfile content ==="
                        cat Dockerfile || echo "Dockerfile not found"
                        echo "=== Requirements content ==="
                        cat requirements.txt || echo "requirements.txt not found"
                        '''
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
                        sh '''
                        echo "=== Checking files in notification-service ==="
                        ls -la
                        echo "=== Dockerfile content ==="
                        cat Dockerfile || echo "Dockerfile not found"
                        echo "=== Requirements content ==="
                        cat requirements.txt || echo "requirements.txt not found"
                        '''
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
                        sh '''
                        echo "=== Checking files in payment-service ==="
                        ls -la
                        echo "=== Dockerfile content ==="
                        cat Dockerfile || echo "Dockerfile not found"
                        echo "=== Requirements content ==="
                        cat requirements.txt || echo "requirements.txt not found"
                        '''
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
                    sh '''
                    echo "=== Checking files in web ==="
                    ls -la
                    echo "=== Dockerfile content ==="
                    cat Dockerfile || echo "Dockerfile not found"
                    echo "=== Requirements content ==="
                    cat requirements.txt || echo "requirements.txt not found"
                    '''
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
                        sh '''
                        echo "=== Checking files in api-gateway ==="
                        ls -la
                        echo "=== Dockerfile content ==="
                        cat Dockerfile || echo "Dockerfile not found"
                        echo "=== Requirements content ==="
                        cat requirements.txt || echo "requirements.txt not found"
                        '''
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
                    sh "kubectl apply -f k8s/"
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
                script {
                    sh """
                    kubectl get pods
                    kubectl get services
                    kubectl get deployments
                    """
                }
            }
        }
    }

    post {
        success {
            script {
                echo 'Pipeline completed successfully!'
            }
        }
        failure {
            script {
                echo '❗ Pipeline failed. Check logs above.'
            }
        }
    }
} 