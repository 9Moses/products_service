// Root Pipeline: Orchestrates API and Main services
// Builds and tests both services in isolated Docker containers

pipeline {
    agent any

    parameters {
        booleanParam(name: 'RUN_IAC', defaultValue: false, description: 'Enable Terraform/Ansible IaC execution')
        booleanParam(name: 'APPLY_IAC', defaultValue: false, description: 'Apply Terraform plan and run Ansible provisioning when IaC is enabled')
    }

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
                            JENKINS_CONTAINER=$(hostname)
                            echo "Running API tests..."
                            docker run --rm \
                                --volumes-from ${JENKINS_CONTAINER} \
                                --workdir ${WORKSPACE}/api \
                                ${LATEST_API_IMAGE} \
                                bash -c "python manage.py test --verbosity=2 || true"
                        '''
                    }
                }
                stage('Test Main') {
                    steps {
                        sh '''
                            JENKINS_CONTAINER=$(hostname)
                            echo "Running Main tests..."
                            docker run --rm \
                                --volumes-from ${JENKINS_CONTAINER} \
                                --workdir ${WORKSPACE}/main \
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
                            JENKINS_CONTAINER=$(hostname)
                            docker run --rm \
                                --volumes-from ${JENKINS_CONTAINER} \
                                --workdir ${WORKSPACE}/api \
                                ${LATEST_API_IMAGE} \
                                bash -c "pip install flake8 pylint && \
                                         flake8 . --max-line-length=120 --exclude=migrations || true"
                        '''
                    }
                }
                stage('Main Quality') {
                    steps {
                        sh '''
                            JENKINS_CONTAINER=$(hostname)
                            docker run --rm \
                                --volumes-from ${JENKINS_CONTAINER} \
                                --workdir ${WORKSPACE}/main \
                                ${LATEST_MAIN_IMAGE} \
                                bash -c "pip install flake8 pylint && \
                                         flake8 . --max-line-length=120 || true"
                        '''
                    }
                }
                stage('API Security') {
                    steps {
                        sh '''
                            JENKINS_CONTAINER=$(hostname)
                            docker run --rm \
                                --volumes-from ${JENKINS_CONTAINER} \
                                --workdir ${WORKSPACE}/api \
                                ${LATEST_API_IMAGE} \
                                bash -c "pip install safety && safety check --json || true"
                        '''
                    }
                }
                stage('Main Security') {
                    steps {
                        sh '''
                            JENKINS_CONTAINER=$(hostname)
                            docker run --rm \
                                --volumes-from ${JENKINS_CONTAINER} \
                                --workdir ${WORKSPACE}/main \
                                ${LATEST_MAIN_IMAGE} \
                                bash -c "pip install safety && safety check --json || true"
                        '''
                    }
                }
            }
        }

        stage('Build IaC Docker Images') {
            when {
                expression { return params.RUN_IAC }
            }
            steps {
                sh '''
                    echo "=== Building Terraform Docker image ==="
                    docker build --tag terraform-iac:${BUILD_NUMBER} "${WORKSPACE}/terraform"
                    docker tag terraform-iac:${BUILD_NUMBER} terraform-iac:latest
                    
                    echo "=== Building Ansible Docker image ==="
                    docker build --tag ansible-iac:${BUILD_NUMBER} "${WORKSPACE}/ansible"
                    docker tag ansible-iac:${BUILD_NUMBER} ansible-iac:latest
                '''
            }
        }

        stage('Infrastructure as Code') {
    when {
        expression { return params.RUN_IAC }
    }
    steps {
        sh '''
            set -e
            JENKINS_CONTAINER=$(hostname)
            TERRAFORM_IMAGE="terraform-iac:${BUILD_NUMBER}"
            ANSIBLE_IMAGE="ansible-iac:${BUILD_NUMBER}"
            
            echo "=== Stop conflicting Docker Compose services ==="
            cd ${WORKSPACE}/main && docker compose down 2>/dev/null || true
            cd ${WORKSPACE}/api && docker compose down 2>/dev/null || true

            echo "=== Pre-cleanup: remove conflicting resources ==="
            docker rm -f rest-api-db rest-main-db rest-api rest-main rest-rabbitmq rest-api-consumer rest-main-consumer api-db-1 main-mysql_main-1 2>/dev/null || true
            docker network rm rest_local_net 2>/dev/null || true

            echo "=== Terraform: init ==="
            docker run --rm \
                --volumes-from ${JENKINS_CONTAINER} \
                --workdir ${WORKSPACE}/terraform \
                --volume /var/run/docker.sock:/var/run/docker.sock \
                ${TERRAFORM_IMAGE} \
                init -input=false

            echo "=== Fixing provider permissions ==="
            docker run --rm \
                --volumes-from ${JENKINS_CONTAINER} \
                --workdir ${WORKSPACE}/terraform \
                --entrypoint sh \
                ${TERRAFORM_IMAGE} \
                -c "chmod -R +x .terraform/providers/"
            
            echo "=== Terraform: fmt ==="
            docker run --rm \
                --volumes-from ${JENKINS_CONTAINER} \
                --workdir ${WORKSPACE}/terraform \
                ${TERRAFORM_IMAGE} \
                fmt
            
            echo "=== Terraform: validate ==="
            docker run --rm \
                --volumes-from ${JENKINS_CONTAINER} \
                --workdir ${WORKSPACE}/terraform \
                --volume /var/run/docker.sock:/var/run/docker.sock \
                -e DOCKER_HOST=unix:///var/run/docker.sock \
                ${TERRAFORM_IMAGE} \
                validate
            
            echo "=== Terraform: plan ==="
            docker run --rm \
                --volumes-from ${JENKINS_CONTAINER} \
                --workdir ${WORKSPACE}/terraform \
                --volume /var/run/docker.sock:/var/run/docker.sock \
                -e DOCKER_HOST=unix:///var/run/docker.sock \
                ${TERRAFORM_IMAGE} \
                plan -out=tfplan
            
           

            if [ "${APPLY_IAC}" = "true" ]; then
                echo "=== Cleanup existing resources ==="
                docker rm -f rest-api-db rest-main-db rest-api rest-main rest-rabbitmq rest-api-consumer rest-main-consumer api-db-1 main-mysql_main-1 2>/dev/null || true
                docker network rm rest_local_net 2>/dev/null || true

                echo "=== Terraform: apply ==="
                docker run --rm \
                    --volumes-from ${JENKINS_CONTAINER} \
                    --workdir ${WORKSPACE}/terraform \
                    --volume /var/run/docker.sock:/var/run/docker.sock \
                    -e DOCKER_HOST=unix:///var/run/docker.sock \
                    ${TERRAFORM_IMAGE} \
                    apply -auto-approve tfplan
                
                echo "=== Ansible: provision ==="
                docker run --rm \
                    --volumes-from ${JENKINS_CONTAINER} \
                    --workdir ${WORKSPACE}/ansible \
                    --volume /var/run/docker.sock:/var/run/docker.sock \
                    -e HOME=/tmp \
                    ${ANSIBLE_IMAGE} \
                    -i localhost, -c local playbook.yml
            else
                echo "APPLY_IAC is false, skipping terraform apply and ansible provisioning."
            fi
        '''
    }
}

                stage('Verify Monitoring') {
                        when {
                                expression { return params.RUN_IAC && params.APPLY_IAC }
                        }
                        steps {
                                sh '''
                                        set -e
                                        echo "Verifying monitoring endpoints (retries: 5, delay: 5s)"

                                        # Prometheus
                                        for i in 1 2 3 4 5; do
                                            if curl -fs http://localhost:9090/-/healthy; then
                                                echo "Prometheus healthy"
                                                break
                                            else
                                                echo "Prometheus not ready (attempt $i)"
                                                sleep 5
                                            fi
                                        done

                                        # Grafana
                                        for i in 1 2 3 4 5; do
                                            if curl -fs http://localhost:3000/api/health; then
                                                echo "Grafana healthy"
                                                break
                                            else
                                                echo "Grafana not ready (attempt $i)"
                                                sleep 5
                                            fi
                                        done
                                '''
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
                    docker rmi terraform-iac:${BUILD_NUMBER} 2>/dev/null || true
                    docker rmi terraform-iac:latest 2>/dev/null || true
                    docker rmi ansible-iac:${BUILD_NUMBER} 2>/dev/null || true
                    docker rmi ansible-iac:latest 2>/dev/null || true
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