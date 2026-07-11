pipeline {
    agent {
        label 'k3d-agent' // Наш настроенный шаблон динамического пода
    }

    environment {
        // Указываем стабильное имя хоста для доступа из контейнера k3d к хосту
        NEXUS_URL = 'host.k3d.internal:5000'
        IMAGE_NAME = 'myapp-flask'
    }

    stages {
        stage('Checkout') {
            steps {
                script { 
                    checkout scm
                    env.COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Сборка образа на хосте через проброшенный docker.sock
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
                    // Оборачиваем в ваш SSH-ключ, чтобы агент имел право пушить в репозиторий GitHub
                    sshagent(['git-key']) {
                        sh """
                            rm -rf gitops-tmp
                            # Явно отключаем проверку хостов для автоматизации клонирования
                            git -c core.sshCommand="ssh -o StrictHostKeyChecking=no" clone git@github.com:endlessfire1/gitops.git gitops-tmp
                            cd gitops-tmp
                            
                            # Обновляем тег образа в манифесте
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
    }

    post {
        always {
            sh "rm -rf gitops-tmp"
        }
    }
}
