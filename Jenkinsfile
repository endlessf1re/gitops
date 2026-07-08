pipeline {
    agent any

    environment {
        NEXUS_URL = 'http://localhost:5000'
        IMAGE_NAME = 'myapp-flask'
    }

    stages {
        stage('Checkout') {
            steps {
                script { // ← Теперь и checkout, и переменнаяCOMMIT находятся внутри script
                    checkout scm
                    env.COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${IMAGE_NAME}:${COMMIT} ."
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                script {
                    sh "docker tag ${IMAGE_NAME}:${COMMIT} ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}"
                    withCredentials([usernamePassword(
                        credentialsId: 'nexus-creds',
                        usernameVariable: 'NEXUS_USER',
                        passwordVariable: 'NEXUS_PASS'
                    )]) {
                        sh "docker login -u ${NEXUS_USER} -p ${NEXUS_PASS} ${NEXUS_URL}"
                        sh "docker push ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}"
                    }
                }
            }
        }

        stage('Update GitOps') {
            steps {   
                script {
                    sh """
                        rm -rf gitops-tmp
                        git clone git@github.com:endlessfire1/gitops.git gitops-tmp
                        cd gitops-tmp
                        sed -i "s|image: .*|image: ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}|g" apps/myapp/deployment.yaml
                        git config user.name "Jenkins CI"
                        git config user.email "jenkins@local"
                        git add .
                        git commit -m "Update image to ${COMMIT} [skip ci]"
                        git push origin main
                    """
                }
            }
        }
    }

    post {
        always {
            sh "rm -rf gitops-tmp"
        }
    }
}
