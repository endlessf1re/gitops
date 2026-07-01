pipeline {
    agent any

    environment {
        NEXUS_URL = 'http://localhost:5000'
        IMAGE_NAME = 'myapp-flask'
        // Переменная для коммита будет установлена в скрипте
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    // Получаем короткий хеш коммита
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
                    // Тегируем образ для Nexus
                    sh "docker tag ${IMAGE_NAME}:${COMMIT} ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}"

                    // Логин в Nexus через credentials
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
                    // Клонируем gitops-репозиторий через SSH
                    sh """
                        rm -rf gitops-tmp
                        git clone git@github.com:endlessfire1/gitops.git gitops-tmp
                        cd gitops-tmp

                        # Обновляем тег образа в values.yaml (если используем Helm)
                        # Или прямо в deployment.yaml, если без Helm
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
            // Очистка после сборки
            sh "rm -rf gitops-tmp"
        }
    }
}
