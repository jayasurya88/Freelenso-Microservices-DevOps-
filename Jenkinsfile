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
                node {
                    git url: 'https://github.com/jayasurya88/Freelenso-Microservices-DevOps-.git', 
                        branch: 'main'
                }
            }
        }

        stage('File System Security Scan') {
            steps {
                node {
                    sh "trivy fs --security-checks vuln,config --format table -o trivy-fs-report.html ."
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                node {
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
        }

        stage('Build User Service Image') {
            steps {
                node {
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
        }

        stage('Build Project Service Image') {
            steps {
                node {
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
        }

        stage('Build Notification Service Image') {
            steps {
                node {
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
        }

        stage('Build Payment Service Image') {
            steps {
                node {
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
        }

        stage('Build Web Application Image') {
            steps {
                node {
                    script {
                        sh '''
                        echo "=== Checking files in web ==="
                        ls -la
                        echo "=== Dockerfile content ==="
                        cat Dockerfile || echo "Dockerfile not found"
                        echo "=== Requirements content ==="
                        cat requirements.txt || echo "requirements.txt not found"
                        '''
                        withDockerRegistry(credentialsId: 'docker', toolName: 'docker') {
                            sh "docker build -t ${WEB_IMAGE} ."
                            sh "docker push ${WEB_IMAGE}"
                        }
                    }
                }
            }
        }

        stage('Build API Gateway Image') {
            steps {
                node {
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

        stage('Docker Scout Analysis') {
            steps {
                node {
                    script {
                        withDockerRegistry(credentialsId: 'docker', toolName: 'docker') {
                            sh """
                                docker-scout quickview ${USER_SERVICE_IMAGE}
                                docker-scout quickview ${PROJECT_SERVICE_IMAGE}
                                docker-scout quickview ${NOTIFICATION_SERVICE_IMAGE}
                                docker-scout quickview ${PAYMENT_SERVICE_IMAGE}
                                docker-scout quickview ${WEB_IMAGE}
                                docker-scout quickview ${API_GATEWAY_IMAGE}
                                
                                docker-scout cves ${USER_SERVICE_IMAGE}
                                docker-scout recommendations ${USER_SERVICE_IMAGE}
                            """
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            node {
                echo '🚀 Pipeline successful!'
                archiveArtifacts artifacts: 'trivy-fs-report.html', allowEmptyArchive: true
            }
        }
        failure {
            node {
                echo '❗ Pipeline failed. Check logs above.'
                sh '''
                echo "=== Error Investigation ==="
                docker ps -a
                '''
            }
        }
        always {
            node {
                archiveArtifacts artifacts: 'trivy-fs-report.html', allowEmptyArchive: true
            }
        }
    }
} 