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
        success {
        sh 'python3.5 jenkins.py success $(git --no-pager show -s --format=\'%an\' HEAD~)'
        }
        failure {
        sh 'python3.5 jenkins.py failure $(git --no-pager show -s --format=\'%an\' HEAD~)'
        }
        unstable {
        sh 'python3.5 jenkins.py unstable $(git --no-pager show -s --format=\'%an\' HEAD~)'
        }
    }
}
