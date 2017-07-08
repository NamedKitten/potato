pipeline {
    agent {
        docker {
            image 'pandentia/jenkins-discordpy-rewrite'
	    args  '-u 0'
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
            sh 'pip3 install requests'
        }
        success {
        sh 'python3.5 jenkins.py success $(git --no-pager show -s --format=\'%an\' HEAD~) $(git log --format="%H" -n 1)'
        }
        failure {
        sh 'python3.5 jenkins.py failure $(git --no-pager show -s --format=\'%an\' HEAD~) $(git log --format="%H" -n 1)'
        }
        unstable {
        sh 'python3.5 jenkins.py unstable $(git --no-pager show -s --format=\'%an\' HEAD~) $(git log --format="%H" -n 1)'
        }
    }
}
