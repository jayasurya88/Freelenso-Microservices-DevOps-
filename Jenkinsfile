pipeline {
    agent any

    triggers {
        githubPush()
    }

    environment {
        DOCKER_REGISTRY = 'jayasurya88'
        VERSION = "${BUILD_NUMBER}"
        SONAR_PROJECT_KEY = 'freelenso-project'
        SONAR_HOST_URL = 'http://sonarqube:9000'
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
                git branch: 'main', url: 'https://github.com/jayasurya88/Freelenso-Microservices-DevOps-.git'
            }
        }

        stage('Verify Tools') {
            steps {
                sh '''
                    echo "Checking required tools..."
                    which docker || { echo "Docker not found"; exit 1; }
                    which trivy || { echo "Trivy not found"; exit 1; }
                    which sonar-scanner || { echo "SonarQube Scanner not found"; exit 1; }
                    docker --version
                    trivy --version
                    sonar-scanner --version
                '''
            }
        }

        stage('File System Security Scan') {
            steps {
                script {
                    try {
                        sh 'trivy fs --security-checks vuln,config --format table -o trivy-fs-report.html .'
                    } catch (Exception e) {
                        echo "Trivy scan failed: ${e.message}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    try {
                        sh """
                            sonar-scanner \
                                -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                -Dsonar.sources=. \
                                -Dsonar.host.url=${SONAR_HOST_URL} \
                                -Dsonar.login=admin \
                                -Dsonar.password=admin
                        """
                    } catch (Exception e) {
                        echo "SonarQube analysis failed: ${e.message}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }

        stage('Build Services') {
            parallel {
                stage('Build User Service') {
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
                                withDockerRegistry(credentialsId: 'docker', toolName: 'docker') {
                                    sh "docker build -t ${USER_SERVICE_IMAGE} ."
                                    sh "docker push ${USER_SERVICE_IMAGE}"
                                }
                            }
                        }
                    }
                }
                stage('Build Project Service') {
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
                                withDockerRegistry(credentialsId: 'docker', toolName: 'docker') {
                                    sh "docker build -t ${PROJECT_SERVICE_IMAGE} ."
                                    sh "docker push ${PROJECT_SERVICE_IMAGE}"
                                }
                            }
                        }
                    }
                }
                stage('Build Notification Service') {
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
                                withDockerRegistry(credentialsId: 'docker', toolName: 'docker') {
                                    sh "docker build -t ${NOTIFICATION_SERVICE_IMAGE} ."
                                    sh "docker push ${NOTIFICATION_SERVICE_IMAGE}"
                                }
                            }
                        }
                    }
                }
                stage('Build Payment Service') {
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
                                withDockerRegistry(credentialsId: 'docker', toolName: 'docker') {
                                    sh "docker build -t ${PAYMENT_SERVICE_IMAGE} ."
                                    sh "docker push ${PAYMENT_SERVICE_IMAGE}"
                                }
                            }
                        }
                    }
                }
                stage('Build API Gateway') {
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
                                withDockerRegistry(credentialsId: 'docker', toolName: 'docker') {
                                    sh "docker build -t ${API_GATEWAY_IMAGE} ."
                                    sh "docker push ${API_GATEWAY_IMAGE}"
                                }
                            }
                        }
                    }
                }
            }
        }

        stage('Docker Scout Analysis') {
            steps {
                script {
                    try {
                        sh """
                            for service in user-service project-service notification-service payment-service api-gateway; do
                                docker scout cves ${DOCKER_REGISTRY}/freelenso-${service}:${VERSION}
                            done
                        """
                    } catch (Exception e) {
                        echo "Docker Scout analysis failed: ${e.message}"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }

        stage('Push Images') {
            when {
                branch 'main'
                expression { currentBuild.result != 'FAILURE' }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        for service in user-service project-service notification-service payment-service api-gateway; do
                            docker push ${DOCKER_REGISTRY}/freelenso-${service}:${VERSION}
                        done
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'trivy-fs-report.html', allowEmptyArchive: true
            
            script {
                if (currentBuild.result == 'FAILURE') {
                    echo '❗ Pipeline failed. Check logs above.'
                    sh '''
                        echo "=== Error Investigation ==="
                        docker ps -a
                        df -h
                        free -m
                    '''
                }
            }
            
            cleanWs()
        }
        
        success {
            echo '✅ Pipeline completed successfully!'
        }
        
        unstable {
            echo '⚠️ Pipeline completed with warnings/unstable status.'
        }
    }
} 