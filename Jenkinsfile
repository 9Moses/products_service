pipeline {
    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '10', daysToKeepStr: '30'))
        timestamps()
        timeout(time: 1, unit: 'HOURS')
    }

    stages {
        stage('Build API Service') {
            steps {
                build job: 'service-api', wait: true, propagate: true
            }
        }

        stage('Build Main Service') {
            steps {
                build job: 'service-main', wait: true, propagate: true
            }
        }
    }

    post {
        success {
            echo "All services built and pushed successfully"
        }
        failure {
            echo "One or more services failed — check individual job logs"
        }
    }
}