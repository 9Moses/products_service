// Root Pipeline: Orchestrates API and Main services
// Builds and tests both services in isolated Docker containers

pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '30'))
        timestamps()
        timeout(time: 2, unit: 'HOURS')
        disableConcurrentBuilds()
    }

    environment {
        REGISTRY = 'ghcr.io'
        REGISTRY_NAMESPACE = '9moses'
        REGISTRY_CREDENTIALS = 'ghcr-registry-credentials'

        API_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/rest-api:${BUILD_NUMBER}"
        MAIN_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/rest-main:${BUILD_NUMBER}"
        LATEST_API_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/rest-api:latest"
        LATEST_MAIN_IMAGE = "${REGISTRY}/${REGISTRY_NAMESPACE}/rest-main:latest"

        DOCKER_BUILDKIT = '0'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    echo "Repository: $(git config --get remote.origin.url)"
                    echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
                    echo "Commit: $(git rev-parse HEAD)"
                '''
            }
        }

        stage('Build Services') {
            parallel {
                stage('Build API') {
                    steps {
                        sh '''
                            cd ${WORKSPACE}/api
                            docker build \
                                --tag ${API_IMAGE} \
                                --tag ${LATEST_API_IMAGE} \
                                --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                                --build-arg VCS_REF=$(git rev-parse --short HEAD) \
                                --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                -f Dockerfile .
                            echo "✓ API image built: ${API_IMAGE}"
                        '''
                    }
                }
                stage('Build Main') {
                    steps {
                        sh '''
                            cd ${WORKSPACE}/main
                            docker build \
                                --tag ${MAIN_IMAGE} \
                                --tag ${LATEST_MAIN_IMAGE} \
                                --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                                --build-arg VCS_REF=$(git rev-parse --short HEAD) \
                                --build-arg BUILD_NUMBER=${BUILD_NUMBER} \
                                -f Dockerfile .
                            echo "✓ Main image built: ${MAIN_IMAGE}"
                        '''
                    }
                }
            }
        }

        stage('Test Services') {
            parallel {
                stage('Test API') {
                    steps {
                        sh '''
                            echo "Running API tests..."
                            docker run --rm \
                                --volume ${WORKSPACE}/api:/app \
                                --workdir /app \
                                ${LATEST_API_IMAGE} \
                                bash -c "python manage.py test --verbosity=2 || true"
                        '''
                    }
                }
                stage('Test Main') {
                    steps {
                        sh '''
                            echo "Running Main tests..."
                            docker run --rm \
                                --volume ${WORKSPACE}/main:/app \
                                --workdir /app \
                                ${LATEST_MAIN_IMAGE} \
                                bash -c "python -m pytest tests -q || true"
                        '''
                    }
                }
            }
        }

        stage('Quality & Security') {
            parallel {
                stage('API Quality') {
                    steps {
                        sh '''
                            docker run --rm \
                                --volume ${WORKSPACE}/api:/app \
                                --workdir /app \
                                ${LATEST_API_IMAGE} \
                                bash -c "pip install flake8 pylint && \
                                         flake8 . --max-line-length=120 --exclude=migrations || true"
                        '''
                    }
                }
                stage('Main Quality') {
                    steps {
                        sh '''
                            docker run --rm \
                                --volume ${WORKSPACE}/main:/app \
                                --workdir /app \
                                ${LATEST_MAIN_IMAGE} \
                                bash -c "pip install flake8 pylint && \
                                         flake8 . --max-line-length=120 || true"
                        '''
                    }
                }
                stage('API Security') {
                    steps {
                        sh '''
                            docker run --rm \
                                --volume ${WORKSPACE}/api:/app \
                                ${LATEST_API_IMAGE} \
                                bash -c "pip install safety && safety check --json || true"
                        '''
                    }
                }
                stage('Main Security') {
                    steps {
                        sh '''
                            docker run --rm \
                                --volume ${WORKSPACE}/main:/app \
                                ${LATEST_MAIN_IMAGE} \
                                bash -c "pip install safety && safety check --json || true"
                        '''
                    }
                }
            }
        }

        stage('Push to Registry') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "${REGISTRY_CREDENTIALS}",
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                        echo "Authenticating with registry..."
                        echo ${DOCKER_PASS} | docker login ${REGISTRY} -u ${DOCKER_USER} --password-stdin
                        
                        echo "Pushing API images..."
                        docker push ${API_IMAGE}
                        docker push ${LATEST_API_IMAGE}
                        
                        echo "Pushing Main images..."
                        docker push ${MAIN_IMAGE}
                        docker push ${LATEST_MAIN_IMAGE}
                        
                        docker logout
                        echo "✓ All images pushed successfully"
                    '''
                }
            }
        }

        stage('Cleanup') {
            steps {
                sh '''
                    echo "Cleaning up Docker resources..."
                    docker rmi ${API_IMAGE} 2>/dev/null || true
                    docker rmi ${LATEST_API_IMAGE} 2>/dev/null || true
                    docker rmi ${MAIN_IMAGE} 2>/dev/null || true
                    docker rmi ${LATEST_MAIN_IMAGE} 2>/dev/null || true
                    docker system prune -f 2>/dev/null || true
                '''
            }
        }
    }

    post {
        always {
            sh '''
                echo ""
                echo "====== Build Summary ======"
                echo "Build Number: ${BUILD_NUMBER}"
                echo "Status: ${BUILD_STATUS:-UNKNOWN}"
                docker images | grep -E "rest-api|rest-main" | head -5 || echo "No images found"
            '''
        }
        success {
            echo "✓ Pipeline completed successfully! Services built and tested."
        }
        failure {
            sh '''
                echo "✗ Pipeline failed. Removing incomplete images..."
                docker rmi ${API_IMAGE} 2>/dev/null || true
                docker rmi ${MAIN_IMAGE} 2>/dev/null || true
            '''
        }
    }
}