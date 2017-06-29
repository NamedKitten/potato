pipeline {
    agent {
        docker {
            image 'chinodesuuu/ci-amethyst'
        }
    }
    environment { 
        WEBHOOK_URL = credentials('WEBHOOK_URL') 
    }
    stages {
        stage('Test') {
            steps {
                sh 'cloc .'
                sh 'flake8 --show-source --max-line-length 120 .'
                sh 'python3 -m compileall .'
            }
        }
    }
    post {
        always {
            sh 'rm -rf * | true'
        }
        success {
        sh 'python jenkins.py successful'
        }
        failure {
        sh 'python jenkins.py successful'
        }
        unstable {
        sh 'python jenkins.py successful'
        }
    }
}
