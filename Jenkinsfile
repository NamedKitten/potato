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
httpRequest contentType: 'APPLICATION_JSON', httpMode: 'POST', requestBody: '{"content": "Pandentia sucks."}', responseHandle: 'NONE', url: 'https://canary.discordapp.com/api/webhooks/292619290090405888/KWmEWBT4FYMVZF2ZmO_7F5DiVXzq9j1PDRKbCv2IuavPYXoG0Qr0Lu0GbX2L7l2Zowio'
        }
    }
}
