pipeline {
    agent {
        docker {
            image 'chinodesuuu/ci-amethyst'
        }
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
            slackSend baseUrl: 'https://canary.discordapp.com/api/webhooks/292619290090405888/KWmEWBT4FYMVZF2ZmO_7F5DiVXzq9j1PDRKbCv2IuavPYXoG0Qr0Lu0GbX2L7l2Zowio/slack', color: '#ffaaff', message: 'beepboop'

        }
    }
}
